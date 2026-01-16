from typing import Any, Dict, List, Optional
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
        # Legacy condition attribute (for backward compatibility with TIP)
        self.condition: Any | None = None
        self.condition_met: bool = False
        
        # New TIA assertion condition structure
        # Format: {
        #     "quantifiers": {
        #         "axis_name": "all" | "some" | "none" | "exists" | "for-each"
        #     },
        #     "condition": True | False | "unsure" | "@#skip@#"
        # }
        self.assertion_condition: Optional[Dict[str, Any]] = None
        
        # Primary filter axis name (from for-each quantifier)
        # Used by downstream steps to know which axis was filtered
        self.primary_filter_axis: Optional[str] = None
        
        self.mfp_env_spec: ModelEnvSpecLite | None = None
        self.mfp_sequence_spec: ModelSequenceSpecLite | None = None
        self.value_order: Dict[str, Any] = field(default_factory=dict)
        self.value_selectors: Optional[Dict[str, Any]] = None
        self.is_relation_output: bool = False
        self.with_thinking: bool = False
        self.create_axis_on_list_output: bool = True
