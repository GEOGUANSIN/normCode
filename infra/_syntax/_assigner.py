import logging
import re
import json
from typing import Optional, List, Dict, Any, Callable, Union

from infra._core import Reference


class UnpackedList(list):
    """Wrapper to signal that a list should be exploded into multiple inputs."""
    pass


def _parse_face_value(face_value: str) -> tuple[Any, bool]:
    """
    Parses a face value string into data and whether it's a singleton.
    
    Returns:
        (parsed_data, is_singleton)
        - For perceptual signs: (sign_string, True)
        - For nested lists: (parsed_list, False)
    """
    if not isinstance(face_value, str):
        # Already parsed (e.g., passed as list directly)
        is_singleton = not isinstance(face_value, list)
        return face_value, is_singleton
    
    face_value = face_value.strip()
    
    # Check if it's a perceptual sign: %{...}...(...) or %(...)
    if face_value.startswith('%'):
        return face_value, True
    
    # Check if it's a list literal: [...] 
    if face_value.startswith('['):
        try:
            # Try to parse as JSON
            parsed = json.loads(face_value)
            return parsed, False
        except json.JSONDecodeError:
            # Might be a NormCode list syntax, treat as singleton
            return face_value, True
    
    # Default: treat as singleton string value
    return face_value, True


def _flatten_to_list(data):
    """Recursively flattens nested lists into a single list of elements."""
    if not isinstance(data, list):
        return [data]

    flat_list = []
    for item in data:
        flat_list.extend(_flatten_to_list(item))
    return flat_list


class Assigner:
    """Encapsulates the logic for assignment operations."""

    def identity(self, concept_a: str, concept_b: str, blackboard) -> bool:
        """
        Registers an identity relationship: concept_a IS concept_b.
        
        This is a concept-level operation (not reference-level). After identity:
        - Both concept names resolve to the same underlying concept
        - Completing one completes the other
        - They share the same reference
        
        Args:
            concept_a: First concept name
            concept_b: Second concept name (will be aliased to first)
            blackboard: The Blackboard instance to register the alias
            
        Returns:
            True if identity was registered successfully
        """
        if blackboard is None:
            logging.error("Assigner.identity requires a blackboard instance")
            return False
        
        blackboard.register_identity(concept_a, concept_b)
        logging.info(f"Assigner: Registered identity between '{concept_a}' and '{concept_b}'")
        return True

    def abstraction(
        self, 
        face_value: Union[str, List], 
        axis_names: Optional[List[str]] = None,
        default_axis: str = "_none_axis"
    ) -> Reference:
        """
        Creates a Reference directly from a literal face value (abstraction).
        
        This reifies the definition itself as data, rather than looking up a computed reference.
        Used for ground concepts and template definitions.
        
        Args:
            face_value: The literal content to become the reference:
                - Perceptual sign string: "%{norm}...(content)" → singleton
                - Nested list: [[val1, val2], [val3]] → structured reference
                - Plain string: "content" → singleton
            axis_names: Optional list of axis names for structured data.
                       If not provided and data is structured, uses default naming.
            default_axis: Axis name to use for singleton values.
        
        Returns:
            Reference containing the face value as data.
        
        Examples:
            # Singleton perceptual sign
            abstraction("%{file_location}a1b(data/input.txt)")
            → Reference(axes=["_none_axis"], tensor=["%{file_location}a1b(data/input.txt)"])
            
            # Structured list with axes
            abstraction([["123", "456"], ["789", "012"]], axis_names=["pair", "number"])
            → Reference(axes=["pair", "number"], tensor=[["123", "456"], ["789", "012"]])
        """
        parsed_data, is_singleton = _parse_face_value(face_value)
        
        if is_singleton:
            # Single value → wrap in singleton reference
            result = Reference.from_data([parsed_data], axis_names=[default_axis])
            logging.debug(f"Assigner.abstraction: Created singleton reference with axis '{default_axis}'")
        else:
            # Structured data → create reference with provided or inferred axes
            if axis_names:
                result = Reference.from_data(parsed_data, axis_names=axis_names)
                logging.debug(f"Assigner.abstraction: Created structured reference with axes {axis_names}")
            else:
                # Infer axes from data depth
                result = Reference.from_data(parsed_data)
                logging.debug(f"Assigner.abstraction: Created structured reference with inferred axes {result.axes}")
        
        return result

    def specification(self, source_refs: List[Optional[Reference]], dest_ref: Optional[Reference]) -> Optional[Reference]:
        """
        Performs specification (assignment) from a prioritized list of source references.
        Returns the first valid (non-None and not empty) source reference from the list.
        If no source is valid, returns the destination reference as a fallback.
        """
        for source_ref in source_refs:
            if source_ref and source_ref.get_tensor(ignore_skip=True):
                logging.info(f"Assigner: Found valid source reference.")
                return source_ref.copy()

        logging.warning(f"No valid source reference found in the provided list; using destination reference as fallback.")
        if dest_ref:
            return dest_ref.copy()

        # If all sources and destination are None, return an empty reference
        return Reference(axes=["result"], shape=(0,))

    def continuation(self, source_ref: Optional[Reference], dest_ref: Optional[Reference], by_axes: Optional[List[str]] = None) -> Reference:
        """
        Performs continuation (addition/concatenation) using the Reference.append() method.
        Appends the data from source_ref to dest_ref.
        If dest_ref has data, appends along the axis specified in by_axes, or the first axis if not specified.
        If dest_ref is None or empty, it effectively returns a copy of source_ref.
        """
        if dest_ref is None:
            return source_ref.copy() if source_ref else Reference.from_data([])

        if source_ref is None:
            return dest_ref.copy()

        logging.debug(f"Continuation called with by_axes: {by_axes}")

        if by_axes and by_axes[0] in dest_ref.axes:
            append_axis = by_axes[0]
        else:
            append_axis = dest_ref.axes[0]
            if by_axes:
                logging.warning(f"Provided axis '{by_axes[0]}' not in destination axes {dest_ref.axes}. Defaulting to '{append_axis}'.")

        logging.debug(f"Appending with axis: '{append_axis}'")
        return dest_ref.append(source_ref, by_axis=append_axis)

    def derelation(self, selector: Dict[str, Any]) -> Callable[[Any], Any]:
        """
        Returns a function (closure) configured with the selector logic for pure structural selection.
        Does NOT handle perception, decoding, or branching.
        """
        index = selector.get("index")
        key = selector.get("key")
        unpack = selector.get("unpack", False)
        unpack_before = selector.get("unpack_before_selection", False)

        def selector_action(element):
            # 1. Determine target for selection (handling unpack_before)
            target = element
            if unpack_before and isinstance(element, list):
                results = []
                for item in element:
                    selected_item = item
                    if key is not None and isinstance(selected_item, dict):
                        selected_item = selected_item.get(key)
                    results.append(selected_item)
                return UnpackedList(results)

            # 2. Standard Selection
            selected = target
            if index is not None and isinstance(selected, list) and len(selected) > index:
                selected = selected[index]

            if key is not None and isinstance(selected, dict):
                selected = selected.get(key)

            # 3. Handle Unpack After
            if unpack and isinstance(selected, list):
                return UnpackedList(selected)

            return selected

        return selector_action
