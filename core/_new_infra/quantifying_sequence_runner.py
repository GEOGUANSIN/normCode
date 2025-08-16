import os
import sys
import logging
from typing import Any, Dict, List, Optional, Callable, Tuple
from types import SimpleNamespace
from dataclasses import dataclass, field
from string import Template
from copy import copy

# Ensure this directory is importable regardless of where the script is run from
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from _inference import Inference, register_inference_sequence, setup_logging
from _concept import Concept
from _reference import Reference, cross_product, cross_action, element_action

# --- Quantifier Class (now self-contained) ---
class Quantifier:
    """
    A class that handles quantification processing for operators in a workspace.
    """
    
    def __init__(self, workspace: dict, loop_base_concept_name: str, loop_concept_index: int = 0):
        self.workspace = workspace
        self.loop_base_concept_name = loop_base_concept_name
        self._initiate_subworkspace(loop_base_concept_name, loop_concept_index)

    def _initiate_subworkspace(self, loop_base_concept_name: str, loop_concept_index: int = 0) -> None:
        self.workspace_key = f"{loop_concept_index}_{loop_base_concept_name}"
        if self.workspace_key not in self.workspace.keys():
            self.workspace[self.workspace_key] = {}
        self.current_subworkspace = self.workspace[self.workspace_key]

    def _get_list_at_index(self, input_list: list, index: int) -> Optional[Any]:
        try:
            if isinstance(input_list, list) and 0 <= index < len(input_list):
                return input_list[index]
            else:
                return None
        except (IndexError, TypeError):
            return None

    def _flatten_list(self, nested_list: list) -> list:
        flattened = []
        def _flatten_recursive(item):
            if isinstance(item, list):
                for element in item:
                    _flatten_recursive(element)
            else:
                flattened.append(item)
        _flatten_recursive(nested_list)
        return flattened
        
    def _check_new_base_element_by_looped_base_element(self, current_looped_element_reference: Reference, loop_base_concept_name: str) -> bool:
        element_found = False
        for loop_index in self.current_subworkspace.keys():
            if (loop_base_concept_name in self.current_subworkspace[loop_index].keys() and 
                current_looped_element_reference.tensor == self.current_subworkspace[loop_index][loop_base_concept_name].tensor):
                element_found = True
                break
        return not element_found

    def _check_index_of_current_looped_base_element(self, looped_base_reference: Reference) -> int:
        for existing_loop_index in self.current_subworkspace.keys():
            if (self.loop_base_concept_name in self.current_subworkspace[existing_loop_index] and 
                self.current_subworkspace[existing_loop_index][self.loop_base_concept_name].tensor == looped_base_reference.tensor):
                return existing_loop_index
        return self._get_next_loop_index()

    def _get_next_loop_index(self) -> int:
        new_loop_index = 0
        if self.current_subworkspace.keys():
             new_loop_index = max(self.current_subworkspace.keys())
        return new_loop_index + 1

    def store_new_base_element(self, looped_base_reference: Reference) -> int:
        loop_index = self._check_index_of_current_looped_base_element(looped_base_reference)
        if loop_index not in self.current_subworkspace:
            self.current_subworkspace[loop_index] = {}
        self.current_subworkspace[loop_index][self.loop_base_concept_name] = looped_base_reference
        return loop_index

    def store_new_in_loop_element(self, looped_base_reference: Reference, looped_concept_name: str, looped_concept_reference: Reference) -> int:
        loop_index = self._check_index_of_current_looped_base_element(looped_base_reference)
        if loop_index not in self.current_subworkspace:
            raise ValueError(f"The {looped_base_reference} is not in the current_subworkspace")
        self.current_subworkspace[loop_index][looped_concept_name] = looped_concept_reference
        return loop_index

    def retireve_next_base_element(self, to_loop_element_reference: Reference, current_loop_base_element: Optional[Reference] = None) -> Tuple[Optional[Reference], Optional[int]]:
        current_loop_index = 0
        max_iterations = 1000
        while True:
            get_element_function = lambda x: self._get_list_at_index(x, current_loop_index)
            current_to_loop_element_reference = element_action(get_element_function, [to_loop_element_reference.copy()])
            elements = self._flatten_list(current_to_loop_element_reference.tensor.copy())
            
            if all(e is None or e == "@#SKIP#@" for e in elements):
                break
            
            is_current = False
            if current_loop_base_element is not None:
                try:
                    if current_to_loop_element_reference.tensor == current_loop_base_element.tensor:
                        is_current = True
                except Exception:
                    pass
            
            is_in_workspace = False
            for loop_index in self.current_subworkspace.keys():
                if self.loop_base_concept_name in self.current_subworkspace[loop_index].keys():
                    if current_to_loop_element_reference.tensor == self.current_subworkspace[loop_index][self.loop_base_concept_name].tensor:
                        is_in_workspace = True
                        break

            if not is_current and not is_in_workspace:
                return current_to_loop_element_reference, current_loop_index

            current_loop_index += 1
            if current_loop_index > max_iterations:
                break
        
        return None, None

    def combine_all_looped_elements_by_concept(self, to_loop_element_reference: Reference, concept_name: str) -> Optional[Reference]:
        all_concept_references = []
        
        # Sort by loop index to ensure order
        sorted_loop_indices = sorted(self.current_subworkspace.keys())

        for loop_index in sorted_loop_indices:
            if concept_name in self.current_subworkspace[loop_index]:
                 all_concept_references.append(self.current_subworkspace[loop_index][concept_name])
        
        if all_concept_references:
            return cross_product(all_concept_references)
        
        return None

    def retrieve_next_in_loop_element(self, concept_name: str, mode: str = 'carry_over', current_loop_index: int = 0, carry_index: int = 0) -> Reference:
        if mode == 'carry_over':
            # The current_loop_index in the original file is the *value* of the carry, not the loop iteration index
            if current_loop_index > 0:
                 # We need to find the previous loop state. The workspace keys are loop indices.
                 # Let's find the largest index that is smaller than the next available index.
                
                # Get the next theoretical index
                next_idx = self._get_next_loop_index()
                
                # The "current" loop index for retrieval purposes is the one just before the next one to be added
                retrieval_idx = next_idx - 1 - (current_loop_index - 1)
                
                if retrieval_idx in self.current_subworkspace and concept_name in self.current_subworkspace[retrieval_idx]:
                    return self.current_subworkspace[retrieval_idx][concept_name]

        return Reference(axes=[], shape=())


