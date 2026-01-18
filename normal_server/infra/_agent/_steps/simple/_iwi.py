from typing import Any, Dict
from infra._core._inference import Inference
from infra._states._simple_states import States
from infra._states._common_states import SequenceStepSpecLite, ReferenceRecordLite


def input_working_interpretation(
    inference: Inference,
    states: States,
    body: Dict[str, Any] | None = None,
    working_interpretation: Dict[str, Any] | None = None,
) -> States:
    """Initialize states with sequence info; other lists are empty initially."""
    # Sequence (fallback to default if not provided)
    wi = working_interpretation or {}
    seq = wi.get("sequence")
    if isinstance(seq, list) and all(isinstance(x, dict) and "step_name" in x for x in seq):
        states.sequence_state.sequence = [
            SequenceStepSpecLite(step_name=x.get("step_name"), step_index=x.get("step_index")) for x in seq
        ]

    # Initialize other lists as empty, they will be populated by IR/other steps
    states.function = []
    states.values = []
    states.context = []

    inf_entries = wi.get("inference") or []
    # ensure OR slot exists even if not provided
    has_or = any((e.get("step_name") == "OR") for e in inf_entries)
    if not has_or:
        inf_entries.append({"step_name": "OR"})
    states.inference = [ReferenceRecordLite(step_name=ie.get("step_name")) for ie in inf_entries]

    states.set_current_step("IWI")
    return states 