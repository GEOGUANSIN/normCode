"""
Canvas-native display tool for showing artifacts on the Canvas.

This tool allows NormCode plans to display artifacts on the Canvas UI:
- Source code viewer
- Structure trees
- Compiled plan graphs
- Node highlights and annotations

Unlike ChatTool (interactive), CanvasDisplayTool is primarily for display.
"""

import logging
from typing import Callable, Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class HighlightStyle(str, Enum):
    """Style for node highlighting."""
    FOCUS = "focus"         # Primary focus (blue glow)
    SUCCESS = "success"     # Success state (green)
    WARNING = "warning"     # Warning state (yellow)
    ERROR = "error"         # Error state (red)
    INFO = "info"           # Informational (gray)


class ArtifactType(str, Enum):
    """Type of artifact to display."""
    SOURCE = "source"       # Source code
    STRUCTURE = "structure" # Concept/inference structure
    GRAPH = "graph"         # Graph preview
    JSON = "json"           # Raw JSON
    TREE = "tree"           # Tree view
    TABLE = "table"         # Table view


@dataclass
class Annotation:
    """An annotation attached to a node."""
    id: str
    flow_index: str
    text: str
    annotation_type: str = "info"


class CanvasDisplayTool:
    """
    Tool for NormCode plans to display artifacts on the Canvas.
    
    Usage in NormCode plan:
        # Show source code
        Body.canvas.show_source(draft_code, language="ncds")
        
        # Show derived structure
        Body.canvas.show_structure(concepts, title="Derived Concepts")
        
        # Load compiled plan into graph
        Body.canvas.load_plan(concepts, inferences)
        
        # Highlight a specific node
        Body.canvas.highlight_node("1.1", style="focus")
    """
    
    def __init__(
        self, 
        emit_callback: Optional[Callable[[str, Dict], None]] = None,
        project_context: Optional[Dict] = None
    ):
        """
        Initialize the Canvas display tool.
        
        Args:
            emit_callback: Callback to emit WebSocket events.
            project_context: Optional context about the current project.
        """
        self._emit_callback = emit_callback
        self._project_context = project_context or {}
        self._annotations: Dict[str, Annotation] = {}
    
    def set_emit_callback(self, callback: Callable[[str, Dict], None]):
        """Set the callback for emitting WebSocket events."""
        self._emit_callback = callback
    
    def set_project_context(self, context: Dict):
        """Set the project context."""
        self._project_context = context
    
    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit a WebSocket event if callback is set."""
        if self._emit_callback:
            try:
                self._emit_callback(event_type, data)
            except Exception as e:
                logger.error(f"Failed to emit event {event_type}: {e}")
    
    # =========================================================================
    # Display Methods
    # =========================================================================
    
    def show_source(
        self, 
        code: str, 
        language: str = "ncds", 
        title: str = None,
        line_numbers: bool = True
    ) -> None:
        """
        Display source code in a source viewer panel.
        
        Args:
            code: The source code to display
            language: Programming language for syntax highlighting
            title: Optional title for the viewer
            line_numbers: Whether to show line numbers
        """
        self._emit("canvas:show_source", {
            "code": code,
            "language": language,
            "title": title or f"Source ({language})",
            "line_numbers": line_numbers,
        })
        
        logger.debug(f"Canvas show source [{language}]: {len(code)} chars")
    
    def show_structure(
        self, 
        structure: Dict, 
        title: str = None,
        view_type: str = "tree"
    ) -> None:
        """
        Display a concept/inference structure as a tree or graph.
        
        Args:
            structure: The structure data (concepts, inferences, etc.)
            title: Optional title for the viewer
            view_type: How to display (tree, json, graph)
        """
        self._emit("canvas:show_structure", {
            "structure": structure,
            "title": title or "Structure",
            "view_type": view_type,
        })
        
        logger.debug(f"Canvas show structure [{view_type}]: {title or 'untitled'}")
    
    def load_plan(
        self, 
        concepts: List[Dict], 
        inferences: List[Dict],
        auto_layout: bool = True
    ) -> None:
        """
        Load a compiled plan into the graph view.
        
        This replaces the current graph with the new plan.
        
        Args:
            concepts: List of concept dictionaries
            inferences: List of inference dictionaries
            auto_layout: Whether to auto-layout the graph
        """
        self._emit("canvas:load_plan", {
            "concepts": concepts,
            "inferences": inferences,
            "auto_layout": auto_layout,
        })
        
        logger.info(f"Canvas load plan: {len(concepts)} concepts, {len(inferences)} inferences")
    
    def update_node(self, flow_index: str, data: Dict) -> None:
        """
        Update data for a specific node.
        
        Args:
            flow_index: The node's flow index
            data: Data to merge into the node
        """
        self._emit("canvas:update_node", {
            "flow_index": flow_index,
            "data": data,
        })
        
        logger.debug(f"Canvas update node {flow_index}")
    
    # =========================================================================
    # Highlighting & Annotations
    # =========================================================================
    
    def highlight_node(
        self, 
        flow_index: str, 
        style: str = "focus",
        duration: float = None
    ) -> None:
        """
        Highlight a specific node in the graph.
        
        Args:
            flow_index: The node's flow index
            style: Highlight style (focus, success, warning, error, info)
            duration: Optional duration in seconds (None = permanent until cleared)
        """
        self._emit("canvas:highlight_node", {
            "flow_index": flow_index,
            "style": style,
            "duration": duration,
        })
        
        logger.debug(f"Canvas highlight node {flow_index} [{style}]")
    
    def clear_highlight(self, flow_index: str = None) -> None:
        """
        Clear node highlighting.
        
        Args:
            flow_index: Specific node to clear, or None to clear all
        """
        self._emit("canvas:clear_highlight", {
            "flow_index": flow_index,
        })
        
        logger.debug(f"Canvas clear highlight: {flow_index or 'all'}")
    
    def add_annotation(
        self, 
        flow_index: str, 
        text: str, 
        annotation_type: str = "info"
    ) -> str:
        """
        Add an annotation to a node.
        
        Args:
            flow_index: The node's flow index
            text: The annotation text
            annotation_type: Type of annotation (info, warning, error, success)
            
        Returns:
            The annotation ID
        """
        import uuid
        annotation_id = str(uuid.uuid4())[:8]
        
        annotation = Annotation(
            id=annotation_id,
            flow_index=flow_index,
            text=text,
            annotation_type=annotation_type,
        )
        
        self._annotations[annotation_id] = annotation
        
        self._emit("canvas:add_annotation", {
            "id": annotation_id,
            "flow_index": flow_index,
            "text": text,
            "type": annotation_type,
        })
        
        logger.debug(f"Canvas add annotation to {flow_index}: {text[:30]}...")
        
        return annotation_id
    
    def remove_annotation(self, annotation_id: str) -> bool:
        """
        Remove an annotation.
        
        Args:
            annotation_id: The annotation ID
            
        Returns:
            True if annotation was found and removed
        """
        if annotation_id not in self._annotations:
            return False
        
        del self._annotations[annotation_id]
        
        self._emit("canvas:remove_annotation", {
            "id": annotation_id,
        })
        
        return True
    
    def clear_annotations(self, flow_index: str = None) -> None:
        """
        Clear annotations.
        
        Args:
            flow_index: Specific node to clear, or None to clear all
        """
        if flow_index:
            # Clear annotations for specific node
            to_remove = [
                aid for aid, ann in self._annotations.items()
                if ann.flow_index == flow_index
            ]
            for aid in to_remove:
                del self._annotations[aid]
        else:
            # Clear all
            self._annotations.clear()
        
        self._emit("canvas:clear_annotations", {
            "flow_index": flow_index,
        })
        
        logger.debug(f"Canvas clear annotations: {flow_index or 'all'}")
    
    # =========================================================================
    # Navigation
    # =========================================================================
    
    def focus_node(self, flow_index: str, zoom: bool = True) -> None:
        """
        Focus and optionally zoom to a specific node.
        
        Args:
            flow_index: The node's flow index
            zoom: Whether to zoom to the node
        """
        self._emit("canvas:focus_node", {
            "flow_index": flow_index,
            "zoom": zoom,
        })
        
        logger.debug(f"Canvas focus node {flow_index}")
    
    def fit_view(self, padding: float = 0.1) -> None:
        """
        Fit all nodes in the view.
        
        Args:
            padding: Padding around the nodes (0.0 - 1.0)
        """
        self._emit("canvas:fit_view", {
            "padding": padding,
        })
    
    # =========================================================================
    # State Methods
    # =========================================================================
    
    def clear(self) -> None:
        """Clear all canvas displays (source viewer, structure, highlights, annotations)."""
        self._annotations.clear()
        
        self._emit("canvas:clear", {})
        
        logger.info("Canvas cleared")
    
    def get_selected_node(self) -> Optional[Dict]:
        """
        Get information about the currently selected node.
        
        Note: This is synchronous and returns cached state.
        For real-time state, the frontend should emit selection events.
        
        Returns:
            Node info dict or None if no selection
        """
        # This would typically be updated via WebSocket events from frontend
        return self._project_context.get("selected_node")
    
    def get_graph_state(self) -> Dict:
        """
        Get current graph state.
        
        Returns:
            Dict with nodes, edges, viewport info
        """
        # This would typically be updated via WebSocket events from frontend
        return self._project_context.get("graph_state", {})

