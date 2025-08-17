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
        # First, check if the reference itself is empty. If so, it can't be "new".
        if self._is_reference_empty(current_looped_element_reference):
            logging.debug(f"[_check_new_base_element] Input element is empty. Returning False (not new).")
            return False

        logging.debug(f"[_check_new_base_element] Checking for element: {current_looped_element_reference.tensor}")
        element_found = False
        for loop_index in self.current_subworkspace.keys():
            if (loop_base_concept_name in self.current_subworkspace[loop_index].keys() and 
                current_looped_element_reference.tensor == self.current_subworkspace[loop_index][loop_base_concept_name].tensor):
                logging.debug(f"[_check_new_base_element] Found match at loop index {loop_index}")
                element_found = True
                break
        logging.debug(f"[_check_new_base_element] Is new? {not element_found}")
        return not element_found

    def _check_index_of_current_looped_base_element(self, looped_base_reference: Reference) -> int:
        logging.debug(f"[_check_index] Checking index for: {looped_base_reference.tensor}")
        for existing_loop_index in self.current_subworkspace.keys():
            if (self.loop_base_concept_name in self.current_subworkspace[existing_loop_index] and 
                self.current_subworkspace[existing_loop_index][self.loop_base_concept_name].tensor == looped_base_reference.tensor):
                logging.debug(f"[_check_index] Found existing index: {existing_loop_index}")
                return existing_loop_index
        
        new_index = self._get_next_loop_index()
        logging.debug(f"[_check_index] No existing index found. Returning new index: {new_index}")
        return new_index

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

    def _is_reference_empty(self, ref: Optional[Reference]) -> bool:
        """Checks if a reference is None, has a None tensor, or a tensor with only Nones."""
        if ref is None or ref.tensor is None:
            return True
        # Flatten the tensor and check if it contains any non-None values.
        flat_tensor = self._flatten_list(ref.tensor if isinstance(ref.tensor, list) else [ref.tensor])
        return all(x is None for x in flat_tensor)

    def retireve_next_base_element(self, to_loop_element_reference: Reference, current_loop_base_element: Optional[Reference] = None) -> Tuple[Optional[Reference], Optional[int]]:
        current_loop_index = 0
        max_iterations = 1000
        while True:
            get_element_function = lambda x: self._get_list_at_index(x, current_loop_index)
            current_to_loop_element_reference = element_action(get_element_function, [to_loop_element_reference.copy()])
            elements = self._flatten_list(current_to_loop_element_reference.tensor.copy())
            
            if all(e is None or e == "@#SKIP#@" for e in elements):
                # We've reached the end of the elements to loop through.
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

    def check_all_base_elements_looped(self, to_loop_element_reference: Reference, in_loop_element_name: Optional[str] = None) -> bool:
        """Checks if all elements in a reference have been processed and stored in the workspace."""
        logging.debug(f"[check_all_looped] Starting check. Looping over {to_loop_element_reference.tensor}")
        
        # Validate that all elements in the tensor are lists
        if to_loop_element_reference.tensor:
            for i, element in enumerate(to_loop_element_reference.tensor):
                if not isinstance(element, list):
                    raise ValueError(f"Element at index {i} is not a list: {element}")
        
        current_loop_index = 0

        while True:
            get_element_function = lambda x: self._get_list_at_index(x, current_loop_index)
            current_to_loop_element_reference = element_action(get_element_function, [to_loop_element_reference.copy()])
            logging.debug(f"[check_all_looped] current_to_loop_element_reference: {current_to_loop_element_reference.tensor}")
            elements = self._flatten_list(current_to_loop_element_reference.tensor.copy())
            logging.debug(f"[check_all_looped] Index {current_loop_index}: Checking element {elements}")
            
            if all(e is None or e == "@#SKIP#@" for e in elements):
                logging.debug(f"[check_all_looped] Reached end of elements at index {current_loop_index}. Loop IS complete.")
                break # Exit the while loop, will return True

            element_found_in_workspace = False
            matching_loop_index = None
            for loop_idx, concepts in self.current_subworkspace.items():
                if self.loop_base_concept_name in concepts and concepts[self.loop_base_concept_name].tensor == current_to_loop_element_reference.tensor:
                    element_found_in_workspace = True
                    matching_loop_index = loop_idx
                    logging.debug(f"[check_all_looped] Index {current_loop_index}: Found element in workspace at loop index {loop_idx}.")
                    break
            
            if not element_found_in_workspace:
                logging.debug(f"[check_all_looped] Index {current_loop_index}: Element NOT found in workspace. Loop is NOT complete. Returning False.")
                return False

            if in_loop_element_name is not None and matching_loop_index is not None:
                if in_loop_element_name not in self.current_subworkspace[matching_loop_index]:
                    logging.debug(f"[check_all_looped] Index {current_loop_index}: Element found, but required in-loop concept '{in_loop_element_name}' is MISSING. Loop is NOT complete. Returning False.")
                    return False

            current_loop_index += 1
        
        logging.debug("[check_all_looped] All elements checked and found in workspace. Loop IS complete. Returning True.")
        return True

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

    # Clear previous state to prevent accumulation in loops
    states.function = []
    states.values = []
    states.context = []
    states.inference = []

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
                step_name="IR",
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
    """Perform the core grouping logic for quantification."""
    # 1. Get value references to be grouped.
    value_refs = [r.reference.copy() for r in states.values if r.reference and r.step_name == 'IR']
    if not value_refs:
        logging.warning("[GR] No value references found for grouping.")
        states.set_current_step("GR")
        return states

    # 2. Find the axis of the concept we are looping over from the value concepts.
    loop_base_concept_name = getattr(states.syntax, 'LoopBaseConcept', None)
    loop_base_axis = None
    if loop_base_concept_name:
        loop_base_axis = next(
            (r.concept.axis_name for r in states.values 
             if r.concept and r.concept.name == loop_base_concept_name), 
            None
        )
    
    if not loop_base_axis and value_refs[0].axes:
        loop_base_axis = value_refs[0].axes[0]
        logging.warning(f"Loop base axis not found for '{loop_base_concept_name}'. Falling back to '{loop_base_axis}'.")

    # 3. Perform grouping. For quantification, this is essentially a flattening operation.
    grouper = Grouper()
    # For quantification, we always use or_across pattern
    # Pass a copy of the axes to prevent destructive modification of the original reference.
    by_axes = [ref.axes.copy() for ref in value_refs]
    to_loop_ref = grouper.or_across(
        references=value_refs, 
        by_axes=by_axes,
    )


    current_loop_base_concept_name = f"{getattr(states.syntax, 'LoopBaseConcept', None)}*" if getattr(states.syntax, 'LoopBaseConcept', None) else None
    # Safely get the axis name from the concept, not the reference.
    current_loop_base_concept_axis = next((r.concept.axis_name for r in states.context if r.concept and r.concept.name == current_loop_base_concept_name), None)


    if current_loop_base_concept_axis:
        if to_loop_ref.axes == ["_none_axis"]:
            new_axes = [current_loop_base_concept_axis]
        else:
            new_axes = to_loop_ref.axes.copy() + [current_loop_base_concept_axis] 
        to_loop_ref.axes = new_axes


    states.values.append(ReferenceRecordLite(step_name="GR", reference=to_loop_ref.copy()))
   
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
            logging.debug(f"[QR Step 4] Found current loop base element in context: {current_loop_base_context_item}")
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

    logging.debug(f"[QR Step 5] From function (inner step result): current_concept_element_opt = {current_concept_element_opt.tensor if current_concept_element_opt else 'None'}")
    # 6) Initialize quantifier and retrieve next element
    quantifier = Quantifier(workspace=workspace, loop_base_concept_name=loop_base_concept_name)
    next_current_loop_base_element_opt, _ = quantifier.retireve_next_base_element(
        to_loop_element_reference=to_loop_elements,
        current_loop_base_element=current_loop_base_element_opt,
    )

    logging.debug(f"[QR Step 6] Retrieved next element to loop: next_current_loop_base_element_opt = {next_current_loop_base_element_opt.tensor if next_current_loop_base_element_opt else 'None'}")

    # 7) Decide if current element is new
    is_new = False
    if current_concept_element_opt is not None and isinstance(current_concept_element_opt, Reference):
        is_new_check_result = quantifier._check_new_base_element_by_looped_base_element(current_concept_element_opt, current_loop_base_concept_name)
        logging.debug(f"[QR Step 7] Checking if '{current_concept_element_opt.tensor if current_concept_element_opt else 'None'}' is a new base element. Result: {is_new_check_result}")

        if is_new_check_result:
            is_new = True
            current_loop_base_element = current_loop_base_element_opt
            logging.debug(f"[QR Step 7] Element IS new. Assigning inner step result to current_loop_base_element: {current_loop_base_element.tensor if current_loop_base_element else 'None'}")
        else:
            current_loop_base_element = next_current_loop_base_element_opt
            logging.debug(f"[QR Step 7] Element is NOT new. Assigning next element to current_loop_base_element: {current_loop_base_element.tensor if current_loop_base_element else 'None'}")
    else:
        current_loop_base_element = next_current_loop_base_element_opt
        logging.debug(f"[QR Step 7] No inner step result. Assigning next element to current_loop_base_element: {current_loop_base_element.tensor if current_loop_base_element else 'None'}")

    # 8) Ensure references
    next_current_loop_base_element = _ensure_reference(next_current_loop_base_element_opt)
    current_concept_element = _ensure_reference(current_concept_element_opt)
    current_loop_base_element = _ensure_reference(current_loop_base_element)

    # 9) On new element, store base and in-loop concept, but only if they have valid references.
    if is_new:
        if not quantifier._is_reference_empty(current_loop_base_element):
            # First, create the entry for the new base element and get its loop index.
            logging.debug(f"[QR Step 9] Storing NEW base element: {current_loop_base_element.tensor}")
            loop_index = quantifier.store_new_base_element(current_loop_base_element)
            
            # Now, safely store the inferred concept using the obtained index.
            if not quantifier._is_reference_empty(current_concept_element):
                logging.debug(f"[QR Step 9] Storing in-loop element '{concept_to_infer_name}' with value {current_concept_element.tensor} for base {current_loop_base_element.tensor} at index {loop_index}")
                quantifier.store_new_in_loop_element(
                    current_loop_base_element,
                    concept_to_infer_name,
                    current_concept_element,
                )

    # 10) Update context: Create new 'QR' step records for the inner loop's context.
    new_qr_context_records = []
    for ctx in context_block:
        concept_info = getattr(ctx, "concept", None)
        ctx_name = getattr(concept_info, "name", None)
        new_ref_for_qr = None

        # Determine the new reference for the loop base concept
        if ctx_name == current_loop_base_concept_name:
            new_ref_for_qr = next_current_loop_base_element.copy()

        # Determine the new reference for any in-loop concepts to be carried over
        elif in_loop_spec is not None and ctx_name in in_loop_spec:
            if not isinstance(ctx_name, str): continue
            
            # For new elements, store the initial value of the in-loop concept (e.g., initial partial_sum).
            if is_new and not quantifier._is_reference_empty(current_loop_base_element):
                quantifier.store_new_in_loop_element(
                    current_loop_base_element,
                    ctx_name,
                    _ensure_reference(getattr(ctx, "reference", None)),
                )
            carry_index = in_loop_spec[ctx_name]
            new_ref_for_qr = quantifier.retrieve_next_in_loop_element(
                ctx_name,
                current_loop_index=carry_index,
            )
        
        # If an updated reference was created, add it to our list for the new QR context.
        if new_ref_for_qr:
            new_qr_context_records.append(ReferenceRecordLite(
                step_name="QR",
                concept=ctx.concept,
                reference=new_ref_for_qr
            ))

    # Prepend the new QR records to the list so they are found first. The original IR records are preserved.
    states.context = new_qr_context_records + states.context

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
    """Finalize the output reference and context from the QR step."""
    # The final result is the one produced by the QR step.
    qr_ref = states.get_reference("inference", "QR")
    if qr_ref:
        states.set_reference("inference", "OR", qr_ref)

    # Copy QR context records to be the new OR context records for the next iteration.
    or_context_records = [
        ReferenceRecordLite(
            step_name="OR",
            concept=ctx.concept,
            reference=ctx.reference.copy() if ctx.reference else None
        ) 
        for ctx in states.context if ctx.step_name == 'QR'
    ]
    
    # Keep all non-OR records and add the new OR records.
    non_or_context = [c for c in states.context if c.step_name != 'OR']
    states.context = or_context_records + non_or_context

    states.set_current_step("OR")
    logging.debug("OR completed.")
    return states

