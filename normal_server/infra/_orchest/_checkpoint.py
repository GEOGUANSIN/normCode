import logging
import json
from typing import Any, Dict, Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from infra._orchest._orchestrator import Orchestrator

class CheckpointManager:
    """Manages saving and loading of the orchestration state using shared DB."""

    def __init__(self, db): # db: OrchestratorDB
        self.db = db

    def export_comprehensive_state(self, orchestrator: 'Orchestrator') -> Dict[str, Any]:
        """
        Exports the complete state of the orchestration including execution history and logs.
        """
        # 1. Get DB History and Logs (use orchestrator's run_id)
        run_id = getattr(orchestrator, 'run_id', None)
        db_state = self.db.get_full_state(run_id) if self.db else {"executions": []}
        
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
        run_id = getattr(orchestrator, 'run_id', None)
        export_data = {
            "timestamp": str(datetime.now()),
            "run_id": run_id,
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

    def save_state(self, cycle: int, orchestrator: 'Orchestrator', inference_count: int = 0):
        """
        Saves the complete state of the orchestrator to the DB checkpoint table.
        This includes blackboard, tracker (counters), workspace, and completed concept references.
        
        Args:
            cycle: The current cycle number
            orchestrator: The orchestrator instance to save
            inference_count: The number of inferences executed in this cycle (allows multiple checkpoints per cycle)
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
            "completed_concepts": {},
            "signatures": {
                "concept_signatures": {},
                "item_signatures": {}
            }
        }

        # 2. Serialize completed concept references and collect signatures
        completed_concepts_data = {}
        concept_signatures = {}
        
        # Iterate over ALL concepts to save any that have data, not just "completed" ones
        for concept_entry in orchestrator.concept_repo.get_all_concepts():
            concept_name = concept_entry.concept_name
            
            # Check if it has data (either in reference or reference_data)
            has_data = False
            ref_data = None
            ref_axes = None
            
            if concept_entry.concept and concept_entry.concept.reference is not None:
                has_data = True
                ref_data = concept_entry.concept.reference.data
                ref_axes = concept_entry.concept.reference.axes
            elif concept_entry.reference_data:
                has_data = True
                ref_data = concept_entry.reference_data
                ref_axes = concept_entry.reference_axis_names
            
            if has_data:
                # Save signature for this concept
                concept_signatures[concept_name] = concept_entry.get_signature()
                
                completed_concepts_data[concept_name] = {
                    "reference_data": ref_data,
                    "reference_axis_names": ref_axes
                }
        
        state_data["completed_concepts"] = completed_concepts_data
        state_data["signatures"]["concept_signatures"] = concept_signatures
        
        # 3. Collect signatures for completed items
        item_signatures = {}
        if hasattr(orchestrator, 'waitlist') and orchestrator.waitlist:
            for item in orchestrator.waitlist.items:
                flow_index = item.inference_entry.flow_info['flow_index']
                if orchestrator.blackboard.get_item_status(flow_index) == 'completed':
                    item_signatures[flow_index] = item.inference_entry.get_signature()
        
        state_data["signatures"]["item_signatures"] = item_signatures

        # 3. Save to DB
        try:
            self.db.save_checkpoint(cycle, state_data, inference_count)
            logging.info(f"Successfully saved checkpoint for cycle {cycle}, inference {inference_count} to DB.")
        except TypeError as e:
            # JSON serialization error - likely due to non-serializable objects
            logging.error(f"Failed to save checkpoint for cycle {cycle}, inference {inference_count}: JSON serialization error - {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
        except Exception as e:
            logging.error(f"Failed to save checkpoint for cycle {cycle}, inference {inference_count} to DB: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")

    def load_latest_checkpoint(self, run_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Loads the most recent checkpoint state from DB for the specified run_id."""
        try:
            result = self.db.load_latest_checkpoint(run_id)
            if result:
                cycle, inference_count, state = result
                logging.info(f"Loaded checkpoint from cycle {cycle}, inference {inference_count} for run_id: {run_id or self.db.run_id}")
                return state
            logging.info(f"No checkpoint found in DB for run_id: {run_id or self.db.run_id}")
            return None
        except Exception as e:
            logging.error(f"Failed to load checkpoint from DB: {e}")
            return None
    
    def load_checkpoint_by_cycle(self, cycle: int, run_id: Optional[str] = None, inference_count: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Loads a specific checkpoint by cycle number (and optionally inference_count) for the specified run_id.
        If inference_count is None, loads the latest checkpoint for that cycle.
        """
        try:
            result = self.db.load_checkpoint_by_cycle(cycle, run_id, inference_count)
            if result:
                checkpoint_cycle, checkpoint_inference_count, state = result
                logging.info(f"Loaded checkpoint from cycle {checkpoint_cycle}, inference {checkpoint_inference_count} for run_id: {run_id or self.db.run_id}")
                return state
            logging.info(f"No checkpoint found at cycle {cycle}, inference {inference_count} for run_id: {run_id or self.db.run_id}")
            return None
        except Exception as e:
            logging.error(f"Failed to load checkpoint from DB: {e}")
            return None
    
    def list_checkpoints(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available checkpoints (with cycle numbers) for the specified run_id."""
        if not self.db:
            return []
        return self.db.list_checkpoints(run_id)

    def reconcile_state(self, checkpoint_data: Dict[str, Any], orchestrator: 'Orchestrator', 
                       mode: str = "PATCH", is_forking: bool = False):
        """
        Reconciles the state of a new orchestrator with data from a checkpoint.
        
        Args:
            checkpoint_data: The checkpoint state to reconcile
            orchestrator: The orchestrator instance to reconcile state into
            mode: Loading mode - one of:
                - "PATCH" (default): Smart merge - discard stale state, keep valid state
                - "OVERWRITE": Trust checkpoint 100%, ignore repo changes
                - "FILL_GAPS": Only fill missing values, prefer new repo defaults
            is_forking: If True, skip restoring item_statuses (items are different inferences in new repo)
        """
        if not checkpoint_data:
            logging.warning("Checkpoint data is empty. Cannot reconcile.")
            return

        logging.info(f"--- Starting Orchestrator State Reconciliation (Mode: {mode}) ---")

        # 1. Restore Tracker counters
        orchestrator.tracker.load_from_dict(checkpoint_data.get("tracker", {}))
        
        # 2. Restore Workspace (Deserialize Reference objects)
        raw_workspace = checkpoint_data.get("workspace", {})
        orchestrator.workspace = self._deserialize_workspace(raw_workspace)
        
        # 3. Get saved signatures for comparison
        saved_signatures = checkpoint_data.get("signatures", {})
        saved_concept_signatures = saved_signatures.get("concept_signatures", {})
        saved_item_signatures = saved_signatures.get("item_signatures", {})
        
        # 4. Restore completed concept references based on mode
        completed_concepts = checkpoint_data.get("completed_concepts", {})
        concepts_discarded = []
        concepts_kept = []
        hydrated_concepts = []
        
        for name, data in completed_concepts.items():
            concept_entry = orchestrator.concept_repo.get_concept(name)
            
            # Check if concept exists in new repo
            if not concept_entry:
                logging.debug(f"Concept '{name}' from checkpoint not found in new repo. Skipping.")
                continue
            
            # Mode-specific logic
            should_apply = False
            
            if mode == "OVERWRITE":
                # Always apply checkpoint value
                should_apply = True
            elif mode == "FILL_GAPS":
                # Only apply if concept is currently empty in new repo
                current_status = orchestrator.blackboard.get_concept_status(name)
                if current_status == "empty":
                    should_apply = True
                else:
                    logging.debug(f"Concept '{name}' already has value in new repo. Skipping checkpoint value (FILL_GAPS mode).")
            elif mode == "PATCH":
                # Smart merge: compare signatures
                saved_sig = saved_concept_signatures.get(name)
                current_sig = concept_entry.get_signature()
                
                if saved_sig == current_sig:
                    # Signatures match - logic hasn't changed, safe to use checkpoint value
                    should_apply = True
                    concepts_kept.append(name)
                else:
                    # Signatures differ - logic has changed, discard stale checkpoint value
                    should_apply = False
                    concepts_discarded.append(name)
                    logging.info(f"Concept '{name}' signature mismatch. Discarding checkpoint value (logic changed).")
            else:
                logging.warning(f"Unknown mode '{mode}'. Defaulting to PATCH behavior.")
                # Default to PATCH logic
                saved_sig = saved_concept_signatures.get(name)
                current_sig = concept_entry.get_signature()
                should_apply = (saved_sig == current_sig)
            
            if should_apply:
                orchestrator.concept_repo.add_reference(
                    concept_name=name,
                    data=data.get("reference_data"),
                    axis_names=data.get("reference_axis_names")
                )
                hydrated_concepts.append(name)
        
        if concepts_discarded:
            logging.info(f"PATCH mode: Discarded {len(concepts_discarded)} stale concept(s): {concepts_discarded}")
        if concepts_kept:
            logging.info(f"PATCH mode: Kept {len(concepts_kept)} valid concept(s): {concepts_kept}")
        
        # 5. Restore Blackboard state (but we'll reconcile items after signature checks)
        blackboard_data = checkpoint_data.get("blackboard", {})
        
        # For PATCH mode, we need to be careful about item statuses too
        if mode == "PATCH":
            # We'll reconcile items after checking signatures
            # First, restore non-status fields
            orchestrator.blackboard.item_results.update(blackboard_data.get("item_results", {}))
            orchestrator.blackboard.item_execution_counts.update(blackboard_data.get("item_execution_counts", {}))
            orchestrator.blackboard.item_completion_details.update(blackboard_data.get("item_completion_details", {}))
            orchestrator.blackboard.completed_concept_timestamps.update(blackboard_data.get("completed_concept_timestamps", {}))
            orchestrator.blackboard.concept_to_flow_index.update(blackboard_data.get("concept_to_flow_index", {}))
            
            # For concept statuses, only restore if we kept the concept reference
            saved_concept_statuses = blackboard_data.get("concept_statuses", {})
            for concept_name, status in saved_concept_statuses.items():
                if concept_name in concepts_kept:
                    orchestrator.blackboard.concept_statuses[concept_name] = status
                elif concept_name in concepts_discarded:
                    # Mark as pending to force re-run
                    orchestrator.blackboard.concept_statuses[concept_name] = "empty"
        else:
            # OVERWRITE or FILL_GAPS: restore all blackboard state
            # BUT: when forking, exclude item_statuses (items are different inferences)
            if is_forking:
                # Manually restore everything EXCEPT item_statuses
                orchestrator.blackboard.concept_statuses.update(blackboard_data.get("concept_statuses", {}))
                orchestrator.blackboard.item_results.update(blackboard_data.get("item_results", {}))
                orchestrator.blackboard.item_execution_counts.update(blackboard_data.get("item_execution_counts", {}))
                orchestrator.blackboard.item_completion_details.update(blackboard_data.get("item_completion_details", {}))
                orchestrator.blackboard.completed_concept_timestamps.update(blackboard_data.get("completed_concept_timestamps", {}))
                orchestrator.blackboard.concept_to_flow_index.update(blackboard_data.get("concept_to_flow_index", {}))
                # item_statuses deliberately SKIPPED - will remain as initialized (all 'pending')
                logging.info("Forking: Restored blackboard state except item_statuses (new repo has different items)")
            else:
                orchestrator.blackboard.load_from_dict(blackboard_data)
            
        # Ensure all hydrated concepts are marked as complete
        # This fixes issues where OVERWRITE restores 'empty' status or FILL_GAPS leaves it empty
        logging.info(f"Marking {len(hydrated_concepts)} hydrated concepts as complete: {hydrated_concepts}")
        for name in hydrated_concepts:
            orchestrator.blackboard.set_concept_status(name, 'complete')

        # 6. Reconcile waitlist items based on mode
        items_discarded = []
        items_kept = []
        
        # CRITICAL: When forking, DO NOT restore item statuses
        # The items in the new repo are completely different inferences
        # (even if they share the same flow_index)
        if is_forking:
            logging.info("Forking mode: Skipping item status restoration (new repo has different inferences)")
        elif orchestrator.waitlist:
            saved_item_statuses = blackboard_data.get("item_statuses", {})
            for item in orchestrator.waitlist.items:
                flow_index = item.inference_entry.flow_info['flow_index']
                concept_name = item.inference_entry.concept_to_infer.concept_name
                
                saved_status = saved_item_statuses.get(flow_index)
                if saved_status == 'completed':
                    should_mark_completed = False
                    
                    if mode == "OVERWRITE":
                        should_mark_completed = True
                    elif mode == "FILL_GAPS":
                        # Only if item is currently pending
                        current_status = orchestrator.blackboard.get_item_status(flow_index)
                        if current_status == "pending":
                            should_mark_completed = True
                    elif mode == "PATCH":
                        # Check if item signature matches
                        saved_sig = saved_item_signatures.get(flow_index)
                        current_sig = item.inference_entry.get_signature()
                        
                        if saved_sig == current_sig:
                            should_mark_completed = True
                            items_kept.append(flow_index)
                        else:
                            should_mark_completed = False
                            items_discarded.append(flow_index)
                            logging.info(f"Item {flow_index} ('{concept_name}') signature mismatch. Discarding checkpoint status (logic changed).")
                    
                    if should_mark_completed:
                        orchestrator.blackboard.set_item_status(flow_index, 'completed')
                        logging.debug(f"Reconciled item {flow_index} ('{concept_name}') as 'completed' from checkpoint.")
                    elif mode == "PATCH" and flow_index in items_discarded:
                        # Mark as pending to force re-run
                        orchestrator.blackboard.set_item_status(flow_index, 'pending')
                        # Also mark the concept as empty if it was discarded
                        if concept_name in concepts_discarded:
                            orchestrator.blackboard.set_concept_status(concept_name, 'empty')
        
        if items_discarded:
            logging.info(f"PATCH mode: Discarded {len(items_discarded)} stale item status(es): {items_discarded}")
        if items_kept:
            logging.info(f"PATCH mode: Kept {len(items_kept)} valid item status(es): {items_kept}")

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
    
    def get_checkpoint_count(self, run_id: Optional[str] = None) -> int:
        """Get the total number of checkpoints for the specified run_id (or self.db.run_id if not provided)."""
        if not self.db:
            return 0
        target_run_id = run_id or self.db.run_id
        if not target_run_id:
            return 0
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM checkpoints WHERE run_id = ?', (target_run_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_all_checkpoints(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all checkpoints for the specified run_id (or self.db.run_id if not provided)."""
        if not self.db:
            return []
        return self.db.get_all_checkpoints(run_id)

