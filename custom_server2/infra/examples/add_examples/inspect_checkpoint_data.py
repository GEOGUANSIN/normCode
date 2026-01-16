import os
import sys
import logging
import pathlib

# Ensure project root is in path
here = pathlib.Path(__file__).resolve().parent
project_root = here.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infra._orchest._db import OrchestratorDB
from infra._orchest._checkpoint import CheckpointManager

def inspect_checkpoint(run_id="demo-run"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "orchestration_checkpoint.db")
    
    print(f"Inspecting checkpoint for run_id: {run_id} in {db_path}")
    
    try:
        db = OrchestratorDB(db_path)
        checkpoint_manager = CheckpointManager(db)
        checkpoint_data = checkpoint_manager.load_latest_checkpoint(run_id)
        
        if not checkpoint_data:
            print("No checkpoint found.")
            return

        completed_concepts = checkpoint_data.get("completed_concepts", {})
        
        # Check {new number pair}
        if '{new number pair}' in completed_concepts:
            data = completed_concepts['{new number pair}']['reference_data']
            print(f"\n{{new number pair}} data: {data}")
        else:
            print("\n{new number pair} not found in completed concepts.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_checkpoint()