# --- Grouper Class (now self-contained) ---
class Grouper:
    """
    A class that abstracts NormCode grouping patterns as functions of references.
    Provides methods for different grouping operations.
    """
    
    def __init__(self, skip_value="@#SKIP#@"):
        self.skip_value = skip_value
    
    def find_share_axes(self, references: List[Reference]) -> List[str]:
        if not references:
            return []
        shared_axes = set(references[0].axes)
        for ref in references[1:]:
            shared_axes.intersection_update(ref.axes)
        return list(shared_axes)
    
    def flatten_element(self, reference: Reference) -> Reference:
        def flatten_all_list(nested_list):
            if not isinstance(nested_list, list):
                return [nested_list]
            return sum((flatten_all_list(item) for item in nested_list), [])
        
        return element_action(flatten_all_list, [reference])
    
    def annotate_element(self, reference: Reference, annotation_list: List[str]) -> Reference:
        def annotate_list(lst: List[Any]) -> Dict[str, Any] | str:
            if len(lst) != len(annotation_list):
                return self.skip_value
            
            annotation_dict = {annotation: lst[i] for i, annotation in enumerate(annotation_list)}
            return annotation_dict
        
        return element_action(annotate_list, [reference])
    
    def create_unified_element_actuation(self, template: Template, annotation_list: Optional[List[str]] = None):
        def element_actuation(element: Any) -> str:
            return_string = ""
            elements = element if isinstance(element, list) else [element]
            
            for one_element in elements:
                input_dict = {}
                if annotation_list is not None:
                    # Annotated case
                    for i, annotation in enumerate(annotation_list):
                        input_value = one_element.get(annotation, self.skip_value)
                        input_dict[f"input{i+1}"] = str(input_value)
                else:
                    # Non-annotated case
                    if isinstance(one_element, list):
                        format_string = "; ".join(map(str, one_element))
                        input_dict = {"input1": format_string}
                    else:
                        input_dict = {"input1": str(one_element)}
            
                template_copy = copy(template)
                result_string = template_copy.safe_substitute(**input_dict) + " \n"
                return_string += result_string
            
            return return_string
        
        return element_actuation

    def and_in(self, references: List[Reference], annotation_list: List[str], by_axes: Optional[List[List[str]]] = None, template: Optional[Template] = None, pop: bool = True) -> Reference:
        shared_axes = self.find_share_axes(references)
        sliced_refs = [ref.slice(*shared_axes) for ref in references]
        
        result = cross_product(sliced_refs)
        result = self.annotate_element(result, annotation_list)

        if by_axes is not None and len(by_axes) > 0:
            preserve_axes = [axis for axis in result.axes if not any(axis in sublist for sublist in by_axes)]
            
            by_axes_copy = copy(by_axes)
            if pop:
                for i in range(len(by_axes_copy)):
                    if by_axes_copy[i]:
                        by_axes_copy[i].pop()

            axes_in_all_groups = [axis for axis in result.axes if all(axis in sublist for sublist in by_axes_copy)] if by_axes_copy and by_axes_copy[0] else []
            final_slice_axes = preserve_axes + axes_in_all_groups
            result = result.slice(*final_slice_axes)
        
        if template:
            element_actuation = self.create_unified_element_actuation(template, annotation_list)
            result = element_action(element_actuation, [result])
        
        return result
    
    def or_across(self, references: List[Reference], by_axes: Optional[List[List[str]]] = None, template: Optional[Template] = None, pop: bool = True) -> Reference:
        shared_axes = self.find_share_axes(references)
        sliced_refs = [ref.slice(*shared_axes) for ref in references]
        
        result = cross_product(sliced_refs)
        
        if by_axes is not None and len(by_axes) > 0:
            preserve_axes = [axis for axis in result.axes if not any(axis in sublist for sublist in by_axes)]
            
            by_axes_copy = copy(by_axes)
            if pop:
                for i in range(len(by_axes_copy)):
                    if by_axes_copy[i]:
                        by_axes_copy[i].pop()

            axes_in_all_groups = [axis for axis in result.axes if all(axis in sublist for sublist in by_axes_copy)] if by_axes_copy and by_axes_copy[0] else []
            final_slice_axes = preserve_axes + axes_in_all_groups
            result = result.slice(*final_slice_axes)
        
        result = self.flatten_element(result)
        
        if template:
            element_actuation = self.create_unified_element_actuation(template, None)
            result = element_action(element_actuation, [result])
        
        return result


