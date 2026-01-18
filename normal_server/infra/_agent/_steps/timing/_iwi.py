from typing import Any, Dict
from infra._core._inference import Inference
from infra._states._timing_states import States
from infra._agent._body import Body


def input_working_interpretation(
    inference: Inference,
    states: States,
    body: Body,
    working_interpretation: Dict[str, Any] | None = None,
) -> States:
    """Initialize states with syntax info, blackboard, workspace, and flow_index."""
    if working_interpretation:
        syntax_info = working_interpretation.get("syntax", {})
        states.syntax.marker = syntax_info.get("marker")
        states.syntax.condition = syntax_info.get("condition")
        states.blackboard = working_interpretation.get("blackboard")
        states.workspace = working_interpretation.get("workspace", {})
        # Get flow_index from inference entry if available
        flow_info = working_interpretation.get("flow_info", {})
        states.flow_index = flow_info.get("flow_index")

    states.set_current_step("IWI")
    return states