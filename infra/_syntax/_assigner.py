import logging
from typing import Optional, List, Dict, Any, Callable

from infra._core import Reference


class UnpackedList(list):
    """Wrapper to signal that a list should be exploded into multiple inputs."""
    pass


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
