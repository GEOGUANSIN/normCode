from typing import Any, Dict
from dataclasses import field
from infra._states._common_states import BaseStates, SequenceStepSpecLite
from infra._states._model_state import ModelEnvSpecLite, ModelSequenceSpecLite


class States(BaseStates):
    """State container for the judgement sequence."""

    def __init__(self) -> None:
        super().__init__()
        self.sequence_state.sequence = [
            SequenceStepSpecLite(step_name="IWI"),
            SequenceStepSpecLite(step_name="IR"),
            SequenceStepSpecLite(step_name="MFP"),
            SequenceStepSpecLite(step_name="MVP"),
            SequenceStepSpecLite(step_name="TVA"),
            SequenceStepSpecLite(step_name="TIP"),
            SequenceStepSpecLite(step_name="MIA"),
            SequenceStepSpecLite(step_name="OR"),
            SequenceStepSpecLite(step_name="OWI"),
        ]
        self.body: Any | None = None
        self.condition: Any | None = None
        self.condition_met: bool = False
        self.mfp_env_spec: ModelEnvSpecLite | None = None
        self.mfp_sequence_spec: ModelSequenceSpecLite | None = None
        self.value_order: Dict[str, Any] = field(default_factory=dict)
        self.is_relation_output: bool = False
        self.with_thinking: bool = False
