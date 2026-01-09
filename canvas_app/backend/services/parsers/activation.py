"""
NCI Activation - Transform NCI format into concept_repo and inference_repo.

This module implements the activation phase of the NormCode compilation pipeline:
  NCI (inference groups) → concept_repo.json + inference_repo.json

These output formats are execution-ready for the orchestrator/runner.

Based on: direct_infra_experiment/nc_ai_planning_ex/iteration_9/activate_nci.py
"""

import re
from typing import Dict, Any, List, Optional
from collections import defaultdict


def parse_comment_value(comment: str, key: str) -> Optional[str]:
    """Extract value from a comment like '| %{key}: value'"""
    pattern = rf"\|\s*%{{\s*{re.escape(key)}\s*}}:\s*(.+)"
    match = re.search(pattern, comment)
    if match:
        return match.group(1).strip()
    return None


def parse_inline_comment(comment: str) -> Dict[str, str]:
    """Parse inline comment like '?{flow_index}: 1.1 | ?{sequence}: imperative'"""
    result = {}
    parts = comment.split("|")
    for part in parts:
        match = re.search(r"\?\{(\w+)\}:\s*(.+)", part.strip())
        if match:
            result[match.group(1)] = match.group(2).strip()
    return result


def extract_concept_type_marker(concept_type: str) -> str:
    """Map concept_type to NormCode marker"""
    mapping = {
        "object": "{}",
        "proposition": "<>",
        "relation": "[]",
    }
    return mapping.get(concept_type, "{}")


def extract_operator_marker(operator_type: str) -> str:
    """Map operator_type to assigning marker"""
    mapping = {
        "specification": ".",
        "identity": "=",
        "abstraction": "%",
        "continuation": "+",
        "derelation": "-",
        "timing_conditional": "if",
        "timing_conditional_negated": "if!",
        "timing_after": "after",
    }
    return mapping.get(operator_type, "")


def get_annotation_value(attached_comments: List[Dict], key: str) -> Optional[str]:
    """Extract annotation value from attached comments"""
    for comment in attached_comments:
        if comment.get("type") == "comment":
            nc_comment = comment.get("nc_comment", "")
            value = parse_comment_value(nc_comment, key)
            if value:
                return value
    return None


def get_sequence_type(attached_comments: List[Dict]) -> Optional[str]:
    """Extract sequence type from inline comments"""
    for comment in attached_comments:
        if comment.get("type") == "inline_comment":
            parsed = parse_inline_comment(comment.get("nc_comment", ""))
            if "sequence" in parsed:
                return parsed["sequence"]
    return None


def extract_literal_value(concept_name: str) -> Optional[str]:
    """Extract literal value from concept names like 'phase_name: "phase_1"'"""
    match = re.search(r':\s*["\']([^"\']+)["\']', concept_name)
    if match:
        return match.group(1)
    return None


def is_literal_concept(concept_name: str) -> bool:
    """Check if concept name represents a literal value"""
    return extract_literal_value(concept_name) is not None


def is_ground_concept(concept_data: Dict, attached_comments: List[Dict]) -> bool:
    """Determine if a concept is a ground concept"""
    # Check for /: Ground: comment
    for comment in attached_comments:
        nc_comment = comment.get("nc_comment", "")
        if "/: Ground:" in nc_comment:
            return True
    
    # Check for file_location annotation
    if get_annotation_value(attached_comments, "file_location"):
        return True
    
    # Check for perceptual_sign element type
    element_type = get_annotation_value(attached_comments, "ref_element")
    if element_type == "perceptual_sign":
        return True
    
    # Check for literal concepts
    concept_name = concept_data.get("concept_name", "")
    if is_literal_concept(concept_name):
        return True
    
    return False


def extract_file_location(attached_comments: List[Dict]) -> Optional[str]:
    """Extract file_location from annotations"""
    return get_annotation_value(attached_comments, "file_location")


def parse_axes(axes_str: str) -> List[str]:
    """Parse axes string like '[_none_axis]' or '[date, signal]'"""
    if not axes_str:
        return ["_none_axis"]
    axes_str = axes_str.strip("[]")
    axes = [a.strip() for a in axes_str.split(",")]
    return axes if axes else ["_none_axis"]


