from infra._states._common_states import BaseStates, SequenceStepSpecLite
from infra._orchest._blackboard import Blackboard
from types import SimpleNamespace
from typing import Optional, Dict, Any


class States(BaseStates):
    """State container for the timing sequence."""

    def __init__(self) -> None:
        super().__init__()
        self.sequence_state.sequence = [
            SequenceStepSpecLite(step_name="IWI", step_index=1),
            SequenceStepSpecLite(step_name="T", step_index=2),  # Timing
            SequenceStepSpecLite(step_name="OWI", step_index=3),
        ]
        self.sequence_state.current_step = "IWI"
        self.syntax: SimpleNamespace = SimpleNamespace(
            marker=None,  # "after", "if", "if!"
            condition=None,
        )
        self.blackboard: Optional[Blackboard] = None
        self.workspace: Dict[str, Any] = {}  # Shared workspace for filter injection
        self.flow_index: Optional[str] = None  # Flow index of this timing inference
        self.timing_ready: bool = False
        self.to_be_skipped: bool = False