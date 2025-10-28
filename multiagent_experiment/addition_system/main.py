import sys
from pathlib import Path
import json

# Add the project root to the Python path to allow for absolute imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from multiagent_experiment.addition_system.agents.controller_agent import ControllerAgent


def main():
    """
    Main function to run the multi-agent addition system.
    """
    # Instantiate the central controller agent
    controller = ControllerAgent()

    # --- Example 1 ---
    # Corresponds to the example in the NormCode: 123 + 98
    num1 = 123
    num2 = 98
    print(f"--- Running addition for: {num1} + {num2} ---")
    trace1 = controller.run(num1, num2)
    print(json.dumps(trace1, indent=2))
    print("-" * 20)

    # --- Example 2 ---
    num3 = 555
    num4 = 555
    print(f"--- Running addition for: {num3} + {num4} ---")
    trace2 = controller.run(num3, num4)
    print(json.dumps(trace2, indent=2))
    print("-" * 20)

    # --- Example 3 ---
    num5 = 999
    num6 = 1
    print(f"--- Running addition for: {num5} + {num6} ---")
    trace3 = controller.run(num5, num6)
    print(json.dumps(trace3, indent=2))
    print("-" * 20)


if __name__ == "__main__":
    main()