# --- State Models (adapted from grouping_sequence_runner.py) ---

@dataclass
class SequenceStepSpecLite:
    step_name: str
    step_index: Optional[int] = None

@dataclass
class SequenceSpecLite:
    sequence: List[SequenceStepSpecLite] = field(default_factory=list)
    current_step: str = "IWI"

@dataclass
class ConceptInfoLite:
    id: Optional[str]
    name: Optional[str]
    type: Optional[str]
    context: Optional[str]
    axis_name: Optional[str] = None

@dataclass
class ReferenceRecordLite:
    step_name: str
    concept: Optional[ConceptInfoLite] = None
    reference: Optional[Reference] = None
    model: Optional[Dict[str, Any]] = None

class States:
    """State container for the quantifying sequence."""
    def __init__(self) -> None:
        self.sequence_state = SequenceSpecLite(
            sequence=[
                SequenceStepSpecLite(step_name="IWI"),
                SequenceStepSpecLite(step_name="IR"),
                SequenceStepSpecLite(step_name="GR"),
                SequenceStepSpecLite(step_name="QR"),
                SequenceStepSpecLite(step_name="OR"),
                SequenceStepSpecLite(step_name="OWI"),
            ]
        )
        self.function: List[ReferenceRecordLite] = []
        self.values: List[ReferenceRecordLite] = []
        self.context: List[ReferenceRecordLite] = []
        self.inference: List[ReferenceRecordLite] = []
        self.syntax: SimpleNamespace = SimpleNamespace()
        self.workspace: Dict[str, Any] = {} # Workspace for Quantifier

    def set_current_step(self, name: str) -> None:
        self.sequence_state.current_step = name

    def get_reference(self, category: str, step_name: str) -> Optional[Reference]:
        cat_list = getattr(self, category, [])
        for record in cat_list:
            if record.step_name == step_name:
                return record.reference
        return None

    def set_reference(self, category: str, step_name: str, ref: Reference) -> None:
        cat_list = getattr(self, category, [])
        for record in cat_list:
            if record.step_name == step_name:
                record.reference = ref.copy()
                return
        cat_list.append(ReferenceRecordLite(step_name=step_name, reference=ref.copy()))


