import uuid
import logging
import asyncio
from typing import List, Optional, Dict, Any

# Import dependencies
from infra import Inference, Concept, AgentFrame, Reference, BaseStates
from infra._orchest._blackboard import Blackboard
from infra._orchest._repo import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo
from infra._orchest._waitlist import WaitlistItem, Waitlist
from infra._orchest._tracker import ProcessTracker
from infra._orchest._db import OrchestratorDB
from infra._orchest._checkpoint import CheckpointManager
from infra._agent._body import Body

class Orchestrator:
    """
    Orchestrates a waitlist of inferences, processing them in a bottom-up fashion
    based on the completion of their "support" dependencies.
    """
    def __init__(self, 
                 concept_repo: ConceptRepo,
                 inference_repo: InferenceRepo, 
                 blackboard: Optional[Blackboard] = None,
                 agent_frame_model: str = "demo",
                 body: Optional[Body] = None,
                 max_cycles: int = 30,
                 db_path: Optional[str] = None,
                 checkpoint_frequency: Optional[int] = None,
                 run_id: Optional[str] = None):
        """
        Args:
            checkpoint_frequency: If provided, save checkpoint every N inferences within a cycle.
                                 If None, only checkpoint at the end of each cycle.
                                 Example: checkpoint_frequency=5 will checkpoint at inferences 5, 10, 15, etc.
            run_id: If provided, uses this run_id instead of generating a new one. Useful for continuing a run.
        """
        self.inference_repo = inference_repo
        self.concept_repo = concept_repo
        self.agent_frame_model = agent_frame_model
        self.body = body or Body()
        self.waitlist: Optional[Waitlist] = None
        self.blackboard = blackboard or Blackboard()
        self.tracker = ProcessTracker()
        self.max_cycles = max_cycles
        self.workspace = {}
        self.checkpoint_frequency = checkpoint_frequency  # Checkpoint every N inferences
        
        # Use provided run_id or generate a unique run_id for this orchestrator instance
        self.run_id = run_id if run_id is not None else str(uuid.uuid4())
        
        # Initialize checkpointing system if db_path is provided
        self.db: Optional[OrchestratorDB] = None
        self.checkpoint_manager: Optional[CheckpointManager] = None
        if db_path:
            self.db = OrchestratorDB(db_path, run_id=self.run_id)
            self.checkpoint_manager = CheckpointManager(self.db)
            self.tracker.set_db(self.db)
            self.tracker.set_run_id(self.run_id)  # Ensure tracker has run_id
            
            # Save run metadata regarding environment and configuration
            self._save_run_metadata()
            
            if self.checkpoint_frequency:
                logging.info(f"Checkpointing enabled with database at: {db_path}, run_id: {self.run_id}, frequency: every {self.checkpoint_frequency} inferences")
            else:
                logging.info(f"Checkpointing enabled with database at: {db_path}, run_id: {self.run_id} (end of cycle only)")
        
        # Track execution IDs for status updates
        self._current_execution_ids: Dict[str, int] = {}  # flow_index -> execution_id
        
        self._create_waitlist()
        self._initialize_blackboard()

        self._item_by_inferred_concept: Dict[str, WaitlistItem] = {
            item.inference_entry.concept_to_infer.concept_name: item for item in self.waitlist.items
        }

    def _save_run_metadata(self):
        """Saves metadata about the current run environment (agent settings, paths, etc.)."""
        if not self.db:
            return

        # Extract relevant metadata
        metadata = {
            "agent_frame_model": self.agent_frame_model,
            "base_dir": self.body.base_dir if self.body else None,
            "max_cycles": self.max_cycles,
            "checkpoint_frequency": self.checkpoint_frequency
        }
        
        # Try to get LLM info if available
        if self.body and hasattr(self.body, "llm"):
            # Handle various LLM object structures (real or mock)
            if hasattr(self.body.llm, "model_name"): 
                metadata["llm_model"] = self.body.llm.model_name
            elif hasattr(self.body.llm, "name"):
                metadata["llm_model"] = self.body.llm.name
            elif hasattr(self.body.llm, "__class__"):
                metadata["llm_model"] = self.body.llm.__class__.__name__
            else:
                metadata["llm_model"] = str(type(self.body.llm).__name__)

        self.db.save_run_metadata(self.run_id, metadata)
        logging.info(f"Saved run metadata for run_id: {self.run_id}")

    def _create_waitlist(self):
        """Creates the waitlist from the inference repository."""
        items = [WaitlistItem(inference_entry=inf) for inf in self.inference_repo.get_all_inferences()]
        self.waitlist = Waitlist(id=str(uuid.uuid4()), items=items)
        self.waitlist.sort_by_flow_index()
        logging.info(f"Created waitlist {self.waitlist.id} with {len(self.waitlist.items)} items.")

    def _initialize_blackboard(self):
        """Initializes all concept and item states in the Blackboard."""
        if not self.waitlist:
            logging.error("Cannot initialize blackboard without a waitlist.")
            return

        all_concepts = list(self.concept_repo._concept_map.values())
        self.blackboard.initialize_states(all_concepts, self.waitlist.items)
        
        logging.info("Blackboard states initialized.")

    def _is_function_concept_ready(self, item: WaitlistItem) -> bool:
        """Checks if the function concept for an item is ready."""
        fc = item.inference_entry.function_concept
        return (fc is None) or (self.blackboard.get_concept_status(fc.concept_name) == 'complete')

    def _are_value_concepts_ready(self, item: WaitlistItem) -> bool:
        """
        Checks if value concepts are ready. For assigning inferences with multiple
        potential sources, it only requires one of the sources to be ready.
        """
        # Check for the special assignment case
        inference_sequence = item.inference_entry.inference_sequence
        wi = item.inference_entry.working_interpretation or {}
        syntax = wi.get("syntax", {})
        assign_source = syntax.get("assign_source")

        if inference_sequence == 'assigning' and isinstance(assign_source, list):
            potential_source_names = set(assign_source)
            other_value_concepts = []
            source_value_concepts = []

            for vc in item.inference_entry.value_concepts:
                if vc.concept_name in potential_source_names:
                    source_value_concepts.append(vc)
                else:
                    other_value_concepts.append(vc)

            # At least one source must be ready
            one_source_ready = any(self.blackboard.get_concept_status(vc.concept_name) == 'complete' for vc in source_value_concepts)
            
            # All other value concepts must be ready
            all_others_ready = all(self.blackboard.get_concept_status(vc.concept_name) == 'complete' for vc in other_value_concepts)
            
            return one_source_ready and all_others_ready

        # Default behavior for all other cases
        return all(self.blackboard.get_concept_status(vc.concept_name) == 'complete' for vc in item.inference_entry.value_concepts)

    def _are_supporting_items_complete(self, item: WaitlistItem) -> bool:
        """
        Checks if all direct supporting items for a given item are in a 'completed' state.
        This is based on the flow index hierarchy (e.g., item '1.1' supports '1').
        """
        supporting_items = self.waitlist.get_supporting_items(item)
        for support_item in supporting_items:
            support_flow_index = support_item.inference_entry.flow_info['flow_index']
            if self.blackboard.get_item_status(support_flow_index) != 'completed':
                logging.debug(f"    - Support item '{support_flow_index}' is NOT 'completed' (Status: {self.blackboard.get_item_status(support_flow_index)})")
                return False
        return True

    def _propagate_skip_state(self, item: WaitlistItem, parent_flow_index: str):
        """Marks the current item as skipped because its parent triggered a skip."""
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.info(f"Item {flow_index} is being skipped because its parent {parent_flow_index} triggered a skip.")

        self.blackboard.set_item_status(flow_index, 'completed')
        self.blackboard.set_item_completion_detail(flow_index, 'skipped')
        self.blackboard.set_item_result(flow_index, f"Skipped due to parent {parent_flow_index}")

        concept_name = item.inference_entry.concept_to_infer.concept_name
        self.blackboard.set_concept_status(concept_name, 'complete')

        # Manually update tracking for this skipped item
        self._update_execution_tracking(item, 'completed')

    def _is_ready(self, item: WaitlistItem) -> bool:
        """
        An item is ready if its dependencies are met. Certain flags can bypass checks.
        """
        flow_index = item.inference_entry.flow_info['flow_index']
        concept_name = item.inference_entry.concept_to_infer.concept_name
        is_first_execution = self.blackboard.get_execution_count(flow_index) == 0
        
        # Use INFO level for better visibility during debugging
        logging.info(f"--- Checking readiness for item {flow_index} [{concept_name}] (Cycle: {self.tracker.cycle_count}, ExecCount: {self.blackboard.get_execution_count(flow_index)}) ---")

        # Check for completion of all supporting items, unless bypassed.
        # This ensures procedural dependencies are met before continuing.
        start_with_support_reference_only = getattr(item.inference_entry, 'start_with_support_reference_only', False)
        start_without_support_reference_only_once = getattr(item.inference_entry, 'start_without_support_reference_only_once', False)
        if not start_with_support_reference_only and not (start_without_support_reference_only_once and is_first_execution):
            supporting_items = self.waitlist.get_supporting_items(item)
            if supporting_items:
                logging.info(f"  - Supporting items ({len(supporting_items)}): {[si.inference_entry.flow_info['flow_index'] for si in supporting_items]}")
            if not self._are_supporting_items_complete(item):
                incomplete_supports = [
                    f"{si.inference_entry.flow_info['flow_index']}={self.blackboard.get_item_status(si.inference_entry.flow_info['flow_index'])}"
                    for si in supporting_items
                    if self.blackboard.get_item_status(si.inference_entry.flow_info['flow_index']) != 'completed'
                ]
                logging.info(f"  - RESULT: NOT READY. Supporting items incomplete: {incomplete_supports}")
                return False
            logging.info(f"  - Supporting items check: PASSED")
        else:
            if start_with_support_reference_only:
                logging.info(f"  - Bypassed supporting items check (start_with_support_reference_only).")
            else:
                logging.info(f"  - Bypassed supporting items check (first execution only).")


        # Check function concept readiness, unless bypassed
        if not item.inference_entry.start_without_function:
            if not (item.inference_entry.start_without_function_only_once and is_first_execution):
                fc = item.inference_entry.function_concept
                fc_name = fc.concept_name if fc else "N/A"
                fc_status = self.blackboard.get_concept_status(fc_name) if fc else "N/A"
                logging.info(f"  - Function concept '{fc_name}': {fc_status}")
                if not self._is_function_concept_ready(item):
                    logging.info(f"  - RESULT: NOT READY. Function concept '{fc_name}' is not complete (Status: {fc_status}).")
                    return False
                logging.info(f"  - Function concept check: PASSED")
            else:
                logging.info(f"  - Bypassed function concept check (first execution only).")
        else:
            logging.info(f"  - Bypassed function concept check (always).")


        # Check value concept readiness, unless bypassed
        if item.inference_entry.start_without_value:
            logging.info(f"  - RESULT: IS READY (start_without_value is True).")
            return True

        if item.inference_entry.start_without_value_only_once and is_first_execution:
            logging.info(f"  - RESULT: IS READY (start_without_value_only_once on first execution).")
            return True

        # Log ALL value concept statuses for visibility
        all_vc_statuses = [
            f"'{vc.concept_name}'={self.blackboard.get_concept_status(vc.concept_name)}"
            for vc in item.inference_entry.value_concepts
        ]
        logging.info(f"  - Value concepts ({len(item.inference_entry.value_concepts)}): {all_vc_statuses}")

        if not self._are_value_concepts_ready(item):
            pending_vcs = [
                f"'{vc.concept_name}' (Status: {self.blackboard.get_concept_status(vc.concept_name)})"
                for vc in item.inference_entry.value_concepts
                if self.blackboard.get_concept_status(vc.concept_name) != 'complete'
            ]
            logging.info(f"  - RESULT: NOT READY. Value concepts not ready: {pending_vcs}")
            return False
        
        logging.info(f"  - Value concepts check: PASSED")
        logging.info(f"  - RESULT: IS READY. All checks passed for {flow_index}.")
        return True

    def _handle_inference_failure(self, item: WaitlistItem, error: Exception):
        """Handles the failed execution of an inference."""
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.error(f"An error occurred during inference for item {flow_index}: {error}")
        import traceback
        traceback.print_exc()
        self.blackboard.set_item_result(flow_index, f"Error: {error}")

    def _inference_execution(self, item: WaitlistItem) -> str:
        """
        Executes a real inference using a fresh AgentFrame for each execution.
        Updates the item's result and returns the new status.
        Captures all logs emitted during execution and stores them in the database.
        """
        flow_index = item.inference_entry.flow_info['flow_index']
        self.blackboard.increment_execution_count(flow_index)

        inference = item.inference_entry.inference
        if not inference:
            logging.error(f"Item {flow_index} has no Inference object to execute.")
            self.blackboard.set_item_result(flow_index, "Error: Missing Inference object")
            return "failed"

        # Set up log capture for this execution
        log_handler = None
        execution_id = None
        
        # Create execution record first to get execution_id (if DB is available)
        if self.tracker.db:
            execution_id = self.tracker.add_execution_record(
                cycle=self.tracker.cycle_count,
                flow_index=flow_index,
                inference_type=item.inference_entry.inference_sequence,
                status='in_progress',
                concept_inferred=item.inference_entry.concept_to_infer.concept_name
            )
            
            # Store execution_id for later status update
            if execution_id is not None:
                self._current_execution_ids[flow_index] = execution_id
                
                # Create and attach log handler to capture all logs
                log_handler = self.tracker.create_log_handler(execution_id=execution_id)
                root_logger = logging.getLogger()
                root_logger.addHandler(log_handler)

        try:
            states = self._execute_agent_frame(item, inference)
            status = self._process_inference_state(states, item)
            
            # Capture and save logs
            if log_handler and execution_id is not None:
                log_content = log_handler.get_log_content()
                if log_content.strip():  # Only save if there's content
                    self.tracker.capture_inference_log(execution_id, log_content)
            
            return status

        except Exception as e:
            # Allow NeedsUserInteraction to propagate to app layer for human-in-the-loop
            if e.__class__.__name__ == 'NeedsUserInteraction':
                raise

            self._handle_inference_failure(item, e)
            
            # Capture logs even on failure
            if log_handler and execution_id is not None:
                log_content = log_handler.get_log_content()
                if log_content.strip():
                    self.tracker.capture_inference_log(execution_id, log_content)
            
            return "failed"
        
        finally:
            # Remove log handler
            if log_handler:
                root_logger = logging.getLogger()
                root_logger.removeHandler(log_handler)
                log_handler.clear()

    async def _inference_execution_async(self, item: WaitlistItem) -> str:
        """
        Executes inference in a separate thread to avoid blocking the event loop.
        """
        return await asyncio.to_thread(self._inference_execution, item)

    def _execute_agent_frame(self, item: WaitlistItem, inference: Inference) -> BaseStates:
        """Creates and executes an AgentFrame for a given inference."""
        working_interpretation = item.inference_entry.working_interpretation or {}
        working_interpretation["blackboard"] = self.blackboard
        working_interpretation["workspace"] = self.workspace
        working_interpretation["flow_info"] = item.inference_entry.flow_info
        
        agent_frame = AgentFrame(
            self.agent_frame_model,
            working_interpretation=working_interpretation,
            body=self.body
        )
        agent_frame.configure(inference, item.inference_entry.inference_sequence)
        return inference.execute()

    def _process_inference_state(self, states: BaseStates, item: WaitlistItem) -> str:
        """
        Processes the state from an inference execution and determines the item's final status.
        """
        self._update_orchestrator_state(states)

        if item.inference_entry.inference_sequence == 'timing':
            return self._handle_timing_inference(states, item)
        
        return self._handle_regular_inference(states, item)

    def _update_orchestrator_state(self, states: BaseStates):
        """Updates the orchestrator's core components from the inference state."""
        if hasattr(states, 'workspace'):
            self.workspace = states.workspace
        if hasattr(states, 'blackboard'):
            self.blackboard = states.blackboard

    def _handle_timing_inference(self, states: BaseStates, item: WaitlistItem) -> str:
        """
        Handles the specific logic for timing inferences.
        This item itself completes, but may trigger a skip for its children.
        """
        flow_index = item.inference_entry.flow_info['flow_index']

        # If timing condition is not met, retry later.
        timing_ready = getattr(states, 'timing_ready', False)
        if not timing_ready:
            logging.info(f"Timing condition for item {flow_index} not met. Item will be retried.")
            return "pending"
        
        # The timing item itself has completed successfully.
        logging.info(f"Timing condition for item {flow_index} met. Item completed successfully.")
        self.blackboard.set_item_result(flow_index, "Success")
        
        # Now, check if this successful completion should trigger a skip for its children.
        if getattr(states, 'to_be_skipped', False):
            logging.info(f"Timing item {flow_index} is now triggering a skip for its dependent items.")
            dependent_items = self.waitlist.get_dependent_items(item)
            for dependent in dependent_items:
                self._propagate_skip_state(dependent, flow_index)

        # Mark the timing concept as complete, allowing dependent items to be checked.
        concept_name = item.inference_entry.concept_to_infer.concept_name
        self.blackboard.set_concept_status(concept_name, 'complete')
        return "completed"

    def _handle_regular_inference(self, states: BaseStates, item: WaitlistItem) -> str:
        """Handles the logic for all non-timing inferences."""
        flow_index = item.inference_entry.flow_info['flow_index']
        concept_name = item.inference_entry.concept_to_infer.concept_name
        logging.info(f"  -> Inference executed successfully for item {flow_index} [{concept_name}]")
        self.blackboard.set_item_result(flow_index, "Success")
        
        if item.inference_entry.inference_sequence.startswith('judgement'):
            condition_met = getattr(states, 'condition_met', None)
            if condition_met is True:
                logging.info(f"[{flow_index}] Judgement condition met. Marking as 'success'.")
                self.blackboard.set_item_completion_detail(flow_index, 'success')
            elif condition_met is False:
                logging.info(f"[{flow_index}] Judgement condition not met. Marking as 'condition_not_met'.")
                self.blackboard.set_item_completion_detail(flow_index, 'condition_not_met')
            
            # Store truth mask for filter injection if available (from TIA step)
            self._store_truth_mask_if_available(states, item)
        
        # Log all OR records found in states for debugging
        or_records_inference = [r for r in getattr(states, 'inference', []) if r.step_name == 'OR']
        or_records_context = [r for r in getattr(states, 'context', []) if r.step_name == 'OR']
        logging.info(f"[{flow_index}] OR records found - inference: {len(or_records_inference)}, context: {len(or_records_context)}")
        for r in or_records_inference:
            logging.info(f"[{flow_index}]   - inference OR: concept={r.concept.name if r.concept else 'None'}, has_ref={r.reference is not None}")
        for r in or_records_context:
            logging.info(f"[{flow_index}]   - context OR: concept={r.concept.name if r.concept else 'None'}, has_ref={r.reference is not None}")
        
        all_conditions_met = self._update_references_and_check_completion(states, item)
        
        return "completed" if all_conditions_met else "pending"

    def _store_truth_mask_if_available(self, states: BaseStates, item: WaitlistItem):
        """
        Store truth mask from judgement inference for filter injection.
        
        When a judgement inference with a 'for-each' quantifier completes,
        the TIA step produces a truth mask. We store this on the blackboard
        so that timing steps can inject it for downstream filtering.
        """
        # Check if there's a primary_filter_axis (indicates for-each quantifier was used)
        primary_filter_axis = getattr(states, 'primary_filter_axis', None)
        if not primary_filter_axis:
            logging.debug(f"No primary_filter_axis in states - no truth mask to store")
            return
        
        # Try to get the TIA output reference
        tia_ref = None
        if hasattr(states, 'get_reference'):
            tia_ref = states.get_reference("inference", "TIA")
        
        if not tia_ref:
            logging.debug(f"No TIA reference found in states")
            return
        
        # Build truth mask data
        concept_name = item.inference_entry.concept_to_infer.concept_name
        truth_mask_data = {
            'tensor': tia_ref.tensor if hasattr(tia_ref, 'tensor') else None,
            'axes': tia_ref.axes if hasattr(tia_ref, 'axes') else [],
            'filter_axis': primary_filter_axis,
            'shape': tia_ref.shape if hasattr(tia_ref, 'shape') else None,
        }
        
        self.blackboard.set_truth_mask(concept_name, truth_mask_data)
        logging.info(f"Stored truth mask for judgement concept '{concept_name}' "
                    f"(filter_axis='{primary_filter_axis}', shape={truth_mask_data['shape']})")

    def _update_references_and_check_completion(self, states: BaseStates, item: WaitlistItem) -> bool:
        """
        For quantifying loops, resets supporting items first, then updates all concept references from the state.
        This "reset first, then update" approach ensures the system is correctly prepared for the next loop iteration.
        Returns True if all conditions are met, False otherwise.
        """
        # 1. Check if the quantifying loop has completed.
        is_quantifying, is_complete = self._check_quantifying_completion(states, item)

        # 2. If the loop is not complete, reset the supporting items first.
        if is_quantifying and not is_complete:
            self._reset_supporting_items(item)

        # 3. Always update all concept references with the results from the latest inference.
        # This populates the blackboard with the necessary inputs for the *next* loop iteration.
        for category in ['inference', 'context']:
            if hasattr(states, category):
                for record in getattr(states, category):
                    if record.step_name == 'OR' and record.reference is not None:
                        self._update_concept_from_record(record, category, item, is_quantifying, is_complete)

        # 4. The overall process is only "complete" if the quantifying loop is finished.
        return not (is_quantifying and not is_complete)

    def _check_quantifying_completion(self, states: BaseStates, item: WaitlistItem) -> tuple[bool, bool]:
        """Checks if an item is a quantifying or looping inference and whether it has completed."""
        sequence_type = item.inference_entry.inference_sequence
        is_iterating = sequence_type in ('quantifying', 'looping')
        if not is_iterating:
            return False, True
        is_complete = getattr(getattr(states, 'syntax', None), 'completion_status', False)
        return True, is_complete

    def _reset_supporting_items(self, item: WaitlistItem):
        """Resets the status of all items that support the given item."""
        supporting_items = self.waitlist.get_supporting_items(item)
        if not supporting_items:
            return
            
        flow_index = item.inference_entry.flow_info['flow_index']
        sequence_type = item.inference_entry.inference_sequence
        logging.info(f"Iterating {sequence_type} for item {flow_index} not complete. Resetting supporters.")
        
        for support_item in supporting_items:
            support_flow_index = support_item.inference_entry.flow_info['flow_index']
            self.blackboard.set_item_status(support_flow_index, 'pending')
            self.blackboard.reset_execution_count(support_flow_index)

            # If the supporting item is an iterating sequence, clear its state from the workspace.
            if support_item.inference_entry.inference_sequence in ('quantifying', 'looping'):
                self._clear_quantifier_workspace_state(support_item)

            inferred_concept_entry = support_item.inference_entry.concept_to_infer
            if not inferred_concept_entry.is_ground_concept:
                # Check if concept is invariant - if so, keep both reference AND status intact
                if inferred_concept_entry.is_invariant:
                    # Invariant concepts keep their 'complete' status since they have valid data
                    # Only reset the item status, not the concept status
                    logging.info(f"  - Invariant concept '{inferred_concept_entry.concept_name}' keeps 'complete' status and reference intact.")
                else:
                    # Normal reset behavior for non-invariant concepts
                    self.blackboard.set_concept_status(inferred_concept_entry.concept_name, 'pending')
                    if inferred_concept_entry.concept:
                        inferred_concept_entry.concept.reference = None
                    logging.info(f"  - Reset item {support_flow_index} and concept '{inferred_concept_entry.concept_name}' to pending.")

    def _clear_quantifier_workspace_state(self, item: WaitlistItem):
        """Clears the state of a quantifier from the workspace."""
        syntax = item.inference_entry.working_interpretation.get("syntax", {})
        loop_base = syntax.get("LoopBaseConcept")
        q_index = syntax.get("quantifier_index")
        if loop_base and q_index is not None:
            workspace_key = f"{q_index}_{loop_base}"
            if workspace_key in self.workspace:
                del self.workspace[workspace_key]
                logging.info(f"  - Cleared workspace state for quantifier '{workspace_key}'.")

    def _update_concept_from_record(self, record: Any, category: str, item: WaitlistItem, is_quantifying: bool, is_complete: bool):
        """Processes a single 'OR' record from the inference state, updating the concept reference."""
        flow_index = item.inference_entry.flow_info['flow_index']
        concept_name = self._get_concept_name_from_record(record, category, item)
        if not concept_name:
            logging.warning(f"[{flow_index}] Could not extract concept name from OR record (category={category})")
            return

        concept_entry = self.concept_repo.get_concept(concept_name)
        if not (concept_entry and concept_entry.concept):
            logging.warning(f"[{flow_index}] Could not find concept '{concept_name}' in repo to update reference.")
            return

        concept_entry.concept.reference = record.reference.copy()
        logging.info(f"[{flow_index}] Updated reference for concept '{concept_name}' from inference state.")

        # For quantifying loops, only set the concept to 'complete' when the loop itself is finished.
        # This rule only applies to the main inferred concept, not context concepts.
        if category == 'context' or not is_quantifying or (is_quantifying and is_complete):
            old_status = self.blackboard.get_concept_status(concept_name)
            self.blackboard.set_concept_status(concept_name, 'complete')
            logging.info(f"[{flow_index}] Concept '{concept_name}' status: '{old_status}' -> 'complete'")
        else:
            logging.info(f"[{flow_index}] Concept '{concept_name}' reference updated, but status remains 'pending' (quantifying loop not complete).")

    def _get_concept_name_from_record(self, record: Any, category: str, item: WaitlistItem) -> Optional[str]:
        """Extracts the concept name from a state record."""
        if record.concept:
            return record.concept.name
        if category == 'inference':
            return item.inference_entry.concept_to_infer.concept_name
        return None

    def _update_execution_tracking(self, item: WaitlistItem, status: str):
        """
        Updates the process tracker after an item execution attempt.
        Note: The execution record is created in _inference_execution() before execution
        to get the execution_id for log capture. This method updates the status and counters.
        """
        flow_index = item.inference_entry.flow_info['flow_index']
        
        # Update the execution record status if we have the execution_id
        execution_id = self._current_execution_ids.get(flow_index)
        if execution_id is not None and self.tracker.db:
            self.tracker.update_execution_status(execution_id, status)
            # Clean up the stored execution_id
            del self._current_execution_ids[flow_index]

        if status == 'completed':
            detail = self.blackboard.get_item_completion_detail(item.inference_entry.flow_info['flow_index'])
            if detail == 'skipped':
                logging.info(f"Item {flow_index} SKIPPED.")
                self.tracker.skipped_executions += 1
            else:  # 'success', 'condition_not_met', or None
                logging.info(f"Item {flow_index} COMPLETED.")
                self.tracker.successful_executions += 1
            
            self.tracker.record_completion(flow_index)
        elif status == 'failed':
            logging.error(f"Item {flow_index} FAILED.")
            self.tracker.failed_executions += 1
        elif status == 'pending':
            logging.info(f"Item {flow_index} did not complete, will retry.")
            self.tracker.retry_count += 1

    def _execute_item(self, item: WaitlistItem) -> str:
        """Executes a single waitlist item and updates its status and tracking info."""
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.info(f"Item {flow_index} is ready. Executing.")

        self.blackboard.set_item_status(flow_index, 'in_progress')
        
        try:
            new_status = self._inference_execution(item)
        except Exception as e:
            # Check for user interaction exception to reset status before propagating
            if e.__class__.__name__ == 'NeedsUserInteraction':
                logging.info(f"Item {flow_index} paused for user interaction. Resetting to 'pending'.")
                self.blackboard.set_item_status(flow_index, 'pending')
                raise
            raise

        self.tracker.total_executions += 1
        self.blackboard.set_item_status(flow_index, new_status)

        self._update_execution_tracking(item, new_status)

        return new_status

    async def _execute_item_async(self, item: WaitlistItem) -> str:
        """Executes a single waitlist item asynchronously and updates its status and tracking info."""
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.info(f"Item {flow_index} is ready. Executing.")

        self.blackboard.set_item_status(flow_index, 'in_progress')
        
        try:
            new_status = await self._inference_execution_async(item)
        except Exception as e:
            # Check for user interaction exception to reset status before propagating
            if e.__class__.__name__ == 'NeedsUserInteraction':
                logging.info(f"Item {flow_index} paused for user interaction. Resetting to 'pending'.")
                self.blackboard.set_item_status(flow_index, 'pending')
                raise
            raise

        self.tracker.total_executions += 1
        self.blackboard.set_item_status(flow_index, new_status)

        self._update_execution_tracking(item, new_status)

        return new_status

    def _run_cycle(self, retries_from_previous_cycle: List[WaitlistItem]) -> tuple[bool, List[WaitlistItem]]:
        """Processes one cycle of the orchestration loop."""
        cycle_executions = 0
        cycle_successes = 0
        next_cycle_retries: List[WaitlistItem] = []
        inference_count_in_cycle = 0  # Track inferences executed in this cycle

        # Get items to process for this cycle, prioritizing retries
        retried_items_set = set(retries_from_previous_cycle)
        items_to_process = retries_from_previous_cycle + [
            item for item in self.waitlist.items if item not in retried_items_set
        ]

        for item in items_to_process:
            flow_index = item.inference_entry.flow_info['flow_index']
            if self.blackboard.get_item_status(flow_index) == 'pending' and self._is_ready(item):
                cycle_executions += 1
                inference_count_in_cycle += 1
                new_status = self._execute_item(item)

                if new_status == 'completed':
                    cycle_successes += 1
                else:
                    next_cycle_retries.append(item)
                
                # Checkpoint based on frequency (if enabled)
                if self.checkpoint_frequency and self.checkpoint_manager:
                    if inference_count_in_cycle % self.checkpoint_frequency == 0:
                        self.checkpoint_manager.save_state(
                            self.tracker.cycle_count, 
                            self, 
                            inference_count=inference_count_in_cycle
                        )
                        logging.info(f"Intra-cycle checkpoint saved at cycle {self.tracker.cycle_count}, inference {inference_count_in_cycle}")

        logging.info(f"Cycle {self.tracker.cycle_count}: {cycle_executions} executions, {cycle_successes} completions")

        return cycle_executions > 0, next_cycle_retries

    async def _run_cycle_async(self, retries_from_previous_cycle: List[WaitlistItem]) -> tuple[bool, List[WaitlistItem]]:
        """Processes one cycle of the orchestration loop asynchronously."""
        cycle_executions = 0
        cycle_successes = 0
        next_cycle_retries: List[WaitlistItem] = []
        inference_count_in_cycle = 0  # Track inferences executed in this cycle

        # Get items to process for this cycle, prioritizing retries
        retried_items_set = set(retries_from_previous_cycle)
        items_to_process = retries_from_previous_cycle + [
            item for item in self.waitlist.items if item not in retried_items_set
        ]

        for item in items_to_process:
            flow_index = item.inference_entry.flow_info['flow_index']
            if self.blackboard.get_item_status(flow_index) == 'pending' and self._is_ready(item):
                cycle_executions += 1
                inference_count_in_cycle += 1
                new_status = await self._execute_item_async(item)

                if new_status == 'completed':
                    cycle_successes += 1
                else:
                    next_cycle_retries.append(item)
                
                # Checkpoint based on frequency (if enabled)
                if self.checkpoint_frequency and self.checkpoint_manager:
                    if inference_count_in_cycle % self.checkpoint_frequency == 0:
                        self.checkpoint_manager.save_state(
                            self.tracker.cycle_count, 
                            self, 
                            inference_count=inference_count_in_cycle
                        )
                        logging.info(f"Intra-cycle checkpoint saved at cycle {self.tracker.cycle_count}, inference {inference_count_in_cycle}")

        logging.info(f"Cycle {self.tracker.cycle_count}: {cycle_executions} executions, {cycle_successes} completions")

        return cycle_executions > 0, next_cycle_retries

    def _log_stuck_items(self):
        """Logs items that are not completed when a deadlock is detected."""
        stuck_items = [i.inference_entry.flow_info['flow_index'] for i in self.waitlist.items if self.blackboard.get_item_status(i.inference_entry.flow_info['flow_index']) != 'completed']
        logging.warning(f"Stuck items: {stuck_items}")

    def _validate_repo_compatibility(self, checkpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates repository compatibility according to REPO_COMPATIBILITY.md.
        Checks for data sufficiency and state validity.
        
        Returns:
            Dictionary with:
            - 'compatible': bool - True if compatible
            - 'warnings': List[str] - List of warnings
            - 'errors': List[str] - List of errors (incompatibility issues)
        """
        warnings = []
        errors = []
        
        # 1. Data Sufficiency Check: Ground Concepts
        # Every ground concept in the new repo must have data (either in repo or checkpoint)
        completed_concepts = checkpoint_data.get("completed_concepts", {})
        missing_ground_concepts = []
        
        for concept_entry in self.concept_repo.get_all_concepts():
            if concept_entry.is_ground_concept:
                concept_name = concept_entry.concept_name
                # Check if it has data in repo
                has_repo_data = (concept_entry.reference_data is not None) or \
                               (concept_entry.concept and concept_entry.concept.reference is not None)
                # Check if it has data in checkpoint
                has_checkpoint_data = concept_name in completed_concepts
                
                if not has_repo_data and not has_checkpoint_data:
                    missing_ground_concepts.append(concept_name)
                    errors.append(f"Ground concept '{concept_name}' is missing data in both repo and checkpoint.")
        
        if missing_ground_concepts:
            errors.append(f"Data Insufficiency: Missing ground concepts: {missing_ground_concepts}")
        
        # 2. Workspace Validity Check
        # Check if loop counters in workspace map to valid flow indices
        workspace = checkpoint_data.get("workspace", {})
        invalid_workspace_keys = []
        
        if self.waitlist:
            valid_flow_indices = {item.inference_entry.flow_info['flow_index'] for item in self.waitlist.items}
            
            # Workspace keys for quantifying loops typically look like "{quantifier_index}_{LoopBaseConcept}"
            # We need to check if the flow indices referenced in workspace still exist
            for key in workspace.keys():
                # Try to match workspace keys to flow indices
                # This is a heuristic - workspace structure depends on quantifying implementation
                if isinstance(key, str):
                    # Check if key might reference a flow index
                    parts = key.split('_')
                    if len(parts) >= 2:
                        # Might be a quantifier workspace key
                        # We'll be lenient here and just warn if we can't validate
                        pass
        
        # 3. Stale Interference Check (for PATCH mode)
        # This is handled in reconcile_state, but we can pre-check here
        saved_signatures = checkpoint_data.get("signatures", {})
        saved_concept_signatures = saved_signatures.get("concept_signatures", {})
        stale_concepts = []
        
        for concept_name, saved_sig in saved_concept_signatures.items():
            concept_entry = self.concept_repo.get_concept(concept_name)
            if concept_entry:
                current_sig = concept_entry.get_signature()
                if saved_sig != current_sig:
                    stale_concepts.append(concept_name)
                    warnings.append(f"Concept '{concept_name}' has changed logic (signature mismatch). Will be re-run in PATCH mode.")
        
        if stale_concepts:
            warnings.append(f"Found {len(stale_concepts)} concept(s) with changed logic: {stale_concepts}")
        
        compatible = len(errors) == 0
        
        return {
            'compatible': compatible,
            'warnings': warnings,
            'errors': errors
        }
    
    @classmethod
    def load_checkpoint(cls,
                       concept_repo: ConceptRepo,
                       inference_repo: InferenceRepo,
                       db_path: str,
                       agent_frame_model: str = "demo",
                       body: Optional[Body] = None,
                       max_cycles: int = 30,
                       run_id: Optional[str] = None,
                       new_run_id: Optional[str] = None,
                       cycle: Optional[int] = None,
                       inference_count: Optional[int] = None,
                       validate_environment: bool = True,
                       mode: str = "PATCH",
                       validate_compatibility: bool = True) -> 'Orchestrator':
        """
        Initialize the system from an existing DB file (checkpoint).
        Creates a new Orchestrator instance and reconciles its state with the checkpoint.
        
        Args:
            run_id: If provided, loads checkpoint for that specific run. 
                   If None, loads the latest checkpoint from any run.
            new_run_id: If provided, starts a NEW run history (fork) with this ID, 
                       initialized with state from the checkpoint.
                       The cycle count and execution history will start fresh.
            cycle: If provided, loads the checkpoint at this specific cycle number.
                  If None, loads the latest checkpoint for the specified run_id.
            inference_count: If provided with cycle, loads the checkpoint at this specific inference count within the cycle.
                            If None (but cycle is provided), loads the latest checkpoint for that cycle.
                            Ignored if cycle is None.
            validate_environment: If True, validates that the current environment matches the saved run metadata
                                 and logs warnings if there are mismatches.
            mode: Loading mode - one of:
                - "PATCH" (default): Smart merge - discard stale state, keep valid state
                - "OVERWRITE": Trust checkpoint 100%, ignore repo changes
                - "FILL_GAPS": Only fill missing values, prefer new repo defaults
            validate_compatibility: If True, validates repository compatibility before loading
        """
        # Initialize DB to find source run_id if needed
        db = OrchestratorDB(db_path)
        
        # If run_id (source) not provided, try to find the latest run
        source_run_id = run_id
        if not source_run_id:
            runs = db.list_runs()
            if runs:
                source_run_id = runs[0]['run_id']  # Most recent run
                logging.info(f"No run_id provided, using latest run as source: {source_run_id}")
            else:
                logging.warning(f"No runs found in {db_path}. Starting fresh orchestration.")
                # Create a new orchestrator with a new run_id (or provided new_run_id)
                orchestrator = cls(
                    concept_repo=concept_repo,
                    inference_repo=inference_repo,
                    agent_frame_model=agent_frame_model,
                    body=body,
                    max_cycles=max_cycles,
                    db_path=db_path,
                    run_id=new_run_id
                )
                return orchestrator
        
        # Determine target_run_id
        # If new_run_id is provided, we use that (Forking).
        # If not, we continue the source run (Continuity).
        target_run_id = new_run_id if new_run_id else source_run_id
        is_forking = (new_run_id is not None)
        
        # Create a new orchestrator instance with the TARGET run_id
        orchestrator = cls(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            agent_frame_model=agent_frame_model,
            body=body,
            max_cycles=max_cycles,
            db_path=db_path,
            run_id=target_run_id
        )
        
        # CheckpointManager needs to load from SOURCE run_id
        # We can use a temporary CheckpointManager with source_run_id
        source_db = OrchestratorDB(db_path, run_id=source_run_id)
        checkpoint_manager = CheckpointManager(source_db)
        
        # Validate environment compatibility of SOURCE run
        if validate_environment:
            validation_result = orchestrator.validate_environment_compatibility(source_run_id)
            if validation_result['warnings']:
                logging.warning(f"Environment validation for run_id {source_run_id} found {len(validation_result['warnings'])} warning(s):")
                for warning in validation_result['warnings']:
                    logging.warning(f"  - {warning}")
            if not validation_result['compatible']:
                logging.error(f"Environment is not fully compatible with saved run_id {source_run_id}. Proceeding anyway, but results may differ.")
        
        # Load checkpoint from SOURCE - either specific cycle/inference_count or latest
        checkpoint_data = None
        if cycle is not None:
            checkpoint_data = checkpoint_manager.load_checkpoint_by_cycle(cycle, source_run_id, inference_count)
            if checkpoint_data:
                if inference_count is not None:
                    logging.info(f"Loaded checkpoint from cycle {cycle}, inference {inference_count} in {db_path} for run_id: {source_run_id}")
                else:
                    logging.info(f"Loaded latest checkpoint from cycle {cycle} in {db_path} for run_id: {source_run_id}")
            else:
                logging.warning(f"No checkpoint found at cycle {cycle}, inference {inference_count} in {db_path} for run_id {source_run_id}. Starting fresh orchestration.")
        else:
            checkpoint_data = checkpoint_manager.load_latest_checkpoint(source_run_id)
            if checkpoint_data:
                logging.info(f"Loaded latest checkpoint from {db_path} for run_id: {source_run_id}")
            else:
                logging.warning(f"No checkpoint found in {db_path} for run_id {source_run_id}. Starting fresh orchestration.")
        
        # Validate repository compatibility if requested
        if checkpoint_data and validate_compatibility:
            compatibility_result = orchestrator._validate_repo_compatibility(checkpoint_data)
            if compatibility_result['warnings']:
                logging.warning(f"Repository compatibility validation found {len(compatibility_result['warnings'])} warning(s):")
                for warning in compatibility_result['warnings']:
                    logging.warning(f"  - {warning}")
            if compatibility_result['errors']:
                logging.error(f"Repository compatibility validation found {len(compatibility_result['errors'])} error(s):")
                for error in compatibility_result['errors']:
                    logging.error(f"  - {error}")
            if not compatibility_result['compatible']:
                logging.error(f"Repository is incompatible with checkpoint. Proceeding with reconciliation anyway, but execution may fail.")
        
        # Reconcile state with the specified mode
        if checkpoint_data:
            checkpoint_manager.reconcile_state(checkpoint_data, orchestrator, mode=mode, is_forking=is_forking)
            logging.info(f"Successfully reconciled checkpoint state (Mode: {mode})")
            
            # If forking, reset the tracker counters (start fresh history)
            if is_forking:
                orchestrator.tracker.reset_counters()
                logging.info(f"Forking enabled: Tracker counters reset for new run_id: {target_run_id}")
        
        return orchestrator

    def validate_environment_compatibility(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validates if the current orchestrator environment matches the saved run metadata.
        Useful for checking if a checkpoint can be safely loaded with different repos/environment.
        
        Args:
            run_id: The run_id to validate against. If None, uses self.run_id.
        
        Returns:
            Dictionary with validation results:
            - 'compatible': bool - True if environments match
            - 'warnings': List[str] - List of warnings about mismatches
            - 'saved_metadata': Dict - The saved metadata from the run
            - 'current_metadata': Dict - The current environment metadata
        """
        if not self.db:
            return {
                'compatible': False,
                'warnings': ['No database connection available'],
                'saved_metadata': None,
                'current_metadata': None
            }
        
        target_run_id = run_id or self.run_id
        if not target_run_id:
            return {
                'compatible': False,
                'warnings': ['No run_id provided'],
                'saved_metadata': None,
                'current_metadata': None
            }
        
        saved_metadata = self.db.get_run_metadata(target_run_id)
        if not saved_metadata:
            return {
                'compatible': True,  # No saved metadata means no constraints
                'warnings': ['No saved metadata found for this run_id'],
                'saved_metadata': None,
                'current_metadata': self._get_current_metadata()
            }
        
        # Get current metadata
        current_metadata = self._get_current_metadata()
        
        # Compare metadata
        warnings = []
        compatible = True
        
        # Check agent_frame_model
        if saved_metadata.get('agent_frame_model') != current_metadata.get('agent_frame_model'):
            warnings.append(f"agent_frame_model mismatch: saved='{saved_metadata.get('agent_frame_model')}', current='{current_metadata.get('agent_frame_model')}'")
            compatible = False
        
        # Check base_dir
        saved_base_dir = saved_metadata.get('base_dir')
        current_base_dir = current_metadata.get('base_dir')
        if saved_base_dir != current_base_dir:
            warnings.append(f"base_dir mismatch: saved='{saved_base_dir}', current='{current_base_dir}'")
            # base_dir mismatch is a warning, not necessarily incompatible (depends on use case)
        
        # Check LLM model
        saved_llm = saved_metadata.get('llm_model')
        current_llm = current_metadata.get('llm_model')
        if saved_llm and current_llm and saved_llm != current_llm:
            warnings.append(f"LLM model mismatch: saved='{saved_llm}', current='{current_llm}'")
            # LLM mismatch might affect results but checkpoint can still be loaded
        
        # Check max_cycles (less critical, but good to know)
        if saved_metadata.get('max_cycles') != current_metadata.get('max_cycles'):
            warnings.append(f"max_cycles mismatch: saved={saved_metadata.get('max_cycles')}, current={current_metadata.get('max_cycles')}")
        
        return {
            'compatible': compatible,
            'warnings': warnings,
            'saved_metadata': saved_metadata,
            'current_metadata': current_metadata
        }

    def _get_current_metadata(self) -> Dict[str, Any]:
        """Helper method to get current environment metadata."""
        metadata = {
            "agent_frame_model": self.agent_frame_model,
            "base_dir": self.body.base_dir if self.body else None,
            "max_cycles": self.max_cycles,
            "checkpoint_frequency": self.checkpoint_frequency
        }
        
        # Try to get LLM info if available
        if self.body and hasattr(self.body, "llm"):
            if hasattr(self.body.llm, "model_name"): 
                metadata["llm_model"] = self.body.llm.model_name
            elif hasattr(self.body.llm, "name"):
                metadata["llm_model"] = self.body.llm.name
            elif hasattr(self.body.llm, "__class__"):
                metadata["llm_model"] = self.body.llm.__class__.__name__
            else:
                metadata["llm_model"] = str(type(self.body.llm).__name__)
        
        return metadata

    def export_state(self) -> Dict[str, Any]:
        """
        Exports the comprehensive state of the orchestration.
        Includes execution history, logs, and concept states.
        """
        if self.checkpoint_manager:
            return self.checkpoint_manager.export_comprehensive_state(self)
        
        logging.warning("Checkpoint manager not initialized. Returning partial in-memory state.")
        return {
            "blackboard": self.blackboard.to_dict(),
            "tracker": self.tracker.to_dict(),
            "workspace": self.workspace, # Note: Reference objects might not be serialized here without CheckpointManager
            "warning": "Full export requires checkpoint manager (DB) to be initialized."
        }
    
    @staticmethod
    def list_available_checkpoints(db_path: str, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available checkpoints for a given database and optionally a specific run_id.
        Returns a list of checkpoints with cycle numbers and timestamps.
        
        Args:
            db_path: Path to the database file
            run_id: If provided, lists checkpoints only for this run. If None, lists all runs.
        
        Returns:
            List of dictionaries with 'run_id', 'cycle', and 'timestamp' keys
        """
        db = OrchestratorDB(db_path, run_id=run_id)
        
        if run_id:
            # List checkpoints for specific run
            checkpoints = db.list_checkpoints(run_id)
            return [{'run_id': run_id, **cp} for cp in checkpoints]
        else:
            # List checkpoints for all runs
            runs = db.list_runs()
            all_checkpoints = []
            for run in runs:
                run_checkpoints = db.list_checkpoints(run['run_id'])
                for cp in run_checkpoints:
                    all_checkpoints.append({'run_id': run['run_id'], **cp})
            return all_checkpoints

    async def run_async(self) -> List[ConceptEntry]:
        """Runs the orchestration loop asynchronously until completion or deadlock."""
        if not self.waitlist:
            logging.error("No waitlist created.")
            return []

        run_id_info = f" (Run ID: {self.run_id})" if self.run_id else ""
        logging.info(f"--- Starting Async Orchestration for Waitlist {self.waitlist.id}{run_id_info} ---")

        retries: List[WaitlistItem] = []

        while self.blackboard.get_all_pending_or_in_progress_items() and self.tracker.cycle_count < self.max_cycles:
            self.tracker.cycle_count += 1
            logging.info(f"--- Cycle {self.tracker.cycle_count} ---")
            
            progress_made, retries = await self._run_cycle_async(retries)
            
            # Save checkpoint at the end of each cycle (if frequency-based checkpointing didn't already save it)
            # Note: We still save at end of cycle even with frequency-based checkpointing to ensure we have a complete state
            if self.checkpoint_manager:
                # Get the current inference count for this cycle from the tracker
                # We'll use 0 as a marker for "end of cycle" checkpoint
                self.checkpoint_manager.save_state(self.tracker.cycle_count, self, inference_count=0)
            
            if not progress_made:
                logging.warning("No progress made in the last cycle. Deadlock detected.")
                self._log_stuck_items()
                break
        
        if self.tracker.cycle_count >= self.max_cycles:
            logging.error(f"Maximum cycles ({self.max_cycles}) reached. Stopping orchestration.")
        
        run_id_info = f" (Run ID: {self.run_id})" if self.run_id else ""
        logging.info(f"--- Orchestration Finished for Waitlist {self.waitlist.id}{run_id_info} ---")
        
        # Automatically log summary when orchestration completes
        if self.waitlist:
            self.tracker.log_summary(self.waitlist.id, self.waitlist.items, self.blackboard, self.concept_repo)

        final_concepts = [c for c in self.concept_repo.get_all_concepts() if c.is_final_concept]
        return final_concepts

    def run(self) -> List[ConceptEntry]:
        """Runs the orchestration loop until completion or deadlock."""
        if not self.waitlist:
            logging.error("No waitlist created.")
            return []

        run_id_info = f" (Run ID: {self.run_id})" if self.run_id else ""
        logging.info(f"--- Starting Orchestration for Waitlist {self.waitlist.id}{run_id_info} ---")

        retries: List[WaitlistItem] = []

        while self.blackboard.get_all_pending_or_in_progress_items() and self.tracker.cycle_count < self.max_cycles:
            self.tracker.cycle_count += 1
            logging.info(f"--- Cycle {self.tracker.cycle_count} ---")
            
            progress_made, retries = self._run_cycle(retries)
            
            # Save checkpoint at the end of each cycle (if frequency-based checkpointing didn't already save it)
            # Note: We still save at end of cycle even with frequency-based checkpointing to ensure we have a complete state
            if self.checkpoint_manager:
                # Get the current inference count for this cycle from the tracker
                # We'll use 0 as a marker for "end of cycle" checkpoint
                self.checkpoint_manager.save_state(self.tracker.cycle_count, self, inference_count=0)
            
            if not progress_made:
                logging.warning("No progress made in the last cycle. Deadlock detected.")
                self._log_stuck_items()
                break
        
        if self.tracker.cycle_count >= self.max_cycles:
            logging.error(f"Maximum cycles ({self.max_cycles}) reached. Stopping orchestration.")
        
        run_id_info = f" (Run ID: {self.run_id})" if self.run_id else ""
        logging.info(f"--- Orchestration Finished for Waitlist {self.waitlist.id}{run_id_info} ---")
        
        # Automatically log summary when orchestration completes
        if self.waitlist:
            self.tracker.log_summary(self.waitlist.id, self.waitlist.items, self.blackboard, self.concept_repo)

        final_concepts = [c for c in self.concept_repo.get_all_concepts() if c.is_final_concept]
        return final_concepts