def output_working_interpretation(states: States) -> States:
    """Check for loop completion and set status."""
    
    syntax_data = getattr(states, "syntax", {})
    loop_base_concept_name = getattr(syntax_data, "LoopBaseConcept", None)
    
    to_loop_elements = None
    values_block = getattr(states, "values", []) or []
    for item in values_block:
        if (getattr(item, "step_name", None) == "GR" and 
            getattr(item, "reference", None) is not None):
            to_loop_elements = item.reference
            break
            
    is_complete = False
    logging.debug(f"[OWI Step 1] Checking if loop is complete. Loop base concept name: {loop_base_concept_name}, To loop elements: {to_loop_elements}")
    if loop_base_concept_name and to_loop_elements:
        quantifier = Quantifier(workspace=states.workspace, loop_base_concept_name=loop_base_concept_name)
        concept_to_infer_name = (getattr(syntax_data, "ConceptToInfer") or [""])[0]
        if quantifier.check_all_base_elements_looped(to_loop_elements, in_loop_element_name=concept_to_infer_name):
            is_complete = True

    setattr(states.syntax, 'completion_status', is_complete)
    
    states.set_current_step("OWI")
    logging.debug(f"OWI completed. Completion status: {is_complete}")
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
    # Check if a persistent state is being passed in
    states = (input_data or {}).get("initial_states")
    if not isinstance(states, States):
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

