"""
NormCode Natural (.ncn) Parser

Parses natural language .ncn files into IR and serializes back.
"""

import re
from typing import List, Optional
from .ir import NormCodeNode


class NCNParser:
    """Parser for .ncn (NormCode Natural) format."""
    
    INDENT_SIZE = 4  # Standard indentation is 4 spaces
    
    @classmethod
    def parse(cls, file_content: str) -> List[NormCodeNode]:
        """
        Parse .ncn file content into IR nodes.
        
        .ncn format is similar to .ncd but with natural language content
        and structure markers (<= for method, <- for component).
        
        Args:
            file_content: Content of .ncn file
            
        Returns:
            List of root-level NormCodeNode objects
        """
        lines = file_content.split('\n')
        return cls._parse_lines(lines)
    
    @classmethod
    def _parse_lines(cls, lines: List[str]) -> List[NormCodeNode]:
        """Parse lines into a tree structure."""
        if not lines:
            return []
        
        nodes = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                i += 1
                continue
            
            # Parse this line and its children
            node, consumed = cls._parse_node(lines, i)
            if node:
                nodes.append(node)
            i += consumed
        
        return nodes
    
    @classmethod
    def _parse_node(cls, lines: List[str], start_idx: int) -> tuple:
        """
        Parse a single node and its children.
        
        Returns:
            Tuple of (node, number of lines consumed)
        """
        line = lines[start_idx]
        
        # Calculate depth from indentation
        depth = cls._get_depth(line)
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            return None, 1
        
        # Parse the line content
        node = cls._parse_line_content(stripped, depth)
        
        # Parse children (lines with greater depth)
        i = start_idx + 1
        while i < len(lines):
            next_line = lines[i]
            if not next_line.strip():
                i += 1
                continue
            
            next_depth = cls._get_depth(next_line)
            
            # If next line is a child (deeper indentation)
            if next_depth > depth:
                child, consumed = cls._parse_node(lines, i)
                if child:
                    node.children.append(child)
                i += consumed
            else:
                # Next line is a sibling or parent, stop processing children
                break
        
        lines_consumed = i - start_idx
        return node, lines_consumed
    
    @classmethod
    def _get_depth(cls, line: str) -> int:
        """Calculate indentation depth."""
        leading_spaces = len(line) - len(line.lstrip())
        return leading_spaces // cls.INDENT_SIZE
    
    @classmethod
    def _parse_line_content(cls, line: str, depth: int) -> NormCodeNode:
        """
        Parse the content of a single line.
        
        .ncn uses <= and <- markers with natural language content.
        """
        node = NormCodeNode(depth=depth)
        
        # Determine node type from syntax
        if line.startswith('<='):
            node.node_type = 'functional_concept'
            node.content = line[2:].strip()
        elif line.startswith('<-'):
            node.node_type = 'value_concept'
            node.content = line[2:].strip()
        elif line.startswith(':<:'):
            node.node_type = 'output_concept'
            node.content = line
        else:
            # Natural language statement
            node.node_type = 'concept'
            node.content = line
        
        # Store as description annotation since .ncn is descriptive
        if node.content:
            node.annotations['description'] = node.content
        
        return node
    
    @classmethod
    def serialize(cls, nodes: List[NormCodeNode]) -> str:
        """
        Serialize IR nodes to .ncn format.
        
        Args:
            nodes: List of NormCodeNode objects
            
        Returns:
            .ncn format string
        """
        lines = []
        for node in nodes:
            cls._serialize_node(node, lines)
        return '\n'.join(lines)
    
    @classmethod
    def _serialize_node(cls, node: NormCodeNode, lines: List[str]) -> None:
        """Recursively serialize a node and its children."""
        indent = ' ' * (node.depth * cls.INDENT_SIZE)
        
        # Use description annotation if available, otherwise use content
        content = node.annotations.get('description', node.content)
        
        # Build the line based on node type
        if node.node_type == 'functional_concept':
            line = f"{indent}<= {content}"
        elif node.node_type == 'value_concept':
            line = f"{indent}<- {content}"
        elif node.node_type == 'output_concept':
            line = f"{indent}{content}"
        else:
            line = f"{indent}{content}"
        
        lines.append(line)
        
        # Serialize children
        for child in node.children:
            cls._serialize_node(child, lines)

