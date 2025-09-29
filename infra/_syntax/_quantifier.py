import logging
from typing import Any, Dict, List, Optional, Tuple

from infra._core import Reference, element_action, cross_product, join


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

    def _check_new_base_element_by_looped_base_element(self, current_looped_element_reference: Reference) -> bool:
        # First, check if the reference itself is empty. If so, it can't be "new".
        if self._is_reference_empty(current_looped_element_reference):
            logging.debug(f"[_check_new_base_element] Input element is empty. Returning False (not new).")
            return False

        loop_base_concept_name = self.loop_base_concept_name

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

    def combine_all_looped_elements_by_concept(self, to_loop_element_reference: Reference, concept_name: str, axis_name: str = None) -> Optional[Reference]:
        all_concept_references = []

        # Sort by loop index to ensure order
        sorted_loop_indices = sorted(self.current_subworkspace.keys())

        for loop_index in sorted_loop_indices:
            if concept_name in self.current_subworkspace[loop_index]:
                 all_concept_references.append(self.current_subworkspace[loop_index][concept_name])

        if not all_concept_references:
            return None

        # If axis_name is not provided, use a default that reflects the looping structure.
        join_axis_name = axis_name if axis_name is not None else 'loop_index'

        # Join all references along the new axis.
        combined_ref = join(all_concept_references, new_axis_name=join_axis_name)

        return combined_ref

    def retrieve_next_in_loop_element(self, concept_name: str, mode: str = 'carry_over', current_loop_index: int = 0, carry_index: int = 0, initial_reference: Optional[Reference] = None) -> Reference:
        if mode == 'carry_over':
            # The current_loop_index in the original file is the *value* of the carry, not the loop iteration index
            if current_loop_index > 0:
                 # We need to find the previous loop state. The workspace keys are loop indices.
                 # Let's find the largest index that is smaller than the next available index.

                # Get the next theoretical index
                next_idx = self._get_next_loop_index()

                # The "current" loop index for retrieval purposes is the one just before the next one to be added
                last_added_idx = next_idx - 1
                retrieval_idx = last_added_idx - (current_loop_index - 1)

                if retrieval_idx <= 0:
                    if initial_reference:
                        return initial_reference
                    else:
                        return Reference(axes=[], shape=())

                if retrieval_idx in self.current_subworkspace and concept_name in self.current_subworkspace[retrieval_idx]:
                    return self.current_subworkspace[retrieval_idx][concept_name]

        return Reference(axes=[], shape=()) 