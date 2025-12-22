"""
Line-by-Line Editor for NormCode Files

Provides structured editing where each line is a separate component,
enabling per-line operations while maintaining a cohesive editor feel.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import uuid


class LineType(Enum):
    """Types of NormCode lines."""
    FUNCTIONAL_CONCEPT = "functional"  # <=
    VALUE_CONCEPT = "value"            # <-
    OUTPUT_CONCEPT = "output"          # :<:
    ANNOTATION_QUESTION = "question"   # ?:
    ANNOTATION_DESC = "description"    # /:
    ANNOTATION_SOURCE = "source"       # ...:
    GENERIC = "generic"                # Other content


@dataclass
class EditableLine:
    """
    Represents a single editable line in the NormCode editor.
    
    Each line is independently editable but displays as part of
    a cohesive document.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    depth: int = 0                     # Indentation level (0, 1, 2, ...)
    line_type: LineType = LineType.GENERIC
    operator: str = ""                 # The operator (<-, <=, ?:, etc.)
    content: str = ""                  # The editable content after operator
    flow_index: str = ""               # e.g., "1.2.3"
    sequence_type: str = ""            # e.g., "imperative"
    is_collapsed: bool = False         # For collapsible sections
    is_modified: bool = False          # Track unsaved changes
    parent_id: Optional[str] = None    # Parent line ID for tree structure
    display_format: str = "draft"      # Per-line format preference: 'draft', 'formal', 'natural'
    
    @property
    def full_content(self) -> str:
        """Get the full line content including operator (draft format)."""
        if self.operator:
            base = f"{self.operator} {self.content}"
        else:
            base = self.content
        
        # Add metadata if present
        metadata_parts = []
        if self.flow_index:
            metadata_parts.append(self.flow_index)
        if self.sequence_type:
            metadata_parts.append(self.sequence_type)
        
        if metadata_parts:
            base += f" | {' '.join(metadata_parts)}"
        
        return base
    
    @property
    def indented_content(self) -> str:
        """Get the full line with proper indentation (draft format)."""
        indent = "    " * self.depth
        return f"{indent}{self.full_content}"
    
    def as_draft(self) -> str:
        """Render line in draft (.ncd) format with indentation."""
        indent = "    " * self.depth
        if self.operator:
            line = f"{indent}{self.operator} {self.content}"
        else:
            line = f"{indent}{self.content}"
        
        # Add metadata if present (optional for draft)
        if self.flow_index and self.sequence_type:
            line += f" | {self.flow_index} {self.sequence_type}"
        elif self.flow_index:
            line += f" | {self.flow_index}"
        
        return line
    
    def as_formal(self) -> str:
        """Render line in formal (.nc) format: flow_index.type|content"""
        # Determine type string
        type_str = self.sequence_type if self.sequence_type else "object"
        
        # Build content with operator
        if self.operator:
            content = f"{self.operator} {self.content}"
        else:
            content = self.content
        
        # Format: flow_index.type|content
        if self.flow_index:
            return f"{self.flow_index}.{type_str}|{content}"
        else:
            return f"{type_str}|{content}"
    
    def as_natural(self) -> str:
        """Render line in natural language (.ncn) format."""
        indent = "    " * self.depth
        
        # Convert operator to natural language prefix
        if self.operator == '<=':
            prefix = "<= "
            # Could expand: "This is accomplished by: "
        elif self.operator == '<-':
            prefix = "<- "
            # Could expand: "Using: "
        elif self.operator == ':<:':
            prefix = ":<: "
            # Could expand: "The result is: "
        elif self.operator == '?:':
            prefix = "Question: "
        elif self.operator == '/:':
            prefix = "Description: "
        elif self.operator == '...:':
            prefix = "Source: "
        else:
            prefix = ""
        
        return f"{indent}{prefix}{self.content}"
    
    def copy(self) -> 'EditableLine':
        """Create a copy with a new ID."""
        return EditableLine(
            id=str(uuid.uuid4())[:8],
            depth=self.depth,
            line_type=self.line_type,
            operator=self.operator,
            content=self.content,
            flow_index=self.flow_index,
            sequence_type=self.sequence_type,
            is_collapsed=False,
            is_modified=True,
            parent_id=self.parent_id,
            display_format=self.display_format
        )