# --- Sequence Step Implementations ---

def input_working_interpretation(
    inference: Inference, 
    states: States, 
    working_interpretation: Optional[Dict[str, Any]] = None
) -> States:
    """Initialize states with syntax info and placeholder records."""
    if working_interpretation:
        states.syntax = SimpleNamespace(**working_interpretation.get("syntax", {}))

    # Seed lists with empty records for each step
    for step in ["GR", "QR", "OR"]:
        states.inference.append(ReferenceRecordLite(step_name=step))

    states.set_current_step("IWI")
    logging.debug(f"IWI completed. Syntax: {states.syntax}")
    return states

def input_references(inference: Inference, states: States) -> States:
    """Populate references and concept info into the state from the inference instance."""
    # This logic is identical to the grouping runner
    if inference.function_concept:
        states.function.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(id=inference.function_concept.id, name=inference.function_concept.name, type=inference.function_concept.type, context=inference.function_concept.context, axis_name=inference.function_concept.axis_name),
                reference=inference.function_concept.reference.copy() if inference.function_concept.reference else None
            )
        )
    
    for vc in inference.value_concepts or []:
        # Store GR concepts under 'GR' to be used by QR later.
        states.values.append(
            ReferenceRecordLite(
                step_name="GR",
                concept=ConceptInfoLite(id=vc.id, name=vc.name, type=vc.type, context=vc.context, axis_name=vc.axis_name),
                reference=vc.reference.copy() if vc.reference else None
            )
        )
    
    for cc in inference.context_concepts or []:
        states.context.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(id=cc.id, name=cc.name, type=cc.type, context=cc.context, axis_name=cc.axis_name),
                reference=cc.reference.copy() if cc.reference else None
            )
        )
    
    states.set_current_step("IR")
    logging.debug(f"IR completed. Loaded {len(states.values)} value and {len(states.context)} context concepts.")
    return states

def grouping_references(states: States) -> States:
    """Perform the core grouping logic."""
    context_refs = [r.reference for r in states.context if r.reference]
    value_refs = [r.reference for r in states.values if r.reference and r.step_name == 'GR'] # Use only GR values
    value_concept_names = [c.concept.name for c in states.values if c.concept and c.step_name == 'GR']

    by_axes = [ref.axes for ref in context_refs]
    
    grouper = Grouper()
    result_ref = None

    marker = getattr(states.syntax, 'marker', None)
    if marker == "in":
        logging.debug(f"Performing 'and_in' grouping with by_axes: {by_axes}")
        result_ref = grouper.and_in(value_refs, value_concept_names, by_axes=by_axes)
    elif marker == "across":
        logging.debug(f"Performing 'or_across' grouping with by_axes: {by_axes}")
        result_ref = grouper.or_across(value_refs, by_axes=by_axes)
    else:
        logging.warning(f"No valid grouping marker found ('{marker}'). Assuming direct pass-through of values.")
        # If no grouping, just combine the values into a single reference for QR
        if value_refs:
            result_ref = cross_product(value_refs)

    if result_ref:
        # The result of grouping becomes an input for QR, so we store it in values.
        gr_record = next((v for v in states.values if v.step_name == "GR"), None)
        if gr_record:
            gr_record.reference = result_ref
        else:
             states.values.append(ReferenceRecordLite(step_name="GR", reference=result_ref))
   
    states.set_current_step("GR")
    logging.debug("GR completed.")
    return states

