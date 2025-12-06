"""
NormCode Draft (.ncd) Parser

Parses indentation-based .ncd files into IR and serializes back.
"""

import re
from typing import List, Tuple, Optional
from .ir import NormCodeNode


class NCDParser:
    """Parser for .ncd (NormCode Draft) format."""
    
    INDENT_SIZE = 4  # Standard indentation is 4 spaces
    
    @classmethod
    def parse(cls, file_content: str) -> List[NormCodeNode]:
        """
        Parse .ncd file content into IR nodes.
        
        Args:
            file_content: Content of .ncd file
            
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
    def _parse_node(cls, lines: List[str], start_idx: int) -> Tuple[Optional[NormCodeNode], int]:
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
        
        Handles:
        - Concept definitions (<-, <=)
        - Flow indices (1.2.3)
        - Annotations (?:, /:, ...:)
        - Sequence types
        """
        node = NormCodeNode(depth=depth)
        
        # Check for annotations
        if line.startswith('?:'):
            # Question annotation
            node.annotations['question'] = line[2:].strip()
            node.node_type = 'annotation'
            node.content = line
            return node
        elif line.startswith('/:'):
            # Description annotation
            node.annotations['description'] = line[2:].strip()
            node.node_type = 'annotation'
            node.content = line
            return node
        elif line.startswith('...:'):
            # Source text annotation
            node.annotations['source_text'] = line[4:].strip()
            node.node_type = 'annotation'
            node.content = line
            return node
        
        # Parse main concept line with optional metadata
        # Format: concept_def | flow_index sequence_type // comment
        parts = line.split('|')
        concept_part = parts[0].strip()
        
        # Extract metadata if present
        if len(parts) > 1:
            metadata_part = parts[1].strip()
            
            # Extract flow index (numeric pattern like 1.2.3)
            flow_match = re.match(r'^([\d.]+)', metadata_part)
            if flow_match:
                node.flow_index = flow_match.group(1).strip()
                metadata_part = metadata_part[len(flow_match.group(1)):].strip()
            
            # Extract sequence type
            # Common types: imperative, grouping, assigning, quantifying, timing, judgement
            sequence_types = ['imperative', 'grouping', 'assigning', 'quantifying', 'timing', 'judgement', 'simple']
            for seq_type in sequence_types:
                if seq_type in metadata_part.lower():
                    node.sequence_type = seq_type
                    break
        
        # Determine node type from concept syntax
        if concept_part.startswith('<='):
            node.node_type = 'functional_concept'
            node.content = concept_part[2:].strip()
        elif concept_part.startswith('<-'):
            node.node_type = 'value_concept'
            node.content = concept_part[2:].strip()
        elif concept_part.startswith(':<:'):
            node.node_type = 'output_concept'
            node.content = concept_part
        else:
            # Generic concept
            node.node_type = 'concept'
            node.content = concept_part
        
        return node
    
    @classmethod
    def serialize(cls, nodes: List[NormCodeNode]) -> str:
        """
        Serialize IR nodes back to .ncd format.
        
        Args:
            nodes: List of NormCodeNode objects
            
        Returns:
            .ncd format string
        """
        lines = []
        for node in nodes:
            cls._serialize_node(node, lines)
        return '\n'.join(lines)
    
    @classmethod
    def _serialize_node(cls, node: NormCodeNode, lines: List[str]) -> None:
        """Recursively serialize a node and its children."""
        indent = ' ' * (node.depth * cls.INDENT_SIZE)
        
        # Handle annotations
        if node.node_type == 'annotation':
            lines.append(f"{indent}{node.content}")
        else:
            # Build the line
            if node.node_type == 'functional_concept':
                line = f"{indent}<= {node.content}"
            elif node.node_type == 'value_concept':
                line = f"{indent}<- {node.content}"
            elif node.node_type == 'output_concept':
                line = f"{indent}{node.content}"
            else:
                line = f"{indent}{node.content}"
            
            # Add metadata if present
            metadata_parts = []
            if node.flow_index:
                metadata_parts.append(node.flow_index)
            if node.sequence_type:
                metadata_parts.append(node.sequence_type)
            
            if metadata_parts:
                line += f" | {' '.join(metadata_parts)}"
            
            lines.append(line)
            
            # Add annotations as children
            for ann_type, ann_value in node.annotations.items():
                if ann_type == 'question':
                    lines.append(f"{indent}    ?: {ann_value}")
                elif ann_type == 'description':
                    lines.append(f"{indent}    /: {ann_value}")
                elif ann_type == 'source_text':
                    lines.append(f"{indent}    ...: {ann_value}")
        
        # Serialize children
        for child in node.children:
            cls._serialize_node(child, lines)