def concept_name_to_id(concept_name: str) -> str:
    """Convert concept name to ID"""
    clean = re.sub(r"[{}[\]<>]", "", concept_name)
    clean = clean.strip().lower()
    clean = re.sub(r"\s+", "-", clean)
    clean = re.sub(r"[^a-z0-9-]", "", clean)
    return f"c-{clean}"


def format_concept_name(name: str, concept_type: str) -> str:
    """Format concept name with proper markers"""
    if concept_type == "object":
        return f"{{{name}}}"
    elif concept_type == "proposition":
        return f"<{name}>"
    elif concept_type == "relation":
        return f"[{name}]"
    return f"{{{name}}}"


def build_concept_repo(nci_data: List[Dict]) -> List[Dict]:
    """Build concept repository from NCI data"""
    concepts = {}
    function_concepts = {}
    
    # First pass: collect all concepts
    for inference in nci_data:
        # Process concept_to_infer
        cti = inference.get("concept_to_infer", {})
        if cti and cti.get("concept_name"):
            name = cti["concept_name"]
            concept_type = cti.get("concept_type", "object")
            attached_comments = cti.get("attached_comments", [])
            flow_index = cti.get("flow_index")
            
            if name not in concepts:
                concepts[name] = {
                    "concept_name": name,
                    "concept_type": concept_type,
                    "flow_indices": [],
                    "attached_comments": attached_comments,
                    "is_final": cti.get("inference_marker") == ":<:",
                }
            if flow_index:
                concepts[name]["flow_indices"].append(flow_index)
            if len(attached_comments) > len(concepts[name].get("attached_comments", [])):
                concepts[name]["attached_comments"] = attached_comments
        
        # Process function_concept
        func = inference.get("function_concept", {})
        if func and func.get("nc_main"):
            nc_main = func["nc_main"]
            concept_type = func.get("concept_type", "operator")
            operator_type = func.get("operator_type")
            attached_comments = func.get("attached_comments", [])
            flow_index = func.get("flow_index")
            
            if nc_main not in function_concepts:
                function_concepts[nc_main] = {
                    "nc_main": nc_main,
                    "concept_type": concept_type,
                    "operator_type": operator_type,
                    "flow_indices": [],
                    "attached_comments": attached_comments,
                    "is_functional": True,
                }
            if flow_index:
                function_concepts[nc_main]["flow_indices"].append(flow_index)
        
        # Process value_concepts
        for vc in inference.get("value_concepts", []):
            if vc.get("concept_name"):
                name = vc["concept_name"]
                concept_type = vc.get("concept_type", "object")
                attached_comments = vc.get("attached_comments", [])
                flow_index = vc.get("flow_index")
                
                if name not in concepts:
                    concepts[name] = {
                        "concept_name": name,
                        "concept_type": concept_type,
                        "flow_indices": [],
                        "attached_comments": attached_comments,
                        "is_final": False,
                    }
                if flow_index:
                    concepts[name]["flow_indices"].append(flow_index)
        
        # Process other_concepts
        for oc in inference.get("other_concepts", []):
            if oc.get("concept_name"):
                name = oc["concept_name"]
                concept_type = oc.get("concept_type", "object")
                attached_comments = oc.get("attached_comments", [])
                flow_index = oc.get("flow_index")
                
                if name not in concepts:
                    concepts[name] = {
                        "concept_name": name,
                        "concept_type": concept_type,
                        "flow_indices": [],
                        "attached_comments": attached_comments,
                        "is_final": False,
                    }
                if flow_index:
                    concepts[name]["flow_indices"].append(flow_index)
    
    # Second pass: build concept repo entries for VALUE concepts
    concept_repo = []
    for name, data in concepts.items():
        attached_comments = data.get("attached_comments", [])
        concept_type = data.get("concept_type", "object")
        
        axes_str = get_annotation_value(attached_comments, "ref_axes")
        element_type = get_annotation_value(attached_comments, "ref_element")
        file_location = extract_file_location(attached_comments)
        
        is_ground = is_ground_concept(data, attached_comments)
        
        reference_data = None
        if is_ground:
            if file_location:
                reference_data = [f"%{{file_location}}({file_location})"]
            elif is_literal_concept(name):
                literal_value = extract_literal_value(name)
                if literal_value:
                    reference_data = [literal_value]
        
        concept_entry = {
            "id": concept_name_to_id(name),
            "concept_name": format_concept_name(name, concept_type),
            "type": extract_concept_type_marker(concept_type),
            "flow_indices": sorted(list(set(data["flow_indices"]))),
            "description": None,
            "is_ground_concept": is_ground,
            "is_final_concept": data.get("is_final", False),
            "reference_data": reference_data,
            "reference_axis_names": parse_axes(axes_str),
            "reference_element_type": element_type,
            "natural_name": name,
        }
        concept_repo.append(concept_entry)
    
    # Third pass: build concept repo entries for FUNCTION concepts
    for nc_main, data in function_concepts.items():
        attached_comments = data.get("attached_comments", [])
        operator_type = data.get("operator_type")
        
        if "<{" in nc_main and "}>" in nc_main:
            func_type_marker = "<{}>"
            element_type = "paradigm"
        elif "::" in nc_main:
            func_type_marker = "({})"
            element_type = "paradigm"
        else:
            func_type_marker = "({})"
            element_type = "operator"
        
        natural_name = nc_main
        name_match = re.search(r"::\(([^)]+)\)", nc_main)
        if name_match:
            natural_name = name_match.group(1)
        else:
            name_match = re.search(r"::<\{([^}]+)\}>", nc_main)
            if name_match:
                natural_name = name_match.group(1)
        
        func_id = "fc-" + re.sub(r"[^a-z0-9]+", "-", natural_name.lower()).strip("-")[:50]
        concept_name = re.sub(r"^<=\s*", "", nc_main)
        
        reference_data = None
        if element_type == "paradigm":
            v_input_provision = get_annotation_value(attached_comments, "v_input_provision")
            
            if v_input_provision:
                if v_input_provision.endswith(".md"):
                    norm = "prompt_location"
                elif v_input_provision.endswith(".py"):
                    norm = "script_location"
                else:
                    norm = "file_location"
                
                import random
                hex_id = ''.join(random.choices('0123456789abcdef', k=3))
                reference_data = [f"%{{{norm}}}{hex_id}({v_input_provision})"]
            else:
                reference_data = ["%{dummy}(_)"]
        
        concept_entry = {
            "id": func_id,
            "concept_name": concept_name,
            "type": func_type_marker,
            "flow_indices": sorted(list(set(data["flow_indices"]))),
            "description": natural_name,
            "is_ground_concept": True,
            "is_final_concept": False,
            "reference_data": reference_data,
            "reference_axis_names": ["_none_axis"],
            "reference_element_type": element_type,
            "natural_name": natural_name,
        }
        concept_repo.append(concept_entry)
    
    # Sort by first flow_index
    def flow_sort_key(x):
        if not x["flow_indices"]:
            return [999]
        idx = x["flow_indices"][0]
        return [int(p) for p in idx.split(".")]
    
    concept_repo.sort(key=flow_sort_key)
    return concept_repo


