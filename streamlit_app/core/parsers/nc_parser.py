"""
NormCode Formal (.nc) Parser

Parses line-based .nc files into IR and serializes back.
"""

import re
from typing import List, Optional
from .ir import NormCodeNode


class NCParser:
    """Parser for .nc (NormCode Formal) format."""
    
    @classmethod
    def parse(cls, file_content: str) -> List[NormCodeNode]:
        """
        Parse .nc file content into IR nodes.
        
        .nc format: flow_index.type|content
        Example: 1.2.3.imperative|<= ::(do something)
        
        Args:
            file_content: Content of .nc file
            
        Returns:
            List of NormCodeNode objects
        """
        lines = file_content.strip().split('\n')
        nodes = []
        
        for line in lines:
            if not line.strip():
                continue
            
            node = cls._parse_line(line)
            if node:
                nodes.append(node)
        
        # Build tree structure from flat list
        return cls._build_tree(nodes)
    
    @classmethod
    def _parse_line(cls, line: str) -> Optional[NormCodeNode]:
        """
        Parse a single .nc format line.
        
        Format: flow_index.type|content
        Example: 1.2.3.imperative|<= ::(do something)
        """
        # Split on first | to separate metadata from content
        if '|' not in line:
            return None
        
        metadata_part, content = line.split('|', 1)
        
        # Parse metadata: flow_index.type or flow_index.type_detail
        parts = metadata_part.split('.')
        
        if len(parts) < 2:
            return None
        
        # Flow index is all parts except the last (type)
        flow_index = '.'.join(parts[:-1])
        type_info = parts[-1]
        
        # Determine depth from flow index
        depth = len(flow_index.split('.')) - 1
        
        # Parse type info (may include additional details like _::{%(composition)})
        node_type, sequence_type = cls._parse_type_info(type_info)
        
        node = NormCodeNode(
            flow_index=flow_index,
            depth=depth,
            node_type=node_type,
            sequence_type=sequence_type,
            content=content.strip()
        )
        
        return node
    
    @classmethod
    def _parse_type_info(cls, type_info: str) -> tuple:
        """
        Parse type information from .nc format.
        
        Examples:
        - "imperative" -> ("inference", "imperative")
        - "object" -> ("concept", "")
        - "imperative_::{%(composition)}" -> ("inference", "imperative")
        """
        # Common sequence types
        sequence_types = ['imperative', 'grouping', 'assigning', 'quantifying', 'timing', 'judgement', 'simple']
        
        for seq_type in sequence_types:
            if type_info.startswith(seq_type):
                return "inference", seq_type
        
        # If it's not a sequence type, it's likely a concept type
        if type_info.startswith('object') or type_info.startswith('statement') or type_info.startswith('relation'):
            return "concept", ""
        
        if type_info == 'output':
            return "output_concept", ""
        
        return "concept", ""
    
    @classmethod
    def _build_tree(cls, nodes: List[NormCodeNode]) -> List[NormCodeNode]:
        """
        Build tree structure from flat list of nodes.
        
        Uses flow indices to determine parent-child relationships.
        """
        if not nodes:
            return []
        
        # Create a map of flow_index -> node
        node_map = {node.flow_index: node for node in nodes}
        
        # Find root nodes and build parent-child relationships
        roots = []
        
        for node in nodes:
            # Determine parent index
            parent_index = cls._get_parent_index(node.flow_index)
            
            if parent_index and parent_index in node_map:
                # Add as child to parent
                parent = node_map[parent_index]
                parent.children.append(node)
            else:
                # This is a root node
                roots.append(node)
        
        return roots
    
    @classmethod
    def _get_parent_index(cls, flow_index: str) -> Optional[str]:
        """
        Get parent flow index.
        
        Example: "1.2.3" -> "1.2"
        """
        parts = flow_index.split('.')
        if len(parts) <= 1:
            return None
        return '.'.join(parts[:-1])
    
    @classmethod
    def serialize(cls, nodes: List[NormCodeNode]) -> str:
        """
        Serialize IR nodes to .nc format.
        
        Args:
            nodes: List of NormCodeNode objects
            
        Returns:
            .nc format string
        """
        lines = []
        cls._serialize_nodes(nodes, lines)
        return '\n'.join(lines)
    
    @classmethod
    def _serialize_nodes(cls, nodes: List[NormCodeNode], lines: List[str]) -> None:
        """Recursively serialize nodes in depth-first order."""
        for node in nodes:
            # Build type info
            if node.sequence_type:
                type_info = node.sequence_type
            elif node.node_type == 'output_concept':
                type_info = 'output'
            elif node.node_type == 'concept' or node.node_type == 'value_concept':
                type_info = 'object'
            else:
                type_info = 'object'
            
            # Build line: flow_index.type|content
            line = f"{node.flow_index}.{type_info}|{node.content}"
            lines.append(line)
            
            # Serialize children
            cls._serialize_nodes(node.children, lines)