class LineManager:
    """
    Manages a collection of EditableLines for the structured editor.
    
    Provides operations for parsing text to lines, serializing back,
    and structural modifications.
    """
    
    OPERATOR_MAP = {
        '<=': LineType.FUNCTIONAL_CONCEPT,
        '<-': LineType.VALUE_CONCEPT,
        ':<:': LineType.OUTPUT_CONCEPT,
        '?:': LineType.ANNOTATION_QUESTION,
        '/:': LineType.ANNOTATION_DESC,
        '...:': LineType.ANNOTATION_SOURCE,
    }
    
    OPERATOR_DISPLAY = {
        LineType.FUNCTIONAL_CONCEPT: '<=',
        LineType.VALUE_CONCEPT: '<-',
        LineType.OUTPUT_CONCEPT: ':<:',
        LineType.ANNOTATION_QUESTION: '?:',
        LineType.ANNOTATION_DESC: '/:',
        LineType.ANNOTATION_SOURCE: '...:',
        LineType.GENERIC: '',
    }
    
    def __init__(self):
        self.lines: List[EditableLine] = []
    
    def migrate_lines(self):
        """
        Migrate existing lines to add new attributes.
        Call this after loading lines from session state for backwards compatibility.
        """
        for line in self.lines:
            if not hasattr(line, 'display_format'):
                object.__setattr__(line, 'display_format', 'draft')
    
    def parse_text(self, text: str) -> List[EditableLine]:
        """
        Parse raw text content into EditableLines.
        
        Args:
            text: Raw NormCode text content
            
        Returns:
            List of EditableLine objects
        """
        self.lines = []
        raw_lines = text.split('\n')
        
        for raw_line in raw_lines:
            if not raw_line.strip():
                # Preserve empty lines
                self.lines.append(EditableLine(
                    depth=0,
                    line_type=LineType.GENERIC,
                    content=""
                ))
                continue
            
            line = self._parse_line(raw_line)
            self.lines.append(line)
        
        # Build parent relationships
        self._build_hierarchy()
        
        return self.lines
    
    def parse_line_from_format(self, raw_line: str, format: str) -> Tuple[str, str, str]:
        """
        Parse a line from any format and return (operator, content, sequence_type).
        
        Args:
            raw_line: The line content to parse
            format: Format type ('draft', 'formal', 'natural')
            
        Returns:
            Tuple of (operator, content, sequence_type)
        """
        import re
        
        operator = ""
        content = raw_line
        sequence_type = ""
        
        if format == 'formal':
            # Parse formal format: flow_index.type|content
            if '|' in raw_line:
                prefix, content = raw_line.split('|', 1)
                content = content.strip()
                
                # Extract sequence type from prefix
                if '.' in prefix:
                    type_part = prefix.split('.')[-1]
                    if type_part and type_part != 'object':
                        sequence_type = type_part
                
                # Extract operator from content
                for op in self.OPERATOR_MAP.keys():
                    if content.startswith(op):
                        operator = op
                        content = content[len(op):].strip()
                        break
        
        elif format == 'natural':
            # Parse natural format - convert natural prefixes back
            content = raw_line.strip()
            
            if content.startswith('Question: '):
                operator = '?:'
                content = content[10:].strip()
            elif content.startswith('Description: '):
                operator = '/:'
                content = content[13:].strip()
            elif content.startswith('Source: '):
                operator = '...:'
                content = content[8:].strip()
            else:
                # Check for symbolic operators
                for op in self.OPERATOR_MAP.keys():
                    if content.startswith(op):
                        operator = op
                        content = content[len(op):].strip()
                        break
        
        else:  # draft format
            # Parse draft format: operator content | metadata
            content = raw_line.strip()
            
            # Extract operator
            for op in self.OPERATOR_MAP.keys():
                if content.startswith(op):
                    operator = op
                    content = content[len(op):].strip()
                    break
            
            # Extract metadata after |
            if '|' in content:
                parts = content.split('|', 1)
                content = parts[0].strip()
                metadata = parts[1].strip()
                
                # Extract sequence type from metadata
                sequence_types = ['imperative', 'grouping', 'assigning', 'quantifying', 
                                'timing', 'judgement', 'simple']
                for st in sequence_types:
                    if st in metadata.lower():
                        sequence_type = st
                        break
        
        return operator, content, sequence_type
    
    def _parse_line(self, raw_line: str) -> EditableLine:
        """Parse a single line of text."""
        # Calculate indentation
        stripped = raw_line.lstrip()
        leading_spaces = len(raw_line) - len(stripped)
        depth = leading_spaces // 4
        
        # Detect operator and line type
        operator = ""
        line_type = LineType.GENERIC
        content = stripped
        flow_index = ""
        sequence_type = ""
        
        # Check for operators
        for op, lt in self.OPERATOR_MAP.items():
            if stripped.startswith(op):
                operator = op
                line_type = lt
                content = stripped[len(op):].strip()
                break
        
        # Parse metadata from content (after |)
        if '|' in content and line_type not in [
            LineType.ANNOTATION_QUESTION,
            LineType.ANNOTATION_DESC,
            LineType.ANNOTATION_SOURCE
        ]:
            parts = content.split('|', 1)
            content = parts[0].strip()
            metadata = parts[1].strip()
            
            # Extract flow index (numbers with dots)
            import re
            flow_match = re.match(r'^([\d.]+)', metadata)
            if flow_match:
                flow_index = flow_match.group(1).strip('.')
                metadata = metadata[len(flow_match.group(1)):].strip()
            
            # Extract sequence type
            sequence_types = ['imperative', 'grouping', 'assigning', 'quantifying', 
                            'timing', 'judgement', 'simple']
            for st in sequence_types:
                if st in metadata.lower():
                    sequence_type = st
                    break
        
        return EditableLine(
            depth=depth,
            line_type=line_type,
            operator=operator,
            content=content,
            flow_index=flow_index,
            sequence_type=sequence_type
        )
    
    def _build_hierarchy(self):
        """Build parent-child relationships and auto-compute flow indices based on indentation."""
        parent_stack: List[EditableLine] = []
        # Track counters at each depth level
        depth_counters: Dict[int, int] = {}
        
        for line in self.lines:
            if not line.content and line.line_type == LineType.GENERIC:
                # Skip empty lines for hierarchy
                line.flow_index = ""
                continue
            
            # Pop parents until we find one with lower depth
            while parent_stack and parent_stack[-1].depth >= line.depth:
                parent_stack.pop()
            
            # Set parent
            if parent_stack:
                line.parent_id = parent_stack[-1].id
            else:
                line.parent_id = None
            
            # Reset counters for deeper levels when we go back up
            keys_to_remove = [k for k in depth_counters.keys() if k > line.depth]
            for k in keys_to_remove:
                del depth_counters[k]
            
            # Increment counter at this depth
            if line.depth not in depth_counters:
                depth_counters[line.depth] = 1
            else:
                depth_counters[line.depth] += 1
            
            # Build flow index from parent + current counter
            if parent_stack:
                parent_flow = parent_stack[-1].flow_index
                line.flow_index = f"{parent_flow}.{depth_counters[line.depth]}"
            else:
                line.flow_index = str(depth_counters[line.depth])
            
            # Push as potential parent
            parent_stack.append(line)
    
    def serialize(self, format: str = 'draft') -> str:
        """
        Serialize EditableLines to text in specified format.
        
        Args:
            format: One of 'draft', 'formal', or 'natural'
        
        Returns:
            NormCode text content in the specified format
        """
        result_lines = []
        
        for line in self.lines:
            if format == 'formal':
                result_lines.append(line.as_formal())
            elif format == 'natural':
                result_lines.append(line.as_natural())
            else:  # draft
                result_lines.append(line.as_draft())
        
        return '\n'.join(result_lines)
    
    def serialize_draft(self) -> str:
        """Serialize to .ncd format."""
        return self.serialize('draft')
    
    def serialize_formal(self) -> str:
        """Serialize to .nc format."""
        return self.serialize('formal')
    
    def serialize_natural(self) -> str:
        """Serialize to .ncn format."""
        return self.serialize('natural')
    
    def get_line_by_id(self, line_id: str) -> Optional[EditableLine]:
        """Get a line by its ID."""
        for line in self.lines:
            if line.id == line_id:
                return line
        return None
    
    def get_line_index(self, line_id: str) -> int:
        """Get the index of a line by ID."""
        for i, line in enumerate(self.lines):
            if line.id == line_id:
                return i
        return -1
    
    def insert_line(self, index: int, line: Optional[EditableLine] = None) -> EditableLine:
        """
        Insert a new line at the specified index.
        
        Args:
            index: Position to insert at
            line: Line to insert (creates new if None)
            
        Returns:
            The inserted line
        """
        if line is None:
            # Create a new line with same depth as previous
            prev_depth = 0
            if index > 0 and self.lines:
                prev_depth = self.lines[min(index - 1, len(self.lines) - 1)].depth
            
            line = EditableLine(
                depth=prev_depth,
                line_type=LineType.VALUE_CONCEPT,
                operator='<-',
                content='',
                is_modified=True
            )
        
        self.lines.insert(index, line)
        self._build_hierarchy()
        return line
    
    def delete_line(self, line_id: str) -> bool:
        """
        Delete a line by ID.
        
        Args:
            line_id: ID of line to delete
            
        Returns:
            True if deleted, False if not found
        """
        index = self.get_line_index(line_id)
        if index >= 0:
            self.lines.pop(index)
            self._build_hierarchy()
            return True
        return False
    
    def indent_line(self, line_id: str) -> bool:
        """
        Increase indentation of a line.
        
        Args:
            line_id: ID of line to indent
            
        Returns:
            True if indented, False if not possible
        """
        line = self.get_line_by_id(line_id)
        if line:
            line.depth += 1
            line.is_modified = True
            self._build_hierarchy()
            return True
        return False
    
    def outdent_line(self, line_id: str) -> bool:
        """
        Decrease indentation of a line.
        
        Args:
            line_id: ID of line to outdent
            
        Returns:
            True if outdented, False if not possible (already at root)
        """
        line = self.get_line_by_id(line_id)
        if line and line.depth > 0:
            line.depth -= 1
            line.is_modified = True
            self._build_hierarchy()
            return True
        return False
    
    def move_line_up(self, line_id: str) -> bool:
        """
        Move a line up in the list.
        
        Args:
            line_id: ID of line to move
            
        Returns:
            True if moved, False if already at top
        """
        index = self.get_line_index(line_id)
        if index > 0:
            self.lines[index], self.lines[index - 1] = self.lines[index - 1], self.lines[index]
            self.lines[index].is_modified = True
            self._build_hierarchy()
            return True
        return False
    
    def move_line_down(self, line_id: str) -> bool:
        """
        Move a line down in the list.
        
        Args:
            line_id: ID of line to move
            
        Returns:
            True if moved, False if already at bottom
        """
        index = self.get_line_index(line_id)
        if 0 <= index < len(self.lines) - 1:
            self.lines[index], self.lines[index + 1] = self.lines[index + 1], self.lines[index]
            self.lines[index].is_modified = True
            self._build_hierarchy()
            return True
        return False
    
    def update_line_content(self, line_id: str, content: str) -> bool:
        """
        Update the content of a line.
        
        Args:
            line_id: ID of line to update
            content: New content
            
        Returns:
            True if updated, False if not found
        """
        line = self.get_line_by_id(line_id)
        if line:
            line.content = content
            line.is_modified = True
            return True
        return False
    
    def update_line_operator(self, line_id: str, operator: str) -> bool:
        """
        Update the operator of a line.
        
        Args:
            line_id: ID of line to update
            operator: New operator
            
        Returns:
            True if updated, False if not found
        """
        line = self.get_line_by_id(line_id)
        if line:
            line.operator = operator
            # Update line type based on operator
            if operator in self.OPERATOR_MAP:
                line.line_type = self.OPERATOR_MAP[operator]
            else:
                line.line_type = LineType.GENERIC
            line.is_modified = True
            return True
        return False
    
    def update_line_metadata(self, line_id: str, flow_index: str = None, 
                            sequence_type: str = None) -> bool:
        """
        Update metadata of a line.
        
        Args:
            line_id: ID of line to update
            flow_index: New flow index (optional)
            sequence_type: New sequence type (optional)
            
        Returns:
            True if updated, False if not found
        """
        line = self.get_line_by_id(line_id)
        if line:
            if flow_index is not None:
                line.flow_index = flow_index
            if sequence_type is not None:
                line.sequence_type = sequence_type
            line.is_modified = True
            return True
        return False
    
    def update_line_display_format(self, line_id: str, display_format: str) -> bool:
        """
        Update the display format preference for a line.
        
        Args:
            line_id: ID of line to update
            display_format: New display format ('draft', 'formal', 'natural')
            
        Returns:
            True if updated, False if not found
        """
        line = self.get_line_by_id(line_id)
        if line and display_format in ['draft', 'formal', 'natural']:
            # Ensure attribute exists (backwards compatibility)
            if not hasattr(line, 'display_format'):
                object.__setattr__(line, 'display_format', 'draft')
            line.display_format = display_format
            return True
        return False
    
    def get_children(self, line_id: str) -> List[EditableLine]:
        """
        Get all direct children of a line.
        
        Args:
            line_id: ID of parent line
            
        Returns:
            List of child lines
        """
        return [line for line in self.lines if line.parent_id == line_id]
    
    def get_descendants(self, line_id: str) -> List[EditableLine]:
        """
        Get all descendants of a line (recursive).
        
        Args:
            line_id: ID of ancestor line
            
        Returns:
            List of descendant lines
        """
        descendants = []
        children = self.get_children(line_id)
        for child in children:
            descendants.append(child)
            descendants.extend(self.get_descendants(child.id))
        return descendants
    
    def toggle_collapse(self, line_id: str) -> bool:
        """
        Toggle collapsed state of a line.
        
        Args:
            line_id: ID of line to toggle
            
        Returns:
            New collapsed state
        """
        line = self.get_line_by_id(line_id)
        if line:
            line.is_collapsed = not line.is_collapsed
            return line.is_collapsed
        return False
    
    def duplicate_line(self, line_id: str, include_children: bool = False) -> Optional[EditableLine]:
        """
        Duplicate a line (optionally with children).
        
        Args:
            line_id: ID of line to duplicate
            include_children: Whether to include child lines
            
        Returns:
            The duplicated line (first one if multiple)
        """
        line = self.get_line_by_id(line_id)
        if not line:
            return None
        
        index = self.get_line_index(line_id)
        
        if include_children:
            # Get all descendants
            descendants = self.get_descendants(line_id)
            
            # Create copies
            new_line = line.copy()
            self.lines.insert(index + 1 + len(descendants), new_line)
            
            # Copy descendants with updated parent IDs
            old_to_new_id = {line_id: new_line.id}
            for desc in descendants:
                new_desc = desc.copy()
                if desc.parent_id in old_to_new_id:
                    new_desc.parent_id = old_to_new_id[desc.parent_id]
                old_to_new_id[desc.id] = new_desc.id
                self.lines.insert(self.get_line_index(new_line.id) + 1, new_desc)
        else:
            new_line = line.copy()
            self.lines.insert(index + 1, new_line)
        
        self._build_hierarchy()
        return new_line
    
    def add_annotation(self, line_id: str, annotation_type: str) -> Optional[EditableLine]:
        """
        Add an annotation below a line.
        
        Args:
            line_id: ID of line to annotate
            annotation_type: Type of annotation ('question', 'description', 'source')
            
        Returns:
            The created annotation line
        """
        line = self.get_line_by_id(line_id)
        if not line:
            return None
        
        operator_map = {
            'question': '?:',
            'description': '/:',
            'source': '...:',
        }
        
        operator = operator_map.get(annotation_type, '/:')
        annotation_line = EditableLine(
            depth=line.depth + 1,
            line_type=self.OPERATOR_MAP[operator],
            operator=operator,
            content='',
            parent_id=line.id,
            is_modified=True
        )
        
        # Insert after the line
        index = self.get_line_index(line_id)
        self.lines.insert(index + 1, annotation_line)
        self._build_hierarchy()
        
        return annotation_line
    
    def has_modifications(self) -> bool:
        """Check if any lines have been modified."""
        return any(line.is_modified for line in self.lines)
    
    def clear_modifications(self):
        """Clear all modification flags."""
        for line in self.lines:
            line.is_modified = False
    
    def get_visible_lines(self) -> List[EditableLine]:
        """
        Get list of visible lines (respecting collapsed state).
        
        Returns:
            List of visible lines
        """
        visible = []
        collapsed_parents = set()
        
        for line in self.lines:
            # Check if any ancestor is collapsed
            is_hidden = False
            if line.parent_id:
                current_parent = line.parent_id
                while current_parent:
                    if current_parent in collapsed_parents:
                        is_hidden = True
                        break
                    parent_line = self.get_line_by_id(current_parent)
                    if parent_line:
                        current_parent = parent_line.parent_id
                    else:
                        break
            
            if not is_hidden:
                visible.append(line)
            
            # Track collapsed lines
            if line.is_collapsed:
                collapsed_parents.add(line.id)
        
        return visible

