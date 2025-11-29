import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from infra._orchest._waitlist import WaitlistItem
from infra._orchest._repo import ConceptRepo
from infra._loggers import ExecutionLogHandler

@dataclass
class ProcessTracker:
    """Tracks the orchestration process and provides statistics."""
    # execution_history is now managed via DB, but we keep a local list fallback or just rely on DB
    # For backward compatibility/simplicity if DB is missing, we could keep it, 
    # but the plan says "Instead of holding execution_history in memory lists... write directly to shared database".
    # So we will prioritize DB.
    
    completion_order: List[str] = field(default_factory=list)
    cycle_count: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    skipped_executions: int = 0
    failed_executions: int = 0
    retry_count: int = 0
    db: Optional[Any] = None  # OrchestratorDB instance
    run_id: Optional[str] = None  # Run ID for this tracker

    def set_db(self, db: Any):
        """Sets the shared database instance."""
        self.db = db
        # Extract run_id from db if available
        if db and hasattr(db, 'run_id'):
            self.run_id = db.run_id
    
    def set_run_id(self, run_id: str):
        """Sets the run_id for this tracker."""
        self.run_id = run_id

    def add_execution_record(self, cycle: int, flow_index: str, inference_type: str, 
                           status: str, concept_inferred: str) -> Optional[int]:
        """Adds a record of an execution attempt. Returns execution_id."""
        if self.db:
            return self.db.insert_execution(cycle, flow_index, inference_type, status, concept_inferred)
        return None
    
    def capture_inference_log(self, execution_id: int, log_content: str):
        """Captures detailed logs for a specific execution."""
        if self.db and execution_id is not None:
            self.db.insert_log(execution_id, log_content)
    
    def update_execution_status(self, execution_id: int, status: str):
        """Updates the status of an execution record."""
        if self.db and execution_id is not None:
            self.db.update_execution_status(execution_id, status)
    
    def create_log_handler(self, execution_id: Optional[int] = None) -> ExecutionLogHandler:
        """Creates a logging handler for capturing logs during execution."""
        return ExecutionLogHandler(execution_id=execution_id, run_id=self.run_id)
    
    def record_completion(self, flow_index: str):
        """Records a successful completion."""
        self.completion_order.append(flow_index)
    
    def reset_counters(self):
        """Resets all execution counters. Useful when forking a run to clear history statistics."""
        self.cycle_count = 0
        self.total_executions = 0
        self.successful_executions = 0
        self.skipped_executions = 0
        self.failed_executions = 0
        self.retry_count = 0
        self.completion_order = []

    def get_success_rate(self) -> float:
        """Calculates the success rate of executions."""
        if self.total_executions == 0:
            return 0.0

        terminal_executions = self.successful_executions + self.failed_executions
        if terminal_executions == 0:
            return 0.0
        return (self.successful_executions / terminal_executions) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize tracker state (counters). History is in DB."""
        return {
            "completion_order": self.completion_order,
            "cycle_count": self.cycle_count,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "skipped_executions": self.skipped_executions,
            "failed_executions": self.failed_executions,
            "retry_count": self.retry_count
        }

    def load_from_dict(self, data: Dict[str, Any]):
        """Restore tracker state."""
        self.completion_order = data.get("completion_order", [])
        self.cycle_count = data.get("cycle_count", 0)
        self.total_executions = data.get("total_executions", 0)
        self.successful_executions = data.get("successful_executions", 0)
        self.skipped_executions = data.get("skipped_executions", 0)
        self.failed_executions = data.get("failed_executions", 0)
        self.retry_count = data.get("retry_count", 0)
    
    def load_from_db(self, run_id: Optional[str] = None):
        """Initialize internal counters (success/fail counts) by querying the DB upon restart."""
        if not self.db:
            logging.warning("No database instance available. Cannot load counters from DB.")
            return
        
        try:
            # Use provided run_id or fall back to db.run_id
            target_run_id = run_id or getattr(self.db, 'run_id', None)
            execution_history = self.db.get_execution_history(target_run_id)
            execution_counts = self.db.get_execution_counts(target_run_id)
            
            # Reset counters
            self.total_executions = len(execution_history)
            self.successful_executions = execution_counts.get('completed', 0)
            self.failed_executions = execution_counts.get('failed', 0)
            self.retry_count = execution_counts.get('pending', 0)
            
            # Determine skipped executions from completion details (would need to check blackboard or logs)
            # For now, we'll use a simple heuristic: count 'completed' status as successful
            # The actual skipped count should come from the checkpoint data
            
            # Get the maximum cycle count
            if execution_history:
                self.cycle_count = max(record.get('cycle', 0) for record in execution_history)
            
            # Rebuild completion order from history
            self.completion_order = [
                record['flow_index'] 
                for record in execution_history 
                if record.get('status') == 'completed'
            ]
            
            logging.info(f"Loaded tracker state from DB (run_id: {target_run_id}): {self.total_executions} total executions, "
                        f"{self.successful_executions} successful, {self.failed_executions} failed, "
                        f"{self.retry_count} retries, cycle {self.cycle_count}")
        except Exception as e:
            logging.error(f"Failed to load tracker state from DB: {e}")
    
    def log_summary(self, waitlist_id: str, waitlist_items: List[WaitlistItem], blackboard, concept_repo: ConceptRepo):
        """Logs a comprehensive summary of the orchestration process."""
        logging.info(f"=== Orchestration Summary (ID: {waitlist_id}) ===")
        
        sorted_items = sorted(waitlist_items, key=lambda i: [int(p) for p in i.inference_entry.flow_info['flow_index'].split('.')])
        logging.info("--- Item Status ---")
        for item in sorted_items:
            fi = item.inference_entry.flow_info['flow_index']
            it = item.inference_entry.inference_sequence
            status = blackboard.get_item_status(fi)
            if status == 'completed':
                detail = blackboard.get_item_completion_detail(fi)
                if detail in ['skipped', 'condition_not_met']:
                    status = detail  # Use the more descriptive detail
            logging.info(f"  - Item {fi:<10} ({it:<12}): {status}")
        
        logging.info(f"--- Process Statistics ---")
        logging.info(f"  - Total cycles: {self.cycle_count}")
        logging.info(f"  - Total executions: {self.total_executions}")
        logging.info(f"  - Successful completions: {self.successful_executions}")
        logging.info(f"  - Skipped completions: {self.skipped_executions}")
        logging.info(f"  - Failed executions: {self.failed_executions}")
        logging.info(f"  - Benign retries (pending): {self.retry_count}")
        logging.info(f"  - Success rate (successful/(successful+failed)): {self.get_success_rate():.1f}%")
        
        logging.info("--- Completion Order ---")
        for i, flow_index in enumerate(self.completion_order, 1):
            logging.info(f"  {i:2d}. {flow_index}")
        
        logging.info("--- Execution Flow ---")
        execution_history = []
        if self.db:
            run_id = getattr(self.db, 'run_id', None)
            execution_history = self.db.get_execution_history(run_id)
            
        for record in execution_history:
            status_symbol = "[OK]" if record['status'] == 'completed' else "[RETRY]" if record['status'] == 'pending' else "[FAIL]"
            logging.info(f"  Cycle {record['cycle']}: {status_symbol} {record['flow_index']} ({record['inference_type']}) -> {record['concept_inferred']}")

        logging.info("--- Final Concepts ---")
        for concept_entry in concept_repo.get_all_concepts():
            if concept_entry.is_final_concept:
                ref_tensor = concept_entry.concept.reference.tensor if concept_entry.concept and concept_entry.concept.reference is not None else "N/A"
                logging.info(f"  - [Data Tensor] {concept_entry.concept_name}: {ref_tensor}")
                ref_axis_names = concept_entry.concept.reference.axes if concept_entry.concept and concept_entry.concept.reference is not None else "N/A"
                logging.info(f"  - [Axis Names] {concept_entry.concept_name}: {ref_axis_names}")
                ref_shape = concept_entry.concept.reference.shape if concept_entry.concept and concept_entry.concept.reference is not None else "N/A"
                logging.info(f"  - [Shape] {concept_entry.concept_name}: {ref_shape}")
