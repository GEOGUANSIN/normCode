"""
Activation Script: Transform .pf.nci.json → concept_repo.json + inference_repo.json

This script implements Phase 4 (Activation) of the NormCode compilation pipeline.
"""

import json
import re
from pathlib import Path
from collections import defaultdict


def parse_comment_value(comment: str, key: str) -> str | None:
    """Extract value from a comment like '| %{key}: value'"""
    pattern = rf"\|\s*%{{\s*{re.escape(key)}\s*}}:\s*(.+)"
    match = re.search(pattern, comment)
    if match:
        return match.group(1).strip()
    return None


def parse_inline_comment(comment: str) -> dict:
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


def get_annotation_value(attached_comments: list, key: str) -> str | None:
    """Extract annotation value from attached comments"""
    for comment in attached_comments:
        if comment.get("type") == "comment":
            nc_comment = comment.get("nc_comment", "")
            value = parse_comment_value(nc_comment, key)
            if value:
                return value
    return None


def get_sequence_type(attached_comments: list) -> str | None:
    """Extract sequence type from inline comments"""
    for comment in attached_comments:
        if comment.get("type") == "inline_comment":
            parsed = parse_inline_comment(comment.get("nc_comment", ""))
            if "sequence" in parsed:
                return parsed["sequence"]
    return None


def is_ground_concept(concept_data: dict, attached_comments: list) -> bool:
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
    
    return False


def extract_file_location(attached_comments: list) -> str | None:
    """Extract file_location from annotations"""
    return get_annotation_value(attached_comments, "file_location")


def parse_axes(axes_str: str) -> list:
    """Parse axes string like '[_none_axis]' or '[date, signal]'"""
    if not axes_str:
        return ["_none_axis"]
    # Remove brackets and split
    axes_str = axes_str.strip("[]")
    axes = [a.strip() for a in axes_str.split(",")]
    return axes if axes else ["_none_axis"]


def concept_name_to_id(concept_name: str) -> str:
    """Convert concept name to ID"""
    # Remove special characters and normalize
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


