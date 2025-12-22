"""
Intermediate Representation (IR) for NormCode

Common data structure used by all parsers and converters.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class NormCodeNode:
    """
    Intermediate representation for a NormCode node.
    
    This structure is format-agnostic and can represent nodes from
    .ncd, .nc, or .ncn files.
    """
    
    flow_index: str = ""  # e.g., "1.2.3"
    depth: int = 0  # Indentation depth
    node_type: str = ""  # e.g., "inference", "concept"
    sequence_type: str = ""  # e.g., "imperative", "grouping", "assigning"
    content: str = ""  # The main content of the node
    
    # Annotations (from .ncd format)
    annotations: Dict[str, str] = field(default_factory=dict)
    # Possible keys: "question" (?:), "description" (/:), "source_text" (...:)
    
    # Child nodes
    children: List['NormCodeNode'] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    # Can store format-specific information
    
    def __repr__(self):
        """String representation for debugging."""
        return f"NormCodeNode(flow={self.flow_index}, type={self.node_type}, depth={self.depth}, content={self.content[:50]}...)"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "flow_index": self.flow_index,
            "depth": self.depth,
            "node_type": self.node_type,
            "sequence_type": self.sequence_type,
            "content": self.content,
            "annotations": self.annotations,
            "children": [child.to_dict() for child in self.children],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NormCodeNode':
        """Create from dictionary."""
        node = cls(
            flow_index=data.get("flow_index", ""),
            depth=data.get("depth", 0),
            node_type=data.get("node_type", ""),
            sequence_type=data.get("sequence_type", ""),
            content=data.get("content", ""),
            annotations=data.get("annotations", {}),
            metadata=data.get("metadata", {})
        )
        node.children = [cls.from_dict(child) for child in data.get("children", [])]
        return node

