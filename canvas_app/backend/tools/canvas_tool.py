"""
Canvas Tool - Display and Query artifacts on the Canvas.

This tool allows NormCode plans (specifically the compiler) to:

DISPLAY (write to frontend):
- Source code with syntax highlighting
- Derived concept structures
- Compiled inference structures
- Graph previews

QUERY (read from execution state):
- Project information and metadata
- Graph structure (concepts, inferences, nodes)
- Execution state (status, completed nodes, values)
- Concept values (reference data)

The tool emits WebSocket events for display and queries the execution
service for read operations.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from services.execution.controller import ExecutionController

logger = logging.getLogger(__name__)


class CanvasDisplayTool:
    """
    A tool for displaying and querying the Canvas graph view.
    
    This tool is used by the compiler/chat controller to:
    
    DISPLAY (write operations):
    1. Source code being compiled
    2. Derived concept structures
    3. Compiled inference graphs
    4. Intermediate compilation results
    
    QUERY (read operations):
    1. Project metadata and info
    2. Graph structure summary
    3. Execution state and node statuses
    4. Concept values (current reference data)
    5. Node details by flow_index
    
    This enables the chat controller to explain what's happening
    in the currently loaded project.
    """
    
    def __init__(
        self, 
        emit_callback: Optional[Callable[[str, Dict], None]] = None,
        execution_getter: Optional[Callable[[], Optional["ExecutionController"]]] = None
    ):
        """
        Initialize the Canvas tool.
        
        Args:
            emit_callback: Callback to emit WebSocket events.
                          Signature: (event_type: str, data: dict) -> None
            execution_getter: Callable that returns the current main ExecutionController.
                             This allows querying the live execution state.
        """
        self._emit_callback = emit_callback
        self._execution_getter = execution_getter
    
    def set_emit_callback(self, callback: Callable[[str, Dict], None]):
        """Set the callback for emitting WebSocket events."""
        self._emit_callback = callback
    
    def set_execution_getter(self, getter: Callable[[], Optional["ExecutionController"]]):
        """
        Set the getter for accessing the main ExecutionController.
        
        This enables query operations to access live execution state.
        """
        self._execution_getter = getter
    
    def _get_execution_controller(self) -> Optional["ExecutionController"]:
        """Get the current main ExecutionController if available."""
        if self._execution_getter:
            return self._execution_getter()
        return None
    
    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit a WebSocket event if callback is set."""
        if self._emit_callback:
            try:
                self._emit_callback(event_type, data)
            except Exception as e:
                logger.error(f"Failed to emit canvas event {event_type}: {e}")
    
    # =========================================================================
    # Display Methods
    # =========================================================================
    
    def display_source(
        self, 
        source: str, 
        language: str = "ncds",
        title: Optional[str] = None,
        highlight_lines: Optional[List[int]] = None
    ):
        """
        Display source code on the canvas.
        
        Args:
            source: The source code content
            language: Language for syntax highlighting (ncds, ncd, ncn, json, python)
            title: Optional title for the source display
            highlight_lines: Optional list of line numbers to highlight
        """
        self._emit("canvas:display_source", {
            "source": source,
            "language": language,
            "title": title,
            "highlight_lines": highlight_lines or [],
        })
        logger.debug(f"Display source [{language}]: {len(source)} chars")
    
    def show_derived_structure(
        self, 
        concepts: List[Dict[str, Any]],
        title: Optional[str] = None
    ):
        """
        Display a derived concept structure on the canvas.
        
        Args:
            concepts: List of derived concept definitions
            title: Optional title for the structure view
        """
        self._emit("canvas:show_structure", {
            "type": "derived",
            "concepts": concepts,
            "title": title or "Derived Structure",
        })
        logger.debug(f"Show derived structure: {len(concepts)} concepts")
    
    def show_inference_structure(
        self,
        inferences: List[Dict[str, Any]],
        title: Optional[str] = None
    ):
        """
        Display an inference structure (flow graph) on the canvas.
        
        Args:
            inferences: List of inference definitions
            title: Optional title for the structure view
        """
        self._emit("canvas:show_structure", {
            "type": "inference",
            "inferences": inferences,
            "title": title or "Inference Structure",
        })
        logger.debug(f"Show inference structure: {len(inferences)} inferences")
    
    def load_compiled_plan(
        self,
        concepts_json: Dict[str, Any],
        inferences_json: Dict[str, Any],
        title: Optional[str] = None
    ):
        """
        Load a fully compiled plan onto the canvas for visualization.
        
        Args:
            concepts_json: The concepts.json content
            inferences_json: The inferences.json content
            title: Optional title for the loaded plan
        """
        self._emit("canvas:load_plan", {
            "concepts": concepts_json,
            "inferences": inferences_json,
            "title": title or "Compiled Plan",
        })
        logger.debug(f"Load compiled plan: {len(concepts_json)} concepts")
    
    def highlight_node(self, flow_index: str, style: str = "focus"):
        """
        Highlight a specific node in the current graph.
        
        Args:
            flow_index: The flow index of the node to highlight
            style: Highlight style ('focus', 'success', 'error', 'warning')
        """
        self._emit("canvas:highlight", {
            "flow_index": flow_index,
            "style": style,
        })
    
    def highlight_nodes(self, flow_indices: List[str], style: str = "focus"):
        """
        Highlight multiple nodes in the current graph.
        
        Args:
            flow_indices: List of flow indices to highlight
            style: Highlight style ('focus', 'success', 'error', 'warning')
        """
        self._emit("canvas:highlight_multiple", {
            "flow_indices": flow_indices,
            "style": style,
        })
    
    def clear_highlights(self):
        """Clear all node highlights."""
        self._emit("canvas:clear_highlights", {})
    
    def show_compilation_step(
        self,
        step_name: str,
        step_index: int,
        total_steps: int,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Display a compilation step progress indicator.
        
        Args:
            step_name: Name of the current step (e.g., 'derivation', 'formalization')
            step_index: Current step index (1-based)
            total_steps: Total number of steps
            data: Optional data associated with this step
        """
        self._emit("canvas:compilation_step", {
            "step_name": step_name,
            "step_index": step_index,
            "total_steps": total_steps,
            "data": data or {},
        })
        logger.info(f"Compilation step {step_index}/{total_steps}: {step_name}")
    
    # =========================================================================
    # Query Methods - Read from Execution State
    # =========================================================================
    
    def get_project_info(self) -> Dict[str, Any]:
        """
        Get information about the currently loaded project.
        
        This checks multiple sources:
        1. ExecutionController (for execution-ready state)
        2. GraphService (for graph visualization data)
        3. ProjectService (for open project config)
        
        Returns:
            Dict containing:
            - project_id: Project identifier
            - is_loaded: Whether repositories are loaded (execution-ready)
            - is_open: Whether a project config is open
            - has_graph: Whether graph data is available for visualization
            - concepts_count: Number of concepts
            - inferences_count: Number of inferences
            - run_id: Current run ID (if executing)
            - config: Project configuration
            - hint: Helpful message about the current state
        """
        # Try to get controller from execution_getter first
        controller = self._get_execution_controller()
        
        # Check graph_service for loaded graph data
        graph_info = self._get_graph_info()
        has_graph = graph_info.get("has_graph", False)
        
        # Check project_service for open project info
        project_config = self._get_project_config()
        
        # Also check if there's a project OPENED (config) even if repos not loaded
        try:
            from services.execution_service import execution_controller_registry, get_execution_controller
            from services.project_service import project_service
            
            active_project_id = execution_controller_registry.get_active_project_id()
            
            # If no controller from getter, try direct lookup by current project ID
            if controller is None and project_service.is_project_open and project_service.current_config:
                current_project_id = project_service.current_config.id
                controller = get_execution_controller(current_project_id)
                logger.debug(f"Direct lookup controller for {current_project_id}: "
                            f"found={controller is not None}, "
                            f"concept_repo={controller.concept_repo is not None if controller else 'N/A'}")
        except Exception as e:
            active_project_id = None
            logger.debug(f"Error in project lookup: {e}")
        
        if controller and controller.concept_repo is not None:
            # Fully execution-ready
            return {
                "is_loaded": True,
                "is_open": True,
                "has_graph": has_graph,
                "project_id": controller.project_id,
                "project_name": project_config.get("name") if project_config else None,
                "concepts_count": len(controller.concept_repo.entries) if controller.concept_repo else 0,
                "inferences_count": len(controller.inference_repo.inferences) if controller.inference_repo else 0,
                "run_id": getattr(controller.orchestrator, 'run_id', None) if controller.orchestrator else None,
                "config": controller._load_config if hasattr(controller, '_load_config') else None,
                "hint": None,
            }
        elif has_graph:
            # Graph is loaded (visible) but execution controller not ready
            return {
                "is_loaded": False,
                "is_open": True,
                "has_graph": True,
                "project_id": active_project_id,
                "project_name": project_config.get("name") if project_config else None,
                "concepts_count": graph_info.get("concepts_count", 0),
                "inferences_count": graph_info.get("inferences_count", 0),
                "hint": "Graph is visible but execution is not ready. Click the 'Load' button to enable execution.",
            }
        elif active_project_id or project_config:
            # Project config is open but nothing loaded
            return {
                "is_loaded": False,
                "is_open": True,
                "has_graph": False,
                "project_id": active_project_id,
                "project_name": project_config.get("name") if project_config else None,
                "hint": "Project is open but data is not loaded. Click 'Load' to load repositories.",
            }
        else:
            return {
                "is_loaded": False,
                "is_open": False,
                "has_graph": False,
                "project_id": None,
                "hint": "No project is currently open. Open a project to get started.",
            }
    
    def _get_graph_info(self) -> Dict[str, Any]:
        """Get info from graph_service if available."""
        try:
            from services.graph_service import graph_service
            if graph_service.current_graph and graph_service.current_graph.nodes:
                return {
                    "has_graph": True,
                    "concepts_count": len(graph_service.concepts_data) if graph_service.concepts_data else 0,
                    "inferences_count": len(graph_service.inferences_data) if graph_service.inferences_data else 0,
                    "nodes_count": len(graph_service.current_graph.nodes),
                    "edges_count": len(graph_service.current_graph.edges),
                }
            return {"has_graph": False}
        except Exception as e:
            logger.debug(f"Could not get graph info: {e}")
            return {"has_graph": False}
    
    def _get_project_config(self) -> Optional[Dict[str, Any]]:
        """Get current project config from project_service if available."""
        try:
            from services.project_service import project_service
            if project_service.is_project_open and project_service.current_config:
                config = project_service.current_config
                return {
                    "name": config.name,
                    "id": config.id,
                    "description": config.description,
                }
            return None
        except Exception as e:
            logger.debug(f"Could not get project config: {e}")
            return None
    
    def get_execution_state(self) -> Dict[str, Any]:
        """
        Get the current execution state of the main project.
        
        Returns:
            Dict containing:
            - status: Current execution status (idle, running, paused, etc.)
            - current_inference: Flow index of currently executing inference
            - completed_count: Number of completed inferences
            - total_count: Total number of inferences
            - cycle_count: Current execution cycle
            - node_statuses: Dict of flow_index -> status
            - breakpoints: List of breakpoint flow indices
        """
        controller = self._get_execution_controller()
        if not controller:
            return {
                "status": "no_project",
                "is_loaded": False,
            }
        
        return controller.get_state()
    
    def get_graph_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the graph structure.
        
        This checks multiple sources:
        1. ExecutionController (for execution state + data)
        2. GraphService (fallback for visualization data)
        
        Returns:
            Dict containing:
            - concepts: List of concept summaries (name, type, is_ground, is_final)
            - inferences: List of inference summaries (flow_index, sequence, concept_to_infer)
            - structure: High-level statistics
        """
        controller = self._get_execution_controller()
        if not controller or not controller.concept_repo:
            # Fall back to graph_service for visualization data
            return self._get_graph_summary_from_graph_service()
        
        # Build concept summaries
        concepts = []
        for entry in controller.concept_repo.entries:
            concept = entry.concept if hasattr(entry, 'concept') else entry
            concepts.append({
                "name": concept.concept_name if hasattr(concept, 'concept_name') else str(concept),
                "type": getattr(concept, 'type', None),
                "is_ground": getattr(concept, 'is_ground_concept', False),
                "is_final": getattr(concept, 'is_final_concept', False),
                "has_value": concept.reference is not None if hasattr(concept, 'reference') else False,
                "natural_name": getattr(concept, 'natural_name', None),
            })
        
        # Build inference summaries
        inferences = []
        if controller.inference_repo:
            for inf in controller.inference_repo.inferences:
                flow_idx = inf.flow_info.get('flow_index', '') if hasattr(inf, 'flow_info') else ''
                inferences.append({
                    "flow_index": flow_idx,
                    "sequence": getattr(inf, 'inference_sequence', ''),
                    "concept_to_infer": inf.concept_to_infer.concept_name if hasattr(inf, 'concept_to_infer') else '',
                    "status": controller.node_statuses.get(flow_idx, 'unknown').value if hasattr(controller.node_statuses.get(flow_idx, 'unknown'), 'value') else str(controller.node_statuses.get(flow_idx, 'unknown')),
                })
        
        return {
            "is_loaded": True,
            "source": "execution_controller",
            "concepts": concepts,
            "inferences": inferences,
            "structure": {
                "concepts_count": len(concepts),
                "inferences_count": len(inferences),
                "ground_concepts": sum(1 for c in concepts if c.get('is_ground')),
                "final_concepts": sum(1 for c in concepts if c.get('is_final')),
                "concepts_with_values": sum(1 for c in concepts if c.get('has_value')),
            }
        }
    
    def _get_graph_summary_from_graph_service(self) -> Dict[str, Any]:
        """
        Fall back to graph_service for graph summary when execution controller isn't available.
        This allows us to describe the graph even when execution isn't ready.
        """
        try:
            from services.graph_service import graph_service
            
            if not graph_service.current_graph or not graph_service.current_graph.nodes:
                return {
                    "is_loaded": False,
                    "source": "none",
                    "concepts": [],
                    "inferences": [],
                    "hint": "No graph data available. Open and load a project first.",
                }
            
            # Extract concepts from graph nodes
            concepts = []
            inferences = []
            
            for node in graph_service.current_graph.nodes:
                node_data = node.data if hasattr(node, 'data') else {}
                
                # Check if this is a concept or inference node
                if node_data.get('node_type') == 'concept' or 'concept_name' in node_data:
                    concepts.append({
                        "name": node_data.get('concept_name', node.id),
                        "type": node_data.get('type'),
                        "is_ground": node_data.get('is_ground', False),
                        "is_final": node_data.get('is_final', False),
                        "natural_name": node_data.get('natural_name'),
                    })
                elif node_data.get('node_type') == 'inference' or 'flow_index' in node_data:
                    inferences.append({
                        "flow_index": node_data.get('flow_index', node.id),
                        "sequence": node_data.get('inference_sequence', ''),
                        "concept_to_infer": node_data.get('concept_to_infer', ''),
                        "status": "not_started",  # We don't have execution state
                    })
            
            return {
                "is_loaded": True,
                "source": "graph_service",
                "concepts": concepts,
                "inferences": inferences,
                "structure": {
                    "concepts_count": len(concepts),
                    "inferences_count": len(inferences),
                    "nodes_total": len(graph_service.current_graph.nodes),
                    "edges_total": len(graph_service.current_graph.edges),
                },
                "hint": "Graph data from visualization. Load repositories to enable execution.",
            }
        except Exception as e:
            logger.debug(f"Could not get graph summary from graph_service: {e}")
            return {
                "is_loaded": False,
                "source": "error",
                "concepts": [],
                "inferences": [],
                "hint": f"Error reading graph: {str(e)}",
            }
    
    def get_concept_value(self, concept_name: str) -> Dict[str, Any]:
        """
        Get the current value (reference data) for a specific concept.
        
        Args:
            concept_name: The name of the concept to query
            
        Returns:
            Dict containing:
            - found: Whether the concept was found
            - concept_name: The concept name
            - has_value: Whether the concept has a reference value
            - data: The reference data (if any)
            - axes: Axis names (if any)
            - shape: Data shape (if applicable)
        """
        controller = self._get_execution_controller()
        if not controller or not controller.concept_repo:
            return {
                "found": False,
                "concept_name": concept_name,
                "error": "No project loaded",
            }
        
        ref_data = controller.get_reference_data(concept_name)
        if ref_data is None:
            # Check if concept exists but has no value
            concept_entry = controller.concept_repo.get_concept(concept_name)
            if concept_entry is None:
                return {
                    "found": False,
                    "concept_name": concept_name,
                    "error": f"Concept '{concept_name}' not found",
                }
            return {
                "found": True,
                "concept_name": concept_name,
                "has_value": False,
                "data": None,
            }
        
        return {
            "found": True,
            "concept_name": concept_name,
            "has_value": True,
            **ref_data,
        }
    
    def get_all_values(self) -> Dict[str, Any]:
        """
        Get all concept values that currently have reference data.
        
        Returns:
            Dict containing:
            - values: Dict of concept_name -> value info
            - count: Number of concepts with values
        """
        controller = self._get_execution_controller()
        if not controller or not controller.concept_repo:
            return {
                "is_loaded": False,
                "values": {},
                "count": 0,
            }
        
        all_refs = controller.get_all_reference_data()
        return {
            "is_loaded": True,
            "values": all_refs,
            "count": len(all_refs),
        }
    
    def get_node_details(self, flow_index: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific node by flow_index.
        
        Args:
            flow_index: The flow index of the node (e.g., "1.3.2")
            
        Returns:
            Dict containing:
            - found: Whether the node was found
            - flow_index: The flow index
            - inference: Inference details (sequence, concept_to_infer, etc.)
            - status: Current execution status
            - value: Current concept value (if computed)
            - inputs: List of input concepts
            - paradigm: The paradigm being used (if any)
        """
        controller = self._get_execution_controller()
        if not controller or not controller.inference_repo:
            return {
                "found": False,
                "flow_index": flow_index,
                "error": "No project loaded",
            }
        
        # Find the inference
        target_inference = None
        for inf in controller.inference_repo.inferences:
            if inf.flow_info.get('flow_index') == flow_index:
                target_inference = inf
                break
        
        if not target_inference:
            return {
                "found": False,
                "flow_index": flow_index,
                "error": f"No inference found at flow_index '{flow_index}'",
            }
        
        # Get concept value
        concept_name = target_inference.concept_to_infer.concept_name
        value_info = self.get_concept_value(concept_name)
        
        # Get status
        status = controller.node_statuses.get(flow_index, 'pending')
        if hasattr(status, 'value'):
            status = status.value
        
        # Get working interpretation
        wi = getattr(target_inference, 'working_interpretation', {})
        if not isinstance(wi, dict):
            wi = {}
        
        return {
            "found": True,
            "flow_index": flow_index,
            "concept_name": concept_name,
            "inference_sequence": target_inference.inference_sequence,
            "function_concept": target_inference.function_concept.concept_name if hasattr(target_inference.function_concept, 'concept_name') else str(target_inference.function_concept),
            "value_concepts": [v.concept_name if hasattr(v, 'concept_name') else str(v) for v in (target_inference.value_concepts or [])],
            "context_concepts": [c.concept_name if hasattr(c, 'concept_name') else str(c) for c in (target_inference.context_concepts or [])],
            "status": status,
            "value": value_info if value_info.get('has_value') else None,
            "paradigm": wi.get('paradigm'),
            "working_interpretation": wi,
        }
    
    def get_execution_logs(self, limit: int = 50, flow_index: Optional[str] = None) -> Dict[str, Any]:
        """
        Get recent execution logs.
        
        Args:
            limit: Maximum number of log entries to return
            flow_index: Optional filter by flow_index
            
        Returns:
            Dict containing:
            - logs: List of log entries
            - count: Number of entries returned
        """
        controller = self._get_execution_controller()
        if not controller:
            return {
                "logs": [],
                "count": 0,
            }
        
        logs = controller.get_logs(limit=limit, flow_index=flow_index)
        return {
            "logs": logs,
            "count": len(logs),
        }
    
    def explain_context(self) -> Dict[str, Any]:
        """
        Gather comprehensive context for LLM to explain the current project/execution.
        
        This method collects all relevant information that would help an LLM
        explain what the project is about and its current state.
        
        Returns:
            Dict containing:
            - project: Project info
            - execution: Execution state
            - graph: Graph summary
            - recent_activity: Recent logs and node completions
            - explanation_prompt: Suggested prompt for LLM explanation
        """
        project_info = self.get_project_info()
        execution_state = self.get_execution_state()
        graph_summary = self.get_graph_summary()
        recent_logs = self.get_execution_logs(limit=10)
        
        # Build a suggested explanation prompt
        status = execution_state.get('status', 'unknown')
        completed = execution_state.get('completed_count', 0)
        total = execution_state.get('total_count', 0)
        is_loaded = project_info.get('is_loaded', False)
        is_open = project_info.get('is_open', False)
        hint = project_info.get('hint')
        
        if not is_loaded:
            if is_open:
                explanation_prompt = (
                    f"A project is open (ID: {project_info.get('project_id')}) but its repositories are not loaded yet. "
                    "The user needs to click the 'Load' button to load the repositories before querying graph data or running execution. "
                    "Suggest they click the reload/load button in the project header."
                )
            else:
                explanation_prompt = "No project is currently open. Ask the user to open a project first."
        elif status == 'idle':
            explanation_prompt = f"The project has {total} inferences. Execution has not started yet. You can explain the graph structure."
        elif status == 'running':
            current = execution_state.get('current_inference', '')
            explanation_prompt = f"Execution is running. Currently at inference {current}. {completed}/{total} complete."
        elif status == 'paused':
            current = execution_state.get('current_inference', '')
            explanation_prompt = f"Execution is paused at {current}. {completed}/{total} complete."
        elif status == 'completed':
            explanation_prompt = f"Execution completed! All {total} inferences finished. You can explain the results."
        else:
            explanation_prompt = f"Current status: {status}. {completed}/{total} inferences complete."
        
        return {
            "project": project_info,
            "execution": execution_state,
            "graph": graph_summary,
            "recent_logs": recent_logs,
            "explanation_prompt": explanation_prompt,
        }
    
    # =========================================================================
    # Factory Methods for NormCode Integration
    # =========================================================================
    
    def create_display_source_function(self, language: str = "ncds") -> Callable:
        """
        Create a function for displaying source code.
        
        Returns:
            A callable that takes (source: str, **kwargs) and displays on canvas
        """
        def display_fn(source: str = "", **kwargs) -> None:
            title = kwargs.get("title")
            highlight_lines = kwargs.get("highlight_lines")
            self.display_source(source, language=language, title=title, highlight_lines=highlight_lines)
        
        return display_fn
    
    def create_show_structure_function(self, structure_type: str = "derived") -> Callable:
        """
        Create a function for showing structure on canvas.
        
        Returns:
            A callable that takes (data: dict, **kwargs) and shows on canvas
        """
        def show_fn(data: Any = None, **kwargs) -> None:
            title = kwargs.get("title")
            if structure_type == "derived":
                concepts = data if isinstance(data, list) else []
                self.show_derived_structure(concepts, title=title)
            elif structure_type == "inference":
                inferences = data if isinstance(data, list) else []
                self.show_inference_structure(inferences, title=title)
        
        return show_fn
    
    # =========================================================================
    # Paradigm Affordances - Functions for composition (MFP → TVA pattern)
    # These return callables that the paradigm's composition_tool uses
    # =========================================================================
    
    @property
    def query_project(self) -> Callable:
        """
        Affordance: Return a function that queries project information.
        
        Used by paradigm: c_CanvasQuery-o_ProjectInfo
        
        The returned function:
        - Takes no arguments (or optional query_type)
        - Returns dict with project info, graph summary, or execution state
        """
        def _query_project_fn(query_type: str = "all", **kwargs) -> Dict[str, Any]:
            if query_type == "project":
                return self.get_project_info()
            elif query_type == "execution":
                return self.get_execution_state()
            elif query_type == "graph":
                return self.get_graph_summary()
            elif query_type == "context":
                return self.explain_context()
            else:
                # Return comprehensive context
                return self.explain_context()
        
        return _query_project_fn
    
    @property
    def query_value(self) -> Callable:
        """
        Affordance: Return a function that queries concept values.
        
        Used by paradigm: c_CanvasQuery-o_ConceptValue
        
        The returned function:
        - Takes concept_name as argument
        - Returns dict with concept value and metadata
        """
        def _query_value_fn(concept_name: str = "", **kwargs) -> Dict[str, Any]:
            name = concept_name or kwargs.get("name", "")
            if not name:
                return self.get_all_values()
            return self.get_concept_value(name)
        
        return _query_value_fn
    
    @property
    def query_node(self) -> Callable:
        """
        Affordance: Return a function that queries node details.
        
        Used by paradigm: c_CanvasQuery-o_NodeDetails
        
        The returned function:
        - Takes flow_index as argument
        - Returns dict with node details, status, and value
        """
        def _query_node_fn(flow_index: str = "", **kwargs) -> Dict[str, Any]:
            fi = flow_index or kwargs.get("flow_index", "")
            if not fi:
                return {"error": "flow_index is required"}
            return self.get_node_details(fi)
        
        return _query_node_fn
    
    @property
    def query_logs(self) -> Callable:
        """
        Affordance: Return a function that queries execution logs.
        
        Used by paradigm: c_CanvasQuery-o_Logs
        
        The returned function:
        - Takes optional limit and flow_index filter
        - Returns dict with log entries
        """
        def _query_logs_fn(limit: int = 50, flow_index: str = "", **kwargs) -> Dict[str, Any]:
            fi = flow_index or kwargs.get("flow_index")
            return self.get_execution_logs(limit=limit, flow_index=fi if fi else None)
        
        return _query_logs_fn
    
    @property
    def execute_command(self) -> Callable:
        """
        Affordance: Return a function that executes a canvas command.
        
        Used by paradigm: h_Command-c_CanvasExecute-o_Status
        
        The returned function:
        - Takes command_type and command_params
        - Executes the appropriate canvas operation
        - Returns status dict with success and data
        """
        def _execute_command_fn(
            command_type: str = "",
            command_params: Optional[Dict[str, Any]] = None,
            **kwargs
        ) -> Dict[str, Any]:
            params = command_params or kwargs.get("params", {})
            cmd_type = command_type or kwargs.get("type", "")
            
            try:
                result = self._dispatch_command(cmd_type, params)
                return {
                    "success": True,
                    "command_type": cmd_type,
                    "data": result,
                }
            except Exception as e:
                logger.error(f"Canvas command failed: {cmd_type} - {e}")
                return {
                    "success": False,
                    "command_type": cmd_type,
                    "error": str(e),
                    "data": None,
                }
        
        return _execute_command_fn
    
    def _dispatch_command(self, command_type: str, params: Dict[str, Any]) -> Any:
        """
        Dispatch a canvas command to the appropriate handler.
        
        Args:
            command_type: Type of command (e.g., 'create_node', 'run', 'zoom_in')
            params: Command parameters
            
        Returns:
            Command result data
        """
        # Node operations
        if command_type == "create_node":
            return self._cmd_create_node(params)
        elif command_type == "delete_node":
            return self._cmd_delete_node(params)
        elif command_type == "move_node":
            return self._cmd_move_node(params)
        elif command_type == "edit_node":
            return self._cmd_edit_node(params)
        elif command_type == "select_node":
            return self._cmd_select_node(params)
        
        # Edge operations
        elif command_type == "create_edge":
            return self._cmd_create_edge(params)
        elif command_type == "delete_edge":
            return self._cmd_delete_edge(params)
        
        # View operations
        elif command_type == "zoom_in":
            return self._cmd_view_operation("zoom_in", params)
        elif command_type == "zoom_out":
            return self._cmd_view_operation("zoom_out", params)
        elif command_type == "fit_view":
            return self._cmd_view_operation("fit_view", params)
        elif command_type == "center_on":
            return self._cmd_view_operation("center_on", params)
        
        # Execution operations
        elif command_type == "run":
            return self._cmd_execution("run", params)
        elif command_type == "step":
            return self._cmd_execution("step", params)
        elif command_type == "pause":
            return self._cmd_execution("pause", params)
        elif command_type == "stop":
            return self._cmd_execution("stop", params)
        elif command_type == "set_breakpoint":
            return self._cmd_breakpoint("set", params)
        elif command_type == "clear_breakpoint":
            return self._cmd_breakpoint("clear", params)
        
        # File operations
        elif command_type == "save":
            return self._cmd_file_operation("save", params)
        elif command_type == "load":
            return self._cmd_file_operation("load", params)
        elif command_type == "export":
            return self._cmd_file_operation("export", params)
        elif command_type == "import":
            return self._cmd_file_operation("import", params)
        
        # Session operations
        elif command_type == "help":
            return self._cmd_help(params)
        elif command_type == "status":
            return self._cmd_status(params)
        elif command_type == "undo":
            return self._cmd_undo_redo("undo", params)
        elif command_type == "redo":
            return self._cmd_undo_redo("redo", params)
        elif command_type in ("quit", "exit"):
            return {"action": "quit"}
        
        # Compilation operations
        elif command_type == "compile":
            return self._cmd_compilation("compile", params)
        elif command_type == "validate":
            return self._cmd_compilation("validate", params)
        elif command_type == "formalize":
            return self._cmd_compilation("formalize", params)
        elif command_type == "activate":
            return self._cmd_compilation("activate", params)
        
        # Query operations
        elif command_type == "query_project":
            return self._cmd_query("project", params)
        elif command_type == "query_execution":
            return self._cmd_query("execution", params)
        elif command_type == "query_graph":
            return self._cmd_query("graph", params)
        elif command_type == "query_value":
            return self._cmd_query("value", params)
        elif command_type == "query_node":
            return self._cmd_query("node", params)
        elif command_type == "query_logs":
            return self._cmd_query("logs", params)
        elif command_type == "explain":
            return self._cmd_query("explain", params)
        
        # Meta operations
        elif command_type == "clarify":
            return {"action": "clarify", "message": "Please clarify your request."}
        elif command_type == "chat":
            return {"action": "chat", "message": params.get("message", "")}
        
        else:
            raise ValueError(f"Unknown command type: {command_type}")
    
    # =========================================================================
    # Command Handlers - emit WebSocket events and return results
    # =========================================================================
    
    def _cmd_create_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create_node command."""
        self._emit("canvas:command", {
            "type": "create_node",
            "params": params,
        })
        return {
            "created": True,
            "node_type": params.get("node_type", "value"),
            "label": params.get("label", "New Node"),
        }
    
    def _cmd_delete_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delete_node command."""
        self._emit("canvas:command", {
            "type": "delete_node",
            "params": params,
        })
        return {
            "deleted": True,
            "node_id": params.get("node_id") or params.get("node_hint"),
        }
    
    def _cmd_move_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle move_node command."""
        self._emit("canvas:command", {
            "type": "move_node",
            "params": params,
        })
        return {
            "moved": True,
            "position": params.get("position"),
        }
    
    def _cmd_edit_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle edit_node command."""
        self._emit("canvas:command", {
            "type": "edit_node",
            "params": params,
        })
        return {
            "edited": True,
            "node_id": params.get("node_id") or params.get("node_hint"),
        }
    
    def _cmd_select_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle select_node command."""
        self._emit("canvas:command", {
            "type": "select_node",
            "params": params,
        })
        return {
            "selected": True,
            "node_id": params.get("node_id") or params.get("node_hint"),
        }
    
    def _cmd_create_edge(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create_edge command."""
        self._emit("canvas:command", {
            "type": "create_edge",
            "params": params,
        })
        return {
            "created": True,
            "source": params.get("source_id") or params.get("source_hint"),
            "target": params.get("target_id") or params.get("target_hint"),
        }
    
    def _cmd_delete_edge(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delete_edge command."""
        self._emit("canvas:command", {
            "type": "delete_edge",
            "params": params,
        })
        return {
            "deleted": True,
        }
    
    def _cmd_view_operation(self, op_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle view operations (zoom, fit, center)."""
        self._emit("canvas:command", {
            "type": op_type,
            "params": params,
        })
        return {
            "operation": op_type,
            "applied": True,
        }
    
    def _cmd_execution(self, op_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execution operations (run, step, pause, stop)."""
        self._emit("canvas:command", {
            "type": op_type,
            "params": params,
        })
        return {
            "operation": op_type,
            "started": True,
        }
    
    def _cmd_breakpoint(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle breakpoint operations."""
        self._emit("canvas:command", {
            "type": f"{action}_breakpoint",
            "params": params,
        })
        return {
            "action": action,
            "flow_index": params.get("flow_index") or params.get("node_id"),
        }
    
    def _cmd_file_operation(self, op_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file operations (save, load, export, import)."""
        self._emit("canvas:command", {
            "type": op_type,
            "params": params,
        })
        return {
            "operation": op_type,
            "path": params.get("path"),
            "success": True,
        }
    
    def _cmd_query(self, query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle query operations - retrieve data from execution state."""
        if query_type == "project":
            return {
                "action": "query",
                "query_type": "project",
                "data": self.get_project_info(),
            }
        elif query_type == "execution":
            return {
                "action": "query",
                "query_type": "execution",
                "data": self.get_execution_state(),
            }
        elif query_type == "graph":
            return {
                "action": "query",
                "query_type": "graph",
                "data": self.get_graph_summary(),
            }
        elif query_type == "value":
            concept_name = params.get("concept_name", "")
            if concept_name:
                return {
                    "action": "query",
                    "query_type": "value",
                    "data": self.get_concept_value(concept_name),
                }
            else:
                return {
                    "action": "query",
                    "query_type": "all_values",
                    "data": self.get_all_values(),
                }
        elif query_type == "node":
            flow_index = params.get("flow_index", "")
            if not flow_index:
                return {
                    "action": "query",
                    "query_type": "node",
                    "error": "flow_index parameter required",
                }
            return {
                "action": "query",
                "query_type": "node",
                "data": self.get_node_details(flow_index),
            }
        elif query_type == "logs":
            limit = params.get("limit", 20)
            flow_index = params.get("flow_index")
            return {
                "action": "query",
                "query_type": "logs",
                "data": self.get_execution_logs(limit=limit, flow_index=flow_index),
            }
        elif query_type == "explain":
            return {
                "action": "query",
                "query_type": "explain",
                "data": self.explain_context(),
            }
        else:
            return {
                "action": "query",
                "query_type": query_type,
                "error": f"Unknown query type: {query_type}",
            }
    
    def _cmd_help(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle help command - provide comprehensive help about available commands.
        
        The help can be filtered by topic or show all available commands.
        """
        topic = params.get("topic", "all")
        
        help_content = {
            "action": "help",
            "topic": topic,
        }
        
        # Define all help categories
        categories = {
            "query": {
                "title": "Query & Understand",
                "description": "Ask questions about the project, execution state, and data values.",
                "commands": {
                    "explain": {
                        "usage": "explain | what's happening",
                        "description": "Get a comprehensive summary of the current project and execution state.",
                        "examples": ["explain what's happening", "summarize the current state", "what is this project doing?"]
                    },
                    "query_project": {
                        "usage": "query project | what project is loaded",
                        "description": "Get information about the loaded project (name, concepts count, etc.).",
                        "examples": ["what project is loaded?", "show project info", "tell me about this project"]
                    },
                    "query_execution": {
                        "usage": "query execution | is it running",
                        "description": "Get the current execution state (status, progress, current node).",
                        "examples": ["what's the execution status?", "how many nodes completed?", "is it running?"]
                    },
                    "query_graph": {
                        "usage": "query graph | describe the structure",
                        "description": "Get a summary of the graph structure (concepts, inferences).",
                        "examples": ["describe the graph", "what concepts exist?", "show me the structure"]
                    },
                    "query_value": {
                        "usage": "query value [concept_name]",
                        "description": "Get the current value of a specific concept.",
                        "examples": ["what is the value of 'user input'?", "show me the output value", "get value of result"]
                    },
                    "query_node": {
                        "usage": "query node [flow_index]",
                        "description": "Get detailed information about a specific node.",
                        "examples": ["tell me about node 1.3", "what does inference 1.2.4 do?", "explain node 1"]
                    },
                    "query_logs": {
                        "usage": "query logs | show logs",
                        "description": "Get recent execution logs.",
                        "examples": ["show me the logs", "what happened recently?", "show execution history"]
                    },
                }
            },
            "execution": {
                "title": "Run & Debug",
                "description": "Control plan execution and debugging.",
                "commands": {
                    "run": {
                        "usage": "run",
                        "description": "Start or resume execution of the plan.",
                        "examples": ["run", "run the plan", "start execution"]
                    },
                    "step": {
                        "usage": "step [count]",
                        "description": "Execute one (or N) inferences at a time.",
                        "examples": ["step", "step once", "step 3 times"]
                    },
                    "pause": {
                        "usage": "pause",
                        "description": "Pause execution at the current point.",
                        "examples": ["pause", "pause execution"]
                    },
                    "stop": {
                        "usage": "stop",
                        "description": "Stop execution completely.",
                        "examples": ["stop", "stop execution", "halt"]
                    },
                    "set_breakpoint": {
                        "usage": "set breakpoint at [node/flow_index]",
                        "description": "Set a breakpoint to pause at a specific node.",
                        "examples": ["set breakpoint at 1.3", "break at 'output'"]
                    },
                    "clear_breakpoint": {
                        "usage": "clear breakpoint [at node | all]",
                        "description": "Remove a breakpoint.",
                        "examples": ["clear breakpoint at 1.3", "remove all breakpoints"]
                    },
                }
            },
            "nodes": {
                "title": "Edit Nodes",
                "description": "Create, edit, and manage graph nodes.",
                "commands": {
                    "create_node": {
                        "usage": "create node [label] as [type]",
                        "description": "Create a new node. Types: value, function, context.",
                        "examples": ["create node 'user input' as value", "create function node 'process'"]
                    },
                    "delete_node": {
                        "usage": "delete node [name or id]",
                        "description": "Delete a node from the graph.",
                        "examples": ["delete node 'temp'", "delete the process node"]
                    },
                    "edit_node": {
                        "usage": "edit node [name] [property] to [value]",
                        "description": "Edit a node's properties.",
                        "examples": ["rename 'temp' to 'result'", "edit node label"]
                    },
                    "select_node": {
                        "usage": "select node [name or flow_index]",
                        "description": "Select a node to view its details.",
                        "examples": ["select node 1.3", "show me the 'output' node"]
                    },
                }
            },
            "edges": {
                "title": "Edit Edges",
                "description": "Create and manage connections between nodes.",
                "commands": {
                    "create_edge": {
                        "usage": "connect [source] to [target]",
                        "description": "Create a connection between two nodes.",
                        "examples": ["connect 'input' to 'process'", "link user data to function"]
                    },
                    "delete_edge": {
                        "usage": "disconnect [source] from [target]",
                        "description": "Remove a connection.",
                        "examples": ["disconnect 'input' from 'process'"]
                    },
                }
            },
            "view": {
                "title": "Navigate",
                "description": "Zoom and navigate the graph view.",
                "commands": {
                    "zoom_in": {"usage": "zoom in", "description": "Zoom in on the graph."},
                    "zoom_out": {"usage": "zoom out", "description": "Zoom out of the graph."},
                    "fit_view": {"usage": "fit view | show all", "description": "Fit entire graph in view."},
                    "center_on": {"usage": "center on [node]", "description": "Center view on a node."},
                }
            },
            "files": {
                "title": "Files",
                "description": "Save, load, import, and export projects.",
                "commands": {
                    "save": {"usage": "save [path]", "description": "Save the current project."},
                    "load": {"usage": "load [path]", "description": "Load a project from file."},
                    "export": {"usage": "export [path] as [format]", "description": "Export to file (ncds, json, png, svg)."},
                    "import": {"usage": "import [path]", "description": "Import from file."},
                }
            },
            "compilation": {
                "title": "Compile",
                "description": "Compile NormCode drafts into executable plans.",
                "commands": {
                    "compile": {"usage": "compile", "description": "Compile the current draft."},
                    "validate": {"usage": "validate", "description": "Validate the plan structure."},
                    "formalize": {"usage": "formalize", "description": "Formalize the draft."},
                    "activate": {"usage": "activate", "description": "Activate into repositories."},
                }
            },
        }
        
        if topic == "all":
            # Return summary of all categories
            help_content["summary"] = "I can help you work with NormCode plans. Here's what I can do:"
            help_content["categories"] = {
                k: {"title": v["title"], "description": v["description"], "command_count": len(v["commands"])}
                for k, v in categories.items()
            }
            help_content["quick_examples"] = [
                {"say": "What is this project?", "does": "Shows project info"},
                {"say": "Run the plan", "does": "Starts execution"},
                {"say": "What's the value of 'result'?", "does": "Shows concept value"},
                {"say": "Explain node 1.3", "does": "Describes what a node does"},
                {"say": "Step", "does": "Executes one inference"},
                {"say": "Set breakpoint at 1.2", "does": "Pauses execution at that node"},
            ]
            help_content["message"] = (
                "**Available Command Categories:**\n"
                "• **Query**: explain, query_project, query_value, query_node\n"
                "• **Execution**: run, step, pause, stop, set_breakpoint\n"
                "• **Graph**: create_node, delete_node, edit_node, select_node\n"
                "• **View**: zoom_in, zoom_out, fit_view, center_on\n"
                "• **Files**: save, load, export, import\n"
                "• **Compile**: compile, validate, formalize, activate\n\n"
                "Say 'help [topic]' for details (e.g., 'help query' or 'help execution')."
            )
        elif topic in categories:
            # Return detailed help for specific category
            cat = categories[topic]
            help_content["category"] = topic
            help_content["title"] = cat["title"]
            help_content["description"] = cat["description"]
            help_content["commands"] = cat["commands"]
            
            # Build readable message
            lines = [f"**{cat['title']}**: {cat['description']}\n"]
            for cmd, info in cat["commands"].items():
                lines.append(f"• **{cmd}**: {info['description']}")
                lines.append(f"  Usage: `{info['usage']}`")
                if "examples" in info:
                    lines.append(f"  Examples: {', '.join(info['examples'][:2])}")
            help_content["message"] = "\n".join(lines)
        else:
            help_content["message"] = f"Unknown help topic: '{topic}'. Try 'help' for all categories."
            help_content["available_topics"] = list(categories.keys())
        
        return help_content
    
    def _cmd_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status command."""
        self._emit("canvas:command", {
            "type": "status",
            "params": params,
        })
        return {
            "action": "status",
            "requested": True,
        }
    
    def _cmd_undo_redo(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle undo/redo commands."""
        self._emit("canvas:command", {
            "type": action,
            "params": params,
        })
        return {
            "action": action,
            "applied": True,
        }
    
    def _cmd_compilation(self, phase: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle compilation commands."""
        self._emit("canvas:command", {
            "type": phase,
            "params": params,
        })
        return {
            "phase": phase,
            "started": True,
        }