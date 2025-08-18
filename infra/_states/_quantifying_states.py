from typing import Any, Dict
from types import SimpleNamespace
from infra._states._common_states import BaseStates, SequenceStepSpecLite


class States(BaseStates):
    """State container for the quantifying sequence."""

    def __init__(self) -> None:
        super().__init__()
        self.sequence_state.sequence = [
            SequenceStepSpecLite(step_name="IWI"),
            SequenceStepSpecLite(step_name="IR"),
            SequenceStepSpecLite(step_name="GR"),
            SequenceStepSpecLite(step_name="QR"),
            SequenceStepSpecLite(step_name="OR"),
            SequenceStepSpecLite(step_name="OWI"),
        ]
        self.syntax: SimpleNamespace = SimpleNamespace()
        self.workspace: Dict[str, Any] = {}  # Workspace for Quantifier 