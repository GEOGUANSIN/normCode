import logging
import json
from typing import Any, Dict, Optional, List
from datetime import datetime

class CheckpointManager:
    """Manages saving and loading of the orchestration state using shared DB."""

    def __init__(self, db): # db: OrchestratorDB
        self.db = db

    def export_comprehensive_state(self, orchestrator: 'Orchestrator') -> Dict[str, Any]:
        """
        Exports the complete state of the orchestration including execution history and logs.
        """
        # 1. Get DB History and Logs
        db_state = self.db.get_full_state() if self.db else {"executions": []}
        
        # 2. Get In-Memory State
        blackboard_data = orchestrator.blackboard.to_dict()
        tracker_counters = orchestrator.tracker.to_dict()
        
        # Serialize Workspace safely
        workspace_data = self._serialize_workspace(orchestrator.workspace)
        
        # 3. Serialize Concepts (Definitions + Current Values)
        concepts_data = []
        for concept_entry in orchestrator.concept_repo.get_all_concepts():
            c_dict = {
                "id": concept_entry.id,
                "concept_name": concept_entry.concept_name,
                "type": concept_entry.type,
                "context": concept_entry.context,
                "is_ground": concept_entry.is_ground_concept,
                "is_final": concept_entry.is_final_concept,
                "status": orchestrator.blackboard.get_concept_status(concept_entry.concept_name),
                "reference": None
            }
            
            # Serialize reference if it exists
            if concept_entry.concept and concept_entry.concept.reference:
                ref = concept_entry.concept.reference
                c_dict["reference"] = {
                    "axes": ref.axes,
                    "shape": ref.shape,
                    "data": ref.data
                }
            elif concept_entry.reference_data:
                 # Fallback to entry data if concept object not fully hydrated or ref missing
                 c_dict["reference"] = {
                     "data": concept_entry.reference_data,
                     "axes": concept_entry.reference_axis_names
                 }
            
            concepts_data.append(c_dict)

        # 4. Construct Final Export Dictionary
        export_data = {
            "timestamp": str(datetime.now()),
            "cycle": orchestrator.tracker.cycle_count,
            "blackboard": blackboard_data,
            "tracker": tracker_counters,
            "workspace": workspace_data,
            "concepts": concepts_data,
            "execution_history": db_state.get("executions", [])
        }
        
        return export_data

    def _serialize_workspace(self, workspace: Any) -> Any:
        """Recursively serialize workspace to handle Reference objects and other complex types."""
        if isinstance(workspace, dict):
            return {k: self._serialize_workspace(v) for k, v in workspace.items()}
        elif isinstance(workspace, list):
            return [self._serialize_workspace(v) for v in workspace]
        elif isinstance(workspace, tuple):
            return [self._serialize_workspace(v) for v in workspace]  # Convert tuple to list for JSON
        elif isinstance(workspace, (str, int, float, bool, type(None))):
            # Primitive types are JSON-serializable
            return workspace
        elif hasattr(workspace, 'data') and hasattr(workspace, 'axes') and hasattr(workspace, 'shape'):
            # Basic check for Reference object duck-typing
            try:
                return {
                    "axes": list(workspace.axes) if hasattr(workspace.axes, '__iter__') else workspace.axes,
                    "shape": list(workspace.shape) if hasattr(workspace.shape, '__iter__') else workspace.shape,
                    "data": workspace.data
                }
            except Exception as e:
                logging.warning(f"Failed to serialize Reference-like object: {e}. Using string representation.")
                return str(workspace)
        else:
            # For other types, try to convert to a serializable format
            # First try converting to string (safe fallback)
            try:
                # Check if it's already a basic type we missed
                if isinstance(workspace, (bytes, bytearray)):
                    return workspace.decode('utf-8', errors='replace')
                # For other objects, convert to string representation
                return str(workspace)
            except Exception:
                # Last resort: return a placeholder
                return f"<non-serializable: {type(workspace).__name__}>"

    def save_state(self, cycle: int, orchestrator: 'Orchestrator'):
        """
        Saves the complete state of the orchestrator to the DB checkpoint table.
        This includes blackboard, tracker (counters), workspace, and completed concept references.
        """
        if not hasattr(orchestrator, 'blackboard') or not hasattr(orchestrator, 'tracker'):
            logging.error("Orchestrator is missing blackboard or tracker. Cannot save state.")
            return

        # 1. Prepare State Data
        # Note: Tracker history is already in DB executions table. We only save counters here.
        state_data = {
            "blackboard": orchestrator.blackboard.to_dict(),
            "tracker": orchestrator.tracker.to_dict(),
            "workspace": self._serialize_workspace(orchestrator.workspace),
            "completed_concepts": {}
        }

        # 2. Serialize completed concept references
        completed_concepts_data = {}
        for concept_name in orchestrator.blackboard.get_completed_concepts():
            concept_entry = orchestrator.concept_repo.get_concept(concept_name)
            if concept_entry and concept_entry.concept and concept_entry.concept.reference is not None:
                # Save dynamic reference data from the live concept object
                completed_concepts_data[concept_name] = {
                    "reference_data": concept_entry.concept.reference.data,
                    "reference_axis_names": concept_entry.concept.reference.axes
                }
            elif concept_entry and concept_entry.reference_data:
                 # Fallback to static definition if live reference is missing but data exists
                 completed_concepts_data[concept_name] = {
                     "reference_data": concept_entry.reference_data,
                     "reference_axis_names": concept_entry.reference_axis_names
                 }
        
        state_data["completed_concepts"] = completed_concepts_data

        # 3. Save to DB
        try:
            self.db.save_checkpoint(cycle, state_data)
            logging.info(f"Successfully saved checkpoint for cycle {cycle} to DB.")
        except TypeError as e:
            # JSON serialization error - likely due to non-serializable objects
            logging.error(f"Failed to save checkpoint for cycle {cycle}: JSON serialization error - {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
        except Exception as e:
            logging.error(f"Failed to save checkpoint for cycle {cycle} to DB: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")

    def load_latest_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Loads the most recent checkpoint state from DB."""
        try:
            result = self.db.load_latest_checkpoint()
            if result:
                cycle, state = result
                logging.info(f"Loaded checkpoint from cycle {cycle}.")
                return state
            logging.info("No checkpoint found in DB.")
            return None
        except Exception as e:
            logging.error(f"Failed to load checkpoint from DB: {e}")
            return None

    def reconcile_state(self, checkpoint_data: Dict[str, Any], orchestrator: 'Orchestrator'):
        """
        Reconciles the state of a new orchestrator with data from a checkpoint.
        """
        if not checkpoint_data:
            logging.warning("Checkpoint data is empty. Cannot reconcile.")
            return

        logging.info("--- Starting Orchestrator State Reconciliation ---")

        # 1. Restore Tracker counters
        orchestrator.tracker.load_from_dict(checkpoint_data.get("tracker", {}))
        
        # 2. Restore Workspace (Deserialize Reference objects)
        raw_workspace = checkpoint_data.get("workspace", {})
        orchestrator.workspace = self._deserialize_workspace(raw_workspace)
        
        # 3. Restore completed concept references
        completed_concepts = checkpoint_data.get("completed_concepts", {})
        for name, data in completed_concepts.items():
            orchestrator.concept_repo.add_reference(
                concept_name=name,
                data=data.get("reference_data"),
                axis_names=data.get("reference_axis_names")
            )
        
        # 4. Restore Blackboard state
        orchestrator.blackboard.load_from_dict(checkpoint_data.get("blackboard", {}))

        # 5. Reconcile waitlist items
        for item in orchestrator.waitlist.items:
            concept_name = item.inference_entry.concept_to_infer.concept_name
            if orchestrator.blackboard.get_concept_status(concept_name) == 'complete':
                flow_index = item.inference_entry.flow_info['flow_index']
                orchestrator.blackboard.set_item_status(flow_index, 'completed')
                logging.info(f"Reconciled item {flow_index} ('{concept_name}') as 'completed' from checkpoint.")

        logging.info("--- State Reconciliation Complete ---")

    def _deserialize_workspace(self, workspace: Any) -> Any:
        """Recursively deserialize workspace to restore Reference objects from dicts."""
        if isinstance(workspace, dict):
            # Check if this dict represents a Reference object
            # A serialized Reference should have axes, shape, and data
            if "axes" in workspace and "shape" in workspace and "data" in workspace:
                try:
                    # Import Reference here to avoid potential circular imports at module level
                    from infra import Reference
                    
                    axes = workspace["axes"]
                    shape = workspace["shape"]
                    data = workspace["data"]
                    
                    # Create basic reference
                    ref = Reference(axes=axes, shape=shape)
                    ref.data = data
                    # logging.debug(f"Deserialized Reference with axes={axes}, shape={shape}")
                    return ref
                except ImportError:
                    logging.error("Could not import Reference class from 'infra' for deserialization. Attempting direct import.")
                    try:
                         from infra._core._reference import Reference
                         ref = Reference(axes=workspace["axes"], shape=workspace["shape"])
                         ref.data = workspace["data"]
                         return ref
                    except Exception as e:
                        logging.error(f"Failed secondary import/creation: {e}. Keeping as dict.")
                        return workspace
                except Exception as e:
                    logging.warning(f"Failed to deserialize Reference object: {e}. Keeping as dict.")
                    return workspace
            
            # Handle integer keys (JSON converts int keys to strings)
            # This is crucial for workspace indices like loop counters
            deserialized_dict = {}
            for k, v in workspace.items():
                final_key = k
                if isinstance(k, str) and k.isdigit():
                    try:
                        final_key = int(k)
                    except ValueError:
                        pass
                
                deserialized_dict[final_key] = self._deserialize_workspace(v)
            
            return deserialized_dict
        
        elif isinstance(workspace, list):
            return [self._deserialize_workspace(v) for v in workspace]
        
        elif isinstance(workspace, tuple):
            return tuple(self._deserialize_workspace(v) for v in workspace)
            
        return workspace
    
    def get_checkpoint_count(self) -> int:
        """Get the total number of checkpoints in the database."""
        if not self.db:
            return 0
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM checkpoints')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_all_checkpoints(self) -> List[Dict[str, Any]]:
        """Get all checkpoints from the database."""
        if not self.db:
            return []
        return self.db.get_all_checkpoints()

