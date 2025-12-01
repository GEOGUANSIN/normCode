"""
Orchestration execution engine - handles the actual execution logic.
Separated from UI for better debugging and testability.
"""

import logging
import asyncio
import streamlit as st
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

from infra import ConceptRepo, InferenceRepo, Orchestrator
from tools import NeedsUserInteraction

from .state import ExecutionState, ExecutionStatus, ExecutionMetrics
from .constants import ExecutionPhase
from orchestration.orchestration_runner import inject_inputs_into_repo, verify_files_if_enabled, create_orchestrator

logger = logging.getLogger(__name__)


class OrchestrationExecutionEngine:
    """
    Handles orchestration execution with comprehensive state tracking.
    Separated from UI for better debugging and testing.
    """
    
    def __init__(self, state: ExecutionState):
        """
        Initialize execution engine.
        
        Args:
            state: ExecutionState instance for tracking
        """
        self.state = state
        self.orchestrator: Optional[Orchestrator] = None
        self.app_config: Optional[Dict[str, Any]] = None
    
    async def execute_full_orchestration(
        self,
        config: Dict[str, Any],
        loaded_concepts: Optional[Dict],
        loaded_inferences: Optional[Dict],
        loaded_inputs: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Execute full orchestration workflow with comprehensive tracking.
        
        Returns:
            Dict with execution results
        """
        try:
            # Phase 1: Setup and data loading
            self.state.set_phase(ExecutionPhase.SETUP)
            logger.info("=== Starting Orchestration Execution ===")
            
            concepts_json, inferences_json, inputs_json = self._load_repository_data(
                config, loaded_concepts, loaded_inferences, loaded_inputs
            )
            
            # Create repositories
            concept_repo = ConceptRepo.from_json_list(concepts_json)
            logger.debug(f"Created concept repo with {len(concept_repo.get_all_concepts())} concepts")
            
            # Phase 2: Input injection
            if inputs_json:
                self.state.set_phase(ExecutionPhase.INPUT_INJECTION)
                count = inject_inputs_into_repo(concept_repo, inputs_json)
                self.state.add_debug_info('inputs_injected', count)
                logger.info(f"Injected {count} input concepts")
            
            inference_repo = InferenceRepo.from_json_list(inferences_json, concept_repo)
            logger.debug(f"Created inference repo with {len(inference_repo.get_all_inferences())} inferences")
            
            # Determine base directory
            body_base_dir = self._determine_base_directory(config)
            self.state.add_debug_info('base_dir', body_base_dir)
            
            # Phase 3: Verification
            if config['verify_files']:
                self.state.set_phase(ExecutionPhase.VERIFICATION)
                logger.info("Running file verification...")
                await verify_files_if_enabled(
                    config['verify_files'],
                    concept_repo,
                    inference_repo,
                    body_base_dir
                )
            
            # Phase 4: Create orchestrator
            self.state.set_phase(ExecutionPhase.ORCHESTRATOR_CREATION)
            logger.info("Creating orchestrator...")
            
            self.orchestrator, self.app_config = await create_orchestrator(
                concept_repo=concept_repo,
                inference_repo=inference_repo,
                llm_model=config['llm_model'],
                max_cycles=config['max_cycles'],
                base_dir=body_base_dir,
                db_path=config['db_path'],
                resume_option=config['resume_option'],
                run_id_to_resume=config['run_id_to_resume'],
                custom_run_id=config['custom_run_id'],
                new_run_id=config['new_run_id'],
                reconciliation_mode=config['reconciliation_mode'],
                concepts_file=config['concepts_file'],
                loaded_concepts=loaded_concepts,
                inferences_file=config['inferences_file'],
                loaded_inferences=loaded_inferences,
                inputs_file=config['inputs_file'],
                loaded_inputs=loaded_inputs,
                base_dir_option=config['base_dir_option'],
                verify_files=config['verify_files']
            )
            
            # Start execution tracking
            self.state.start(self.orchestrator.run_id)
            self.state.add_debug_info('max_cycles', config['max_cycles'])
            logger.info(f"Orchestrator created with run_id: {self.orchestrator.run_id}")
            
            # Phase 5: Execute
            self.state.set_phase(ExecutionPhase.EXECUTION)
            final_concepts = await self._run_orchestration_async()
            
            # Phase 6: Completion
            self.state.set_phase(ExecutionPhase.COMPLETION)
            self.state.complete()
            
            return {
                'status': 'success',
                'run_id': self.orchestrator.run_id,
                'final_concepts': final_concepts,
                'duration': self.state.metrics.elapsed_time,
                'app_config': self.app_config
            }
            
        except NeedsUserInteraction as interaction:
            logger.info(f"User interaction required: {interaction.interaction_id}")
            self.state.pause()
            raise
        
        except Exception as e:
            logger.exception(f"Execution failed: {str(e)}")
            self.state.fail(str(e))
            raise
    
    async def _run_orchestration_async(self):
        """Run the orchestration with progress tracking."""
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not initialized")
        
        # Start async execution as a task
        task = asyncio.create_task(self.orchestrator.run_async())
        
        # Track progress while running
        while not task.done():
            self._update_metrics_from_orchestrator()
            await asyncio.sleep(0.1)  # Fast polling for metrics
        
        # Get final result
        final_concepts = await task
        self._update_metrics_from_orchestrator()  # Final update
        
        logger.info(f"Orchestration completed: {len(final_concepts)} final concepts")
        return final_concepts
    
    def _update_metrics_from_orchestrator(self):
        """Update execution metrics from orchestrator state."""
        if not self.orchestrator:
            return
        
        # Update from waitlist and blackboard
        if self.orchestrator.waitlist and self.orchestrator.blackboard:
            total_items = len(self.orchestrator.waitlist.items)
            completed_count = 0
            pending_count = 0
            in_progress_count = 0
            
            for item in self.orchestrator.waitlist.items:
                flow_index = item.inference_entry.flow_info['flow_index']
                status = self.orchestrator.blackboard.get_item_status(flow_index)
                if status == 'completed':
                    completed_count += 1
                elif status == 'in_progress':
                    in_progress_count += 1
                elif status == 'pending':
                    pending_count += 1
            
            self.state.update_metrics(
                total_items=total_items,
                completed_items=completed_count,
                in_progress_items=in_progress_count,
                pending_items=pending_count
            )
        
        # Update from tracker
        if self.orchestrator.tracker:
            self.state.update_metrics(
                cycle_count=self.orchestrator.tracker.cycle_count,
                total_executions=self.orchestrator.tracker.total_executions,
                successful_executions=self.orchestrator.tracker.successful_executions,
                failed_items=self.orchestrator.tracker.failed_executions,
                retry_count=self.orchestrator.tracker.retry_count
            )
    
    def get_current_metrics(self) -> ExecutionMetrics:
        """Get current execution metrics."""
        self._update_metrics_from_orchestrator()
        return self.state.metrics
    
    def _load_repository_data(
        self,
        config: Dict[str, Any],
        loaded_concepts: Optional[Dict],
        loaded_inferences: Optional[Dict],
        loaded_inputs: Optional[Dict]
    ) -> Tuple[Dict, Dict, Optional[Dict]]:
        """
        Load repository data from files or session state.
        
        Returns:
            Tuple of (concepts_json, inferences_json, inputs_json)
        """
        import json
        
        # Load concepts
        if config['concepts_file']:
            config['concepts_file'].seek(0)
            content = config['concepts_file'].read().decode('utf-8')
            concepts_json = json.loads(content)
            # Store for resumption
            st.session_state.loaded_repo_files['concepts'] = {
                'name': config['concepts_file'].name,
                'content': content,
                'path': None
            }
        else:
            concepts_json = json.loads(loaded_concepts['content'])
        
        # Load inferences
        if config['inferences_file']:
            config['inferences_file'].seek(0)
            content = config['inferences_file'].read().decode('utf-8')
            inferences_json = json.loads(content)
            st.session_state.loaded_repo_files['inferences'] = {
                'name': config['inferences_file'].name,
                'content': content,
                'path': None
            }
        else:
            inferences_json = json.loads(loaded_inferences['content'])
        
        # Load inputs (optional)
        inputs_json = None
        if config['inputs_file']:
            config['inputs_file'].seek(0)
            content = config['inputs_file'].read().decode('utf-8')
            inputs_json = json.loads(content)
            st.session_state.loaded_repo_files['inputs'] = {
                'name': config['inputs_file'].name,
                'content': content,
                'path': None
            }
        elif loaded_inputs:
            inputs_json = json.loads(loaded_inputs['content'])
        
        return concepts_json, inferences_json, inputs_json
    
    def _determine_base_directory(self, config: Dict[str, Any]) -> str:
        """Determine base directory from configuration."""
        from core.config import SCRIPT_DIR, PROJECT_ROOT
        
        if config['base_dir_option'] == "Project Root":
            return str(PROJECT_ROOT)
        elif config['base_dir_option'] == "Custom Path" and config['custom_base_dir']:
            return config['custom_base_dir']
        else:
            return str(SCRIPT_DIR)

