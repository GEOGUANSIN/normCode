import json
from pathlib import Path
import sys

# --- Path Correction ---
# Add the project root to the Python path to allow importing from 'infra'
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))
# --- End Path Correction ---


from agents.orchestrator_agent import OrchestratorAgent

def main():
    """Main entry point to run the multi-agent love inquiry system."""
    print("Starting the multi-agent love inquiry system...")

    # Get the directory of the current script to build a robust path
    # script_dir = Path(__file__).parent
    plan_path = script_dir / 'plan' / 'love_plan.json'
    
    # Load the plan
    with open(plan_path, 'r') as f:
        plan = json.load(f)
        
    # Initialize the orchestrator
    orchestrator = OrchestratorAgent(plan)
    
    # Initialize the state
    initial_state = {
        "responses": {},
        "judgements": {},
        "current_concept_node": None
    }
    
    # Run the system
    orchestrator.execute(initial_state)
    
    print("\nSystem finished.")

if __name__ == "__main__":
    main()
