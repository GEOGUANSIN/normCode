from typing import Any, Dict
import logging

from infra._core import Inference
from infra._states._grouping_states import States
from infra._states._common_states import ReferenceRecordLite
from infra._agent._body import Body


def input_working_interpretation(
    inference: Inference,
    states: States,
    body: Body,
    working_interpretation: Dict[str, Any] | None = None,
) -> States:
    """Initialize states with syntax info and placeholder records."""
    if working_interpretation:
        states.syntax.marker = working_interpretation.get("syntax", {}).get("marker")
        states.syntax.by_axis_concepts = working_interpretation.get("syntax", {}).get("by_axis_concepts", [])

    # Seed lists with empty records for each step
    for step in ["GR", "OR"]:
        states.inference.append(ReferenceRecordLite(step_name=step))

    states.set_current_step("IWI")
    logging.debug(f"IWI completed. Syntax marker: {states.syntax.marker}. By axis concepts: {states.syntax.by_axis_concepts}")
    return states 