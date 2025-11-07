import json


class ExecutionState:
    """
    Manages the state of a NormCode execution trace, attributing results to
    specific flow indices and concepts.
    """

    def __init__(self):
        """
        Initializes the trace. The state is a dictionary where keys are
        flow indices and values are dictionaries mapping concepts to their results.
        """
        self._trace = {}

    def set(self, flow_index: str, concept: str, value):
        """
        Sets a value in the state, associated with a flow index and concept.

        Args:
            flow_index (str): The flow index from the NormCode (e.g., "1.1.2.").
            concept (str): The concept name being produced (e.g., "{digit sum}").
            value: The result of the inference.
        """
        if flow_index not in self._trace:
            self._trace[flow_index] = {}
        self._trace[flow_index][concept] = value

    def get_full_trace(self):
        """Returns the complete execution trace."""
        return self._trace

    def to_json(self):
        """Returns a JSON string representation of the execution trace."""
        # Sort by flow_index for readability
        sorted_trace = dict(sorted(self._trace.items()))
        return json.dumps(sorted_trace, indent=2)