def infer_sequence_type_from_nc_main(nc_main: str, concept_data: Dict) -> Optional[str]:
    """Infer sequence type from nc_main pattern"""
    if "::<{" in nc_main and "}>" in nc_main:
        return "judgement"
    if "&[{}]" in nc_main or "&[#]" in nc_main:
        return "grouping"
    if "*." in nc_main and "%>" in nc_main:
        return "looping"
    if re.match(r"(<=\s*)?\$[.=%+-]", nc_main):
        return "assigning"
    if "@:'" in nc_main or "@:!" in nc_main or "@." in nc_main:
        return "timing"
    if concept_data.get("operator_type"):
        op_type = concept_data["operator_type"]
        if "timing" in op_type:
            return "timing"
        if op_type in ["specification", "identity", "abstraction", "continuation", "derelation"]:
            return "assigning"
    if "::" in nc_main and "::<{" not in nc_main:
        return "imperative"
    if concept_data.get("concept_type") == "imperative":
        return "imperative"
    return None


def build_working_interpretation(inference: Dict, sequence_type: str) -> Dict:
    """Build working_interpretation based on sequence type"""
    func_concept = inference.get("function_concept", {})
    cti = inference.get("concept_to_infer", {})
    value_concepts = inference.get("value_concepts", [])
    other_concepts = inference.get("other_concepts", [])
    
    func_comments = func_concept.get("attached_comments", [])
    cti_flow_index = cti.get("flow_index", "")
    
    wi: Dict[str, Any] = {
        "workspace": {},
        "flow_info": {"flow_index": cti_flow_index}
    }
    
    if sequence_type == "imperative":
        paradigm = get_annotation_value(func_comments, "norm_input")
        body_faculty = get_annotation_value(func_comments, "body_faculty")
        
        value_order = {}
        has_any_binding = any(re.search(r"<:\{(\d+)\}>", vc.get("nc_main", "")) for vc in value_concepts)
        
        for i, vc in enumerate(value_concepts):
            vc_name = vc.get("concept_name")
            if vc_name:
                nc_main = vc.get("nc_main", "")
                binding_match = re.search(r"<:\{(\d+)\}>", nc_main)
                if binding_match:
                    value_order[format_concept_name(vc_name, vc.get("concept_type", "object"))] = int(binding_match.group(1))
                elif not has_any_binding:
                    value_order[format_concept_name(vc_name, vc.get("concept_type", "object"))] = i + 1
        
        wi["paradigm"] = paradigm
        wi["body_faculty"] = body_faculty
        wi["value_order"] = value_order
    
    elif sequence_type == "judgement":
        paradigm = get_annotation_value(func_comments, "norm_input")
        body_faculty = get_annotation_value(func_comments, "body_faculty")
        
        value_order = {}
        has_any_binding = any(re.search(r"<:\{(\d+)\}>", vc.get("nc_main", "")) for vc in value_concepts)
        
        for i, vc in enumerate(value_concepts):
            vc_name = vc.get("concept_name")
            if vc_name:
                nc_main = vc.get("nc_main", "")
                binding_match = re.search(r"<:\{(\d+)\}>", nc_main)
                if binding_match:
                    value_order[format_concept_name(vc_name, vc.get("concept_type", "object"))] = int(binding_match.group(1))
                elif not has_any_binding:
                    value_order[format_concept_name(vc_name, vc.get("concept_type", "object"))] = i + 1
        
        wi["paradigm"] = paradigm
        wi["body_faculty"] = body_faculty
        wi["value_order"] = value_order
        
        nc_main = func_concept.get("nc_main", "")
        if "<ALL True>" in nc_main:
            wi["assertion_condition"] = {
                "quantifiers": {"axis": "all"},
                "condition": True
            }
    
    elif sequence_type == "assigning":
        operator_type = func_concept.get("operator_type", "specification")
        nc_main = func_concept.get("nc_main", "")
        marker = extract_operator_marker(operator_type)
        
        assign_source = None
        
        if marker == ".":
            candidate_sources = []
            for vc in value_concepts:
                vc_name = vc.get("concept_name")
                vc_type = vc.get("concept_type", "object")
                if vc_name and vc_type != "proposition":
                    candidate_sources.append(format_concept_name(vc_name, vc_type))
            
            if len(candidate_sources) >= 2:
                assign_source = candidate_sources
            elif len(candidate_sources) == 1:
                assign_source = candidate_sources[0]
        else:
            source_match = re.search(r"%>\(\{([^}]+)\}\)", nc_main)
            source_match_list = re.search(r"%>\[([^\]]+)\]", nc_main)
            
            if source_match:
                assign_source = f"{{{source_match.group(1)}}}"
            elif source_match_list:
                assign_source = source_match_list.group(1)
        
        wi["syntax"] = {
            "marker": marker,
            "assign_source": assign_source,
        }
    
    elif sequence_type == "grouping":
        nc_main = func_concept.get("nc_main", "")
        
        if "&[{}]" in nc_main:
            marker = "in"
        elif "&[#]" in nc_main:
            marker = "across"
        else:
            marker = "in"
        
        create_axis_match = re.search(r"%\+\(([^)]+)\)", nc_main)
        create_axis = create_axis_match.group(1) if create_axis_match else None
        
        sources_section_match = re.search(r"%>\[(.+)\]", nc_main)
        sources = []
        if sources_section_match:
            sources_text = sources_section_match.group(1)
            current = ""
            depth = 0
            for char in sources_text:
                if char in "{[<":
                    depth += 1
                    current += char
                elif char in "}]>":
                    depth -= 1
                    current += char
                elif char == "," and depth == 0:
                    if current.strip():
                        sources.append(current.strip())
                    current = ""
                else:
                    current += char
            if current.strip():
                sources.append(current.strip())
        
        wi["syntax"] = {
            "marker": marker,
            "sources": sources,
            "create_axis": create_axis,
        }
    
    elif sequence_type == "timing":
        nc_main = func_concept.get("nc_main", "")
        
        if "@:!" in nc_main:
            marker = "if!"
        elif "@:'" in nc_main:
            marker = "if"
        elif "@." in nc_main:
            marker = "after"
        else:
            marker = "if"
        
        condition_match = re.search(r"@[:'!\.]+\s*\(<?([^>)]+)>?\)", nc_main)
        condition = condition_match.group(1) if condition_match else None
        
        wi["syntax"] = {
            "marker": marker,
            "condition": f"<{condition}>" if condition else None,
        }
        wi["blackboard"] = None
    
    elif sequence_type == "looping":
        nc_main = func_concept.get("nc_main", "")
        
        base_match = re.search(r"%>\(\[?([^\])\]]+)\]?\)", nc_main)
        result_match = re.search(r"%<\(\{([^}]+)\}\)", nc_main)
        axis_match = re.search(r"%:\(\{([^}]+)\}\)", nc_main)
        index_match = re.search(r"%@\((\d+)\)", nc_main)
        
        current_element = None
        for oc in other_concepts:
            if oc.get("inference_marker") == "<*":
                current_element = oc.get("concept_name")
                break
        
        wi["syntax"] = {
            "marker": "every",
            "loop_index": int(index_match.group(1)) if index_match else 1,
            "LoopBaseConcept": f"[{base_match.group(1)}]" if base_match else None,
            "CurrentLoopBaseConcept": f"{{{current_element}}}*1" if current_element else None,
            "group_base": axis_match.group(1) if axis_match else None,
            "ConceptToInfer": [f"{{{result_match.group(1)}}}"] if result_match else [],
        }
    
    return wi