def _build_demo_concepts_for_quant_controller() -> tuple[Concept, List[Concept], Concept, List[Concept]]:
    """Builds concepts for the outer quantification controller."""
    # Value Concept: The list of digits to be looped over.
    ref_digits = Reference(axes=["digit_pos"], shape=(4,))
    for i, v in enumerate([1, 8, 2, 5]):
        ref_digits.set(f"%({v})", digit_pos=i)
    concept_digits = Concept("{digit}", "digit", "digit_pos", ref_digits)

    # Context Concepts for Loop Control
    concept_current_digit = Concept("{digit}*", "digit*", "digit*")
    concept_partial_sum = Concept("{partial_sum}*", "partial_sum*", "partial_sum*")

    # Placeholder for the function concept, which will be the *result* of the inner imperative step
    quantification_concept = Concept("::(add_result)", "add_result", "f", Reference(axes=["f"], shape=(1,)))

    # Concept to Infer: The final accumulated sum.
    concept_to_infer = Concept("{sum}", "sum", "sum")

    return (
        concept_to_infer,
        [concept_digits],
        quantification_concept,
        [concept_current_digit, concept_partial_sum]
    )

def _build_demo_working_interpretation() -> Dict[str, Any]:
    """Provides the syntax needed for the QR step."""
    return {
        "syntax": {
            "marker": None, 
            "LoopBaseConcept": "{digit}",
            "ConceptToInfer": ["{sum}"],
            "InLoopConcept": {
                "{partial_sum}*": 1  # Carry over partial sum from 1 step ago
            },
            "completion_status": False
        }
    }

