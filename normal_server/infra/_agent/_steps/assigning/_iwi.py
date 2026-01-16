import logging
from typing import Dict, Any

from infra._core import Inference
from infra._agent._body import Body
from infra._states._assigning_states import States
from infra._states._common_states import ReferenceRecordLite


def input_working_interpretation(
    inference: Inference,
    states: States,
    body: Body,
    working_interpretation: Dict[str, Any] | None = None,
) -> States:
    """Initialize states with syntax info and placeholder records."""
    if working_interpretation:
        syntax_info = working_interpretation.get("syntax", {})
        states.syntax.marker = syntax_info.get("marker")
        states.syntax.assign_source = syntax_info.get("assign_source")
        states.syntax.assign_destination = syntax_info.get("assign_destination")
        states.syntax.by_axes = syntax_info.get("by_axes", [])
        # Abstraction fields
        states.syntax.face_value = syntax_info.get("face_value")
        states.syntax.axis_names = syntax_info.get("axis_names")
        # Derelation fields
        states.syntax.selector = syntax_info.get("selector")
        # Identity fields
        states.syntax.canonical_concept = syntax_info.get("canonical_concept")
        states.syntax.alias_concept = syntax_info.get("alias_concept")

    states.workspace = working_interpretation.get("workspace", {})
    flow_info = working_interpretation.get("flow_info", {})
    states.flow_index = flow_info.get("flow_index")

    # Seed lists with empty records for each step
    for step in ["AR", "OR"]:
        states.inference.append(ReferenceRecordLite(step_name=step))

    states.set_current_step("IWI")
    logging.debug(f"IWI completed. Syntax marker: {states.syntax.marker}")
    return states 