def build_nested_operator_inference(oc: Dict) -> Optional[Dict]:
    """Build an inference entry from a nested operator in other_concepts."""
    nc_main = oc.get("nc_main", "")
    flow_index = oc.get("flow_index", "")
    
    sequence_type = infer_sequence_type_from_nc_main(nc_main, oc)
    if not sequence_type:
        return None
    
    func_concept_name = re.sub(r"^<=\s*", "", nc_main)
    
    concept_to_infer = None
    if sequence_type == "assigning":
        source_match = re.search(r"%>\(\{([^}]+)\}\)", nc_main)
        source_match_list = re.search(r"%>\(\[([^\]]+)\]\)", nc_main)
        if source_match:
            concept_to_infer = f"{{{source_match.group(1)}}}"
        elif source_match_list:
            concept_to_infer = f"[{source_match_list.group(1)}]"
        else:
            concept_to_infer = f"{{assigning_{flow_index.replace('.', '_')}}}"
    elif sequence_type == "timing":
        concept_to_infer = func_concept_name
    else:
        concept_to_infer = func_concept_name
    
    wi: Dict[str, Any] = {
        "workspace": {},
        "flow_info": {"flow_index": flow_index}
    }
    
    if sequence_type == "assigning":
        operator_type = oc.get("operator_type", "specification")
        marker = extract_operator_marker(operator_type)
        
        assign_source = None
        source_match = re.search(r"%>\(\{([^}]+)\}\)", nc_main)
        if source_match:
            assign_source = f"{{{source_match.group(1)}}}"
        
        wi["syntax"] = {
            "marker": marker,
            "assign_source": assign_source,
        }
    
    sequence_mapping = {
        "imperative": "imperative_in_composition",
        "judgement": "judgement_in_composition",
        "assigning": "assigning",
        "grouping": "grouping",
        "timing": "timing",
        "looping": "looping",
    }
    
    return {
        "flow_info": {"flow_index": flow_index},
        "inference_sequence": sequence_mapping.get(sequence_type, sequence_type),
        "concept_to_infer": concept_to_infer,
        "function_concept": func_concept_name,
        "value_concepts": [],
        "context_concepts": [],
        "working_interpretation": wi,
    }