def quantifying_references(states: States) -> States:
    """
    Quantifying References (QR) step using only the `states` object.
    """
    def _ensure_reference(ref: Optional[Reference]) -> Reference:
        if isinstance(ref, Reference):
            return ref
        return Reference(axes=[], shape=())

    # 1) Read syntax data (parsed quantification)
    syntax_data = getattr(states, "syntax", {})
    if not isinstance(syntax_data, SimpleNamespace) and not isinstance(syntax_data, dict):
        logging.warning("[QR] states.syntax is not a dict or SimpleNamespace; QR step requires parsed syntax data. Skipping.")
        return states
    
    # Handle both SimpleNamespace and dict for syntax_data
    def get_syntax_attr(attr, default=None):
        if isinstance(syntax_data, SimpleNamespace):
            return getattr(syntax_data, attr, default)
        return syntax_data.get(attr, default)

    loop_base_concept_name = get_syntax_attr("LoopBaseConcept")
    concept_to_infer_list = get_syntax_attr("ConceptToInfer", [])
    in_loop_spec = get_syntax_attr("InLoopConcept")

    if not loop_base_concept_name or not concept_to_infer_list:
        logging.warning("[QR] Missing LoopBaseConcept or ConceptToInfer in syntax data. Skipping.")
        return states
    concept_to_infer_name = concept_to_infer_list[0]
    current_loop_base_concept_name = f"{loop_base_concept_name}*"

    # 2) Get to-loop elements reference (from GR step)
    to_loop_elements: Optional[Reference] = None
    values_block = getattr(states, "values", []) or []
    for item in values_block:
        if getattr(item, "step_name", None) == "GR" and getattr(item, "reference", None) is not None:
            to_loop_elements = item.reference
            break
    if to_loop_elements is None:
        logging.warning("[QR] No to-loop elements found in states.values for step 'GR'. Skipping.")
        return states

    # 3) Prepare workspace
    if not hasattr(states, "workspace") or getattr(states, "workspace") is None:
        setattr(states, "workspace", {})
    workspace = getattr(states, "workspace")

    # 4) Current loop base element from context (if any)
    current_loop_base_context_item = None
    context_block = getattr(states, "context", []) or []
    for ctx in context_block:
        concept_info = getattr(ctx, "concept", None)
        concept_name = getattr(concept_info, "name", None)
        if concept_name == current_loop_base_concept_name:
            current_loop_base_context_item = ctx
            break
    
    current_loop_base_element_opt = None
    if current_loop_base_context_item is not None:
        current_loop_base_element_opt = getattr(current_loop_base_context_item, "reference", None)

    # 5) Determine current concept element from function block (first available reference)
    current_concept_element_opt = None
    function_block = getattr(states, "function", []) or []
    for fn in function_block:
        ref = getattr(fn, "reference", None)
        if ref is not None:
            current_concept_element_opt = ref
            break

    # 6) Initialize quantifier and retrieve next element
    quantifier = Quantifier(workspace=workspace, loop_base_concept_name=loop_base_concept_name)
    next_current_loop_base_element_opt, _ = quantifier.retireve_next_base_element(
        to_loop_element_reference=to_loop_elements,
        current_loop_base_element=current_loop_base_element_opt,
    )

    # 7) Decide if current element is new
    is_new = False
    if current_loop_base_element_opt is not None and isinstance(current_loop_base_element_opt, Reference):
        if quantifier._check_new_base_element_by_looped_base_element(current_loop_base_element_opt, loop_base_concept_name):
            is_new = True
            current_loop_base_element = current_loop_base_element_opt
        else:
            current_loop_base_element = next_current_loop_base_element_opt
    else:
        current_loop_base_element = next_current_loop_base_element_opt

    # 8) Ensure references
    next_current_loop_base_element = _ensure_reference(next_current_loop_base_element_opt)
    current_concept_element = _ensure_reference(current_concept_element_opt)
    current_loop_base_element = _ensure_reference(current_loop_base_element)

    # 9) On new element, store base and in-loop concept
    if is_new:
        quantifier.store_new_base_element(current_loop_base_element)
        quantifier.store_new_in_loop_element(
            current_loop_base_element,
            concept_to_infer_name,
            current_concept_element,
        )

    # 10) Update context: advance loop base and carry-over for declared in-loop concepts
    for ctx in context_block:
        concept_info = getattr(ctx, "concept", None)
        ctx_name = getattr(concept_info, "name", None)
        if ctx_name == current_loop_base_concept_name:
            setattr(ctx, "reference", next_current_loop_base_element.copy())
            continue
        if in_loop_spec is not None and ctx_name in in_loop_spec:
            if not isinstance(ctx_name, str): continue
            if is_new:
                quantifier.store_new_in_loop_element(
                    current_loop_base_element,
                    ctx_name,
                    _ensure_reference(getattr(ctx, "reference", None)),
                )
            carry_index = in_loop_spec[ctx_name]
            retrieved = quantifier.retrieve_next_in_loop_element(
                ctx_name,
                current_loop_index=carry_index,
            )
            setattr(ctx, "reference", retrieved)

    # 11) Combine all stored references for the inferred concept
    combined_reference: Optional[Reference] = None
    if is_new:
        combined_reference = quantifier.combine_all_looped_elements_by_concept(
            to_loop_element_reference=to_loop_elements,
            concept_name=concept_to_infer_name,
        )
        if combined_reference is not None:
            # Axis normalization
            loop_base_axis, current_loop_axis = None, None
            for v in values_block:
                ci = getattr(v, "concept", None)
                if ci and getattr(ci, "name", None) == loop_base_concept_name:
                    loop_base_axis = getattr(ci, "axis_name", None)
                    break
            for c in context_block:
                ci = getattr(c, "concept", None)
                if ci and getattr(ci, "name", None) == current_loop_base_concept_name:
                    current_loop_axis = getattr(ci, "axis_name", None)
                    break

            if loop_base_axis is not None and current_loop_axis is not None:
                new_axes = combined_reference.axes.copy()
                new_axes[-1] = concept_to_infer_name
                if current_loop_axis in new_axes:
                    new_axes[new_axes.index(current_loop_axis)] = loop_base_axis
                combined_reference.axes = new_axes

    # 12) Write result into states.inference under QR if the entry exists
    if combined_reference is not None:
        for inf in getattr(states, "inference", []) or []:
            if getattr(inf, "step_name", None) == "QR":
                setattr(inf, "reference", combined_reference)
                break
    
    states.set_current_step("QR")
    logging.debug("QR completed.")
    return states


