"""
Canvas Display Tool - Display artifacts on the Canvas.

This tool allows NormCode plans (specifically the compiler) to display
artifacts on the Canvas graph view:
- Source code with syntax highlighting
- Derived concept structures
- Compiled inference structures
- Graph previews

The tool emits WebSocket events that the frontend handles to update
the canvas display.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class CanvasDisplayTool:
    """
    A tool for displaying artifacts on the Canvas graph view.
    
    This tool is used by the compiler to show:
    1. Source code being compiled
    2. Derived concept structures
    3. Compiled inference graphs
    4. Intermediate compilation results
    
    All displays are non-blocking and purely for visualization.
    """
    
    def __init__(self, emit_callback: Optional[Callable[[str, Dict], None]] = None):
        """
        Initialize the Canvas display tool.
        
        Args:
            emit_callback: Callback to emit WebSocket events.
                          Signature: (event_type: str, data: dict) -> None
        """
        self._emit_callback = emit_callback
    
    def set_emit_callback(self, callback: Callable[[str, Dict], None]):
        """Set the callback for emitting WebSocket events."""
        self._emit_callback = callback
    
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
    # =========================================================================
    
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
    
    def _cmd_help(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle help command."""
        return {
            "action": "help",
            "message": "Available commands: create_node, delete_node, run, step, pause, stop, save, load, quit",
        }
    
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