def build_inference_repo(nci_data: List[Dict]) -> List[Dict]:
    """Build inference repository from NCI data"""
    inference_repo = []
    
    for inference in nci_data:
        cti = inference.get("concept_to_infer", {})
        func_concept = inference.get("function_concept", {})
        value_concepts = inference.get("value_concepts", [])
        other_concepts = inference.get("other_concepts", [])
        
        if not func_concept:
            continue
        
        func_comments = func_concept.get("attached_comments", [])
        sequence_type = get_sequence_type(func_comments)
        
        if not sequence_type:
            nc_main = func_concept.get("nc_main", "")
            sequence_type = infer_sequence_type_from_nc_main(nc_main, func_concept)
        
        if not sequence_type:
            continue
        
        cti_name = cti.get("concept_name")
        cti_type = cti.get("concept_type", "object")
        cti_nc_main = cti.get("nc_main", "")
        
        if cti_type in ["imperative", "judgement", "operator"]:
            concept_to_infer = re.sub(r"^<=\s*", "", cti_nc_main) if cti_nc_main else None
        else:
            concept_to_infer = format_concept_name(cti_name, cti_type) if cti_name else None
        
        if concept_to_infer is None:
            func_nc_main = func_concept.get("nc_main", "")
            
            if sequence_type == "assigning":
                source_match = re.search(r"%>\(\{([^}]+)\}\)", func_nc_main)
                source_match_list = re.search(r"%>\[\{([^}]+)\}", func_nc_main)
                if source_match:
                    concept_to_infer = f"{{{source_match.group(1)}}}"
                elif source_match_list:
                    concept_to_infer = f"{{{source_match_list.group(1)}}}"
                else:
                    flow_idx = func_concept.get("flow_index", "unknown")
                    concept_to_infer = f"{{assigning_{flow_idx.replace('.', '_')}}}"
            elif sequence_type == "timing":
                func_nc_main_stripped = re.sub(r"^<=\s*", "", func_nc_main)
                concept_to_infer = func_nc_main_stripped
        
        func_nc_main = func_concept.get("nc_main", "")
        func_concept_name = re.sub(r"^<=\s*", "", func_nc_main)
        
        vc_list = []
        for vc in value_concepts:
            vc_name = vc.get("concept_name")
            if vc_name:
                vc_list.append(format_concept_name(vc_name, vc.get("concept_type", "object")))
        
        ctx_list = []
        for oc in other_concepts:
            if oc.get("inference_marker") == "<*":
                oc_name = oc.get("concept_name")
                if oc_name:
                    ctx_list.append(format_concept_name(oc_name, oc.get("concept_type", "object")))
        
        if sequence_type == "timing" and ctx_list:
            vc_list.extend(ctx_list)
        
        wi = build_working_interpretation(inference, sequence_type)
        
        sequence_mapping = {
            "imperative": "imperative_in_composition",
            "judgement": "judgement_in_composition",
            "assigning": "assigning",
            "grouping": "grouping",
            "timing": "timing",
            "looping": "looping",
        }
        
        cti_flow_index = cti.get("flow_index", func_concept.get("flow_index", ""))
        
        inference_entry = {
            "flow_info": {"flow_index": cti_flow_index},
            "inference_sequence": sequence_mapping.get(sequence_type, sequence_type),
            "concept_to_infer": concept_to_infer,
            "function_concept": func_concept_name,
            "value_concepts": vc_list,
            "context_concepts": ctx_list,
            "working_interpretation": wi,
        }
        
        inference_repo.append(inference_entry)
        
        # Process nested operators
        for oc in other_concepts:
            if oc.get("inference_marker") == "<=":
                nested_inf = build_nested_operator_inference(oc)
                if nested_inf:
                    inference_repo.append(nested_inf)
    
    # Sort by flow_index
    def flow_index_sort_key(item):
        idx = item.get("flow_info", {}).get("flow_index", "999")
        parts = idx.split(".")
        return [int(p) for p in parts]
    
    inference_repo.sort(key=flow_index_sort_key)
    return inference_repo


