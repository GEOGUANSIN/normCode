import json
import textwrap


class ExecutionState:
    def __init__(self):
        self.trace = []

    def _log_to_console(self, entry):
        """Pretty prints a log entry to the console."""
        step = entry.get('step', 'N/A')
        log_type = entry.get('type', 'INFO')
        details = entry.get('details', '')

        print("-" * 70)
        print(f"STEP {step}  [{log_type}]")
        print(f"DETAILS: {details}")

        if entry.get('agent'):
            print(f"AGENT:   {entry['agent']}")

        if 'data' in entry and entry.get('data') is not None:
            # Using default=str to handle non-serializable objects gracefully for printing
            data_str = json.dumps(entry['data'], indent=2, default=str)
            indented_data = textwrap.indent(data_str, '    ')
            print(f"DATA:\n{indented_data}")
        print("-" * 70)

    def log_action(self, step, agent, details, data):
        """Logs an action being taken, including its inputs."""
        entry = {
            "step": step,
            "type": "ACTION",
            "agent": agent,
            "details": details,
            "data": data
        }
        self.trace.append(entry)
        self._log_to_console(entry)

    def record(self, step, concept, result):
        """Logs the result of an action."""
        entry = {
            "step": step,
            "type": "RESULT",
            "concept": concept,
            "data": result
        }
        # Add details for console clarity, but not to the stored trace entry
        console_display_entry = entry.copy()
        console_display_entry["details"] = f"Stored result for concept '{concept}'"

        self.trace.append(entry)
        self._log_to_console(console_display_entry)

    def save_trace(self, filepath="love_execution_trace.json"):
        """Saves the final execution trace to a JSON file."""
        with open(filepath, 'w') as f:
            # Using default=str to handle any potential non-serializable objects
            json.dump(self.trace, f, indent=2, default=str)
        print(f"\nExecution trace saved to {filepath}")
