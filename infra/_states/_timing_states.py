from infra._states._common_states import BaseStates, SequenceStepSpecLite
from infra._orchest._blackboard import Blackboard
from types import SimpleNamespace
from typing import Optional


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
            marker=None,  # "after"
            condition=None,
        )
        self.blackboard: Optional[Blackboard] = None
        self.timing_ready: bool = False
        self.to_be_skipped: bool = False 