def generate_activation_warnings(
    nci_data: List[Dict],
    concept_repo: List[Dict],
    inference_repo: List[Dict]
) -> List[Dict[str, Any]]:
    """
    Generate warnings about potential issues in the activated repos.
    
    Returns:
        List of warning dicts with 'level', 'code', 'message', and optional 'details'
    """
    warnings = []
    
    # Track which NCI entries became inferences
    nci_flow_indices = set()
    for nci in nci_data:
        cti = nci.get("concept_to_infer", {})
        if cti.get("flow_index"):
            nci_flow_indices.add(cti["flow_index"])
    
    inf_flow_indices = set()
    for inf in inference_repo:
        fi = inf.get("flow_info", {}).get("flow_index")
        if fi:
            inf_flow_indices.add(fi)
    
    # WARNING: Skipped inferences (NCI entries that didn't become inferences)
    skipped = nci_flow_indices - inf_flow_indices
    for fi in sorted(skipped, key=lambda x: [int(p) for p in x.split(".")]):
        # Find the NCI entry
        nci_entry = None
        for nci in nci_data:
            if nci.get("concept_to_infer", {}).get("flow_index") == fi:
                nci_entry = nci
                break
        
        if nci_entry:
            func = nci_entry.get("function_concept", {})
            nc_main = func.get("nc_main", "")[:50]
            warnings.append({
                "level": "warning",
                "code": "SKIPPED_INFERENCE",
                "message": f"Inference at {fi} was skipped (no sequence type detected)",
                "details": {
                    "flow_index": fi,
                    "function_nc_main": nc_main,
                    "hint": "Add | ?{sequence}: <type> annotation to the function concept"
                }
            })
    
    # WARNING: Bundled values from grouping operations
    grouping_outputs = []
    for inf in inference_repo:
        if inf["inference_sequence"] == "grouping":
            cti = inf["concept_to_infer"]
            fi = inf["flow_info"]["flow_index"]
            grouping_outputs.append({"concept": cti, "flow_index": fi})
    
    if grouping_outputs:
        # Check if any of these are used as value_concepts elsewhere
        for g in grouping_outputs:
            for inf in inference_repo:
                if g["concept"] in inf.get("value_concepts", []):
                    warnings.append({
                        "level": "critical",
                        "code": "BUNDLED_VALUE_INPUT",
                        "message": f"Bundled value '{g['concept']}' used as input without 'packed: true'",
                        "details": {
                            "source_flow_index": g["flow_index"],
                            "used_in_flow_index": inf["flow_info"]["flow_index"],
                            "concept": g["concept"],
                            "fix": f'Add to working_interpretation: "value_selectors": {{"{g["concept"]}": {{"packed": true}}}}'
                        }
                    })
    
    # WARNING: Missing paradigm annotations for imperatives/judgements
    for inf in inference_repo:
        seq = inf["inference_sequence"]
        if seq in ["imperative_in_composition", "judgement_in_composition"]:
            wi = inf.get("working_interpretation", {})
            if not wi.get("paradigm"):
                warnings.append({
                    "level": "warning",
                    "code": "MISSING_PARADIGM",
                    "message": f"Inference at {inf['flow_info']['flow_index']} has no paradigm annotation",
                    "details": {
                        "flow_index": inf["flow_info"]["flow_index"],
                        "concept_to_infer": inf["concept_to_infer"],
                        "hint": "Add | %{norm_input}: paradigm_name.json annotation"
                    }
                })
    
    # WARNING: Missing body_faculty for imperatives
    for inf in inference_repo:
        seq = inf["inference_sequence"]
        if seq in ["imperative_in_composition", "judgement_in_composition"]:
            wi = inf.get("working_interpretation", {})
            if wi.get("paradigm") and not wi.get("body_faculty"):
                warnings.append({
                    "level": "info",
                    "code": "MISSING_BODY_FACULTY",
                    "message": f"Inference at {inf['flow_info']['flow_index']} has paradigm but no body_faculty",
                    "details": {
                        "flow_index": inf["flow_info"]["flow_index"],
                        "paradigm": wi.get("paradigm"),
                        "hint": "Add | %{body_faculty}: llm/file_system/python_interpreter"
                    }
                })
    
    # WARNING: No final concepts
    final_concepts = [c for c in concept_repo if c["is_final_concept"]]
    if not final_concepts:
        warnings.append({
            "level": "info",
            "code": "NO_FINAL_CONCEPTS",
            "message": "No final concepts found (no :<: markers)",
            "details": {
                "hint": "Mark output concepts with :<: marker for explicit outputs"
            }
        })
    
    # WARNING: No ground concepts
    ground_concepts = [c for c in concept_repo if c["is_ground_concept"]]
    if not ground_concepts:
        warnings.append({
            "level": "warning",
            "code": "NO_GROUND_CONCEPTS",
            "message": "No ground concepts found (no inputs defined)",
            "details": {
                "hint": "Add /: Ground: comments or file_location annotations for inputs"
            }
        })
    
    return warnings


