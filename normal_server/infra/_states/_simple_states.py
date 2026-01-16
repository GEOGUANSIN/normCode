from infra._states._common_states import BaseStates, SequenceStepSpecLite, ReferenceRecordLite
from infra._core import Reference


class States(BaseStates):
    """State container inspired by _syntax model_state but self-contained."""

    def __init__(self) -> None:
        super().__init__()
        self.sequence_state.sequence = [
            SequenceStepSpecLite(step_name="IWI", step_index=1),
            SequenceStepSpecLite(step_name="IR", step_index=2),
            SequenceStepSpecLite(step_name="OR", step_index=3),
            SequenceStepSpecLite(step_name="OWI", step_index=4),
        ]
        self.sequence_state.current_step = "IWI"
        self.inference = [ReferenceRecordLite(step_name="OR", reference=None)]

    def get_or_reference(self) -> Reference | None:
        for i in self.inference:
            if i.step_name == "OR":
                return i.reference
        return None

    def set_or_reference(self, ref: Reference | None) -> None:
        for i in self.inference:
            if i.step_name == "OR":
                i.reference = ref
                break 