from typing import Any, Dict, Optional, List, Union
from types import SimpleNamespace
from infra._states._common_states import BaseStates, SequenceStepSpecLite


class States(BaseStates):
    """A collection of states for the quantifying sequence."""

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
        self.output: SimpleNamespace = SimpleNamespace()

        # Holds all syntax-related information for the quantification loop.
        self.syntax: SimpleNamespace = SimpleNamespace()
        self.syntax.marker: Optional[str] = None
        """The keyword that triggered the quantification (e.g., 'every')."""

        self.syntax.quantifier_index: Optional[int] = 0
        """The index of the quantifier, used to distinguish nested loops."""

        self.syntax.LoopBaseConcept: Optional[str] = None
        """The name of the concept that is being iterated over (e.g., '{number}')."""

        self.syntax.CurrentLoopBaseConcept: Optional[str] = None
        """The explicit name for the concept representing the current item in the loop (e.g., '{number}*'). If not provided, it defaults to `LoopBaseConcept` with a '*' appended."""

        self.syntax.group_base: Optional[str] = None
        """The name of the concept whose axis will be used for grouping."""

        self.syntax.InLoopConcept: Optional[Dict[str, Union[int, Dict[str, Any]]]] = None
        """
        A dictionary defining in-loop concepts. Supports two formats for backward compatibility:
        1. New, structured format: {"{index}": {"current_name": "{index}*", "carry_over": 1}}
        2. Old, flat format: {"{index}*": 1}
        """

        self.syntax.ConceptToInfer: Optional[List[str]] = None
        """A list containing the name of the concept being inferred or calculated inside the loop."""

        self.workspace: Dict[str, Any] = {}  # Workspace for Quantifier
        self.is_quantifier_progress: Optional[bool] = False  # Tracks if quantifier made progress (new element found) 