def activate_nci(nci_data: List[Dict]) -> Dict[str, Any]:
    """
    Activate NCI data into concept_repo and inference_repo.
    
    Args:
        nci_data: List of inference groups from NCI format
        
    Returns:
        Dict with:
        - concept_repo: List of concept entries
        - inference_repo: List of inference entries
        - summary: Statistics about the activation
        - warnings: List of warnings about potential issues
    """
    concept_repo = build_concept_repo(nci_data)
    inference_repo = build_inference_repo(nci_data)
    
    # Generate warnings
    warnings = generate_activation_warnings(nci_data, concept_repo, inference_repo)
    
    # Build summary
    value_concepts = [c for c in concept_repo if c["type"] in ["{}", "[]", "<>"]]
    func_concepts = [c for c in concept_repo if c["type"] in ["({})", "<{}>"]]
    ground_concepts = [c for c in concept_repo if c["is_ground_concept"]]
    final_concepts = [c for c in concept_repo if c["is_final_concept"]]
    
    seq_counts = defaultdict(int)
    for inf in inference_repo:
        seq_counts[inf["inference_sequence"]] += 1
    
    # Count warnings by level
    warning_counts = defaultdict(int)
    for w in warnings:
        warning_counts[w["level"]] += 1
    
    summary = {
        "total_concepts": len(concept_repo),
        "value_concepts": len(value_concepts),
        "function_concepts": len(func_concepts),
        "ground_concepts": len(ground_concepts),
        "final_concepts": len(final_concepts),
        "total_inferences": len(inference_repo),
        "inference_sequences": dict(seq_counts),
        "warning_counts": dict(warning_counts),
    }
    
    return {
        "concept_repo": concept_repo,
        "inference_repo": inference_repo,
        "summary": summary,
        "warnings": warnings,
    }


