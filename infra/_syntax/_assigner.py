import logging
from typing import Optional

from infra._core import Reference


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

    def specification(self, source_ref: Optional[Reference], dest_ref: Optional[Reference]) -> Optional[Reference]:
        """
        Performs specification (assignment).
        Returns the source reference, or the destination reference if the source is None.
        """
        if source_ref:
            return source_ref.copy()

        logging.warning(f"Source reference is missing for specification; using destination reference as fallback.")
        if dest_ref:
            return dest_ref.copy()

        # If both are None, return an empty reference
        return Reference(axes=["result"], shape=(0,))

    def continuation(self, source_ref: Optional[Reference], dest_ref: Optional[Reference]) -> Reference:
        """
        Performs continuation (addition/concatenation).
        Returns a new reference with the source's data appended to the destination's data.
        """
        source_val = source_ref.get() if source_ref else []
        dest_val = dest_ref.get() if dest_ref else []

        source_flat = _flatten_to_list(source_val)
        dest_flat = _flatten_to_list(dest_val)

        new_val = dest_flat + source_flat
        return Reference.from_data(new_val, axis_names=dest_ref.axes)
