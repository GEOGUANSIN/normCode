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