def format_warnings(warnings: List[Dict[str, Any]], use_colors: bool = True) -> str:
    """
    Format warnings as a human-readable string.
    
    Args:
        warnings: List of warning dicts from activate_nci
        use_colors: Whether to use ANSI color codes
        
    Returns:
        Formatted string with all warnings
    """
    if not warnings:
        return "[OK] No warnings\n"
    
    # ANSI colors
    if use_colors:
        RESET = "\033[0m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        BOLD = "\033[1m"
    else:
        RESET = RED = YELLOW = CYAN = BOLD = ""
    
    level_colors = {
        "critical": RED,
        "warning": YELLOW,
        "info": CYAN,
    }
    
    level_icons = {
        "critical": "[!]",
        "warning": "[*]", 
        "info": "[i]",
    }
    
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"{BOLD}ACTIVATION WARNINGS ({len(warnings)} total){RESET}")
    lines.append(f"{'='*60}\n")
    
    # Group by level
    by_level = defaultdict(list)
    for w in warnings:
        by_level[w["level"]].append(w)
    
    for level in ["critical", "warning", "info"]:
        level_warnings = by_level.get(level, [])
        if not level_warnings:
            continue
        
        color = level_colors.get(level, "")
        icon = level_icons.get(level, "")
        
        lines.append(f"{color}{BOLD}[{level.upper()}] ({len(level_warnings)}){RESET}")
        lines.append("-" * 40)
        
        for w in level_warnings:
            lines.append(f"{color}{icon} [{w['code']}]{RESET}")
            lines.append(f"   {w['message']}")
            
            if "details" in w:
                details = w["details"]
                if "flow_index" in details:
                    lines.append(f"   Flow: {details['flow_index']}")
                if "hint" in details:
                    lines.append(f"   Hint: {details['hint']}")
                if "fix" in details:
                    lines.append(f"   Fix: {details['fix']}")
            lines.append("")
        
        lines.append("")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)


def print_warnings(warnings: List[Dict[str, Any]], use_colors: bool = True) -> None:
    """Print warnings to stdout."""
    print(format_warnings(warnings, use_colors))

