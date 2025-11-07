class SystemState:
    """A simple class to manage the state of the multi-agent system."""

    def __init__(self, initial_state: dict = None):
        """
        Initializes the state.

        Args:
            initial_state (dict): An optional dictionary to initialize the state with.
        """
        self._state = dict(initial_state) if initial_state else {}

    def get(self, key: str, default=None):
        """
        Gets a value from the state.

        Args:
            key (str): The key of the value to retrieve.
            default: The default value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value.
        """
        return self._state.get(key, default)

    def set(self, key: str, value):
        """
        Sets a value in the state.

        Args:
            key (str): The key of the value to set.
            value: The value to set.
        """
        self._state[key] = value

    def __str__(self):
        """Returns a string representation of the state."""
        return str(self._state)
