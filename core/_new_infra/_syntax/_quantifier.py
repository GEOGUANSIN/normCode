from _reference import Reference, cross_product, element_action
import _logger
from _logger import logger
from copy import copy
from typing import Optional, Any, Tuple




class Quantifier:
    """
    A class that handles quantification processing for operators in a workspace.
    
    The Quantifier manages the state of looped elements and their references,
    providing methods to store, retrieve, and combine references across iterations.
    
    Key Features:
    - Manages a workspace dictionary to track quantification state
    - Handles nested element references and loop indices
    - Provides utilities for flattening and combining references
    
    Args:
        workspace (dict): Dictionary containing quantification state
        loop_base_concept_name (str): Name of the base concept being looped over
        loop_concept_index (int, optional): Starting loop index (default: 0)
    """
    
    def __init__(self, workspace: dict, loop_base_concept_name: str, loop_concept_index: int = 0):
        """
        Initialize the Quantifier with a workspace and base concept.
        
        Args:
            workspace (dict): Dictionary to store quantification state
            loop_base_concept_name (str): Name of the base concept being looped over
            loop_concept_index (int, optional): Starting index for the loop (default: 0)
        """
        self.workspace = workspace
        logger.debug(f"[Quantifier.__init__] Initialized with workspace keys: {list(workspace.keys())}, loop_base_concept_name: {loop_base_concept_name}, loop_concept_index: {loop_concept_index}")
        self.loop_base_concept_name = loop_base_concept_name
        self._initiate_subworkspace(loop_base_concept_name, loop_concept_index)

        # initiate the workspace for a specific CONCEPT's reference (after GP)
    def _initiate_subworkspace(self, loop_base_concept_name: str, loop_concept_index: int = 0) -> None:
        """
        Initialize a subworkspace for a specific concept and loop index.
        
        Creates a workspace key in the format "{loop_index}_{concept_name}"
        and initializes the current subworkspace.
        
        Args:
            loop_base_concept_name (str): Name of the base concept
            loop_concept_index (int, optional): Loop index (default: 0)
        """
        self.workspace_key = f"{loop_concept_index}_{loop_base_concept_name}"
        if self.workspace_key not in self.workspace.keys():
            self.workspace[self.workspace_key] = {}
        self.current_subworkspace = self.workspace[self.workspace_key]
        logger.debug(f"[Quantifier._initiate_subworkspace] workspace_key: {self.workspace_key}, current_subworkspace keys: {list(self.current_subworkspace.keys())}")
        self._log_current_subworkspace_tensors()

    def _get_list_at_index(self, input_list: list, index: int) -> Optional[Any]:
        """
        Retrieve an element from a list at a specific index.
        
        Handles nested lists and out-of-bounds indices.
        
        Args:
            input_list: Input list (can be nested)
            index (int): Index to retrieve
            
        Returns:
            Element at index or None if index is invalid
        """
        logger.debug(f"[Quantifier._get_list_at_index] input_list type: {type(input_list)}, index: {index}")
        try:
            if isinstance(input_list, list) and 0 <= index < len(input_list):
                logger.debug(f"[Quantifier._get_list_at_index] Returning element at index {index}: {input_list[index]}")
                return input_list[index]
            else:
                logger.debug(f"[Quantifier._get_list_at_index] Index {index} out of bounds or input is not a list.")
                return None
        except (IndexError, TypeError) as e:
            logger.error(f"[Quantifier._get_list_at_index] Exception: {e}")
            return None

    def _flatten_list(self, nested_list: list) -> list:
        """
        Recursively flatten a nested list.
        
        Args:
            nested_list: Input list (can be deeply nested)
            
        Returns:
            list: Flattened single-level list
        """
        logger.debug(f"[Quantifier._flatten_list] Flattening nested_list: {nested_list}")
        flattened = []
        def _flatten_recursive(item):
            if isinstance(item, list):
                for element in item:
                    _flatten_recursive(element)
            else:
                flattened.append(item)
        _flatten_recursive(nested_list)
        logger.debug(f"[Quantifier._flatten_list] Result: {flattened}")
        return flattened
        

    def _check_new_base_element_by_looped_base_element(self, current_looped_element_reference: Reference, loop_base_concept_name: str) -> bool:
        """
        Check if an element is new by comparing with workspace entries.
        
        Args:
            current_looped_element_reference: Reference to check
            loop_base_concept_name (str): Base concept name to match against
            
        Returns:
            bool: True if element is new (not in workspace), False otherwise
        """
        logger.debug(f"[Quantifier._check_new_base_element_by_looped_base_element] Checking for new element: tensor={getattr(current_looped_element_reference, 'tensor', None)}, loop_base_concept_name: {loop_base_concept_name}")
        element_found = False
        for loop_index in self.current_subworkspace.keys():
            if (loop_base_concept_name in self.current_subworkspace[loop_index].keys() and 
                current_looped_element_reference.tensor == self.current_subworkspace[loop_index][loop_base_concept_name].tensor):
                logger.debug(f"[Quantifier._check_new_base_element_by_looped_base_element] Found existing element at loop_index: {loop_index}")
                element_found = True
                break
        logger.debug(f"[Quantifier._check_new_base_element_by_looped_base_element] Is new: {not element_found}")
        return not element_found

    def _check_index_of_current_looped_base_element(self, looped_base_reference: Reference) -> int:
        """
        Find existing loop index for a reference or get next available index.
        
        Args:
            looped_base_reference: Reference to find
            
        Returns:
            int: Existing index if found, next available index otherwise
        """
        logger.debug(f"[Quantifier._check_index_of_current_looped_base_element] Checking for looped_base_reference.tensor: {getattr(looped_base_reference, 'tensor', None)}")
        for existing_loop_index in self.current_subworkspace.keys():
            if (self.loop_base_concept_name in self.current_subworkspace[existing_loop_index] and 
                self.current_subworkspace[existing_loop_index][self.loop_base_concept_name].tensor == looped_base_reference.tensor):
                logger.debug(f"[Quantifier._check_index_of_current_looped_base_element] Found at index: {existing_loop_index}")
                return existing_loop_index
        next_index = self._get_next_loop_index()
        logger.debug(f"[Quantifier._check_index_of_current_looped_base_element] Not found, returning next available index: {next_index}")
        return next_index

    def _get_next_loop_index(self) -> int:
        """
        Get the next available loop index in the subworkspace.
        """
        logger.debug(f"[Quantifier._get_next_loop_index] Current subworkspace keys: {list(self.current_subworkspace.keys())}")
        new_loop_index = 0
        for existing_loop_index in self.current_subworkspace.keys():
            if existing_loop_index > new_loop_index:
                new_loop_index = existing_loop_index
        logger.debug(f"[Quantifier._get_next_loop_index] Next loop index: {new_loop_index + 1}")
        return new_loop_index + 1

    def store_new_base_element(self, looped_base_reference: Reference) -> int:
        """
        Store a new base element reference in the workspace.
        
        Args:
            looped_base_reference: Reference to store
            
        Returns:
            int: Loop index where element was stored
        """
        logger.debug(f"[Quantifier.store_new_base_element] Storing base element: tensor={getattr(looped_base_reference, 'tensor', None)}")
        loop_index = self._check_index_of_current_looped_base_element(looped_base_reference)
        if loop_index not in self.current_subworkspace:
            self.current_subworkspace[loop_index] = {}
            logger.debug(f"[Quantifier.store_new_base_element] Initialized new entry at loop_index: {loop_index}")
        self.current_subworkspace[loop_index][self.loop_base_concept_name] = looped_base_reference
        logger.debug(f"[Quantifier.store_new_base_element] Stored at loop_index: {loop_index}")
        return loop_index


    def store_new_in_loop_element(self, looped_base_reference: Reference, looped_concept_name: str, looped_concept_reference: Reference) -> int:
        """
        Store a new in-loop element reference under a concept name.
        
        Args:
            looped_base_reference: Base reference to associate with
            looped_concept_name (str): Concept name to store under
            looped_concept_reference: Reference to store
            
        Returns:
            int: Loop index where element was stored
            
        Raises:
            ValueError: If base reference not found in subworkspace
        """
        logger.debug(f"[Quantifier.store_new_in_loop_element] Storing in-loop element: base tensor={getattr(looped_base_reference, 'tensor', None)}, concept_name: {looped_concept_name}, concept_reference.tensor={getattr(looped_concept_reference, 'tensor', None)}")
        loop_index = self._check_index_of_current_looped_base_element(looped_base_reference)
        if loop_index not in self.current_subworkspace:
            logger.error(f"[Quantifier.store_new_in_loop_element] Base reference not found in subworkspace for loop_index: {loop_index}")
            raise ValueError(f"The {looped_base_reference} is not in the current_subworkspace")
        self.current_subworkspace[loop_index][looped_concept_name] = looped_concept_reference
        logger.debug(f"[Quantifier.store_new_in_loop_element] Stored at loop_index: {loop_index}")
        return loop_index


    def retireve_next_base_element(self, to_loop_element_reference: Reference, current_loop_base_element: Optional[Reference] = None) -> Tuple[Optional[Reference], Optional[int]]:
        """
        Retrieve the next unprocessed base element from a reference.
        
        Skips elements matching current_loop_base_element and those already in workspace.
        
        Args:
            to_loop_element_reference: Reference containing elements
            current_loop_base_element: Current element to skip (optional)
            
        Returns:
            tuple: (element_reference, loop_index) or (None, None) if no elements left
        """
        logger.debug(f"[Quantifier.retireve_next_base_element] START: to_loop_element_reference.tensor={getattr(to_loop_element_reference, 'tensor', None)}, type={type(to_loop_element_reference)}, current_loop_base_element.tensor={getattr(current_loop_base_element, 'tensor', None) if current_loop_base_element else None}")
        logger.debug(f"[Quantifier.retireve_next_base_element] current_subworkspace keys: {list(self.current_subworkspace.keys())}")
        current_loop_index = 0
        max_iterations = 1000
        while True:
            logger.debug(f"[Quantifier.retireve_next_base_element] Loop index: {current_loop_index}")
            get_element_function = lambda x: self._get_list_at_index(x, current_loop_index)
            current_to_loop_element_reference = element_action(get_element_function, [to_loop_element_reference.copy()])
            logger.debug(f"[Quantifier.retireve_next_base_element] current_to_loop_element_reference.tensor: {getattr(current_to_loop_element_reference, 'tensor', None)}")
            elements = self._flatten_list(current_to_loop_element_reference.tensor.copy())
            logger.debug(f"[Quantifier.retireve_next_base_element] elements: {elements}")
            if all(e is None or e == "@#SKIP#@" for e in elements):
                logger.debug(f"[Quantifier.retireve_next_base_element] All elements are None or SKIP at index {current_loop_index}, breaking loop.")
                break
            if current_loop_base_element is not None:
                try:
                    current_tensor = getattr(current_to_loop_element_reference, 'tensor', None)
                    base_tensor = getattr(current_loop_base_element, 'tensor', None)
                    logger.debug(f"[Quantifier.retireve_next_base_element] Comparing current_tensor: {current_tensor} with base_tensor: {base_tensor}")
                    if current_tensor == base_tensor:
                        logger.debug(f"[Quantifier.retireve_next_base_element] current_tensor matches base_tensor, incrementing index.")
                        current_loop_index += 1
                        continue
                except Exception as e:
                    logger.error(f"[Quantifier.retireve_next_base_element] Error comparing tensors: {e}")
            found_in_workspace = False
            for loop_index in self.current_subworkspace.keys():
                logger.debug(f"[Quantifier.retireve_next_base_element] Checking workspace at loop_index {loop_index}")
                if self.loop_base_concept_name in self.current_subworkspace[loop_index].keys():
                    workspace_ref = self.current_subworkspace[loop_index][self.loop_base_concept_name]
                    workspace_tensor = getattr(workspace_ref, 'tensor', None)
                    logger.debug(f"[Quantifier.retireve_next_base_element] Workspace tensor: {workspace_tensor}")
                    if current_to_loop_element_reference.tensor == workspace_tensor:
                        logger.debug(f"[Quantifier.retireve_next_base_element] Found tensor in workspace at index {loop_index}, incrementing current_loop_index.")
                        current_loop_index += 1
                        found_in_workspace = True
                        break
            if found_in_workspace:
                continue
            logger.debug(f"[Quantifier.retireve_next_base_element] Returning element at index {current_loop_index}")
            return current_to_loop_element_reference, current_loop_index
            if current_loop_index > max_iterations:
                logger.error("[Quantifier.retireve_next_base_element] Exceeded max iterations, stopping to avoid infinite loop.")
                break
        logger.debug(f"[Quantifier.retireve_next_base_element] END: returning None, None")
        return current_to_loop_element_reference, current_loop_index



    def check_all_base_elements_looped(self, to_loop_element_reference: Reference, in_loop_element_name: Optional[str] = None) -> bool:
        """
        Check if all elements in a reference have been processed.
        
        Args:
            to_loop_element_reference: Reference containing elements to check
            in_loop_element_name (str, optional): Additional concept to check for
            
        Returns:
            bool: True if all elements processed (and concept exists if specified)
        """
        logger.debug(f"[Quantifier.check_all_base_elements_looped] Checking all elements in tensor: {getattr(to_loop_element_reference, 'tensor', None)}, in_loop_element_name: {in_loop_element_name}")
        current_loop_index = 0
        while True:
            get_element_function = lambda x: self._get_list_at_index(x, current_loop_index)
            current_to_loop_element_reference = element_action(get_element_function, [to_loop_element_reference.copy()])
            elements = self._flatten_list(current_to_loop_element_reference.tensor.copy())
            logger.debug(f"[Quantifier.check_all_base_elements_looped] elements at index {current_loop_index}: {elements}")
            if all(e is None or e == "@#SKIP#@" for e in elements):
                logger.debug(f"[Quantifier.check_all_base_elements_looped] All elements processed at index {current_loop_index}")
                current_loop_index += 1
                break
            element_found = False
            matching_loop_index = None
            for loop_index in self.current_subworkspace.keys():
                if (self.loop_base_concept_name in self.current_subworkspace[loop_index].keys() and 
                    current_to_loop_element_reference.tensor == self.current_subworkspace[loop_index][self.loop_base_concept_name].tensor):
                    element_found = True
                    matching_loop_index = loop_index
                    logger.debug(f"[Quantifier.check_all_base_elements_looped] Found element at loop_index: {loop_index}")
                    break
            if not element_found:
                logger.debug(f"[Quantifier.check_all_base_elements_looped] Element not found at index {current_loop_index}, returning False")
                return False
            if in_loop_element_name is not None and matching_loop_index is not None:
                if in_loop_element_name not in self.current_subworkspace[matching_loop_index].keys():
                    logger.debug(f"[Quantifier.check_all_base_elements_looped] In-loop element '{in_loop_element_name}' not found in loop index {matching_loop_index}")
                    return False
            current_loop_index += 1
        logger.debug(f"[Quantifier.check_all_base_elements_looped] All elements found and processed.")
        return True

    def combine_all_looped_elements_by_concept(self, to_loop_element_reference: Reference, concept_name: str) -> Optional[Reference]:
        """
        Combine references for a concept across all looped elements.
        
        Args:
            to_loop_element_reference: Reference containing elements to loop over
            concept_name (str): Concept name to combine
        
        Returns:
            Reference: Combined reference of all elements for the concept
                    or None if no references found
        """
        logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] START: concept_name={concept_name}, to_loop_element_reference.tensor={getattr(to_loop_element_reference, 'tensor', None)}")
        current_loop_index = 0
        all_concept_references = []
        while True:
            logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] Loop index: {current_loop_index}")
            get_element_function = lambda x: self._get_list_at_index(x, current_loop_index)
            current_to_loop_element_reference = element_action(get_element_function, [to_loop_element_reference.copy()])
            logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] current_to_loop_element_reference.tensor: {getattr(current_to_loop_element_reference, 'tensor', None)}")
            elements = self._flatten_list(current_to_loop_element_reference.tensor.copy())
            logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] elements at index {current_loop_index}: {elements}")
            if all(e is None or e == "@#SKIP#@" for e in elements):
                logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] End of elements at index {current_loop_index}")
                current_loop_index += 1
                break
            matching_loop_index = None
            for loop_index in self.current_subworkspace.keys():
                logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] Checking subworkspace loop_index {loop_index}")
                if (self.loop_base_concept_name in self.current_subworkspace[loop_index].keys() and 
                    current_to_loop_element_reference.tensor == self.current_subworkspace[loop_index][self.loop_base_concept_name].tensor):
                    matching_loop_index = loop_index
                    logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] Found matching loop_index {matching_loop_index} for element {getattr(current_to_loop_element_reference, 'tensor', None)}")
                    break
            if matching_loop_index is not None and concept_name in self.current_subworkspace[matching_loop_index].keys():
                concept_reference = self.current_subworkspace[matching_loop_index][concept_name]
                all_concept_references.append(concept_reference)
                logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] Added concept reference for index {matching_loop_index}: {getattr(concept_reference, 'tensor', None)} with axes {getattr(concept_reference, 'axes', None)}")
            else:
                logger.warning(f"[Quantifier.combine_all_looped_elements_by_concept] Concept '{concept_name}' not found for loop index {matching_loop_index}")
            current_loop_index += 1
        logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] Collected {len(all_concept_references)} references for concept '{concept_name}'")
        if all_concept_references:
            combined_reference = cross_product(all_concept_references)
            logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] Combined reference tensor: {getattr(combined_reference, 'tensor', None)}, axes: {getattr(combined_reference, 'axes', None)}")
            logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] END: returning combined reference")
            return combined_reference
        else:
            logger.warning(f"[Quantifier.combine_all_looped_elements_by_concept] No references found for concept '{concept_name}'")
            logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] END: returning None")
            return None

    def retrieve_next_in_loop_element(self, concept_name: str, mode: str = 'carry_over', current_loop_index: int = 0, carry_index: int = 0) -> Reference:
        """
        Retrieve the next in-loop element for a concept.
        
        Args:
            concept_name (str): Concept name to retrieve
            mode (str): Retrieval mode ('carry_over' only currently supported)
            current_loop_index (int): Current loop index
            carry_index (int): Carry offset index
            
        Returns:
            Reference: Retrieved element reference
        """
        logger.debug(f"[Quantifier.retrieve_next_in_loop_element] concept_name: {concept_name}, mode: {mode}, current_loop_index: {current_loop_index}, carry_index: {carry_index}")
        if mode == 'carry_over':
            if current_loop_index > carry_index:
                concept_reference = self.current_subworkspace[current_loop_index - carry_index][concept_name]
                logger.debug(f"[Quantifier.retrieve_next_in_loop_element] Retrieved concept_reference.tensor: {getattr(concept_reference, 'tensor', None)}")
            else:
                concept_reference = Reference(initial_value=None, axes=None, shape=None)
                logger.debug(f"[Quantifier.retrieve_next_in_loop_element] Returning empty Reference (None)")
        return concept_reference

    def _log_current_subworkspace_tensors(self) -> None:
        """
        Log the current state of the subworkspace.
        
        Shows for each loop index: concept names and their reference tensors.
        """
        msg = "[Quantifier._log_current_subworkspace_tensors] current_subworkspace:"
        for loop_index, concept_dict in self.current_subworkspace.items():
            msg += f"\n  loop_index={loop_index}:"
            for concept_name, ref in concept_dict.items():
                tensor = getattr(ref, 'tensor', None)
                msg += f"  {concept_name}: tensor={tensor};"
        logger.debug(msg)

