import logging
from typing import Optional

from infra._core import Reference


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

        # Ensure both are lists for concatenation
        if not isinstance(source_val, list):
            source_val = [source_val]
        if not isinstance(dest_val, list):
            dest_val = [dest_val]

        new_val = dest_val + source_val
        return Reference.from_data(new_val)
