import logging
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class ProcessTracker:
    """Tracks the orchestration process and provides statistics."""
    execution_history: List[Dict] = field(default_factory=list)
    completion_order: List[str] = field(default_factory=list)
    cycle_count: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    retry_count: int = 0
    
    def add_execution_record(self, cycle: int, flow_index: str, inference_type: str, 
                           status: str, concept_inferred: str):
        """Adds a record of an execution attempt."""
        record = {
            'cycle': cycle,
            'flow_index': flow_index,
            'inference_type': inference_type,
            'status': status,
            'concept_inferred': concept_inferred
        }
        self.execution_history.append(record)
    
    def record_completion(self, flow_index: str):
        """Records a successful completion."""
        self.completion_order.append(flow_index)
    
    def get_success_rate(self) -> float:
        """Calculates the success rate as a percentage."""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100
    
    def log_summary(self, waitlist_id: str, waitlist_items: List['WaitlistItem'], blackboard, concept_repo: 'ConceptRepo'):
        """Logs a comprehensive summary of the orchestration process."""
        logging.info(f"=== Orchestration Summary (ID: {waitlist_id}) ===")
        
        sorted_items = sorted(waitlist_items, key=lambda i: [int(p) for p in i.inference_entry.flow_info['flow_index'].split('.')])
        logging.info("--- Item Status ---")
        for item in sorted_items:
            fi = item.inference_entry.flow_info['flow_index']
            it = item.inference_entry.inference_sequence
            status = blackboard.get_item_status(fi)
            logging.info(f"  - Item {fi:<10} ({it:<12}): {status}")
        
        logging.info("--- Process Statistics ---")
        logging.info(f"  - Total cycles: {self.cycle_count}")
        logging.info(f"  - Total executions: {self.total_executions}")
        logging.info(f"  - Successful completions: {self.successful_executions}")
        logging.info(f"  - Retry attempts: {self.retry_count}")
        logging.info(f"  - Success rate: {self.get_success_rate():.1f}%")
        
        logging.info("--- Completion Order ---")
        for i, flow_index in enumerate(self.completion_order, 1):
            logging.info(f"  {i:2d}. {flow_index}")
        
        logging.info("--- Execution Flow ---")
        for record in self.execution_history:
            status_symbol = "[OK]" if record['status'] == 'completed' else "[RETRY]"
            logging.info(f"  Cycle {record['cycle']}: {status_symbol} {record['flow_index']} ({record['inference_type']}) -> {record['concept_inferred']}")

        logging.info("--- Final Concepts ---")
        for concept_entry in concept_repo.get_all_concepts():
            if concept_entry.is_final_concept:
                ref_tensor = concept_entry.concept.reference.tensor if concept_entry.concept and concept_entry.concept.reference is not None else "N/A"
                logging.info(f"  - {concept_entry.concept_name}: {ref_tensor}")
                ref_axis_names = concept_entry.concept.reference.axes if concept_entry.concept and concept_entry.concept.reference is not None else "N/A"
                logging.info(f"  - {concept_entry.concept_name}: {ref_axis_names}")
                ref_shape = concept_entry.concept.reference.shape if concept_entry.concept and concept_entry.concept.reference is not None else "N/A"
                logging.info(f"  - {concept_entry.concept_name}: {ref_shape}")