def output_reference(states: States) -> States:
    """Finalize the output reference from the last inference step (QR)."""
    # The final result is the one produced by the QR step.
    qr_ref = states.get_reference("inference", "QR")
    if qr_ref:
        states.set_reference("inference", "OR", qr_ref)
    states.set_current_step("OR")
    logging.debug("OR completed.")
    return states

def output_working_interpretation(states: States) -> States:
    """No-op finalization for demo."""
    states.set_current_step("OWI")
    logging.debug("OWI completed.")
    return states

# --- Logging ---
def log_states_progress(states: States, step_name: str, step_filter: Optional[str] = None):
    logger = logging.getLogger(__name__)
    logger.info(f"--- States after {step_name} (Filtered by: {step_filter or 'None'}) ---")
    logger.info(f"Current Step: {states.sequence_state.current_step}")
    
    def _log_record_list(label: str, record_list: List[ReferenceRecordLite]):
        logger.info(f"{label}:")
        filtered_records = [item for item in record_list if step_filter is None or item.step_name == step_filter]
        if not filtered_records:
            logger.info("  (Empty or no matching records for filter)")
            return
        for item in filtered_records:
            logger.info(f"  Step Name: {item.step_name}")
            if item.concept:
                logger.info(f"    Concept: Name={item.concept.name}, Axis={item.concept.axis_name}")
            if item.reference and isinstance(item.reference, Reference):
                logger.info(f"    Reference: Axes={item.reference.axes}, Shape={item.reference.shape}")
                # Log tensor but truncate if too long
                tensor_str = str(item.reference.tensor)
                logger.info(f"    Tensor: {tensor_str[:200]}{'...' if len(tensor_str) > 200 else ''}")

    _log_record_list("Function", states.function)
    _log_record_list("Values", states.values)
    _log_record_list("Context", states.context)
    _log_record_list("Inference", states.inference)
    logger.info("-" * 20)


