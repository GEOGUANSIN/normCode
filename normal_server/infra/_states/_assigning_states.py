from types import SimpleNamespace
from infra._states._common_states import BaseStates, SequenceStepSpecLite


class States(BaseStates):
    """State container for the assigning sequence."""

    def __init__(self) -> None:
        super().__init__()
        self.sequence_state.sequence = [
            SequenceStepSpecLite(step_name="IWI"),
            SequenceStepSpecLite(step_name="IR"),
            SequenceStepSpecLite(step_name="AR"),
            SequenceStepSpecLite(step_name="OR"),
            SequenceStepSpecLite(step_name="OWI"),
        ]
        self.syntax: SimpleNamespace = SimpleNamespace(
            marker=None,
            assign_source=None,
            assign_destination=None,
            by_axes=[],
            # For abstraction ($%)
            face_value=None,
            axis_names=None,
            # For derelation ($-)
            selector=None,
            # For identity ($=) - uses blackboard
            canonical_concept=None,
            alias_concept=None
        )