from ._state_models import (
    AgentSequenceState, StepDescriptor, ReferenceInterpretationState,
    FunctionReference, ValuesReference, ContextReference, InferenceReference,
    ToolSpec, ConceptInfo, StepReferenceAccessor 
)


# States-only QR step

def quantifying_references(states):
    """
    Quantifying References (QR) step using only the `states` object.

    Expectations:
    - states.syntax contains quantification syntax data (parsed dict) with keys like
      'LoopBaseConcept', 'ConceptToInfer', 'InLoopConcept'.
    - The to-loop elements reference comes from the Grouping References step result,
      stored under states.values with step_name == 'GR' (preferred) or states.inference
      with step_name == 'GA' (fallback).
    - Workspace is stored on states.workspace (dict). If missing, it will be created.

    Side effects:
    - Updates states.context carry-over references and advances the current loop base.
    - Updates states.inference with a 'QR' entry holding the combined reference when a
      new element is processed.
    """
    st = StepReferenceAccessor

    def _ensure_reference(ref: Optional[Reference]) -> Reference:
        if isinstance(ref, Reference):
            return ref
        return Reference(initial_value=None, axes=None, shape=None)

    # 1) Read syntax data (parsed quantification)
    syntax_data = getattr(states, "syntax", {}) or {}
    if not isinstance(syntax_data, dict):
        logger.warning("[QR] states.syntax is not a dict; QR step requires parsed syntax data. Skipping.")
        return states

    loop_base_concept_name = syntax_data.get("LoopBaseConcept")
    concept_to_infer_list = syntax_data.get("ConceptToInfer") or []
    in_loop_spec = syntax_data.get("InLoopConcept")
    if not loop_base_concept_name or not concept_to_infer_list:
        logger.warning("[QR] Missing LoopBaseConcept or ConceptToInfer in syntax data. Skipping.")
        return states
    concept_to_infer_name = concept_to_infer_list[0]
    current_loop_base_concept_name = f"{loop_base_concept_name}*"

    # 2) Get to-loop elements reference (GR preferred, GA fallback)
    to_loop_elements: Optional[Reference] = None
    values_block = getattr(states, "values", []) or []
    for item in values_block:
        try:
            if getattr(item, "step_name", None) == "GR" and getattr(item, "reference", None) is not None:
                to_loop_elements = item.reference
                break
        except Exception:
            continue
    if to_loop_elements is None:
        logger.warning("[QR] No to-loop elements found in states.values for step 'GR'. Skipping.")
        return states

    # 3) Prepare workspace
    if not hasattr(states, "workspace") or getattr(states, "workspace") is None:
        setattr(states, "workspace", {})
    workspace = getattr(states, "workspace")

    # 4) Current loop base element from context (if any)
    current_loop_base_context_item = None
    context_block = getattr(states, "context", []) or []
    for ctx in context_block:
        try:
            concept_info = getattr(ctx, "concept", None)
            concept_name = getattr(concept_info, "name", None) if concept_info is not None else getattr(ctx, "name", None)
            if concept_name == current_loop_base_concept_name:
                current_loop_base_context_item = ctx
                break
        except Exception:
            continue

    current_loop_base_element_opt = None
    if current_loop_base_context_item is not None:
        current_loop_base_element_opt = getattr(current_loop_base_context_item, "reference", None)

    # 5) Determine current concept element from function block (first available reference)
    current_concept_element_opt = None
    function_block = getattr(states, "function", []) or []
    for fn in function_block:
        try:
            ref = getattr(fn, "reference", None)
            if ref is not None:
                current_concept_element_opt = ref
                break
        except Exception:
            continue

    # 6) Initialize quantifier and retrieve next element
    quantifier = Quantifier(workspace=workspace, loop_base_concept_name=loop_base_concept_name)
    next_current_loop_base_element_opt, _ = quantifier.retireve_next_base_element(
        to_loop_element_reference=to_loop_elements,
        current_loop_base_element=current_loop_base_element_opt,
    )

    # 7) Decide if current element is new
    is_new = False
    if current_loop_base_element_opt is not None and isinstance(current_loop_base_element_opt, Reference):
        if quantifier._check_new_base_element_by_looped_base_element(current_loop_base_element_opt, current_loop_base_concept_name):
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
        try:
            concept_info = getattr(ctx, "concept", None)
            ctx_name = getattr(concept_info, "name", None) if concept_info is not None else getattr(ctx, "name", None)
            if ctx_name == current_loop_base_concept_name:
                setattr(ctx, "reference", next_current_loop_base_element.copy())
                continue
            if in_loop_spec is not None and ctx_name in in_loop_spec:
                # Ensure ctx_name is a valid string for downstream calls
                if not isinstance(ctx_name, str):
                    continue
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
        except Exception as e:
            logger.debug(f"[QR] Skipping context update due to error: {e}")
            continue

    # 11) Combine all stored references for the inferred concept
    combined_reference: Optional[Reference] = None
    if is_new:
        combined_reference = quantifier.combine_all_looped_elements_by_concept(
            to_loop_element_reference=to_loop_elements,
            concept_name=concept_to_infer_name,
        )
        if combined_reference is not None:
            # Axis normalization
            loop_base_axis = None
            current_loop_axis = None
            try:
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
            except Exception:
                pass
            if loop_base_axis is not None and current_loop_axis is not None:
                new_axes = combined_reference.axes.copy()
                # Last axis becomes the inferred concept's axis (use concept name)
                new_axes[-1] = concept_to_infer_name
                # Replace transient current-loop axis with the base axis
                if current_loop_axis in new_axes:
                    new_axes[new_axes.index(current_loop_axis)] = loop_base_axis
                combined_reference.axes = new_axes

    # 12) Write result into states.inference under QR if the entry exists
    if combined_reference is not None:
        for inf in getattr(states, "inference", []) or []:
            try:
                if getattr(inf, "step_name", None) == "QR":
                    setattr(inf, "reference", combined_reference)
                    break
            except Exception:
                continue

    return states
    