# --- Quantifying Sequence Runner ---

@register_inference_sequence("quantifying_v2")
def quantifying_v2(self: Inference, input_data: Optional[Dict[str, Any]] = None) -> States:
    """New quantifying sequence runner."""
    states = States()
    working_interpretation = (input_data or {}).get("working_interpretation")
    
    # IWI
    states = input_working_interpretation(self, states, working_interpretation=working_interpretation)
    log_states_progress(states, "IWI")
    # IR
    states = input_references(self, states)
    log_states_progress(states, "IR")
    # GR
    states = grouping_references(states)
    log_states_progress(states, "GR", step_filter="GR")
    # QR
    states = quantifying_references(states)
    log_states_progress(states, "QR", step_filter="QR")
    # OR
    states = output_reference(states)
    log_states_progress(states, "OR", step_filter="OR")
    # OWI
    states = output_working_interpretation(states)
    log_states_progress(states, "OWI")
    
    return states


# --- Demo Setup: Summing Digits ---

def _build_demo_concepts() -> tuple[Concept, List[Concept], Concept, List[Concept]]:
    """Builds concepts for a quantification demo: summing digits with carry-over."""
    logger = logging.getLogger(__name__)
    logger.info("Building demo concepts for quantification.")

    # Value Concept: The list of digits to be looped over.
    # This would typically be the output of a GR step.
    ref_digits = Reference(axes=["digit_pos"], shape=(4,))
    for i, v in enumerate([1, 8, 2, 5]):
        ref_digits.set(f"%({v})", digit_pos=i)
    concept_digits = Concept("{digit}", "digit", "digit_pos", ref_digits)

    # Context Concepts for Quantification Loop Control
    # 1. The loop base concept, which drives the iteration.
    ref_digit_pos = Reference(axes=["digit_pos"], shape=(4,))
    for i in range(4):
        ref_digit_pos.set(f"%({i})", digit_pos=i)
    concept_digit_pos = Concept("{digit position}", "digit position", "digit_pos", ref_digit_pos)
    
    # 2. The "current" version of the loop base, which advances.
    concept_current_digit_pos = Concept("{digit position}*", "digit position*", "digit_pos*")
    
    # 3. The "carry-over" concept for the running sum.
    concept_partial_sum = Concept("{partial_sum}*", "partial_sum*", "partial_sum*")

    # Function Concept: A dummy "add" function. In a real scenario, this could be
    # a complex model-driven function. For the demo, QR just needs a value to store
    # for each loop iteration, which we'll simulate as the "new sum".
    # Let's say we just add the digit to the previous sum (or 0 if first).
    # The actual addition logic isn't in this runner, but we provide the function concept.
    ref_add = Reference(axes=["f"], shape=(1,)); ref_add.set("%(add)", f=0)
    function_concept = Concept("::(add)", "add", "f", ref_add)

    # Concept to Infer: The final sum.
    concept_to_infer = Concept("{sum}", "sum", "sum")

    return (
        concept_to_infer,
        [concept_digits],
        function_concept,
        [concept_digit_pos, concept_current_digit_pos, concept_partial_sum]
    )

def _build_demo_working_interpretation() -> Dict[str, Any]:
    """Provides the syntax needed for the QR step."""
    return {
        "syntax": {
            "marker": None, # No grouping needed, values are passed through
            "LoopBaseConcept": "{digit position}",
            "ConceptToInfer": ["{sum}"],
            "InLoopConcept": {
                "{partial_sum}*": 1  # Carry over partial sum from 1 step ago
            }
        }
    }

# --- Main Execution ---