def build_concept_repo(nci_data: list) -> list:
    """Build concept repository from NCI data"""
    concepts = {}  # concept_name -> concept_data
    function_concepts = {}  # function_concept nc_main -> function_concept_data
    
    # First pass: collect all concepts and their flow indices
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
            # Merge comments if they have more annotations
            if len(attached_comments) > len(concepts[name].get("attached_comments", [])):
                concepts[name]["attached_comments"] = attached_comments
        
        # Process function_concept (NEW: add function concepts to repo)
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
        
        # Process other_concepts (context concepts)
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
        
        # Extract annotations
        axes_str = get_annotation_value(attached_comments, "ref_axes")
        element_type = get_annotation_value(attached_comments, "ref_element")
        shape_str = get_annotation_value(attached_comments, "ref_shape")
        file_location = extract_file_location(attached_comments)
        
        is_ground = is_ground_concept(data, attached_comments)
        
        # Build reference_data for ground concepts
        reference_data = None
        if is_ground and file_location:
            reference_data = [f"%{{file_location}}({file_location})"]
        
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
        concept_type = data.get("concept_type", "operator")
        
        # Determine function concept type marker
        if "<{" in nc_main and "}>" in nc_main:
            # Judgement
            func_type_marker = "<{}>"
            element_type = "paradigm"
        elif "::" in nc_main:
            # Imperative
            func_type_marker = "({})"
            element_type = "paradigm"
        else:
            # Operator (assigning, grouping, timing, looping)
            func_type_marker = "({})"
            element_type = "operator"
        
        # Generate natural name from nc_main
        natural_name = nc_main
        # Try to extract a cleaner name
        name_match = re.search(r"::\(([^)]+)\)", nc_main)
        if name_match:
            natural_name = name_match.group(1)
        else:
            name_match = re.search(r"::<\{([^}]+)\}>", nc_main)
            if name_match:
                natural_name = name_match.group(1)
        
        # Generate unique ID
        func_id = "fc-" + re.sub(r"[^a-z0-9]+", "-", natural_name.lower()).strip("-")[:50]
        
        concept_entry = {
            "id": func_id,
            "concept_name": nc_main,
            "type": func_type_marker,
            "flow_indices": sorted(list(set(data["flow_indices"]))),
            "description": natural_name,
            "is_ground_concept": False,
            "is_final_concept": False,
            "reference_data": None,
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


def build_working_interpretation(inference: dict, sequence_type: str) -> dict:
    """Build working_interpretation based on sequence type"""
    func_concept = inference.get("function_concept", {})
    cti = inference.get("concept_to_infer", {})
    value_concepts = inference.get("value_concepts", [])
    other_concepts = inference.get("other_concepts", [])
    
    func_comments = func_concept.get("attached_comments", [])
    cti_flow_index = cti.get("flow_index", "")
    
    # Common fields
    wi = {
        "workspace": {},
        "flow_info": {"flow_index": cti_flow_index}
    }
    
    if sequence_type == "imperative":
        # Extract paradigm from norm_input
        paradigm = get_annotation_value(func_comments, "norm_input")
        body_faculty = get_annotation_value(func_comments, "body_faculty")
        v_input_provision = get_annotation_value(func_comments, "v_input_provision")
        
        # Build value_order from value concepts
        value_order = {}
        for i, vc in enumerate(value_concepts):
            vc_name = vc.get("concept_name")
            if vc_name:
                # Check for explicit binding like <:{1}>
                nc_main = vc.get("nc_main", "")
                binding_match = re.search(r"<:\{(\d+)\}>", nc_main)
                if binding_match:
                    value_order[format_concept_name(vc_name, vc.get("concept_type", "object"))] = int(binding_match.group(1))
                else:
                    value_order[format_concept_name(vc_name, vc.get("concept_type", "object"))] = i + 1
        
        wi["paradigm"] = paradigm
        wi["body_faculty"] = body_faculty
        wi["value_order"] = value_order
        if v_input_provision:
            wi["prompt_path"] = v_input_provision
    
    elif sequence_type == "judgement":
        # Same as imperative plus assertion_condition
        paradigm = get_annotation_value(func_comments, "norm_input")
        body_faculty = get_annotation_value(func_comments, "body_faculty")
        v_input_provision = get_annotation_value(func_comments, "v_input_provision")
        
        value_order = {}
        for i, vc in enumerate(value_concepts):
            vc_name = vc.get("concept_name")
            if vc_name:
                nc_main = vc.get("nc_main", "")
                binding_match = re.search(r"<:\{(\d+)\}>", nc_main)
                if binding_match:
                    value_order[format_concept_name(vc_name, vc.get("concept_type", "object"))] = int(binding_match.group(1))
                else:
                    value_order[format_concept_name(vc_name, vc.get("concept_type", "object"))] = i + 1
        
        wi["paradigm"] = paradigm
        wi["body_faculty"] = body_faculty
        wi["value_order"] = value_order
        if v_input_provision:
            wi["prompt_path"] = v_input_provision
        
        # Extract assertion from function concept
        nc_main = func_concept.get("nc_main", "")
        if "<ALL True>" in nc_main:
            wi["assertion_condition"] = {
                "quantifiers": {"axis": "all"},
                "condition": True
            }
    
    elif sequence_type == "assigning":
        operator_type = func_concept.get("operator_type", "specification")
        nc_main = func_concept.get("nc_main", "")
        
        # Extract source from %>({...})
        source_match = re.search(r"%>\(\{([^}]+)\}\)", nc_main)
        source_match_list = re.search(r"%>\[([^\]]+)\]", nc_main)
        
        assign_source = None
        if source_match:
            assign_source = f"{{{source_match.group(1)}}}"
        elif source_match_list:
            # Multiple sources
            assign_source = source_match_list.group(1)
        
        wi["syntax"] = {
            "marker": extract_operator_marker(operator_type),
            "assign_source": assign_source,
        }
    
    elif sequence_type == "grouping":
        nc_main = func_concept.get("nc_main", "")
        
        # Determine marker: &[{}] = in, &[#] = across
        if "&[{}]" in nc_main:
            marker = "in"
        elif "&[#]" in nc_main:
            marker = "across"
        else:
            marker = "in"
        
        # Extract create_axis from %+(...)
        create_axis_match = re.search(r"%\+\(([^)]+)\)", nc_main)
        create_axis = create_axis_match.group(1) if create_axis_match else None
        
        # Extract sources from %>[...] - handle nested brackets in concept names
        # Pattern: %>[{...}, [...], ...] where items can have internal brackets
        sources_section_match = re.search(r"%>\[(.+)\]", nc_main)
        sources = []
        if sources_section_match:
            sources_text = sources_section_match.group(1)
            # Parse by tracking bracket depth
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
        operator_type = func_concept.get("operator_type", "timing_conditional")
        nc_main = func_concept.get("nc_main", "")
        
        # Determine marker
        if "@:!" in nc_main:
            marker = "if!"
        elif "@:'" in nc_main:
            marker = "if"
        elif "@." in nc_main:
            marker = "after"
        else:
            marker = "if"
        
        # Extract condition
        condition_match = re.search(r"@[:'!\.]+\s*\(<?([^>)]+)>?\)", nc_main)
        condition = condition_match.group(1) if condition_match else None
        
        wi["syntax"] = {
            "marker": marker,
            "condition": f"<{condition}>" if condition else None,
        }
        wi["blackboard"] = None
    
    elif sequence_type == "looping":
        nc_main = func_concept.get("nc_main", "")
        
        # Extract components from *. %>(...) %<(...) %:(...) %@(...)
        base_match = re.search(r"%>\(\[?([^\])\]]+)\]?\)", nc_main)
        result_match = re.search(r"%<\(\{([^}]+)\}\)", nc_main)
        axis_match = re.search(r"%:\(\{([^}]+)\}\)", nc_main)
        index_match = re.search(r"%@\((\d+)\)", nc_main)
        
        # Get context concept (current element)
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


def build_inference_repo(nci_data: list) -> list:
    """Build inference repository from NCI data"""
    inference_repo = []
    
    for inference in nci_data:
        cti = inference.get("concept_to_infer", {})
        func_concept = inference.get("function_concept", {})
        value_concepts = inference.get("value_concepts", [])
        other_concepts = inference.get("other_concepts", [])
        
        if not func_concept:
            continue
        
        # Get sequence type
        func_comments = func_concept.get("attached_comments", [])
        sequence_type = get_sequence_type(func_comments)
        
        if not sequence_type:
            # Try to infer from operator_type or concept_type
            if func_concept.get("operator_type"):
                op_type = func_concept["operator_type"]
                if "timing" in op_type:
                    sequence_type = "timing"
                elif op_type in ["specification", "identity", "abstraction", "continuation", "derelation"]:
                    sequence_type = "assigning"
            elif func_concept.get("concept_type") == "imperative":
                sequence_type = "imperative"
        
        if not sequence_type:
            continue
        
        # Build concept_to_infer name
        cti_name = cti.get("concept_name")
        cti_type = cti.get("concept_type", "object")
        concept_to_infer = format_concept_name(cti_name, cti_type) if cti_name else None
        
        # Handle null concept_to_infer for specific sequence types
        if concept_to_infer is None:
            func_nc_main = func_concept.get("nc_main", "")
            
            if sequence_type == "assigning":
                # For assigning (e.g., $. %>({x})), derive from the source
                source_match = re.search(r"%>\(\{([^}]+)\}\)", func_nc_main)
                source_match_list = re.search(r"%>\[\{([^}]+)\}", func_nc_main)
                if source_match:
                    concept_to_infer = f"{{{source_match.group(1)}}}"
                elif source_match_list:
                    concept_to_infer = f"{{{source_match_list.group(1)}}}"
                else:
                    # Fallback: use flow_index as synthetic name
                    flow_idx = func_concept.get("flow_index", "unknown")
                    concept_to_infer = f"{{assigning_{flow_idx.replace('.', '_')}}}"
            
            elif sequence_type == "timing":
                # For timing, derive from the parent function concept it's attached to
                # Extract the action name from the timing target
                condition_match = re.search(r"@[:'!\.]+\s*\(<?([^>)]+)>?\)", func_nc_main)
                if condition_match:
                    # Create a synthetic name based on the condition
                    cond_name = condition_match.group(1).replace(" ", "_")
                    flow_idx = func_concept.get("flow_index", "unknown")
                    concept_to_infer = f"{{timing_gate_{cond_name}}}"
                else:
                    flow_idx = func_concept.get("flow_index", "unknown")
                    concept_to_infer = f"{{timing_{flow_idx.replace('.', '_')}}}"
        
        # Build function_concept string
        func_nc_main = func_concept.get("nc_main", "")
        
        # Build value_concepts list
        vc_list = []
        for vc in value_concepts:
            vc_name = vc.get("concept_name")
            if vc_name:
                vc_list.append(format_concept_name(vc_name, vc.get("concept_type", "object")))
        
        # Build context_concepts list
        ctx_list = []
        for oc in other_concepts:
            if oc.get("inference_marker") == "<*":
                oc_name = oc.get("concept_name")
                if oc_name:
                    ctx_list.append(format_concept_name(oc_name, oc.get("concept_type", "object")))
        
        # Build working_interpretation
        wi = build_working_interpretation(inference, sequence_type)
        
        # Map sequence to inference_sequence
        sequence_mapping = {
            "imperative": "imperative_in_composition",
            "judgement": "judgement_in_composition",
            "assigning": "assigning",
            "grouping": "grouping",
            "timing": "timing",
            "looping": "looping",
        }
        
        # Use concept_to_infer's flow_index for consistency (it's the inference result position)
        cti_flow_index = cti.get("flow_index", func_concept.get("flow_index", ""))
        
        inference_entry = {
            "flow_info": {"flow_index": cti_flow_index},
            "inference_sequence": sequence_mapping.get(sequence_type, sequence_type),
            "concept_to_infer": concept_to_infer,
            "function_concept": func_nc_main,
            "value_concepts": vc_list,
            "context_concepts": ctx_list,
            "working_interpretation": wi,
        }
        
        inference_repo.append(inference_entry)
    
    # Sort by flow_index
    def flow_index_sort_key(item):
        idx = item.get("flow_info", {}).get("flow_index", "999")
        parts = idx.split(".")
        return [int(p) for p in parts]
    
    inference_repo.sort(key=flow_index_sort_key)
    
    return inference_repo


def main():
    # Paths
    base_dir = Path(__file__).parent
    nci_path = base_dir / "derivation.pf.nci.json"
    repos_dir = base_dir / "repos"
    repos_dir.mkdir(exist_ok=True)
    
    concept_repo_path = repos_dir / "concept_repo.json"
    inference_repo_path = repos_dir / "inference_repo.json"
    
    # Load NCI data
    print(f"Loading NCI from: {nci_path}")
    with open(nci_path, "r", encoding="utf-8") as f:
        nci_data = json.load(f)
    
    print(f"Found {len(nci_data)} inferences in NCI")
    
    # Build repositories
    print("Building concept repository...")
    concept_repo = build_concept_repo(nci_data)
    print(f"  -> {len(concept_repo)} unique concepts")
    
    print("Building inference repository...")
    inference_repo = build_inference_repo(nci_data)
    print(f"  -> {len(inference_repo)} inferences")
    
    # Write repositories
    print(f"\nWriting concept repo to: {concept_repo_path}")
    with open(concept_repo_path, "w", encoding="utf-8") as f:
        json.dump(concept_repo, f, indent=2, ensure_ascii=False)
    
    print(f"Writing inference repo to: {inference_repo_path}")
    with open(inference_repo_path, "w", encoding="utf-8") as f:
        json.dump(inference_repo, f, indent=2, ensure_ascii=False)
    
    print("\n[OK] Activation complete!")
    
    # Summary
    print("\n--- Summary ---")
    value_concepts = [c for c in concept_repo if c["type"] in ["{}", "[]", "<>"]]
    func_concepts = [c for c in concept_repo if c["type"] in ["({})", "<{}>"]]
    ground_concepts = [c for c in concept_repo if c["is_ground_concept"]]
    final_concepts = [c for c in concept_repo if c["is_final_concept"]]
    
    print(f"Value concepts: {len(value_concepts)}")
    print(f"Function concepts: {len(func_concepts)}")
    
    print(f"\nGround concepts ({len(ground_concepts)}):")
    for c in ground_concepts:
        print(f"  - {c['concept_name']}")
    
    print(f"\nFinal concepts ({len(final_concepts)}):")
    for c in final_concepts:
        print(f"  - {c['concept_name']}")
    
    # Inference sequence breakdown
    seq_counts = defaultdict(int)
    for inf in inference_repo:
        seq_counts[inf["inference_sequence"]] += 1
    
    print(f"\nInference sequences:")
    for seq, count in sorted(seq_counts.items()):
        print(f"  - {seq}: {count}")


if __name__ == "__main__":
    main()