# --- Utility Functions ---
def _get_workspace_tensor_view(workspace: Dict) -> Dict:
    """Recursively converts a workspace of Reference objects to a dictionary of their tensors."""
    tensor_view = {}
    for key, value in workspace.items():
        if isinstance(value, dict):
            tensor_view[key] = _get_workspace_tensor_view(value)
        elif hasattr(value, 'tensor'): # Check if it's a Reference-like object
            tensor_view[key] = value.tensor
        else:
            tensor_view[key] = value
    return tensor_view

# --- Main Execution ---

def run_quantifying_sequence() -> States:
    """Demonstrates the iterative controller-actor pattern for quantification."""
    setup_logging(logging.DEBUG)

    # --- Mock Inner "Imperative" Sequence ---
    def mock_imperative_add_step(current_digit_concept: Concept, partial_sum_concept: Concept) -> Concept:
        """Simulates an inner sequence that performs addition for one loop step."""
        # Strip wrappers like %() to get raw numbers
        try:
            current_digit = int(str(current_digit_concept.reference.copy().tensor[0]).strip("%()"))
        except (AttributeError, IndexError, ValueError):
            current_digit = 0
        try:
            partial_sum = int(str(partial_sum_concept.reference.copy().tensor[0]).strip("%()"))
        except (AttributeError, IndexError, ValueError, TypeError):
            partial_sum = 1  # Default to 0 if no partial sum yet

        new_sum = current_digit + partial_sum
        logging.info(f"[Inner Worker] Adding {current_digit} + {partial_sum} = {new_sum}")

        # The result is a new concept holding the calculated sum
        ref_new_sum = Reference(axes=["sum"], shape=(1,)); ref_new_sum.set(f"%({new_sum})", sum=0)
        return Concept("{new_sum}", "new_sum", "sum", ref_new_sum)

    # --- Setup for Outer "Quantifying" Controller ---
    concept_to_infer, value_concepts, quantification_concept, context_concepts = _build_demo_concepts_for_quant_controller()
    
    quantification_inference = Inference(
        "quantifying_v2",
        concept_to_infer,
        value_concepts,
        quantification_concept, # Starts with a placeholder
        context_concepts=context_concepts
    )
    
    # --- Main Execution Loop ---
    working_interpretation = _build_demo_working_interpretation()
    iteration = 0
    
    # We need a state object that persists across loop iterations
    states = States()

    while not working_interpretation.get("syntax", {}).get("completion_status", False):
        iteration += 1
        logging.info(f"--- QUANTIFICATION LOOP: ITERATION {iteration} ---")
        if iteration > 5: # Safety break
            logging.warning("Safety break triggered to prevent infinite loop.")
            break

        # 1. Run the controller to get the current state and context for the inner worker
        logging.info("[Controller] Running to get context for inner worker...")
        
        # Pass the whole states object to persist workspace and other attributes
        workspace_tensor = _get_workspace_tensor_view(states.workspace)
        states = quantification_inference.execute(input_data={"working_interpretation": working_interpretation, "initial_states": states, "initial_workspace": workspace_tensor})
        
        # Check if the loop is complete right after the execution runs
        if states.syntax.completion_status == True:
            logging.info("[Controller] Loop is complete. Exiting loop.")
            break

        # Extract the current digit and partial sum from the controller's 'OR' context
        current_digit_ctx = next((c for c in states.context if c.step_name == 'OR' and c.concept and c.concept.name == "{digit}*"), Concept("","", "", Reference(axes=[], shape=())))
        partial_sum_ctx = next((c for c in states.context if c.step_name == 'OR' and c.concept and c.concept.name == "{partial_sum}*"), Concept("","", "", Reference(axes=[], shape=())))

        logging.info(f"[Controller] Current digit context for worker: {current_digit_ctx.reference.tensor}")
        logging.info(f"[Controller] Partial sum context for worker: {partial_sum_ctx.reference.tensor}")

        # 2. Run the inner worker (mocked) with the context provided by the controller
        new_sum_concept = mock_imperative_add_step(current_digit_ctx, partial_sum_ctx)

        # 3. Feed the result of the inner worker back to the controller
        # The result becomes the "function_concept" for the controller's next run
        quantification_inference.function_concept = new_sum_concept

        # 4. Renew the context concepts in the states object
        [current_digit, partial_sum] = context_concepts
        current_digit.reference = current_digit_ctx.reference.copy()
        partial_sum.reference = partial_sum_ctx.reference.copy()
        quantification_inference.context_concepts = [current_digit, partial_sum]
        
        # Update the working interpretation with the latest completion status from the state
        if hasattr(states, 'syntax') and hasattr(states.syntax, 'completion_status'):
            working_interpretation["syntax"]["completion_status"] = states.syntax.completion_status
        else:
            working_interpretation["syntax"]["completion_status"] = True # Failsafe

    logging.info("--- QUANTIFICATION COMPLETE ---")
    
    # Final state after loop terminates
    final_states = states
    final_ref = final_states.get_reference("inference", "OR")

    # Final log
    logger = logging.getLogger(__name__)
    if isinstance(final_ref, Reference):
        logger.info("--- Final Output (OR) ---")
        tensor_content = final_ref.get_tensor(ignore_skip=True)
        logger.info(f"Final Tensor: {tensor_content}")
        print("\n--- Final Output (OR) ---")
        # The result is a list of all the intermediate sums
        print(f"Tensor: {tensor_content}")
        # Expected: [['%(1)'], ['%(9)'], ['%(11)'], ['%(16)']]
    
    return final_states

if __name__ == "__main__":
    run_quantifying_sequence() 