def run_quantifying_sequence() -> States:
    setup_logging(logging.DEBUG)

    concept_to_infer, value_concepts, function_concept, context_concepts = _build_demo_concepts()

    inference = Inference(
        "quantifying_v2",
        concept_to_infer,
        value_concepts,
        function_concept,
        context_concepts=context_concepts
    )
    
    # The QR step needs a function reference to be available in the states.
    # We will manually put a placeholder function result in each loop.
    # In a real run, another sequence (like imperative) would run inside the loop.
    # We will manually drive the quantification loop to simulate a real scenario
    # where an imperative sequence would run in each iteration.

    # 1. Initial setup
    states = States()
    working_interpretation = _build_demo_working_interpretation()
    states = input_working_interpretation(inference, states, working_interpretation)
    states = input_references(inference, states)
    states = grouping_references(states)

    # 2. Loop simulation
    running_sum = 0
    digits_to_process = value_concepts[0].reference.get_tensor(ignore_skip=True) # [ '%(1)', '%(8)', ... ]
    
    # The `quantifying_references` function looks for the "current" loop base element in the context.
    # We must seed it before the first iteration.
    initial_loop_base_ref = Reference(axes=['digit_pos'], shape=(1,))
    initial_loop_base_ref.set('%(0)', digit_pos=0)
    for ctx in states.context:
        if ctx.concept and ctx.concept.name == '{digit position}*':
            ctx.reference = initial_loop_base_ref
            break

    for i, digit_str in enumerate(digits_to_process):
        logging.info(f"--- SIMULATING LOOP ITERATION {i+1} ---")
        
        # Strip wrapper to get the number
        digit = int(digit_str.strip('%()'))
        
        # Simulate the "add" function: update running_sum
        # In a real scenario, a model would do this.
        # We need to get the "carry" value from the previous step.
        
        # Find the partial_sum reference from the context
        partial_sum_ref = None
        for ctx in states.context:
            if ctx.concept and ctx.concept.name == '{partial_sum}*':
                partial_sum_ref = ctx.reference
                break
        
        previous_sum = 0
        if partial_sum_ref:
            try:
                val = partial_sum_ref.get_tensor(ignore_skip=True)
                if val: previous_sum = int(val[0])
            except (ValueError, IndexError):
                previous_sum = 0 # Default to 0 if parsing fails
        
        running_sum = previous_sum + digit
        logging.info(f"Digit: {digit}, Previous Sum: {previous_sum}, New Sum: {running_sum}")

        # Update the function reference in states to hold the new sum.
        # This is what the QR step will read.
        new_sum_ref = Reference(axes=['sum'], shape=(1,))
        new_sum_ref.set(running_sum, sum=0)
        states.function = [ReferenceRecordLite("MFP_Result", reference=new_sum_ref)]
        
        # Now, call the QR step. It will:
        # 1. See the current loop base element ('digit_pos' i) is new.
        # 2. Store the `new_sum_ref` in its workspace associated with this digit.
        # 3. Update the context concepts (advance 'digit_pos*', update 'partial_sum*').
        states = quantifying_references(states)
        log_states_progress(states, f"QR_Iter_{i+1}")

        # CRITICAL: Update the main state's partial_sum* with the one from the workspace for the next loop
        new_partial_sum_ref = Reference(axes=['sum'], shape=(1,))
        new_partial_sum_ref.set(running_sum, sum=0)
        for ctx in states.context:
            if ctx.concept and ctx.concept.name == '{partial_sum}*':
                ctx.reference = new_partial_sum_ref
                break

    # One final call to QR to combine the last element
    states = quantifying_references(states)
    
    # 3. Finalization
    states = output_reference(states)
    states = output_working_interpretation(states)

    # Final log
    logger = logging.getLogger(__name__)
    final_ref = states.get_reference("inference", "OR")
    if isinstance(final_ref, Reference):
        logger.info("--- Final Output (OR) ---")
        logger.info(f"Axes: {final_ref.axes}")
        logger.info(f"Shape: {final_ref.shape}")
        tensor_content = final_ref.get_tensor(ignore_skip=True)
        logger.info(f"Tensor (without skips): {tensor_content}")
        print("\n--- Final Output (OR) ---")
        print(f"Tensor: {tensor_content}")
        # Expected: [[[[1], [9]], [[11], [16]]]] or similar nested structure based on axes
    
    return states

if __name__ == "__main__":
    run_quantifying_sequence() 