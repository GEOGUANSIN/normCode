import argparse
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from multiagent_experiment.nc_compiler.agents.master_controller_agent import MasterControllerAgent

def main():
    """
    Main entry point for the NormCode Compiler multi-agent system.
    """
    parser = argparse.ArgumentParser(description="NormCode Compiler System")
    parser.add_argument(
        "--normtext_file",
        type=str,
        default="multiagent_experiment/nc_compiler/normtext.md",
        help="Path to the normtext file to be compiled. Defaults to its own normtext."
    )
    args = parser.parse_args()

    # Initialize and run the master controller
    controller = MasterControllerAgent()
    controller.run(initial_normtext_path=args.normtext_file)

if __name__ == "__main__":
    main()
