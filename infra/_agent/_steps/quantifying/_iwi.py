from typing import Any, Dict
from types import SimpleNamespace
import logging

from infra._core._inference import Inference
from infra._states._quantifying_states import States
from infra._states._common_states import ReferenceRecordLite
from infra._agent._body import Body

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def input_working_interpretation(
    inference: Inference,
    states: States,
    body: Body,
    working_interpretation: Dict[str, Any] | None = None,
) -> States:
    """Initialize states with syntax info and placeholder records."""
    if working_interpretation:
        states.syntax = SimpleNamespace(**working_interpretation.get("syntax", {}))

        states.workspace = working_interpretation.get("workspace", {})
        logger.debug(f"[IWI Step 1] Workspace: {states.workspace}")

    # Clear previous state to prevent accumulation in loops
    states.function = []
    states.values = []
    states.context = []
    states.inference = []

    # Seed lists with empty records for each step
    for step in ["GR", "QR", "OR"]:
        states.inference.append(ReferenceRecordLite(step_name=step))

    states.set_current_step("IWI")
    logger.debug(f"IWI completed. Syntax: {states.syntax}")
    return states 