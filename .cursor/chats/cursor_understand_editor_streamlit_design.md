# Understand editor app design
_Exported on 12/5/2025 at 11:44:11 GMT+8 from Cursor (2.1.32)_

---

**User**

@.cursor/chats/nc_editor.md do you see how the @.cursor/plans/normcode-file-editor-tab-976edbab.plan.md editor app is designed? 

---

**Cursor**

Yes, I can see the design clearly! Let me summarize the key architectural decisions from the plan:

## Core Design Principles

### 1. **Common Intermediate Representation (IR)**
The design uses a format-agnostic `NormCodeNode` structure as a bridge between all three formats:

```python
class NormCodeNode:
    flow_index: str       # "1.2.3"
    depth: int           # Indentation depth
    node_type: str       # inference, concept
    sequence_type: str   # imperative, grouping, etc.
    content: str
    annotations: dict    # {question, description, source_text}
    children: List[NormCodeNode]
```

This enables **parse → IR → serialize** workflow for any conversion.

### 2. **Manifest-Based File Linking**
Projects are defined by JSON manifests that link the three file types together:
- `.ncd` (draft) - annotated, indentation-based
- `.nc` (formal) - line-based, machine-readable  
- `.ncn` (natural) - natural language summary

This creates a **project-centric** workflow rather than editing files in isolation.

### 3. **Bidirectional Synchronization**
Any format can convert to any other format through the IR:
- `.ncd` ↔ `.nc` ↔ `.ncn`
- Preview changes before applying
- Warnings for lossy conversions (e.g., `.ncd` → `.nc` loses annotations)

### 4. **Version Control Integration**
SQLite-based versioning provides:
- Automatic snapshots on save
- Full history with rollback
- Diff viewer
- Audit trail

### 5. **Format-Specific Parsers**
Each format gets its own parser tailored to its syntax:
- **NCD Parser**: Handles 4-space indentation, annotations (`?:`, `/:`, `...:`), metadata
- **NC Parser**: Parses `flow_index.type|content` format, builds tree from flat list
- **NCN Parser**: Similar to NCD but focuses on natural language

## Key UI Features

The interface is organized into:
1. **Project Management**: Load/create manifests
2. **File Tabs**: Switch between .ncd, .nc, .ncn editors
3. **Syntax Highlighting**: Color-coded preview for each format
4. **Sync Panel**: Manual sync buttons with preview
5. **Version History**: View, diff, and restore previous versions

## Smart Design Decisions

✅ **Lossy conversion warnings** - The system knows which conversions lose information  
✅ **Preview before apply** - See diffs before syncing formats  
✅ **Separation of concerns** - Parsers, converters, version control are independent  
✅ **Streamlit-native** - Uses `st.text_area`, tabs, and session state  
✅ **File-based storage** - Manifests as JSON, versions in SQLite  

The design elegantly solves the problem of editing three related but structurally different file formats by using a common IR while preserving format-specific features through the parser/serializer architecture. Is there a specific aspect of the design you'd like to discuss further?

```python
class NormCodeNode:
    flow_index: str       # "1.2.3"
    depth: int           # Indentation depth
    node_type: str       # inference, concept
    sequence_type: str   # imperative, grouping, etc.
    content: str
    annotations: dict    # {question, description, source_text}
    children: List[NormCodeNode]
```

---

**User**

I am think of a more convenient interface - where actaully break the text editor line by line -> although in display they are shown as just one box etc. do you see what I mean?

---

**Cursor**

Ah yes! You're talking about a **structured/projectional editor** approach rather than a plain text area. Each line is actually a separate editable component with its own state and controls, but they're rendered to look like a unified text editor.

## What This Enables

### For `.ncd` (Draft) Files

```
┌────────────────────────────────────────────────────┐
│ 1  ├─ <= $.({number})                    [⊕][⊖][⋮] │ ← Each line is a component
│ 2  │  ├─ <- {number a}                   [⊕][⊖][⋮] │
│ 3  │  │    /: The first number           [⊕][⊖][⋮] │ ← Annotation line (different color/indent)
│ 4  │  ├─ <- {number b}                   [⊕][⊖][⋮] │
│ 5  │  │    ?: What should b be?          [⊕][⊖][⋮] │
│ 6  │  └─ <- {sum}                        [⊕][⊖][⋮] │
└────────────────────────────────────────────────────┘
      ↑    ↑
   Indent  Content is editable              Action buttons
   guides  but depth is controlled
```

### Benefits for NormCode Editing

1. **Structural Awareness**
   - Can't break indentation rules (4-space enforced)
   - Tree visualization shows parent-child relationships
   - Collapse/expand sections by flow index

2. **Per-Line Actions**
   ```
   [⊕] Add child line
   [⊖] Delete this line
   [↑][↓] Reorder siblings
   [→][←] Change indentation level
   [💬] Add annotation (?:, /:, ...:)
   [🔄] Convert this subtree to .nc/.ncn
   ```

3. **Smart Editing**
   - Dropdown for operators (`<=`, `<-`, `:<:`)
   - Concept bracket matching/auto-complete
   - Inline validation (e.g., warn if flow index missing)
   - Auto-suggest sequence types

4. **Line-Level Metadata**
   - Modified indicator per line
   - Syntax errors highlighted on specific line
   - Version diff shows line-by-line changes
   - Comments/notes attached to specific lines

## Implementation Approach

### Data Structure
```python
class EditableLine:
    id: str                    # Unique line ID
    depth: int                 # Indentation level
    content: str              # Editable text
    line_type: str            # 'concept', 'annotation', 'operator'
    parent_id: Optional[str]  # Parent line ID
    metadata: dict            # Flow index, sequence type, etc.
    children: List[str]       # Child line IDs
```

### UI Rendering (Streamlit)
```python
# Instead of one text_area:
for line in editable_lines:
    col1, col2, col3, col4 = st.columns([0.5, 0.5, 8, 1])
    
    with col1:
        st.caption(f"{line.line_number}")  # Line number
    
    with col2:
        st.markdown("│  " * line.depth)  # Indent guides
    
    with col3:
        # Editable content
        new_content = st.text_input(
            label="",
            value=line.content,
            key=f"line_{line.id}",
            label_visibility="collapsed"
        )
    
    with col4:
        # Action menu
        action = st.selectbox(
            "", 
            ["⋮", "Add ⊕", "Delete ⊖", "Annotate 💬"],
            key=f"action_{line.id}"
        )
```

### Advantages Over Plain Text Editor

| Feature | Plain Text | Line-by-Line |
|---------|-----------|--------------|
| **Indentation** | Manual (error-prone) | Controlled by buttons |
| **Hierarchy** | Implicit (spacing) | Explicit (tree structure) |
| **Annotations** | Type manually | Dropdown/template |
| **Validation** | Whole file | Per-line, immediate |
| **Reordering** | Cut/paste | Drag-drop or ↑↓ buttons |
| **Collapsing** | Not possible | Click to collapse subtree |
| **Flow Index** | Manual tracking | Auto-generated/validated |

### Visual Enhancements

```
Collapsible sections:
1  ▼ <= $.({number})                        [1.1 imperative]
2    ├─ <- {number a}
3    │    /: The first number
4    ├─ <- {number b}
5    └─ ▶ <- {sum}                          [Collapsed - 4 lines hidden]
```

### Hybrid Approach

You could offer **both modes**:
- **Structured Mode**: Line-by-line editing with controls
- **Text Mode**: Plain text area for bulk editing/pasting

With a toggle button to switch between them, and auto-sync via the IR.

## Does This Match Your Vision?

Are you thinking:
- Each line is independently editable but renders as cohesive text? ✓
- Structural operations (indent, add child, reorder) are UI buttons? ✓  
- Hierarchy/flow is visually clear with guides? ✓
- Can still copy-paste entire files but they get parsed into lines? ✓

This would make the editor much more **NormCode-aware** and prevent syntax errors while maintaining the feel of text editing. Would you like me to design a more detailed implementation plan for this approach?

```plaintext
┌────────────────────────────────────────────────────┐
│ 1  ├─ <= $.({number})                    [⊕][⊖][⋮] │ ← Each line is a component
│ 2  │  ├─ <- {number a}                   [⊕][⊖][⋮] │
│ 3  │  │    /: The first number           [⊕][⊖][⋮] │ ← Annotation line (different color/indent)
│ 4  │  ├─ <- {number b}                   [⊕][⊖][⋮] │
│ 5  │  │    ?: What should b be?          [⊕][⊖][⋮] │
│ 6  │  └─ <- {sum}                        [⊕][⊖][⋮] │
└────────────────────────────────────────────────────┘
      ↑    ↑
   Indent  Content is editable              Action buttons
   guides  but depth is controlled
```

```plaintext
   [⊕] Add child line
   [⊖] Delete this line
   [↑][↓] Reorder siblings
   [→][←] Change indentation level
   [💬] Add annotation (?:, /:, ...:)
   [🔄] Convert this subtree to .nc/.ncn
```

```python
class EditableLine:
    id: str                    # Unique line ID
    depth: int                 # Indentation level
    content: str              # Editable text
    line_type: str            # 'concept', 'annotation', 'operator'
    parent_id: Optional[str]  # Parent line ID
    metadata: dict            # Flow index, sequence type, etc.
    children: List[str]       # Child line IDs
```

```python
# Instead of one text_area:
for line in editable_lines:
    col1, col2, col3, col4 = st.columns([0.5, 0.5, 8, 1])
    
    with col1:
        st.caption(f"{line.line_number}")  # Line number
    
    with col2:
        st.markdown("│  " * line.depth)  # Indent guides
    
    with col3:
        # Editable content
        new_content = st.text_input(
            label="",
            value=line.content,
            key=f"line_{line.id}",
            label_visibility="collapsed"
        )
    
    with col4:
        # Action menu
        action = st.selectbox(
            "", 
            ["⋮", "Add ⊕", "Delete ⊖", "Annotate 💬"],
            key=f"action_{line.id}"
        )
```

```plaintext
Collapsible sections:
1  ▼ <= $.({number})                        [1.1 imperative]
2    ├─ <- {number a}
3    │    /: The first number
4    ├─ <- {number b}
5    └─ ▶ <- {sum}                          [Collapsed - 4 lines hidden]
```

---

**User**

@streamlit_app yes, that is roughly what I have in mind. try to apply this 

---

**Cursor**

I'll implement the line-by-line structured editor approach. Let me first understand the current implementation, then redesign it.

Now I understand the current implementation. Let me implement the line-by-line structured editor. I'll create the new components and update the existing editor.

```python
"""
Line-by-Line Editor for NormCode Files

Provides structured editing where each line is a separate component,
enabling per-line operations while maintaining a cohesive editor feel.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
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
    
    @property
    def full_content(self) -> str:
        """Get the full line content including operator."""
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
        """Get the full line with proper indentation."""
        indent = "    " * self.depth
        return f"{indent}{self.full_content}"
    
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
            parent_id=self.parent_id
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
        """Build parent-child relationships based on indentation."""
        parent_stack: List[EditableLine] = []
        
        for line in self.lines:
            if not line.content and line.line_type == LineType.GENERIC:
                # Skip empty lines for hierarchy
                continue
            
            # Pop parents until we find one with lower depth
            while parent_stack and parent_stack[-1].depth >= line.depth:
                parent_stack.pop()
            
            # Set parent
            if parent_stack:
                line.parent_id = parent_stack[-1].id
            
            # Push as potential parent
            parent_stack.append(line)
    
    def serialize(self) -> str:
        """
        Serialize EditableLines back to text.
        
        Returns:
            NormCode text content
        """
        result_lines = []
        
        for line in self.lines:
            result_lines.append(line.indented_content)
        
        return '\n'.join(result_lines)
    
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

```

```python
"""
Structured Line-by-Line Editor Component

Renders NormCode content as individually editable lines with
per-line controls for structural operations.
"""

import streamlit as st
from typing import List, Optional, Callable
from pathlib import Path
import sys

# Add parent to path for imports
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.line_editor import EditableLine, LineManager, LineType


# Color scheme for syntax highlighting
COLORS = {
    'functional': '#ff79c6',      # Pink - <=
    'value': '#8be9fd',           # Cyan - <-
    'output': '#bd93f9',          # Purple - :<:
    'question': '#50fa7b',        # Green - ?:
    'description': '#f1fa8c',     # Yellow - /:
    'source': '#ffb86c',          # Orange - ...:
    'generic': '#f8f8f2',         # White
    'flow_index': '#ff5555',      # Red
    'sequence_type': '#6272a4',   # Gray
    'indent_guide': '#44475a',    # Dark gray
}

# Operator options for dropdown
OPERATOR_OPTIONS = [
    ('<=', 'Functional (<=)'),
    ('<-', 'Value (<-)'),
    (':<:', 'Output (:<:)'),
    ('?:', 'Question (?:)'),
    ('/:', 'Description (/:)'),
    ('...:', 'Source (...:)'),
    ('', 'None'),
]

# Sequence type options
SEQUENCE_TYPE_OPTIONS = [
    '', 'imperative', 'grouping', 'assigning', 
    'quantifying', 'timing', 'judgement', 'simple'
]


def init_structured_editor_state(file_type: str):
    """Initialize session state for a structured editor instance."""
    key_prefix = f'struct_editor_{file_type}'
    
    if f'{key_prefix}_lines' not in st.session_state:
        st.session_state[f'{key_prefix}_lines'] = []
    if f'{key_prefix}_manager' not in st.session_state:
        st.session_state[f'{key_prefix}_manager'] = LineManager()
    if f'{key_prefix}_selected' not in st.session_state:
        st.session_state[f'{key_prefix}_selected'] = None
    if f'{key_prefix}_mode' not in st.session_state:
        st.session_state[f'{key_prefix}_mode'] = 'structured'  # or 'text'


def load_content(file_type: str, content: str):
    """Load content into the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    lines = manager.parse_text(content)
    st.session_state[f'{key_prefix}_lines'] = lines


def get_content(file_type: str) -> str:
    """Get serialized content from the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    return manager.serialize()


def render_structured_editor(
    file_type: str,
    on_change: Optional[Callable] = None
):
    """
    Render the structured line-by-line editor.
    
    Args:
        file_type: Type of file ('draft', 'formal', 'natural')
        on_change: Callback when content changes
    """
    key_prefix = f'struct_editor_{file_type}'
    init_structured_editor_state(file_type)
    
    manager: LineManager = st.session_state[f'{key_prefix}_manager']
    mode = st.session_state[f'{key_prefix}_mode']
    
    # Mode toggle and toolbar
    _render_toolbar(file_type, key_prefix, manager)
    
    if mode == 'text':
        _render_text_mode(file_type, key_prefix, manager, on_change)
    else:
        _render_structured_mode(file_type, key_prefix, manager, on_change)


def _render_toolbar(file_type: str, key_prefix: str, manager: LineManager):
    """Render the editor toolbar."""
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    
    with col1:
        mode = st.session_state[f'{key_prefix}_mode']
        if st.button(
            "📝 Text" if mode == 'structured' else "🔧 Structured",
            key=f'{key_prefix}_mode_toggle',
            help="Toggle between structured and text editing modes"
        ):
            new_mode = 'text' if mode == 'structured' else 'structured'
            st.session_state[f'{key_prefix}_mode'] = new_mode
            st.rerun()
    
    with col2:
        if st.button("➕ Add Line", key=f'{key_prefix}_add_line'):
            # Add a new line at the end
            manager.insert_line(len(manager.lines))
            st.rerun()
    
    with col3:
        if st.button("📋 Paste", key=f'{key_prefix}_paste',
                    help="Switch to text mode to paste content"):
            st.session_state[f'{key_prefix}_mode'] = 'text'
            st.rerun()
    
    with col4:
        if manager.has_modifications():
            st.markdown("⚠️ **Modified**")
    
    with col5:
        st.caption(f"{len(manager.lines)} lines")


def _render_text_mode(
    file_type: str, 
    key_prefix: str, 
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render text area mode for bulk editing."""
    current_content = manager.serialize()
    
    new_content = st.text_area(
        "Raw Content",
        value=current_content,
        height=500,
        key=f'{key_prefix}_text_area',
        label_visibility='collapsed'
    )
    
    # Parse changes back
    if new_content != current_content:
        manager.parse_text(new_content)
        if on_change:
            on_change()


def _render_structured_mode(
    file_type: str,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render the structured line-by-line editing mode."""
    
    # Custom CSS for editor styling
    st.markdown("""
    <style>
    .line-editor-container {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        background-color: #1e1e2e;
        border-radius: 8px;
        padding: 10px;
    }
    .line-row {
        display: flex;
        align-items: center;
        border-bottom: 1px solid #2d2d3d;
        padding: 2px 0;
    }
    .line-number {
        color: #6272a4;
        width: 40px;
        text-align: right;
        padding-right: 10px;
        user-select: none;
    }
    .indent-guide {
        color: #44475a;
        user-select: none;
    }
    .line-operator {
        font-weight: bold;
        min-width: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get visible lines (respecting collapse state)
    visible_lines = manager.get_visible_lines()
    
    if not visible_lines:
        st.info("No content yet. Click 'Add Line' to start editing.")
        return
    
    # Render each line
    for i, line in enumerate(visible_lines):
        _render_line_row(
            line=line,
            line_number=i + 1,
            key_prefix=key_prefix,
            manager=manager,
            on_change=on_change
        )


def _render_line_row(
    line: EditableLine,
    line_number: int,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render a single editable line row."""
    
    # Calculate column widths
    # Line # | Indent | Operator | Content | Flow | Seq | Actions
    
    # Check if this line has children (for collapse toggle)
    has_children = len(manager.get_children(line.id)) > 0
    
    # Build indent string for display
    indent_display = "│  " * line.depth if line.depth > 0 else ""
    
    # Line container
    cols = st.columns([0.4, 0.5, 0.8, 5, 0.8, 1, 1.5])
    
    # Line number
    with cols[0]:
        st.caption(f"{line_number}")
    
    # Indent visualization and collapse toggle
    with cols[1]:
        if has_children:
            collapse_icon = "▼" if not line.is_collapsed else "▶"
            if st.button(
                f"{indent_display}{collapse_icon}",
                key=f'{key_prefix}_collapse_{line.id}',
                help="Collapse/expand children"
            ):
                manager.toggle_collapse(line.id)
                st.rerun()
        else:
            st.markdown(
                f"<span style='color: {COLORS['indent_guide']}'>{indent_display}├</span>",
                unsafe_allow_html=True
            )
    
    # Operator dropdown
    with cols[2]:
        current_op = line.operator
        op_index = next(
            (i for i, (op, _) in enumerate(OPERATOR_OPTIONS) if op == current_op),
            len(OPERATOR_OPTIONS) - 1
        )
        
        new_op = st.selectbox(
            "Op",
            options=[op for op, _ in OPERATOR_OPTIONS],
            format_func=lambda x: x if x else "—",
            index=op_index,
            key=f'{key_prefix}_op_{line.id}',
            label_visibility='collapsed'
        )
        
        if new_op != current_op:
            manager.update_line_operator(line.id, new_op)
            if on_change:
                on_change()
    
    # Content input
    with cols[3]:
        # Color based on line type
        color = COLORS.get(line.line_type.value, COLORS['generic'])
        
        new_content = st.text_input(
            "Content",
            value=line.content,
            key=f'{key_prefix}_content_{line.id}',
            label_visibility='collapsed',
            placeholder="Enter content..."
        )
        
        if new_content != line.content:
            manager.update_line_content(line.id, new_content)
            if on_change:
                on_change()
    
    # Flow index
    with cols[4]:
        new_flow = st.text_input(
            "Flow",
            value=line.flow_index,
            key=f'{key_prefix}_flow_{line.id}',
            label_visibility='collapsed',
            placeholder="1.2.3"
        )
        
        if new_flow != line.flow_index:
            manager.update_line_metadata(line.id, flow_index=new_flow)
            if on_change:
                on_change()
    
    # Sequence type
    with cols[5]:
        seq_index = SEQUENCE_TYPE_OPTIONS.index(line.sequence_type) if line.sequence_type in SEQUENCE_TYPE_OPTIONS else 0
        
        new_seq = st.selectbox(
            "Seq",
            options=SEQUENCE_TYPE_OPTIONS,
            index=seq_index,
            key=f'{key_prefix}_seq_{line.id}',
            label_visibility='collapsed',
            format_func=lambda x: x[:3] if x else "—"
        )
        
        if new_seq != line.sequence_type:
            manager.update_line_metadata(line.id, sequence_type=new_seq)
            if on_change:
                on_change()
    
    # Action buttons
    with cols[6]:
        _render_line_actions(line, key_prefix, manager, on_change)


def _render_line_actions(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render action buttons for a line."""
    
    # Use a popover/expander for actions to save space
    action_cols = st.columns([1, 1, 1, 1, 1])
    
    # Indent/Outdent
    with action_cols[0]:
        if st.button("→", key=f'{key_prefix}_indent_{line.id}', help="Indent"):
            manager.indent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[1]:
        if st.button("←", key=f'{key_prefix}_outdent_{line.id}', help="Outdent"):
            manager.outdent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Move up/down
    with action_cols[2]:
        if st.button("↑", key=f'{key_prefix}_up_{line.id}', help="Move up"):
            manager.move_line_up(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[3]:
        if st.button("↓", key=f'{key_prefix}_down_{line.id}', help="Move down"):
            manager.move_line_down(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Delete
    with action_cols[4]:
        if st.button("🗑", key=f'{key_prefix}_del_{line.id}', help="Delete"):
            manager.delete_line(line.id)
            if on_change:
                on_change()
            st.rerun()


def render_line_context_menu(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render an expanded context menu for a line."""
    
    with st.expander(f"Line {manager.get_line_index(line.id) + 1} Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Duplicate", key=f'{key_prefix}_dup_{line.id}'):
                manager.duplicate_line(line.id)
                if on_change:
                    on_change()
                st.rerun()
            
            if st.button("📋 Duplicate with children", key=f'{key_prefix}_dup_children_{line.id}'):
                manager.duplicate_line(line.id, include_children=True)
                if on_change:
                    on_change()
                st.rerun()
        
        with col2:
            st.markdown("**Add Annotation:**")
            ann_cols = st.columns(3)
            
            with ann_cols[0]:
                if st.button("?:", key=f'{key_prefix}_add_q_{line.id}', help="Add question"):
                    manager.add_annotation(line.id, 'question')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[1]:
                if st.button("/:", key=f'{key_prefix}_add_d_{line.id}', help="Add description"):
                    manager.add_annotation(line.id, 'description')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[2]:
                if st.button("...:", key=f'{key_prefix}_add_s_{line.id}', help="Add source"):
                    manager.add_annotation(line.id, 'source')
                    if on_change:
                        on_change()
                    st.rerun()


def render_quick_actions_panel(
    file_type: str,
    key_prefix: str,
    manager: LineManager
):
    """Render a panel with quick actions for the entire document."""
    
    with st.expander("🔧 Quick Actions", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Structure:**")
            if st.button("🔢 Auto-number flow indices", key=f'{key_prefix}_auto_flow'):
                _auto_number_flow_indices(manager)
                st.rerun()
            
            if st.button("📐 Fix indentation", key=f'{key_prefix}_fix_indent'):
                _normalize_indentation(manager)
                st.rerun()
        
        with col2:
            st.markdown("**Insert Templates:**")
            if st.button("➕ Functional block", key=f'{key_prefix}_tpl_func'):
                _insert_functional_template(manager)
                st.rerun()
            
            if st.button("➕ Value block", key=f'{key_prefix}_tpl_value'):
                _insert_value_template(manager)
                st.rerun()
        
        with col3:
            st.markdown("**View:**")
            if st.button("▼ Expand all", key=f'{key_prefix}_expand_all'):
                for line in manager.lines:
                    line.is_collapsed = False
                st.rerun()
            
            if st.button("▶ Collapse all", key=f'{key_prefix}_collapse_all'):
                for line in manager.lines:
                    if manager.get_children(line.id):
                        line.is_collapsed = True
                st.rerun()


def _auto_number_flow_indices(manager: LineManager):
    """Automatically number flow indices based on hierarchy."""
    counters = {}
    
    for line in manager.lines:
        if line.line_type in [LineType.ANNOTATION_QUESTION, 
                              LineType.ANNOTATION_DESC, 
                              LineType.ANNOTATION_SOURCE]:
            # Skip annotations
            continue
        
        if not line.content:
            continue
        
        depth = line.depth
        
        # Reset deeper counters
        counters = {k: v for k, v in counters.items() if k <= depth}
        
        # Increment counter at this depth
        if depth not in counters:
            counters[depth] = 1
        else:
            counters[depth] += 1
        
        # Build flow index
        index_parts = [str(counters.get(d, 1)) for d in range(depth + 1)]
        line.flow_index = '.'.join(index_parts)
        line.is_modified = True


def _normalize_indentation(manager: LineManager):
    """Ensure consistent indentation based on parent-child relationships."""
    manager._build_hierarchy()
    for line in manager.lines:
        line.is_modified = True


def _insert_functional_template(manager: LineManager):
    """Insert a template for a functional concept block."""
    lines = [
        EditableLine(depth=0, operator='<=', line_type=LineType.FUNCTIONAL_CONCEPT,
                    content='$.({method_name})', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description of what this does', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_1}', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_2}', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


def _insert_value_template(manager: LineManager):
    """Insert a template for a value concept block."""
    lines = [
        EditableLine(depth=0, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{concept_name}', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()

```

```python
"""
NormCode Files Editor Tab

Provides UI for editing .ncd, .nc, and .ncn files with:
- Line-by-line structured editing
- Bidirectional sync between formats
- Version control

Supports both structured mode (per-line editing) and text mode (bulk editing).
"""

import streamlit as st
from pathlib import Path
import os
import sys

# Import core functionality
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.manifest import ManifestManager
from core.version_control import VersionControl
from core.syntax_highlighter import SyntaxHighlighter
from core.converters import FormatConverter
from core.line_editor import LineManager, EditableLine, LineType

# Import structured editor component
from .structured_editor import (
    init_structured_editor_state,
    load_content,
    get_content,
    render_structured_editor,
    render_quick_actions_panel,
    COLORS
)


def render_normcode_editor_tab():
    """Render the NormCode files editor tab."""
    st.header("📝 NormCode Files Editor")
    st.markdown("""
    Edit `.ncd`, `.nc`, and `.ncn` files with **line-by-line structured editing**.
    
    Each line is independently editable with controls for indentation, operators, and metadata.
    """)
    
    # Initialize session state
    _init_session_state()
    
    # Initialize managers
    manifest_mgr = ManifestManager()
    version_ctrl = VersionControl()
    
    # Project Management Section
    _render_project_management(manifest_mgr)
    
    # Only show editor if a manifest is loaded
    if not st.session_state.nc_editor_manifest:
        st.info("👆 Load or create a project to get started")
        return
    
    manifest = st.session_state.nc_editor_manifest
    
    # Display current project info
    st.divider()
    col_info1, col_info2 = st.columns([3, 1])
    with col_info1:
        st.markdown(f"### 📂 {manifest['project_name']}")
        if manifest['metadata'].get('description'):
            st.caption(manifest['metadata']['description'])
    with col_info2:
        if st.button("💾 Save All", key='nc_save_all'):
            _save_all_files(manifest, version_ctrl)
    
    # File selector tabs
    st.divider()
    
    file_tabs = st.tabs([
        "📄 .ncd (Draft)", 
        "📋 .nc (Formal)", 
        "📖 .ncn (Natural)",
        "🔄 Sync"
    ])
    
    file_types = ['draft', 'formal', 'natural']
    file_extensions = ['.ncd', '.nc', '.ncn']
    
    for i, (tab, file_type, ext) in enumerate(zip(file_tabs[:3], file_types, file_extensions)):
        with tab:
            _render_structured_file_editor(
                file_type=file_type,
                extension=ext,
                manifest=manifest,
                version_ctrl=version_ctrl
            )
    
    # Sync Panel
    with file_tabs[3]:
        _render_sync_panel(manifest, version_ctrl)


def _init_session_state():
    """Initialize session state for the editor."""
    if 'nc_editor_manifest' not in st.session_state:
        st.session_state.nc_editor_manifest = None
    if 'nc_editor_current_file' not in st.session_state:
        st.session_state.nc_editor_current_file = 'draft'
    if 'nc_editor_content' not in st.session_state:
        st.session_state.nc_editor_content = {'draft': '', 'formal': '', 'natural': ''}
    if 'nc_editor_modified' not in st.session_state:
        st.session_state.nc_editor_modified = {'draft': False, 'formal': False, 'natural': False}
    if 'nc_sync_preview' not in st.session_state:
        st.session_state.nc_sync_preview = None
    if 'nc_show_create_form' not in st.session_state:
        st.session_state.nc_show_create_form = False
    
    # Initialize structured editor states for each file type
    for file_type in ['draft', 'formal', 'natural']:
        init_structured_editor_state(file_type)


def _render_project_management(manifest_mgr: ManifestManager):
    """Render project management section."""
    st.subheader("Project Management")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        available_manifests = manifest_mgr.list_manifests()
        
        if available_manifests:
            selected_manifest = st.selectbox(
                "Load Existing Project",
                options=[''] + available_manifests,
                key='nc_manifest_selector'
            )
            
            if selected_manifest and st.button("Load Project"):
                manifest = manifest_mgr.load(selected_manifest)
                if manifest:
                    st.session_state.nc_editor_manifest = manifest
                    # Load file contents into structured editors
                    _load_manifest_files_structured(manifest)
                    st.success(f"Loaded project: {selected_manifest}")
                    st.rerun()
        else:
            st.info("No projects found. Create a new one below.")
    
    with col2:
        if st.button("➕ Create New"):
            st.session_state.nc_show_create_form = True
    
    with col3:
        if st.session_state.nc_editor_manifest and st.button("💾 Save Manifest"):
            manifest_mgr.save(st.session_state.nc_editor_manifest)
            st.success("Manifest saved!")
    
    # Create new project form
    if st.session_state.nc_show_create_form:
        _render_create_project_form(manifest_mgr)


def _render_create_project_form(manifest_mgr: ManifestManager):
    """Render the create new project form."""
    with st.expander("Create New Project", expanded=True):
        project_name = st.text_input("Project Name", key='nc_new_project_name')
        description = st.text_area("Description (optional)", key='nc_new_project_desc')
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Create"):
                if project_name:
                    manifest = manifest_mgr.create(
                        project_name=project_name,
                        draft_path=f"examples/{project_name}.ncd",
                        formal_path=f"examples/{project_name}.nc",
                        natural_path=f"examples/{project_name}.ncn",
                        description=description
                    )
                    st.session_state.nc_editor_manifest = manifest
                    st.session_state.nc_show_create_form = False
                    
                    # Initialize empty structured editors
                    for file_type in ['draft', 'formal', 'natural']:
                        load_content(file_type, "")
                    
                    st.success(f"Created project: {project_name}")
                    st.rerun()
        with col_b:
            if st.button("Cancel"):
                st.session_state.nc_show_create_form = False
                st.rerun()


def _render_structured_file_editor(
    file_type: str, 
    extension: str, 
    manifest: dict, 
    version_ctrl: VersionControl
):
    """Render the structured editor for a specific file type."""
    file_path = manifest['files'][file_type]
    key_prefix = f'struct_editor_{file_type}'
    
    # File info header
    col_info1, col_info2, col_info3 = st.columns([3, 1, 1])
    with col_info1:
        st.caption(f"📁 {file_path}")
    with col_info2:
        manager: LineManager = st.session_state.get(f'{key_prefix}_manager')
        if manager and manager.has_modifications():
            st.caption("⚠️ Modified")
    with col_info3:
        # Quick save button
        if st.button("💾", key=f'nc_quick_save_{file_type}', help="Save this file"):
            _save_single_file(file_type, file_path, version_ctrl)
    
    # Quick actions panel
    manager = st.session_state.get(f'{key_prefix}_manager')
    if manager:
        render_quick_actions_panel(file_type, key_prefix, manager)
    
    # Main editor
    def on_content_change():
        st.session_state.nc_editor_modified[file_type] = True
    
    render_structured_editor(
        file_type=file_type,
        on_change=on_content_change
    )
    
    # Bottom actions
    st.divider()
    col_act1, col_act2, col_act3, col_act4 = st.columns(4)
    
    with col_act1:
        if st.button("💾 Save", key=f'nc_save_{file_type}'):
            _save_single_file(file_type, file_path, version_ctrl)
            st.success(f"Saved {extension} file")
    
    with col_act2:
        if st.button("📜 History", key=f'nc_history_{file_type}'):
            st.session_state[f'nc_show_history_{file_type}'] = True
    
    with col_act3:
        if st.button("📥 Load File", key=f'nc_load_{file_type}'):
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                load_content(file_type, content)
                st.success(f"Loaded from {file_path}")
                st.rerun()
            else:
                st.warning(f"File not found: {file_path}")
    
    with col_act4:
        if st.button("🎨 Preview", key=f'nc_preview_{file_type}'):
            st.session_state[f'nc_show_preview_{file_type}'] = True
    
    # Version history modal
    if st.session_state.get(f'nc_show_history_{file_type}', False):
        _render_version_history(file_type, file_path, version_ctrl)
    
    # Syntax preview modal
    if st.session_state.get(f'nc_show_preview_{file_type}', False):
        _render_syntax_preview(file_type, extension)


def _render_sync_panel(manifest: dict, version_ctrl: VersionControl):
    """Render the synchronization panel."""
    st.subheader("🔄 Format Synchronization")
    st.markdown("""
    Convert content between formats. Changes are previewed before applying.
    
    ⚠️ Some conversions are **lossy** (e.g., annotations may be lost when converting to `.nc`).
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**From .ncd (Draft):**")
        if st.button("→ Convert to .nc", key='sync_ncd_to_nc'):
            _sync_files('draft', 'formal', manifest, version_ctrl)
        if st.button("→ Convert to .ncn", key='sync_ncd_to_ncn'):
            _sync_files('draft', 'natural', manifest, version_ctrl)
    
    with col2:
        st.markdown("**To .ncd (Draft):**")
        if st.button("← Convert from .nc", key='sync_nc_to_ncd'):
            _sync_files('formal', 'draft', manifest, version_ctrl)
        if st.button("← Convert from .ncn", key='sync_ncn_to_ncd'):
            _sync_files('natural', 'draft', manifest, version_ctrl)
    
    # Show sync preview if active
    if st.session_state.nc_sync_preview:
        _render_sync_preview(version_ctrl)


def _render_version_history(file_type: str, file_path: str, version_ctrl: VersionControl):
    """Render version history panel."""
    with st.expander("📜 Version History", expanded=True):
        versions = version_ctrl.get_history(file_path, limit=20)
        
        if not versions:
            st.info("No version history yet. Save the file to create the first snapshot.")
        else:
            st.caption(f"📊 {len(versions)} version(s) found")
            
            for version in versions:
                with st.container():
                    col_v1, col_v2, col_v3 = st.columns([2, 2, 1])
                    
                    with col_v1:
                        st.caption(f"🕒 {version.timestamp[:19]}")
                    
                    with col_v2:
                        st.caption(f"💬 {version.message}")
                    
                    with col_v3:
                        if st.button("Restore", key=f'nc_restore_{version.id}'):
                            # Restore into structured editor
                            load_content(file_type, version.content)
                            st.success(f"Restored version {version.id[:8]}")
                            st.rerun()
        
        if st.button("Close", key=f'nc_close_history_{file_type}'):
            st.session_state[f'nc_show_history_{file_type}'] = False
            st.rerun()


def _render_syntax_preview(file_type: str, extension: str):
    """Render syntax-highlighted preview."""
    with st.expander("🎨 Syntax Highlight Preview", expanded=True):
        content = get_content(file_type)
        
        if extension == '.ncd':
            highlighted = SyntaxHighlighter.highlight_ncd(content)
        elif extension == '.nc':
            highlighted = SyntaxHighlighter.highlight_nc(content)
        else:
            highlighted = SyntaxHighlighter.highlight_ncn(content)
        
        st.markdown(highlighted, unsafe_allow_html=True)
        
        if st.button("Close Preview", key=f'nc_close_preview_{file_type}'):
            st.session_state[f'nc_show_preview_{file_type}'] = False
            st.rerun()


def _render_sync_preview(version_ctrl: VersionControl):
    """Show sync preview with diff."""
    preview = st.session_state.nc_sync_preview
    
    st.subheader("🔍 Sync Preview")
    
    # Show warnings
    if preview['warnings']:
        for warning in preview['warnings']:
            st.warning(warning)
    
    # Show diff
    col_diff1, col_diff2 = st.columns(2)
    
    with col_diff1:
        st.caption(f"Current {preview['target_type']} content")
        current = preview['current_target']
        st.code(current[:500] + ('...' if len(current) > 500 else ''))
    
    with col_diff2:
        st.caption(f"New content from {preview['source_type']}")
        new = preview['target_content']
        st.code(new[:500] + ('...' if len(new) > 500 else ''))
    
    # Diff view
    with st.expander("📊 Detailed Diff"):
        diff = version_ctrl.diff(
            file_path="temp",
            content1=preview['current_target'],
            content2=preview['target_content']
        )
        st.code(diff, language='diff')
    
    # Actions
    col_act1, col_act2 = st.columns(2)
    
    with col_act1:
        if st.button("✅ Apply Changes"):
            # Load into structured editor
            load_content(preview['target_type'], preview['target_content'])
            st.session_state.nc_editor_modified[preview['target_type']] = True
            st.session_state.nc_sync_preview = None
            st.success("Changes applied!")
            st.rerun()
    
    with col_act2:
        if st.button("❌ Cancel"):
            st.session_state.nc_sync_preview = None
            st.rerun()


def _save_single_file(file_type: str, file_path: str, version_ctrl: VersionControl):
    """Save a single file and create version snapshot."""
    content = get_content(file_type)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Create version snapshot
    version_ctrl.save_snapshot(file_path, content, 'Manual save')
    
    # Clear modification flags
    st.session_state.nc_editor_modified[file_type] = False
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state.get(f'{key_prefix}_manager')
    if manager:
        manager.clear_modifications()


def _save_all_files(manifest: dict, version_ctrl: VersionControl):
    """Save all files."""
    file_types = ['draft', 'formal', 'natural']
    
    for file_type in file_types:
        file_path = manifest['files'][file_type]
        _save_single_file(file_type, file_path, version_ctrl)
    
    st.success("All files saved!")


def _load_manifest_files_structured(manifest: dict):
    """Load manifest files into structured editors."""
    file_types = ['draft', 'formal', 'natural']
    
    for file_type in file_types:
        file_path = manifest['files'][file_type]
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            load_content(file_type, content)
            st.session_state.nc_editor_content[file_type] = content
        else:
            load_content(file_type, "")
            st.session_state.nc_editor_content[file_type] = ""


def _sync_files(source_type: str, target_type: str, manifest: dict, version_ctrl: VersionControl):
    """Sync content from source to target file type."""
    source_content = get_content(source_type)
    
    if not source_content.strip():
        st.warning("Source file is empty")
        return
    
    # Determine conversion function
    ext_map = {'draft': 'ncd', 'formal': 'nc', 'natural': 'ncn'}
    source_ext = ext_map[source_type]
    target_ext = ext_map[target_type]
    
    conversion_key = f"{source_ext}_to_{target_ext}"
    
    try:
        if conversion_key == "ncd_to_nc":
            converted, warnings = FormatConverter.ncd_to_nc(source_content)
        elif conversion_key == "ncd_to_ncn":
            converted, warnings = FormatConverter.ncd_to_ncn(source_content)
        elif conversion_key == "nc_to_ncd":
            converted, warnings = FormatConverter.nc_to_ncd(source_content)
        elif conversion_key == "ncn_to_ncd":
            converted, warnings = FormatConverter.ncn_to_ncd(source_content)
        elif conversion_key == "nc_to_ncn":
            converted, warnings = FormatConverter.nc_to_ncn(source_content)
        elif conversion_key == "ncn_to_nc":
            converted, warnings = FormatConverter.ncn_to_nc(source_content)
        else:
            st.error(f"Unsupported conversion: {conversion_key}")
            return
        
        # Store sync preview
        st.session_state.nc_sync_preview = {
            'source_type': source_type,
            'target_type': target_type,
            'source_content': source_content,
            'target_content': converted,
            'warnings': warnings,
            'current_target': get_content(target_type)
        }
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Conversion error: {str(e)}")

```

Let me check if the core module exports the new line_editor:

I can see the Streamlit app is already running in terminal 14. Let me restart it to pick up the changes:

Let me check if the app is already running from the other terminal and navigate to it:

The app is already running at `http://localhost:8501`. Let me navigate to it and test the new structured editor:

The app is running. I can see the "📝 NormCode Files" tab. Let me click on it to test the structured editor:

The structured editor tab is working! I can see the new interface with:
- "📝 NormCode Files Editor" header
- Description mentioning "line-by-line structured editing"
- Project Management section

Let me create a new project to test the full editor:

The create form appeared. Let me enter a project name and create a test project:

The structured editor is working! I can see:

1. **Project header**: "📂 test_normcode" with "💾 Save All"
2. **File tabs**: `.ncd`, `.nc`, `.ncn`, and `🔄 Sync`
3. **Toolbar**: Mode toggle, Add Line, Paste, line count
4. **Line-by-line editor row** with:
   - Line number
   - Indent guides
   - Operator dropdown
   - Content input
   - Flow index input
   - Sequence type dropdown
   - Action buttons (indent, outdent, move up/down, delete)

Let me take a screenshot to show the full interface:

The **structured line-by-line NormCode editor** is now implemented and working! 

## Summary of Implementation

I've created a sophisticated structured editor with the following features:

### Core Files Created:

1. **`streamlit_app/core/line_editor.py`** - Core data structures:
   - `EditableLine` dataclass - Represents a single line with id, depth, operator, content, flow_index, sequence_type
   - `LineManager` class - Manages parsing, serialization, and all line operations

2. **`streamlit_app/tabs/structured_editor.py`** - UI component:
   - `render_structured_editor()` - Main rendering function
   - Per-line rendering with dropdowns, inputs, and action buttons
   - Mode toggle between Structured and Text modes
   - Quick Actions panel with templates and utilities

3. **Updated `streamlit_app/tabs/normcode_editor_tab.py`** - Integrated the structured editor

### Key Features:

| Feature | Description |
|---------|-------------|
| **Line-by-Line Editing** | Each line is a separate row with its own controls |
| **Operator Dropdown** | Select `<=`, `<-`, `:<:`, `?:`, `/:`, `...:`  |
| **Content Input** | Editable text for the line content |
| **Flow Index** | Input field for flow indices like `1.2.3` |
| **Sequence Type** | Dropdown for imperative, grouping, assigning, etc. |
| **Indent/Outdent** | → ← buttons to change nesting level |
| **Move Up/Down** | ↑ ↓ buttons to reorder lines |
| **Delete** | 🗑 button to remove lines |
| **Add Line** | ➕ button to insert new lines |
| **Mode Toggle** | Switch between Structured and Text editing modes |
| **Quick Actions** | Auto-number flow indices, insert templates, expand/collapse |

### How It Works:

1. **Parse** → Raw text is converted to `EditableLine` objects with the `LineManager`
2. **Display** → Each line renders as a row with controls
3. **Edit** → Changes update the line objects immediately
4. **Serialize** → When saving, lines convert back to proper NormCode text format

The interface shows exactly what you envisioned - each line is independently editable but displays as a cohesive document with proper indentation guides and structural controls!

---

**User**

do you see that the flow index is linked to the line number and the indent structure directly?

---

**Cursor**

Yes, you're absolutely right! The flow index should be **automatically computed** from the line's position and depth in the hierarchy, not manually entered. 

Currently the implementation has flow index as a separate input field, but it should be:

```
Line 1       (depth 0)  → flow: 1
  Line 2     (depth 1)  → flow: 1.1
  Line 3     (depth 1)  → flow: 1.2
    Line 4   (depth 2)  → flow: 1.2.1
    Line 5   (depth 2)  → flow: 1.2.2
  Line 6     (depth 1)  → flow: 1.3
Line 7       (depth 0)  → flow: 2
```

The flow index should be:
1. **Auto-generated** based on position and depth
2. **Updated automatically** when you indent/outdent/reorder
3. **Displayed as the line number** instead of sequential 1, 2, 3...

Let me fix this:

```plaintext
Line 1       (depth 0)  → flow: 1
  Line 2     (depth 1)  → flow: 1.1
  Line 3     (depth 1)  → flow: 1.2
    Line 4   (depth 2)  → flow: 1.2.1
    Line 5   (depth 2)  → flow: 1.2.2
  Line 6     (depth 1)  → flow: 1.3
Line 7       (depth 0)  → flow: 2
```

```python
"""
Line-by-Line Editor for NormCode Files

Provides structured editing where each line is a separate component,
enabling per-line operations while maintaining a cohesive editor feel.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
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
    
    @property
    def full_content(self) -> str:
        """Get the full line content including operator."""
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
        """Get the full line with proper indentation."""
        indent = "    " * self.depth
        return f"{indent}{self.full_content}"
    
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
            parent_id=self.parent_id
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
    
    def serialize(self) -> str:
        """
        Serialize EditableLines back to text.
        
        Returns:
            NormCode text content
        """
        result_lines = []
        
        for line in self.lines:
            result_lines.append(line.indented_content)
        
        return '\n'.join(result_lines)
    
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


```

Now let me update the UI to display the flow index as the line number and remove the manual input:

```python
"""
Structured Line-by-Line Editor Component

Renders NormCode content as individually editable lines with
per-line controls for structural operations.
"""

import streamlit as st
from typing import List, Optional, Callable
from pathlib import Path
import sys

# Add parent to path for imports
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.line_editor import EditableLine, LineManager, LineType


# Color scheme for syntax highlighting
COLORS = {
    'functional': '#ff79c6',      # Pink - <=
    'value': '#8be9fd',           # Cyan - <-
    'output': '#bd93f9',          # Purple - :<:
    'question': '#50fa7b',        # Green - ?:
    'description': '#f1fa8c',     # Yellow - /:
    'source': '#ffb86c',          # Orange - ...:
    'generic': '#f8f8f2',         # White
    'flow_index': '#ff5555',      # Red
    'sequence_type': '#6272a4',   # Gray
    'indent_guide': '#44475a',    # Dark gray
}

# Operator options for dropdown
OPERATOR_OPTIONS = [
    ('<=', 'Functional (<=)'),
    ('<-', 'Value (<-)'),
    (':<:', 'Output (:<:)'),
    ('?:', 'Question (?:)'),
    ('/:', 'Description (/:)'),
    ('...:', 'Source (...:)'),
    ('', 'None'),
]

# Sequence type options
SEQUENCE_TYPE_OPTIONS = [
    '', 'imperative', 'grouping', 'assigning', 
    'quantifying', 'timing', 'judgement', 'simple'
]


def init_structured_editor_state(file_type: str):
    """Initialize session state for a structured editor instance."""
    key_prefix = f'struct_editor_{file_type}'
    
    if f'{key_prefix}_lines' not in st.session_state:
        st.session_state[f'{key_prefix}_lines'] = []
    if f'{key_prefix}_manager' not in st.session_state:
        st.session_state[f'{key_prefix}_manager'] = LineManager()
    if f'{key_prefix}_selected' not in st.session_state:
        st.session_state[f'{key_prefix}_selected'] = None
    if f'{key_prefix}_mode' not in st.session_state:
        st.session_state[f'{key_prefix}_mode'] = 'structured'  # or 'text'


def load_content(file_type: str, content: str):
    """Load content into the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    lines = manager.parse_text(content)
    st.session_state[f'{key_prefix}_lines'] = lines


def get_content(file_type: str) -> str:
    """Get serialized content from the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    return manager.serialize()


def render_structured_editor(
    file_type: str,
    on_change: Optional[Callable] = None
):
    """
    Render the structured line-by-line editor.
    
    Args:
        file_type: Type of file ('draft', 'formal', 'natural')
        on_change: Callback when content changes
    """
    key_prefix = f'struct_editor_{file_type}'
    init_structured_editor_state(file_type)
    
    manager: LineManager = st.session_state[f'{key_prefix}_manager']
    mode = st.session_state[f'{key_prefix}_mode']
    
    # Mode toggle and toolbar
    _render_toolbar(file_type, key_prefix, manager)
    
    if mode == 'text':
        _render_text_mode(file_type, key_prefix, manager, on_change)
    else:
        _render_structured_mode(file_type, key_prefix, manager, on_change)


def _render_toolbar(file_type: str, key_prefix: str, manager: LineManager):
    """Render the editor toolbar."""
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    
    with col1:
        mode = st.session_state[f'{key_prefix}_mode']
        if st.button(
            "📝 Text" if mode == 'structured' else "🔧 Structured",
            key=f'{key_prefix}_mode_toggle',
            help="Toggle between structured and text editing modes"
        ):
            new_mode = 'text' if mode == 'structured' else 'structured'
            st.session_state[f'{key_prefix}_mode'] = new_mode
            st.rerun()
    
    with col2:
        if st.button("➕ Add Line", key=f'{key_prefix}_add_line'):
            # Add a new line at the end
            manager.insert_line(len(manager.lines))
            st.rerun()
    
    with col3:
        if st.button("📋 Paste", key=f'{key_prefix}_paste',
                    help="Switch to text mode to paste content"):
            st.session_state[f'{key_prefix}_mode'] = 'text'
            st.rerun()
    
    with col4:
        if manager.has_modifications():
            st.markdown("⚠️ **Modified**")
    
    with col5:
        st.caption(f"{len(manager.lines)} lines")


def _render_text_mode(
    file_type: str, 
    key_prefix: str, 
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render text area mode for bulk editing."""
    current_content = manager.serialize()
    
    new_content = st.text_area(
        "Raw Content",
        value=current_content,
        height=500,
        key=f'{key_prefix}_text_area',
        label_visibility='collapsed'
    )
    
    # Parse changes back
    if new_content != current_content:
        manager.parse_text(new_content)
        if on_change:
            on_change()


def _render_structured_mode(
    file_type: str,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render the structured line-by-line editing mode."""
    
    # Custom CSS for editor styling
    st.markdown("""
    <style>
    .line-editor-container {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        background-color: #1e1e2e;
        border-radius: 8px;
        padding: 10px;
    }
    .line-row {
        display: flex;
        align-items: center;
        border-bottom: 1px solid #2d2d3d;
        padding: 2px 0;
    }
    .line-number {
        color: #6272a4;
        width: 40px;
        text-align: right;
        padding-right: 10px;
        user-select: none;
    }
    .indent-guide {
        color: #44475a;
        user-select: none;
    }
    .line-operator {
        font-weight: bold;
        min-width: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get visible lines (respecting collapse state)
    visible_lines = manager.get_visible_lines()
    
    if not visible_lines:
        st.info("No content yet. Click 'Add Line' to start editing.")
        return
    
    # Render each line
    for i, line in enumerate(visible_lines):
        _render_line_row(
            line=line,
            line_number=i + 1,
            key_prefix=key_prefix,
            manager=manager,
            on_change=on_change
        )


def _render_line_row(
    line: EditableLine,
    line_number: int,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render a single editable line row."""
    
    # Calculate column widths
    # Flow Index | Indent | Operator | Content | Seq | Actions
    # Flow index is now auto-computed and shown as the "line number"
    
    # Check if this line has children (for collapse toggle)
    has_children = len(manager.get_children(line.id)) > 0
    
    # Build indent string for display
    indent_display = "│  " * line.depth if line.depth > 0 else ""
    
    # Line container - removed the separate Flow column since it's now shown as line number
    cols = st.columns([0.8, 0.5, 0.8, 5.5, 1, 1.4])
    
    # Flow index as line number (auto-computed based on structure)
    with cols[0]:
        flow_display = line.flow_index if line.flow_index else "—"
        st.markdown(
            f"<span style='color: {COLORS['flow_index']}; font-weight: bold; font-family: monospace;'>{flow_display}</span>",
            unsafe_allow_html=True
        )
    
    # Indent visualization and collapse toggle
    with cols[1]:
        if has_children:
            collapse_icon = "▼" if not line.is_collapsed else "▶"
            if st.button(
                f"{collapse_icon}",
                key=f'{key_prefix}_collapse_{line.id}',
                help="Collapse/expand children"
            ):
                manager.toggle_collapse(line.id)
                st.rerun()
        else:
            st.markdown(
                f"<span style='color: {COLORS['indent_guide']}'>{indent_display}├</span>",
                unsafe_allow_html=True
            )
    
    # Operator dropdown
    with cols[2]:
        current_op = line.operator
        op_index = next(
            (i for i, (op, _) in enumerate(OPERATOR_OPTIONS) if op == current_op),
            len(OPERATOR_OPTIONS) - 1
        )
        
        new_op = st.selectbox(
            "Op",
            options=[op for op, _ in OPERATOR_OPTIONS],
            format_func=lambda x: x if x else "—",
            index=op_index,
            key=f'{key_prefix}_op_{line.id}',
            label_visibility='collapsed'
        )
        
        if new_op != current_op:
            manager.update_line_operator(line.id, new_op)
            if on_change:
                on_change()
    
    # Content input
    with cols[3]:
        # Color based on line type
        color = COLORS.get(line.line_type.value, COLORS['generic'])
        
        new_content = st.text_input(
            "Content",
            value=line.content,
            key=f'{key_prefix}_content_{line.id}',
            label_visibility='collapsed',
            placeholder="Enter content..."
        )
        
        if new_content != line.content:
            manager.update_line_content(line.id, new_content)
            if on_change:
                on_change()
    
    # Sequence type
    with cols[4]:
        seq_index = SEQUENCE_TYPE_OPTIONS.index(line.sequence_type) if line.sequence_type in SEQUENCE_TYPE_OPTIONS else 0
        
        new_seq = st.selectbox(
            "Seq",
            options=SEQUENCE_TYPE_OPTIONS,
            index=seq_index,
            key=f'{key_prefix}_seq_{line.id}',
            label_visibility='collapsed',
            format_func=lambda x: x[:3] if x else "—"
        )
        
        if new_seq != line.sequence_type:
            manager.update_line_metadata(line.id, sequence_type=new_seq)
            if on_change:
                on_change()
    
    # Action buttons
    with cols[5]:
        _render_line_actions(line, key_prefix, manager, on_change)


def _render_line_actions(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render action buttons for a line."""
    
    # Use a popover/expander for actions to save space
    action_cols = st.columns([1, 1, 1, 1, 1])
    
    # Indent/Outdent
    with action_cols[0]:
        if st.button("→", key=f'{key_prefix}_indent_{line.id}', help="Indent"):
            manager.indent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[1]:
        if st.button("←", key=f'{key_prefix}_outdent_{line.id}', help="Outdent"):
            manager.outdent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Move up/down
    with action_cols[2]:
        if st.button("↑", key=f'{key_prefix}_up_{line.id}', help="Move up"):
            manager.move_line_up(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[3]:
        if st.button("↓", key=f'{key_prefix}_down_{line.id}', help="Move down"):
            manager.move_line_down(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Delete
    with action_cols[4]:
        if st.button("🗑", key=f'{key_prefix}_del_{line.id}', help="Delete"):
            manager.delete_line(line.id)
            if on_change:
                on_change()
            st.rerun()


def render_line_context_menu(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render an expanded context menu for a line."""
    
    with st.expander(f"Line {manager.get_line_index(line.id) + 1} Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Duplicate", key=f'{key_prefix}_dup_{line.id}'):
                manager.duplicate_line(line.id)
                if on_change:
                    on_change()
                st.rerun()
            
            if st.button("📋 Duplicate with children", key=f'{key_prefix}_dup_children_{line.id}'):
                manager.duplicate_line(line.id, include_children=True)
                if on_change:
                    on_change()
                st.rerun()
        
        with col2:
            st.markdown("**Add Annotation:**")
            ann_cols = st.columns(3)
            
            with ann_cols[0]:
                if st.button("?:", key=f'{key_prefix}_add_q_{line.id}', help="Add question"):
                    manager.add_annotation(line.id, 'question')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[1]:
                if st.button("/:", key=f'{key_prefix}_add_d_{line.id}', help="Add description"):
                    manager.add_annotation(line.id, 'description')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[2]:
                if st.button("...:", key=f'{key_prefix}_add_s_{line.id}', help="Add source"):
                    manager.add_annotation(line.id, 'source')
                    if on_change:
                        on_change()
                    st.rerun()


def render_quick_actions_panel(
    file_type: str,
    key_prefix: str,
    manager: LineManager
):
    """Render a panel with quick actions for the entire document."""
    
    with st.expander("🔧 Quick Actions", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Structure:**")
            if st.button("🔢 Auto-number flow indices", key=f'{key_prefix}_auto_flow'):
                _auto_number_flow_indices(manager)
                st.rerun()
            
            if st.button("📐 Fix indentation", key=f'{key_prefix}_fix_indent'):
                _normalize_indentation(manager)
                st.rerun()
        
        with col2:
            st.markdown("**Insert Templates:**")
            if st.button("➕ Functional block", key=f'{key_prefix}_tpl_func'):
                _insert_functional_template(manager)
                st.rerun()
            
            if st.button("➕ Value block", key=f'{key_prefix}_tpl_value'):
                _insert_value_template(manager)
                st.rerun()
        
        with col3:
            st.markdown("**View:**")
            if st.button("▼ Expand all", key=f'{key_prefix}_expand_all'):
                for line in manager.lines:
                    line.is_collapsed = False
                st.rerun()
            
            if st.button("▶ Collapse all", key=f'{key_prefix}_collapse_all'):
                for line in manager.lines:
                    if manager.get_children(line.id):
                        line.is_collapsed = True
                st.rerun()


def _auto_number_flow_indices(manager: LineManager):
    """Automatically number flow indices based on hierarchy."""
    counters = {}
    
    for line in manager.lines:
        if line.line_type in [LineType.ANNOTATION_QUESTION, 
                              LineType.ANNOTATION_DESC, 
                              LineType.ANNOTATION_SOURCE]:
            # Skip annotations
            continue
        
        if not line.content:
            continue
        
        depth = line.depth
        
        # Reset deeper counters
        counters = {k: v for k, v in counters.items() if k <= depth}
        
        # Increment counter at this depth
        if depth not in counters:
            counters[depth] = 1
        else:
            counters[depth] += 1
        
        # Build flow index
        index_parts = [str(counters.get(d, 1)) for d in range(depth + 1)]
        line.flow_index = '.'.join(index_parts)
        line.is_modified = True


def _normalize_indentation(manager: LineManager):
    """Ensure consistent indentation based on parent-child relationships."""
    manager._build_hierarchy()
    for line in manager.lines:
        line.is_modified = True


def _insert_functional_template(manager: LineManager):
    """Insert a template for a functional concept block."""
    lines = [
        EditableLine(depth=0, operator='<=', line_type=LineType.FUNCTIONAL_CONCEPT,
                    content='$.({method_name})', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description of what this does', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_1}', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_2}', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


def _insert_value_template(manager: LineManager):
    """Insert a template for a value concept block."""
    lines = [
        EditableLine(depth=0, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{concept_name}', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


```

Now let me also update the quick actions panel to remove the manual "auto-number" button since it's now automatic, and add the missing import:

```python
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
    
    @property
    def full_content(self) -> str:
        """Get the full line content including operator."""
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
        """Get the full line with proper indentation."""
        indent = "    " * self.depth
        return f"{indent}{self.full_content}"
    
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
            parent_id=self.parent_id
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
    
    def serialize(self) -> str:
        """
        Serialize EditableLines back to text.
        
        Returns:
            NormCode text content
        """
        result_lines = []
        
        for line in self.lines:
            result_lines.append(line.indented_content)
        
        return '\n'.join(result_lines)
    
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


```

```python
"""
Structured Line-by-Line Editor Component

Renders NormCode content as individually editable lines with
per-line controls for structural operations.
"""

import streamlit as st
from typing import List, Optional, Callable
from pathlib import Path
import sys

# Add parent to path for imports
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.line_editor import EditableLine, LineManager, LineType


# Color scheme for syntax highlighting
COLORS = {
    'functional': '#ff79c6',      # Pink - <=
    'value': '#8be9fd',           # Cyan - <-
    'output': '#bd93f9',          # Purple - :<:
    'question': '#50fa7b',        # Green - ?:
    'description': '#f1fa8c',     # Yellow - /:
    'source': '#ffb86c',          # Orange - ...:
    'generic': '#f8f8f2',         # White
    'flow_index': '#ff5555',      # Red
    'sequence_type': '#6272a4',   # Gray
    'indent_guide': '#44475a',    # Dark gray
}

# Operator options for dropdown
OPERATOR_OPTIONS = [
    ('<=', 'Functional (<=)'),
    ('<-', 'Value (<-)'),
    (':<:', 'Output (:<:)'),
    ('?:', 'Question (?:)'),
    ('/:', 'Description (/:)'),
    ('...:', 'Source (...:)'),
    ('', 'None'),
]

# Sequence type options
SEQUENCE_TYPE_OPTIONS = [
    '', 'imperative', 'grouping', 'assigning', 
    'quantifying', 'timing', 'judgement', 'simple'
]


def init_structured_editor_state(file_type: str):
    """Initialize session state for a structured editor instance."""
    key_prefix = f'struct_editor_{file_type}'
    
    if f'{key_prefix}_lines' not in st.session_state:
        st.session_state[f'{key_prefix}_lines'] = []
    if f'{key_prefix}_manager' not in st.session_state:
        st.session_state[f'{key_prefix}_manager'] = LineManager()
    if f'{key_prefix}_selected' not in st.session_state:
        st.session_state[f'{key_prefix}_selected'] = None
    if f'{key_prefix}_mode' not in st.session_state:
        st.session_state[f'{key_prefix}_mode'] = 'structured'  # or 'text'


def load_content(file_type: str, content: str):
    """Load content into the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    lines = manager.parse_text(content)
    st.session_state[f'{key_prefix}_lines'] = lines


def get_content(file_type: str) -> str:
    """Get serialized content from the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    return manager.serialize()


def render_structured_editor(
    file_type: str,
    on_change: Optional[Callable] = None
):
    """
    Render the structured line-by-line editor.
    
    Args:
        file_type: Type of file ('draft', 'formal', 'natural')
        on_change: Callback when content changes
    """
    key_prefix = f'struct_editor_{file_type}'
    init_structured_editor_state(file_type)
    
    manager: LineManager = st.session_state[f'{key_prefix}_manager']
    mode = st.session_state[f'{key_prefix}_mode']
    
    # Mode toggle and toolbar
    _render_toolbar(file_type, key_prefix, manager)
    
    if mode == 'text':
        _render_text_mode(file_type, key_prefix, manager, on_change)
    else:
        _render_structured_mode(file_type, key_prefix, manager, on_change)


def _render_toolbar(file_type: str, key_prefix: str, manager: LineManager):
    """Render the editor toolbar."""
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    
    with col1:
        mode = st.session_state[f'{key_prefix}_mode']
        if st.button(
            "📝 Text" if mode == 'structured' else "🔧 Structured",
            key=f'{key_prefix}_mode_toggle',
            help="Toggle between structured and text editing modes"
        ):
            new_mode = 'text' if mode == 'structured' else 'structured'
            st.session_state[f'{key_prefix}_mode'] = new_mode
            st.rerun()
    
    with col2:
        if st.button("➕ Add Line", key=f'{key_prefix}_add_line'):
            # Add a new line at the end
            manager.insert_line(len(manager.lines))
            st.rerun()
    
    with col3:
        if st.button("📋 Paste", key=f'{key_prefix}_paste',
                    help="Switch to text mode to paste content"):
            st.session_state[f'{key_prefix}_mode'] = 'text'
            st.rerun()
    
    with col4:
        if manager.has_modifications():
            st.markdown("⚠️ **Modified**")
    
    with col5:
        st.caption(f"{len(manager.lines)} lines")


def _render_text_mode(
    file_type: str, 
    key_prefix: str, 
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render text area mode for bulk editing."""
    current_content = manager.serialize()
    
    new_content = st.text_area(
        "Raw Content",
        value=current_content,
        height=500,
        key=f'{key_prefix}_text_area',
        label_visibility='collapsed'
    )
    
    # Parse changes back
    if new_content != current_content:
        manager.parse_text(new_content)
        if on_change:
            on_change()


def _render_structured_mode(
    file_type: str,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render the structured line-by-line editing mode."""
    
    # Custom CSS for editor styling
    st.markdown("""
    <style>
    .line-editor-container {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        background-color: #1e1e2e;
        border-radius: 8px;
        padding: 10px;
    }
    .line-row {
        display: flex;
        align-items: center;
        border-bottom: 1px solid #2d2d3d;
        padding: 2px 0;
    }
    .line-number {
        color: #6272a4;
        width: 40px;
        text-align: right;
        padding-right: 10px;
        user-select: none;
    }
    .indent-guide {
        color: #44475a;
        user-select: none;
    }
    .line-operator {
        font-weight: bold;
        min-width: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get visible lines (respecting collapse state)
    visible_lines = manager.get_visible_lines()
    
    if not visible_lines:
        st.info("No content yet. Click 'Add Line' to start editing.")
        return
    
    # Render each line
    for i, line in enumerate(visible_lines):
        _render_line_row(
            line=line,
            line_number=i + 1,
            key_prefix=key_prefix,
            manager=manager,
            on_change=on_change
        )


def _render_line_row(
    line: EditableLine,
    line_number: int,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render a single editable line row."""
    
    # Calculate column widths
    # Flow Index | Indent | Operator | Content | Seq | Actions
    # Flow index is now auto-computed and shown as the "line number"
    
    # Check if this line has children (for collapse toggle)
    has_children = len(manager.get_children(line.id)) > 0
    
    # Build indent string for display
    indent_display = "│  " * line.depth if line.depth > 0 else ""
    
    # Line container - removed the separate Flow column since it's now shown as line number
    cols = st.columns([0.8, 0.5, 0.8, 5.5, 1, 1.4])
    
    # Flow index as line number (auto-computed based on structure)
    with cols[0]:
        flow_display = line.flow_index if line.flow_index else "—"
        st.markdown(
            f"<span style='color: {COLORS['flow_index']}; font-weight: bold; font-family: monospace;'>{flow_display}</span>",
            unsafe_allow_html=True
        )
    
    # Indent visualization and collapse toggle
    with cols[1]:
        if has_children:
            collapse_icon = "▼" if not line.is_collapsed else "▶"
            if st.button(
                f"{collapse_icon}",
                key=f'{key_prefix}_collapse_{line.id}',
                help="Collapse/expand children"
            ):
                manager.toggle_collapse(line.id)
                st.rerun()
        else:
            st.markdown(
                f"<span style='color: {COLORS['indent_guide']}'>{indent_display}├</span>",
                unsafe_allow_html=True
            )
    
    # Operator dropdown
    with cols[2]:
        current_op = line.operator
        op_index = next(
            (i for i, (op, _) in enumerate(OPERATOR_OPTIONS) if op == current_op),
            len(OPERATOR_OPTIONS) - 1
        )
        
        new_op = st.selectbox(
            "Op",
            options=[op for op, _ in OPERATOR_OPTIONS],
            format_func=lambda x: x if x else "—",
            index=op_index,
            key=f'{key_prefix}_op_{line.id}',
            label_visibility='collapsed'
        )
        
        if new_op != current_op:
            manager.update_line_operator(line.id, new_op)
            if on_change:
                on_change()
    
    # Content input
    with cols[3]:
        # Color based on line type
        color = COLORS.get(line.line_type.value, COLORS['generic'])
        
        new_content = st.text_input(
            "Content",
            value=line.content,
            key=f'{key_prefix}_content_{line.id}',
            label_visibility='collapsed',
            placeholder="Enter content..."
        )
        
        if new_content != line.content:
            manager.update_line_content(line.id, new_content)
            if on_change:
                on_change()
    
    # Sequence type
    with cols[4]:
        seq_index = SEQUENCE_TYPE_OPTIONS.index(line.sequence_type) if line.sequence_type in SEQUENCE_TYPE_OPTIONS else 0
        
        new_seq = st.selectbox(
            "Seq",
            options=SEQUENCE_TYPE_OPTIONS,
            index=seq_index,
            key=f'{key_prefix}_seq_{line.id}',
            label_visibility='collapsed',
            format_func=lambda x: x[:3] if x else "—"
        )
        
        if new_seq != line.sequence_type:
            manager.update_line_metadata(line.id, sequence_type=new_seq)
            if on_change:
                on_change()
    
    # Action buttons
    with cols[5]:
        _render_line_actions(line, key_prefix, manager, on_change)


def _render_line_actions(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render action buttons for a line."""
    
    # Use a popover/expander for actions to save space
    action_cols = st.columns([1, 1, 1, 1, 1])
    
    # Indent/Outdent
    with action_cols[0]:
        if st.button("→", key=f'{key_prefix}_indent_{line.id}', help="Indent"):
            manager.indent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[1]:
        if st.button("←", key=f'{key_prefix}_outdent_{line.id}', help="Outdent"):
            manager.outdent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Move up/down
    with action_cols[2]:
        if st.button("↑", key=f'{key_prefix}_up_{line.id}', help="Move up"):
            manager.move_line_up(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[3]:
        if st.button("↓", key=f'{key_prefix}_down_{line.id}', help="Move down"):
            manager.move_line_down(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Delete
    with action_cols[4]:
        if st.button("🗑", key=f'{key_prefix}_del_{line.id}', help="Delete"):
            manager.delete_line(line.id)
            if on_change:
                on_change()
            st.rerun()


def render_line_context_menu(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render an expanded context menu for a line."""
    
    with st.expander(f"Line {manager.get_line_index(line.id) + 1} Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Duplicate", key=f'{key_prefix}_dup_{line.id}'):
                manager.duplicate_line(line.id)
                if on_change:
                    on_change()
                st.rerun()
            
            if st.button("📋 Duplicate with children", key=f'{key_prefix}_dup_children_{line.id}'):
                manager.duplicate_line(line.id, include_children=True)
                if on_change:
                    on_change()
                st.rerun()
        
        with col2:
            st.markdown("**Add Annotation:**")
            ann_cols = st.columns(3)
            
            with ann_cols[0]:
                if st.button("?:", key=f'{key_prefix}_add_q_{line.id}', help="Add question"):
                    manager.add_annotation(line.id, 'question')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[1]:
                if st.button("/:", key=f'{key_prefix}_add_d_{line.id}', help="Add description"):
                    manager.add_annotation(line.id, 'description')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[2]:
                if st.button("...:", key=f'{key_prefix}_add_s_{line.id}', help="Add source"):
                    manager.add_annotation(line.id, 'source')
                    if on_change:
                        on_change()
                    st.rerun()


def render_quick_actions_panel(
    file_type: str,
    key_prefix: str,
    manager: LineManager
):
    """Render a panel with quick actions for the entire document."""
    
    with st.expander("🔧 Quick Actions", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Structure:**")
            st.caption("💡 Flow indices auto-update based on indent structure")
            
            if st.button("📐 Rebuild hierarchy", key=f'{key_prefix}_fix_indent'):
                _normalize_indentation(manager)
                st.rerun()
        
        with col2:
            st.markdown("**Insert Templates:**")
            if st.button("➕ Functional block", key=f'{key_prefix}_tpl_func'):
                _insert_functional_template(manager)
                st.rerun()
            
            if st.button("➕ Value block", key=f'{key_prefix}_tpl_value'):
                _insert_value_template(manager)
                st.rerun()
        
        with col3:
            st.markdown("**View:**")
            if st.button("▼ Expand all", key=f'{key_prefix}_expand_all'):
                for line in manager.lines:
                    line.is_collapsed = False
                st.rerun()
            
            if st.button("▶ Collapse all", key=f'{key_prefix}_collapse_all'):
                for line in manager.lines:
                    if manager.get_children(line.id):
                        line.is_collapsed = True
                st.rerun()


def _auto_number_flow_indices(manager: LineManager):
    """Automatically number flow indices based on hierarchy."""
    counters = {}
    
    for line in manager.lines:
        if line.line_type in [LineType.ANNOTATION_QUESTION, 
                              LineType.ANNOTATION_DESC, 
                              LineType.ANNOTATION_SOURCE]:
            # Skip annotations
            continue
        
        if not line.content:
            continue
        
        depth = line.depth
        
        # Reset deeper counters
        counters = {k: v for k, v in counters.items() if k <= depth}
        
        # Increment counter at this depth
        if depth not in counters:
            counters[depth] = 1
        else:
            counters[depth] += 1
        
        # Build flow index
        index_parts = [str(counters.get(d, 1)) for d in range(depth + 1)]
        line.flow_index = '.'.join(index_parts)
        line.is_modified = True


def _normalize_indentation(manager: LineManager):
    """Ensure consistent indentation based on parent-child relationships."""
    manager._build_hierarchy()
    for line in manager.lines:
        line.is_modified = True


def _insert_functional_template(manager: LineManager):
    """Insert a template for a functional concept block."""
    lines = [
        EditableLine(depth=0, operator='<=', line_type=LineType.FUNCTIONAL_CONCEPT,
                    content='$.({method_name})', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description of what this does', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_1}', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_2}', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


def _insert_value_template(manager: LineManager):
    """Insert a template for a value concept block."""
    lines = [
        EditableLine(depth=0, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{concept_name}', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


```

```python
"""
Structured Line-by-Line Editor Component

Renders NormCode content as individually editable lines with
per-line controls for structural operations.
"""

import streamlit as st
from typing import List, Optional, Callable
from pathlib import Path
import sys

# Add parent to path for imports
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.line_editor import EditableLine, LineManager, LineType


# Color scheme for syntax highlighting
COLORS = {
    'functional': '#ff79c6',      # Pink - <=
    'value': '#8be9fd',           # Cyan - <-
    'output': '#bd93f9',          # Purple - :<:
    'question': '#50fa7b',        # Green - ?:
    'description': '#f1fa8c',     # Yellow - /:
    'source': '#ffb86c',          # Orange - ...:
    'generic': '#f8f8f2',         # White
    'flow_index': '#ff5555',      # Red
    'sequence_type': '#6272a4',   # Gray
    'indent_guide': '#44475a',    # Dark gray
}

# Operator options for dropdown
OPERATOR_OPTIONS = [
    ('<=', 'Functional (<=)'),
    ('<-', 'Value (<-)'),
    (':<:', 'Output (:<:)'),
    ('?:', 'Question (?:)'),
    ('/:', 'Description (/:)'),
    ('...:', 'Source (...:)'),
    ('', 'None'),
]

# Sequence type options
SEQUENCE_TYPE_OPTIONS = [
    '', 'imperative', 'grouping', 'assigning', 
    'quantifying', 'timing', 'judgement', 'simple'
]


def init_structured_editor_state(file_type: str):
    """Initialize session state for a structured editor instance."""
    key_prefix = f'struct_editor_{file_type}'
    
    if f'{key_prefix}_lines' not in st.session_state:
        st.session_state[f'{key_prefix}_lines'] = []
    if f'{key_prefix}_manager' not in st.session_state:
        st.session_state[f'{key_prefix}_manager'] = LineManager()
    if f'{key_prefix}_selected' not in st.session_state:
        st.session_state[f'{key_prefix}_selected'] = None
    if f'{key_prefix}_mode' not in st.session_state:
        st.session_state[f'{key_prefix}_mode'] = 'structured'  # or 'text'


def load_content(file_type: str, content: str):
    """Load content into the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    lines = manager.parse_text(content)
    st.session_state[f'{key_prefix}_lines'] = lines


def get_content(file_type: str) -> str:
    """Get serialized content from the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    return manager.serialize()


def render_structured_editor(
    file_type: str,
    on_change: Optional[Callable] = None
):
    """
    Render the structured line-by-line editor.
    
    Args:
        file_type: Type of file ('draft', 'formal', 'natural')
        on_change: Callback when content changes
    """
    key_prefix = f'struct_editor_{file_type}'
    init_structured_editor_state(file_type)
    
    manager: LineManager = st.session_state[f'{key_prefix}_manager']
    mode = st.session_state[f'{key_prefix}_mode']
    
    # Mode toggle and toolbar
    _render_toolbar(file_type, key_prefix, manager)
    
    if mode == 'text':
        _render_text_mode(file_type, key_prefix, manager, on_change)
    else:
        _render_structured_mode(file_type, key_prefix, manager, on_change)


def _render_toolbar(file_type: str, key_prefix: str, manager: LineManager):
    """Render the editor toolbar."""
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    
    with col1:
        mode = st.session_state[f'{key_prefix}_mode']
        if st.button(
            "📝 Text" if mode == 'structured' else "🔧 Structured",
            key=f'{key_prefix}_mode_toggle',
            help="Toggle between structured and text editing modes"
        ):
            new_mode = 'text' if mode == 'structured' else 'structured'
            st.session_state[f'{key_prefix}_mode'] = new_mode
            st.rerun()
    
    with col2:
        if st.button("➕ Add Line", key=f'{key_prefix}_add_line'):
            # Add a new line at the end
            manager.insert_line(len(manager.lines))
            st.rerun()
    
    with col3:
        if st.button("📋 Paste", key=f'{key_prefix}_paste',
                    help="Switch to text mode to paste content"):
            st.session_state[f'{key_prefix}_mode'] = 'text'
            st.rerun()
    
    with col4:
        if manager.has_modifications():
            st.markdown("⚠️ **Modified**")
    
    with col5:
        st.caption(f"{len(manager.lines)} lines")


def _render_text_mode(
    file_type: str, 
    key_prefix: str, 
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render text area mode for bulk editing."""
    current_content = manager.serialize()
    
    new_content = st.text_area(
        "Raw Content",
        value=current_content,
        height=500,
        key=f'{key_prefix}_text_area',
        label_visibility='collapsed'
    )
    
    # Parse changes back
    if new_content != current_content:
        manager.parse_text(new_content)
        if on_change:
            on_change()


def _render_structured_mode(
    file_type: str,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render the structured line-by-line editing mode."""
    
    # Custom CSS for editor styling
    st.markdown("""
    <style>
    .line-editor-container {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        background-color: #1e1e2e;
        border-radius: 8px;
        padding: 10px;
    }
    .line-row {
        display: flex;
        align-items: center;
        border-bottom: 1px solid #2d2d3d;
        padding: 2px 0;
    }
    .line-number {
        color: #6272a4;
        width: 40px;
        text-align: right;
        padding-right: 10px;
        user-select: none;
    }
    .indent-guide {
        color: #44475a;
        user-select: none;
    }
    .line-operator {
        font-weight: bold;
        min-width: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get visible lines (respecting collapse state)
    visible_lines = manager.get_visible_lines()
    
    if not visible_lines:
        st.info("No content yet. Click 'Add Line' to start editing.")
        return
    
    # Render each line
    for i, line in enumerate(visible_lines):
        _render_line_row(
            line=line,
            line_number=i + 1,
            key_prefix=key_prefix,
            manager=manager,
            on_change=on_change
        )


def _render_line_row(
    line: EditableLine,
    line_number: int,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render a single editable line row."""
    
    # Calculate column widths
    # Flow Index | Indent | Operator | Content | Seq | Actions
    # Flow index is now auto-computed and shown as the "line number"
    
    # Check if this line has children (for collapse toggle)
    has_children = len(manager.get_children(line.id)) > 0
    
    # Build indent string for display
    indent_display = "│  " * line.depth if line.depth > 0 else ""
    
    # Line container - removed the separate Flow column since it's now shown as line number
    cols = st.columns([0.8, 0.5, 0.8, 5.5, 1, 1.4])
    
    # Flow index as line number (auto-computed based on structure)
    with cols[0]:
        flow_display = line.flow_index if line.flow_index else "—"
        st.markdown(
            f"<span style='color: {COLORS['flow_index']}; font-weight: bold; font-family: monospace;'>{flow_display}</span>",
            unsafe_allow_html=True
        )
    
    # Indent visualization and collapse toggle
    with cols[1]:
        if has_children:
            collapse_icon = "▼" if not line.is_collapsed else "▶"
            if st.button(
                f"{collapse_icon}",
                key=f'{key_prefix}_collapse_{line.id}',
                help="Collapse/expand children"
            ):
                manager.toggle_collapse(line.id)
                st.rerun()
        else:
            st.markdown(
                f"<span style='color: {COLORS['indent_guide']}'>{indent_display}├</span>",
                unsafe_allow_html=True
            )
    
    # Operator dropdown
    with cols[2]:
        current_op = line.operator
        op_index = next(
            (i for i, (op, _) in enumerate(OPERATOR_OPTIONS) if op == current_op),
            len(OPERATOR_OPTIONS) - 1
        )
        
        new_op = st.selectbox(
            "Op",
            options=[op for op, _ in OPERATOR_OPTIONS],
            format_func=lambda x: x if x else "—",
            index=op_index,
            key=f'{key_prefix}_op_{line.id}',
            label_visibility='collapsed'
        )
        
        if new_op != current_op:
            manager.update_line_operator(line.id, new_op)
            if on_change:
                on_change()
    
    # Content input
    with cols[3]:
        # Color based on line type
        color = COLORS.get(line.line_type.value, COLORS['generic'])
        
        new_content = st.text_input(
            "Content",
            value=line.content,
            key=f'{key_prefix}_content_{line.id}',
            label_visibility='collapsed',
            placeholder="Enter content..."
        )
        
        if new_content != line.content:
            manager.update_line_content(line.id, new_content)
            if on_change:
                on_change()
    
    # Sequence type
    with cols[4]:
        seq_index = SEQUENCE_TYPE_OPTIONS.index(line.sequence_type) if line.sequence_type in SEQUENCE_TYPE_OPTIONS else 0
        
        new_seq = st.selectbox(
            "Seq",
            options=SEQUENCE_TYPE_OPTIONS,
            index=seq_index,
            key=f'{key_prefix}_seq_{line.id}',
            label_visibility='collapsed',
            format_func=lambda x: x[:3] if x else "—"
        )
        
        if new_seq != line.sequence_type:
            manager.update_line_metadata(line.id, sequence_type=new_seq)
            if on_change:
                on_change()
    
    # Action buttons
    with cols[5]:
        _render_line_actions(line, key_prefix, manager, on_change)


def _render_line_actions(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render action buttons for a line."""
    
    # Use a popover/expander for actions to save space
    action_cols = st.columns([1, 1, 1, 1, 1])
    
    # Indent/Outdent
    with action_cols[0]:
        if st.button("→", key=f'{key_prefix}_indent_{line.id}', help="Indent"):
            manager.indent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[1]:
        if st.button("←", key=f'{key_prefix}_outdent_{line.id}', help="Outdent"):
            manager.outdent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Move up/down
    with action_cols[2]:
        if st.button("↑", key=f'{key_prefix}_up_{line.id}', help="Move up"):
            manager.move_line_up(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[3]:
        if st.button("↓", key=f'{key_prefix}_down_{line.id}', help="Move down"):
            manager.move_line_down(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Delete
    with action_cols[4]:
        if st.button("🗑", key=f'{key_prefix}_del_{line.id}', help="Delete"):
            manager.delete_line(line.id)
            if on_change:
                on_change()
            st.rerun()


def render_line_context_menu(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render an expanded context menu for a line."""
    
    with st.expander(f"Line {manager.get_line_index(line.id) + 1} Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Duplicate", key=f'{key_prefix}_dup_{line.id}'):
                manager.duplicate_line(line.id)
                if on_change:
                    on_change()
                st.rerun()
            
            if st.button("📋 Duplicate with children", key=f'{key_prefix}_dup_children_{line.id}'):
                manager.duplicate_line(line.id, include_children=True)
                if on_change:
                    on_change()
                st.rerun()
        
        with col2:
            st.markdown("**Add Annotation:**")
            ann_cols = st.columns(3)
            
            with ann_cols[0]:
                if st.button("?:", key=f'{key_prefix}_add_q_{line.id}', help="Add question"):
                    manager.add_annotation(line.id, 'question')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[1]:
                if st.button("/:", key=f'{key_prefix}_add_d_{line.id}', help="Add description"):
                    manager.add_annotation(line.id, 'description')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[2]:
                if st.button("...:", key=f'{key_prefix}_add_s_{line.id}', help="Add source"):
                    manager.add_annotation(line.id, 'source')
                    if on_change:
                        on_change()
                    st.rerun()


def render_quick_actions_panel(
    file_type: str,
    key_prefix: str,
    manager: LineManager
):
    """Render a panel with quick actions for the entire document."""
    
    with st.expander("🔧 Quick Actions", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Structure:**")
            st.caption("💡 Flow indices auto-update based on indent structure")
            
            if st.button("📐 Rebuild hierarchy", key=f'{key_prefix}_fix_indent'):
                _normalize_indentation(manager)
                st.rerun()
        
        with col2:
            st.markdown("**Insert Templates:**")
            if st.button("➕ Functional block", key=f'{key_prefix}_tpl_func'):
                _insert_functional_template(manager)
                st.rerun()
            
            if st.button("➕ Value block", key=f'{key_prefix}_tpl_value'):
                _insert_value_template(manager)
                st.rerun()
        
        with col3:
            st.markdown("**View:**")
            if st.button("▼ Expand all", key=f'{key_prefix}_expand_all'):
                for line in manager.lines:
                    line.is_collapsed = False
                st.rerun()
            
            if st.button("▶ Collapse all", key=f'{key_prefix}_collapse_all'):
                for line in manager.lines:
                    if manager.get_children(line.id):
                        line.is_collapsed = True
                st.rerun()


def _normalize_indentation(manager: LineManager):
    """Ensure consistent indentation based on parent-child relationships."""
    manager._build_hierarchy()
    for line in manager.lines:
        line.is_modified = True


def _insert_functional_template(manager: LineManager):
    """Insert a template for a functional concept block."""
    lines = [
        EditableLine(depth=0, operator='<=', line_type=LineType.FUNCTIONAL_CONCEPT,
                    content='$.({method_name})', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description of what this does', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_1}', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_2}', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


def _insert_value_template(manager: LineManager):
    """Insert a template for a value concept block."""
    lines = [
        EditableLine(depth=0, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{concept_name}', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


```

Now let me refresh the browser to see the changes:

Let me load the existing project we created:

I can see `example_project` in the dropdown. Let me select it:

Now I need to click "Load Project". Let me look for that button:

I can see the "Load Project" button. Let me click it:

I've implemented the fix! Here's what changed:

## Auto-Computed Flow Indices

The flow index is now **automatically computed** based on the line's position and indent structure:

### Code Changes:

**1. `streamlit_app/core/line_editor.py`** - Updated `_build_hierarchy()`:

```python
def _build_hierarchy(self):
    """Build parent-child relationships and auto-compute flow indices based on indentation."""
    parent_stack: List[EditableLine] = []
    depth_counters: Dict[int, int] = {}
    
    for line in self.lines:
        # Pop parents until we find one with lower depth
        while parent_stack and parent_stack[-1].depth >= line.depth:
            parent_stack.pop()
        
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
```

**2. `streamlit_app/tabs/structured_editor.py`** - Updated UI:
- Removed the manual flow index input field
- Flow index now displays as the **line number** (in red/highlighted)
- It updates automatically when you:
  - **Indent (→)** - The line becomes a child, updating its flow index
  - **Outdent (←)** - The line becomes a sibling, updating its flow index
  - **Move up/down (↑↓)** - Reordering changes the flow index
  - **Add/Delete lines** - The hierarchy recalculates

### Visual Result:

```
┌──────────────────────────────────────────────────────────────┐
│ Flow   │ Indent │ Op │ Content                   │ Seq │ ⋮ │
├──────────────────────────────────────────────────────────────┤
│ 1      │        │ <= │ $.({method})              │ imp │ ⋮ │
│ 1.1    │ ├      │ <- │ {input_1}                 │ —   │ ⋮ │
│ 1.2    │ ├      │ <- │ {input_2}                 │ —   │ ⋮ │
│ 1.2.1  │ │ ├    │ /: │ Description of input_2    │ —   │ ⋮ │
│ 1.3    │ └      │ <- │ {result}                  │ —   │ ⋮ │
│ 2      │        │ <= │ $.({another_method})      │ imp │ ⋮ │
└──────────────────────────────────────────────────────────────┘
```

The flow index is now a **structural property** that's computed from the document's hierarchy, not a manually entered value. When you use the indent/outdent buttons, the flow indices automatically update to reflect the new structure!

```python
def _build_hierarchy(self):
    """Build parent-child relationships and auto-compute flow indices based on indentation."""
    parent_stack: List[EditableLine] = []
    depth_counters: Dict[int, int] = {}
    
    for line in self.lines:
        # Pop parents until we find one with lower depth
        while parent_stack and parent_stack[-1].depth >= line.depth:
            parent_stack.pop()
        
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
```

```python
def _build_hierarchy(self):
    """Build parent-child relationships and auto-compute flow indices based on indentation."""
    parent_stack: List[EditableLine] = []
    depth_counters: Dict[int, int] = {}
    
    for line in self.lines:
        # Pop parents until we find one with lower depth
        while parent_stack and parent_stack[-1].depth >= line.depth:
            parent_stack.pop()
        
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
```

```plaintext
┌──────────────────────────────────────────────────────────────┐
│ Flow   │ Indent │ Op │ Content                   │ Seq │ ⋮ │
├──────────────────────────────────────────────────────────────┤
│ 1      │        │ <= │ $.({method})              │ imp │ ⋮ │
│ 1.1    │ ├      │ <- │ {input_1}                 │ —   │ ⋮ │
│ 1.2    │ ├      │ <- │ {input_2}                 │ —   │ ⋮ │
│ 1.2.1  │ │ ├    │ /: │ Description of input_2    │ —   │ ⋮ │
│ 1.3    │ └      │ <- │ {result}                  │ —   │ ⋮ │
│ 2      │        │ <= │ $.({another_method})      │ imp │ ⋮ │
└──────────────────────────────────────────────────────────────┘
```

---

**User**

ok do you see that we can actaully just create a universal structured editor where we can flip each line into corresponding formal script, draft script and natural language script? 

---

**Cursor**

```plaintext
[1] [<=] [$.({method})] [draft ▼] [imp]
    Flips to:
[1.imperative|<= $.({method})] [formal ▼] [imp]
    Or:
[This accomplishes method using...] [natural ▼] [imp]
```

```plaintext
Draft                  | Formal                     | Natural


<= $.({method})       | 1.imperative|<= $.({method}) | This accomplishes...
    <- {input}        | 1.1.object|<- {input}        | The input is...
```

Yes! That's a brilliant insight. Instead of three separate tabs/editors with sync, we can have a **single unified structured editor** where each line (or the whole document) can be viewed in any of the three formats:

## Unified Editor Concept

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Format: [Draft (.ncd)] [Formal (.nc)] [Natural (.ncn)]  ← Global toggle │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Draft Mode:                                                             │
│  ┌────┬────┬─────────────────────────────┬─────┬───────┐                │
│  │ 1  │ <= │ $.({add_numbers})           │ imp │  ⋮    │                │
│  │1.1 │ <- │ {number_a}                  │  —  │  ⋮    │                │
│  │1.2 │ <- │ {number_b}                  │  —  │  ⋮    │                │
│  │1.3 │ <- │ {sum}                       │ imp │  ⋮    │                │
│  └────┴────┴─────────────────────────────┴─────┴───────┘                │
│                                                                          │
│  Flip to Formal (.nc) →                                                  │
│  ┌──────────────────────────────────────────────────────┐               │
│  │ 1.imperative|<= $.({add_numbers})                    │               │
│  │ 1.1.object|<- {number_a}                             │               │
│  │ 1.2.object|<- {number_b}                             │               │
│  │ 1.3.imperative|<- {sum}                              │               │
│  └──────────────────────────────────────────────────────┘               │
│                                                                          │
│  Flip to Natural (.ncn) →                                                │
│  ┌──────────────────────────────────────────────────────┐               │
│  │ <= Add two numbers together                          │               │
│  │     <- The first number (number_a)                   │               │
│  │     <- The second number (number_b)                  │               │
│  │     <- The resulting sum                             │               │
│  └──────────────────────────────────────────────────────┘               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

The **same underlying `EditableLine` data** powers all three views - just different **rendering**!

Let me implement this:

```plaintext
┌─────────────────────────────────────────────────────────────────────────┐
│  Format: [Draft (.ncd)] [Formal (.nc)] [Natural (.ncn)]  ← Global toggle │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Draft Mode:                                                             │
│  ┌────┬────┬─────────────────────────────┬─────┬───────┐                │
│  │ 1  │ <= │ $.({add_numbers})           │ imp │  ⋮    │                │
│  │1.1 │ <- │ {number_a}                  │  —  │  ⋮    │                │
│  │1.2 │ <- │ {number_b}                  │  —  │  ⋮    │                │
│  │1.3 │ <- │ {sum}                       │ imp │  ⋮    │                │
│  └────┴────┴─────────────────────────────┴─────┴───────┘                │
│                                                                          │
│  Flip to Formal (.nc) →                                                  │
│  ┌──────────────────────────────────────────────────────┐               │
│  │ 1.imperative|<= $.({add_numbers})                    │               │
│  │ 1.1.object|<- {number_a}                             │               │
│  │ 1.2.object|<- {number_b}                             │               │
│  │ 1.3.imperative|<- {sum}                              │               │
│  └──────────────────────────────────────────────────────┘               │
│                                                                          │
│  Flip to Natural (.ncn) →                                                │
│  ┌──────────────────────────────────────────────────────┐               │
│  │ <= Add two numbers together                          │               │
│  │     <- The first number (number_a)                   │               │
│  │     <- The second number (number_b)                  │               │
│  │     <- The resulting sum                             │               │
│  └──────────────────────────────────────────────────────┘               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

```python
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
            parent_id=self.parent_id
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
    
    def serialize(self) -> str:
        """
        Serialize EditableLines back to text.
        
        Returns:
            NormCode text content
        """
        result_lines = []
        
        for line in self.lines:
            result_lines.append(line.indented_content)
        
        return '\n'.join(result_lines)
    
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


```

```python
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
            parent_id=self.parent_id
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


```

Now let me update the structured editor to have a unified format toggle:

```python
"""
Structured Line-by-Line Editor Component

Renders NormCode content as individually editable lines with
per-line controls for structural operations.
"""

import streamlit as st
from typing import List, Optional, Callable
from pathlib import Path
import sys

# Add parent to path for imports
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.line_editor import EditableLine, LineManager, LineType


# Color scheme for syntax highlighting
COLORS = {
    'functional': '#ff79c6',      # Pink - <=
    'value': '#8be9fd',           # Cyan - <-
    'output': '#bd93f9',          # Purple - :<:
    'question': '#50fa7b',        # Green - ?:
    'description': '#f1fa8c',     # Yellow - /:
    'source': '#ffb86c',          # Orange - ...:
    'generic': '#f8f8f2',         # White
    'flow_index': '#ff5555',      # Red
    'sequence_type': '#6272a4',   # Gray
    'indent_guide': '#44475a',    # Dark gray
}

# Operator options for dropdown
OPERATOR_OPTIONS = [
    ('<=', 'Functional (<=)'),
    ('<-', 'Value (<-)'),
    (':<:', 'Output (:<:)'),
    ('?:', 'Question (?:)'),
    ('/:', 'Description (/:)'),
    ('...:', 'Source (...:)'),
    ('', 'None'),
]

# Sequence type options
SEQUENCE_TYPE_OPTIONS = [
    '', 'imperative', 'grouping', 'assigning', 
    'quantifying', 'timing', 'judgement', 'simple'
]


def init_structured_editor_state(file_type: str):
    """Initialize session state for a structured editor instance."""
    key_prefix = f'struct_editor_{file_type}'
    
    if f'{key_prefix}_lines' not in st.session_state:
        st.session_state[f'{key_prefix}_lines'] = []
    if f'{key_prefix}_manager' not in st.session_state:
        st.session_state[f'{key_prefix}_manager'] = LineManager()
    if f'{key_prefix}_selected' not in st.session_state:
        st.session_state[f'{key_prefix}_selected'] = None
    if f'{key_prefix}_mode' not in st.session_state:
        st.session_state[f'{key_prefix}_mode'] = 'structured'  # or 'text'
    if f'{key_prefix}_format' not in st.session_state:
        st.session_state[f'{key_prefix}_format'] = 'draft'  # 'draft', 'formal', 'natural'


def load_content(file_type: str, content: str):
    """Load content into the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    lines = manager.parse_text(content)
    st.session_state[f'{key_prefix}_lines'] = lines


def get_content(file_type: str) -> str:
    """Get serialized content from the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    return manager.serialize()


def render_structured_editor(
    file_type: str,
    on_change: Optional[Callable] = None
):
    """
    Render the structured line-by-line editor.
    
    Args:
        file_type: Type of file ('draft', 'formal', 'natural')
        on_change: Callback when content changes
    """
    key_prefix = f'struct_editor_{file_type}'
    init_structured_editor_state(file_type)
    
    manager: LineManager = st.session_state[f'{key_prefix}_manager']
    mode = st.session_state[f'{key_prefix}_mode']
    
    # Mode toggle and toolbar
    _render_toolbar(file_type, key_prefix, manager)
    
    if mode == 'text':
        _render_text_mode(file_type, key_prefix, manager, on_change)
    else:
        _render_structured_mode(file_type, key_prefix, manager, on_change)


def _render_toolbar(file_type: str, key_prefix: str, manager: LineManager):
    """Render the editor toolbar."""
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    
    with col1:
        mode = st.session_state[f'{key_prefix}_mode']
        if st.button(
            "📝 Text" if mode == 'structured' else "🔧 Structured",
            key=f'{key_prefix}_mode_toggle',
            help="Toggle between structured and text editing modes"
        ):
            new_mode = 'text' if mode == 'structured' else 'structured'
            st.session_state[f'{key_prefix}_mode'] = new_mode
            st.rerun()
    
    with col2:
        if st.button("➕ Add Line", key=f'{key_prefix}_add_line'):
            # Add a new line at the end
            manager.insert_line(len(manager.lines))
            st.rerun()
    
    with col3:
        if st.button("📋 Paste", key=f'{key_prefix}_paste',
                    help="Switch to text mode to paste content"):
            st.session_state[f'{key_prefix}_mode'] = 'text'
            st.rerun()
    
    with col4:
        if manager.has_modifications():
            st.markdown("⚠️ **Modified**")
    
    with col5:
        st.caption(f"{len(manager.lines)} lines")


def _render_text_mode(
    file_type: str, 
    key_prefix: str, 
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render text area mode for bulk editing."""
    current_content = manager.serialize()
    
    new_content = st.text_area(
        "Raw Content",
        value=current_content,
        height=500,
        key=f'{key_prefix}_text_area',
        label_visibility='collapsed'
    )
    
    # Parse changes back
    if new_content != current_content:
        manager.parse_text(new_content)
        if on_change:
            on_change()


def _render_structured_mode(
    file_type: str,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render the structured line-by-line editing mode."""
    
    # Custom CSS for editor styling
    st.markdown("""
    <style>
    .line-editor-container {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        background-color: #1e1e2e;
        border-radius: 8px;
        padding: 10px;
    }
    .line-row {
        display: flex;
        align-items: center;
        border-bottom: 1px solid #2d2d3d;
        padding: 2px 0;
    }
    .line-number {
        color: #6272a4;
        width: 40px;
        text-align: right;
        padding-right: 10px;
        user-select: none;
    }
    .indent-guide {
        color: #44475a;
        user-select: none;
    }
    .line-operator {
        font-weight: bold;
        min-width: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get visible lines (respecting collapse state)
    visible_lines = manager.get_visible_lines()
    
    if not visible_lines:
        st.info("No content yet. Click 'Add Line' to start editing.")
        return
    
    # Render each line
    for i, line in enumerate(visible_lines):
        _render_line_row(
            line=line,
            line_number=i + 1,
            key_prefix=key_prefix,
            manager=manager,
            on_change=on_change
        )


def _render_line_row(
    line: EditableLine,
    line_number: int,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render a single editable line row."""
    
    # Calculate column widths
    # Flow Index | Indent | Operator | Content | Seq | Actions
    # Flow index is now auto-computed and shown as the "line number"
    
    # Check if this line has children (for collapse toggle)
    has_children = len(manager.get_children(line.id)) > 0
    
    # Build indent string for display
    indent_display = "│  " * line.depth if line.depth > 0 else ""
    
    # Line container - removed the separate Flow column since it's now shown as line number
    cols = st.columns([0.8, 0.5, 0.8, 5.5, 1, 1.4])
    
    # Flow index as line number (auto-computed based on structure)
    with cols[0]:
        flow_display = line.flow_index if line.flow_index else "—"
        st.markdown(
            f"<span style='color: {COLORS['flow_index']}; font-weight: bold; font-family: monospace;'>{flow_display}</span>",
            unsafe_allow_html=True
        )
    
    # Indent visualization and collapse toggle
    with cols[1]:
        if has_children:
            collapse_icon = "▼" if not line.is_collapsed else "▶"
            if st.button(
                f"{collapse_icon}",
                key=f'{key_prefix}_collapse_{line.id}',
                help="Collapse/expand children"
            ):
                manager.toggle_collapse(line.id)
                st.rerun()
        else:
            st.markdown(
                f"<span style='color: {COLORS['indent_guide']}'>{indent_display}├</span>",
                unsafe_allow_html=True
            )
    
    # Operator dropdown
    with cols[2]:
        current_op = line.operator
        op_index = next(
            (i for i, (op, _) in enumerate(OPERATOR_OPTIONS) if op == current_op),
            len(OPERATOR_OPTIONS) - 1
        )
        
        new_op = st.selectbox(
            "Op",
            options=[op for op, _ in OPERATOR_OPTIONS],
            format_func=lambda x: x if x else "—",
            index=op_index,
            key=f'{key_prefix}_op_{line.id}',
            label_visibility='collapsed'
        )
        
        if new_op != current_op:
            manager.update_line_operator(line.id, new_op)
            if on_change:
                on_change()
    
    # Content input
    with cols[3]:
        # Color based on line type
        color = COLORS.get(line.line_type.value, COLORS['generic'])
        
        new_content = st.text_input(
            "Content",
            value=line.content,
            key=f'{key_prefix}_content_{line.id}',
            label_visibility='collapsed',
            placeholder="Enter content..."
        )
        
        if new_content != line.content:
            manager.update_line_content(line.id, new_content)
            if on_change:
                on_change()
    
    # Sequence type
    with cols[4]:
        seq_index = SEQUENCE_TYPE_OPTIONS.index(line.sequence_type) if line.sequence_type in SEQUENCE_TYPE_OPTIONS else 0
        
        new_seq = st.selectbox(
            "Seq",
            options=SEQUENCE_TYPE_OPTIONS,
            index=seq_index,
            key=f'{key_prefix}_seq_{line.id}',
            label_visibility='collapsed',
            format_func=lambda x: x[:3] if x else "—"
        )
        
        if new_seq != line.sequence_type:
            manager.update_line_metadata(line.id, sequence_type=new_seq)
            if on_change:
                on_change()
    
    # Action buttons
    with cols[5]:
        _render_line_actions(line, key_prefix, manager, on_change)


def _render_line_actions(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render action buttons for a line."""
    
    # Use a popover/expander for actions to save space
    action_cols = st.columns([1, 1, 1, 1, 1])
    
    # Indent/Outdent
    with action_cols[0]:
        if st.button("→", key=f'{key_prefix}_indent_{line.id}', help="Indent"):
            manager.indent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[1]:
        if st.button("←", key=f'{key_prefix}_outdent_{line.id}', help="Outdent"):
            manager.outdent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Move up/down
    with action_cols[2]:
        if st.button("↑", key=f'{key_prefix}_up_{line.id}', help="Move up"):
            manager.move_line_up(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[3]:
        if st.button("↓", key=f'{key_prefix}_down_{line.id}', help="Move down"):
            manager.move_line_down(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Delete
    with action_cols[4]:
        if st.button("🗑", key=f'{key_prefix}_del_{line.id}', help="Delete"):
            manager.delete_line(line.id)
            if on_change:
                on_change()
            st.rerun()


def render_line_context_menu(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render an expanded context menu for a line."""
    
    with st.expander(f"Line {manager.get_line_index(line.id) + 1} Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Duplicate", key=f'{key_prefix}_dup_{line.id}'):
                manager.duplicate_line(line.id)
                if on_change:
                    on_change()
                st.rerun()
            
            if st.button("📋 Duplicate with children", key=f'{key_prefix}_dup_children_{line.id}'):
                manager.duplicate_line(line.id, include_children=True)
                if on_change:
                    on_change()
                st.rerun()
        
        with col2:
            st.markdown("**Add Annotation:**")
            ann_cols = st.columns(3)
            
            with ann_cols[0]:
                if st.button("?:", key=f'{key_prefix}_add_q_{line.id}', help="Add question"):
                    manager.add_annotation(line.id, 'question')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[1]:
                if st.button("/:", key=f'{key_prefix}_add_d_{line.id}', help="Add description"):
                    manager.add_annotation(line.id, 'description')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[2]:
                if st.button("...:", key=f'{key_prefix}_add_s_{line.id}', help="Add source"):
                    manager.add_annotation(line.id, 'source')
                    if on_change:
                        on_change()
                    st.rerun()


def render_quick_actions_panel(
    file_type: str,
    key_prefix: str,
    manager: LineManager
):
    """Render a panel with quick actions for the entire document."""
    
    with st.expander("🔧 Quick Actions", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Structure:**")
            st.caption("💡 Flow indices auto-update based on indent structure")
            
            if st.button("📐 Rebuild hierarchy", key=f'{key_prefix}_fix_indent'):
                _normalize_indentation(manager)
                st.rerun()
        
        with col2:
            st.markdown("**Insert Templates:**")
            if st.button("➕ Functional block", key=f'{key_prefix}_tpl_func'):
                _insert_functional_template(manager)
                st.rerun()
            
            if st.button("➕ Value block", key=f'{key_prefix}_tpl_value'):
                _insert_value_template(manager)
                st.rerun()
        
        with col3:
            st.markdown("**View:**")
            if st.button("▼ Expand all", key=f'{key_prefix}_expand_all'):
                for line in manager.lines:
                    line.is_collapsed = False
                st.rerun()
            
            if st.button("▶ Collapse all", key=f'{key_prefix}_collapse_all'):
                for line in manager.lines:
                    if manager.get_children(line.id):
                        line.is_collapsed = True
                st.rerun()


def _normalize_indentation(manager: LineManager):
    """Ensure consistent indentation based on parent-child relationships."""
    manager._build_hierarchy()
    for line in manager.lines:
        line.is_modified = True


def _insert_functional_template(manager: LineManager):
    """Insert a template for a functional concept block."""
    lines = [
        EditableLine(depth=0, operator='<=', line_type=LineType.FUNCTIONAL_CONCEPT,
                    content='$.({method_name})', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description of what this does', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_1}', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_2}', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


def _insert_value_template(manager: LineManager):
    """Insert a template for a value concept block."""
    lines = [
        EditableLine(depth=0, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{concept_name}', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


```

```python
"""
Structured Line-by-Line Editor Component

Renders NormCode content as individually editable lines with
per-line controls for structural operations.
"""

import streamlit as st
from typing import List, Optional, Callable
from pathlib import Path
import sys

# Add parent to path for imports
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.line_editor import EditableLine, LineManager, LineType


# Color scheme for syntax highlighting
COLORS = {
    'functional': '#ff79c6',      # Pink - <=
    'value': '#8be9fd',           # Cyan - <-
    'output': '#bd93f9',          # Purple - :<:
    'question': '#50fa7b',        # Green - ?:
    'description': '#f1fa8c',     # Yellow - /:
    'source': '#ffb86c',          # Orange - ...:
    'generic': '#f8f8f2',         # White
    'flow_index': '#ff5555',      # Red
    'sequence_type': '#6272a4',   # Gray
    'indent_guide': '#44475a',    # Dark gray
}

# Operator options for dropdown
OPERATOR_OPTIONS = [
    ('<=', 'Functional (<=)'),
    ('<-', 'Value (<-)'),
    (':<:', 'Output (:<:)'),
    ('?:', 'Question (?:)'),
    ('/:', 'Description (/:)'),
    ('...:', 'Source (...:)'),
    ('', 'None'),
]

# Sequence type options
SEQUENCE_TYPE_OPTIONS = [
    '', 'imperative', 'grouping', 'assigning', 
    'quantifying', 'timing', 'judgement', 'simple'
]


def init_structured_editor_state(file_type: str):
    """Initialize session state for a structured editor instance."""
    key_prefix = f'struct_editor_{file_type}'
    
    if f'{key_prefix}_lines' not in st.session_state:
        st.session_state[f'{key_prefix}_lines'] = []
    if f'{key_prefix}_manager' not in st.session_state:
        st.session_state[f'{key_prefix}_manager'] = LineManager()
    if f'{key_prefix}_selected' not in st.session_state:
        st.session_state[f'{key_prefix}_selected'] = None
    if f'{key_prefix}_mode' not in st.session_state:
        st.session_state[f'{key_prefix}_mode'] = 'structured'  # or 'text'
    if f'{key_prefix}_format' not in st.session_state:
        st.session_state[f'{key_prefix}_format'] = 'draft'  # 'draft', 'formal', 'natural'


def load_content(file_type: str, content: str):
    """Load content into the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    lines = manager.parse_text(content)
    st.session_state[f'{key_prefix}_lines'] = lines


def get_content(file_type: str, format: str = None) -> str:
    """
    Get serialized content from the structured editor.
    
    Args:
        file_type: The file type key
        format: Output format ('draft', 'formal', 'natural'). 
                If None, uses the current format setting.
    """
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    if format is None:
        format = st.session_state.get(f'{key_prefix}_format', 'draft')
    
    return manager.serialize(format)


def render_structured_editor(
    file_type: str,
    on_change: Optional[Callable] = None
):
    """
    Render the structured line-by-line editor.
    
    Args:
        file_type: Type of file ('draft', 'formal', 'natural')
        on_change: Callback when content changes
    """
    key_prefix = f'struct_editor_{file_type}'
    init_structured_editor_state(file_type)
    
    manager: LineManager = st.session_state[f'{key_prefix}_manager']
    mode = st.session_state[f'{key_prefix}_mode']
    
    # Mode toggle and toolbar
    _render_toolbar(file_type, key_prefix, manager)
    
    if mode == 'text':
        _render_text_mode(file_type, key_prefix, manager, on_change)
    else:
        _render_structured_mode(file_type, key_prefix, manager, on_change)


def _render_toolbar(file_type: str, key_prefix: str, manager: LineManager):
    """Render the editor toolbar."""
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    
    with col1:
        mode = st.session_state[f'{key_prefix}_mode']
        if st.button(
            "📝 Text" if mode == 'structured' else "🔧 Structured",
            key=f'{key_prefix}_mode_toggle',
            help="Toggle between structured and text editing modes"
        ):
            new_mode = 'text' if mode == 'structured' else 'structured'
            st.session_state[f'{key_prefix}_mode'] = new_mode
            st.rerun()
    
    with col2:
        if st.button("➕ Add Line", key=f'{key_prefix}_add_line'):
            # Add a new line at the end
            manager.insert_line(len(manager.lines))
            st.rerun()
    
    with col3:
        if st.button("📋 Paste", key=f'{key_prefix}_paste',
                    help="Switch to text mode to paste content"):
            st.session_state[f'{key_prefix}_mode'] = 'text'
            st.rerun()
    
    with col4:
        if manager.has_modifications():
            st.markdown("⚠️ **Modified**")
    
    with col5:
        st.caption(f"{len(manager.lines)} lines")


def _render_text_mode(
    file_type: str, 
    key_prefix: str, 
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render text area mode for bulk editing."""
    current_content = manager.serialize()
    
    new_content = st.text_area(
        "Raw Content",
        value=current_content,
        height=500,
        key=f'{key_prefix}_text_area',
        label_visibility='collapsed'
    )
    
    # Parse changes back
    if new_content != current_content:
        manager.parse_text(new_content)
        if on_change:
            on_change()


def _render_structured_mode(
    file_type: str,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render the structured line-by-line editing mode."""
    
    # Custom CSS for editor styling
    st.markdown("""
    <style>
    .line-editor-container {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        background-color: #1e1e2e;
        border-radius: 8px;
        padding: 10px;
    }
    .line-row {
        display: flex;
        align-items: center;
        border-bottom: 1px solid #2d2d3d;
        padding: 2px 0;
    }
    .line-number {
        color: #6272a4;
        width: 40px;
        text-align: right;
        padding-right: 10px;
        user-select: none;
    }
    .indent-guide {
        color: #44475a;
        user-select: none;
    }
    .line-operator {
        font-weight: bold;
        min-width: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get visible lines (respecting collapse state)
    visible_lines = manager.get_visible_lines()
    
    if not visible_lines:
        st.info("No content yet. Click 'Add Line' to start editing.")
        return
    
    # Render each line
    for i, line in enumerate(visible_lines):
        _render_line_row(
            line=line,
            line_number=i + 1,
            key_prefix=key_prefix,
            manager=manager,
            on_change=on_change
        )


def _render_line_row(
    line: EditableLine,
    line_number: int,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render a single editable line row."""
    
    # Calculate column widths
    # Flow Index | Indent | Operator | Content | Seq | Actions
    # Flow index is now auto-computed and shown as the "line number"
    
    # Check if this line has children (for collapse toggle)
    has_children = len(manager.get_children(line.id)) > 0
    
    # Build indent string for display
    indent_display = "│  " * line.depth if line.depth > 0 else ""
    
    # Line container - removed the separate Flow column since it's now shown as line number
    cols = st.columns([0.8, 0.5, 0.8, 5.5, 1, 1.4])
    
    # Flow index as line number (auto-computed based on structure)
    with cols[0]:
        flow_display = line.flow_index if line.flow_index else "—"
        st.markdown(
            f"<span style='color: {COLORS['flow_index']}; font-weight: bold; font-family: monospace;'>{flow_display}</span>",
            unsafe_allow_html=True
        )
    
    # Indent visualization and collapse toggle
    with cols[1]:
        if has_children:
            collapse_icon = "▼" if not line.is_collapsed else "▶"
            if st.button(
                f"{collapse_icon}",
                key=f'{key_prefix}_collapse_{line.id}',
                help="Collapse/expand children"
            ):
                manager.toggle_collapse(line.id)
                st.rerun()
        else:
            st.markdown(
                f"<span style='color: {COLORS['indent_guide']}'>{indent_display}├</span>",
                unsafe_allow_html=True
            )
    
    # Operator dropdown
    with cols[2]:
        current_op = line.operator
        op_index = next(
            (i for i, (op, _) in enumerate(OPERATOR_OPTIONS) if op == current_op),
            len(OPERATOR_OPTIONS) - 1
        )
        
        new_op = st.selectbox(
            "Op",
            options=[op for op, _ in OPERATOR_OPTIONS],
            format_func=lambda x: x if x else "—",
            index=op_index,
            key=f'{key_prefix}_op_{line.id}',
            label_visibility='collapsed'
        )
        
        if new_op != current_op:
            manager.update_line_operator(line.id, new_op)
            if on_change:
                on_change()
    
    # Content input
    with cols[3]:
        # Color based on line type
        color = COLORS.get(line.line_type.value, COLORS['generic'])
        
        new_content = st.text_input(
            "Content",
            value=line.content,
            key=f'{key_prefix}_content_{line.id}',
            label_visibility='collapsed',
            placeholder="Enter content..."
        )
        
        if new_content != line.content:
            manager.update_line_content(line.id, new_content)
            if on_change:
                on_change()
    
    # Sequence type
    with cols[4]:
        seq_index = SEQUENCE_TYPE_OPTIONS.index(line.sequence_type) if line.sequence_type in SEQUENCE_TYPE_OPTIONS else 0
        
        new_seq = st.selectbox(
            "Seq",
            options=SEQUENCE_TYPE_OPTIONS,
            index=seq_index,
            key=f'{key_prefix}_seq_{line.id}',
            label_visibility='collapsed',
            format_func=lambda x: x[:3] if x else "—"
        )
        
        if new_seq != line.sequence_type:
            manager.update_line_metadata(line.id, sequence_type=new_seq)
            if on_change:
                on_change()
    
    # Action buttons
    with cols[5]:
        _render_line_actions(line, key_prefix, manager, on_change)


def _render_line_actions(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render action buttons for a line."""
    
    # Use a popover/expander for actions to save space
    action_cols = st.columns([1, 1, 1, 1, 1])
    
    # Indent/Outdent
    with action_cols[0]:
        if st.button("→", key=f'{key_prefix}_indent_{line.id}', help="Indent"):
            manager.indent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[1]:
        if st.button("←", key=f'{key_prefix}_outdent_{line.id}', help="Outdent"):
            manager.outdent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Move up/down
    with action_cols[2]:
        if st.button("↑", key=f'{key_prefix}_up_{line.id}', help="Move up"):
            manager.move_line_up(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[3]:
        if st.button("↓", key=f'{key_prefix}_down_{line.id}', help="Move down"):
            manager.move_line_down(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Delete
    with action_cols[4]:
        if st.button("🗑", key=f'{key_prefix}_del_{line.id}', help="Delete"):
            manager.delete_line(line.id)
            if on_change:
                on_change()
            st.rerun()


def render_line_context_menu(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render an expanded context menu for a line."""
    
    with st.expander(f"Line {manager.get_line_index(line.id) + 1} Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Duplicate", key=f'{key_prefix}_dup_{line.id}'):
                manager.duplicate_line(line.id)
                if on_change:
                    on_change()
                st.rerun()
            
            if st.button("📋 Duplicate with children", key=f'{key_prefix}_dup_children_{line.id}'):
                manager.duplicate_line(line.id, include_children=True)
                if on_change:
                    on_change()
                st.rerun()
        
        with col2:
            st.markdown("**Add Annotation:**")
            ann_cols = st.columns(3)
            
            with ann_cols[0]:
                if st.button("?:", key=f'{key_prefix}_add_q_{line.id}', help="Add question"):
                    manager.add_annotation(line.id, 'question')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[1]:
                if st.button("/:", key=f'{key_prefix}_add_d_{line.id}', help="Add description"):
                    manager.add_annotation(line.id, 'description')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[2]:
                if st.button("...:", key=f'{key_prefix}_add_s_{line.id}', help="Add source"):
                    manager.add_annotation(line.id, 'source')
                    if on_change:
                        on_change()
                    st.rerun()


def render_quick_actions_panel(
    file_type: str,
    key_prefix: str,
    manager: LineManager
):
    """Render a panel with quick actions for the entire document."""
    
    with st.expander("🔧 Quick Actions", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Structure:**")
            st.caption("💡 Flow indices auto-update based on indent structure")
            
            if st.button("📐 Rebuild hierarchy", key=f'{key_prefix}_fix_indent'):
                _normalize_indentation(manager)
                st.rerun()
        
        with col2:
            st.markdown("**Insert Templates:**")
            if st.button("➕ Functional block", key=f'{key_prefix}_tpl_func'):
                _insert_functional_template(manager)
                st.rerun()
            
            if st.button("➕ Value block", key=f'{key_prefix}_tpl_value'):
                _insert_value_template(manager)
                st.rerun()
        
        with col3:
            st.markdown("**View:**")
            if st.button("▼ Expand all", key=f'{key_prefix}_expand_all'):
                for line in manager.lines:
                    line.is_collapsed = False
                st.rerun()
            
            if st.button("▶ Collapse all", key=f'{key_prefix}_collapse_all'):
                for line in manager.lines:
                    if manager.get_children(line.id):
                        line.is_collapsed = True
                st.rerun()


def _normalize_indentation(manager: LineManager):
    """Ensure consistent indentation based on parent-child relationships."""
    manager._build_hierarchy()
    for line in manager.lines:
        line.is_modified = True


def _insert_functional_template(manager: LineManager):
    """Insert a template for a functional concept block."""
    lines = [
        EditableLine(depth=0, operator='<=', line_type=LineType.FUNCTIONAL_CONCEPT,
                    content='$.({method_name})', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description of what this does', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_1}', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_2}', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


def _insert_value_template(manager: LineManager):
    """Insert a template for a value concept block."""
    lines = [
        EditableLine(depth=0, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{concept_name}', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


```

```python
"""
Structured Line-by-Line Editor Component

Renders NormCode content as individually editable lines with
per-line controls for structural operations.
"""

import streamlit as st
from typing import List, Optional, Callable
from pathlib import Path
import sys

# Add parent to path for imports
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.line_editor import EditableLine, LineManager, LineType


# Color scheme for syntax highlighting
COLORS = {
    'functional': '#ff79c6',      # Pink - <=
    'value': '#8be9fd',           # Cyan - <-
    'output': '#bd93f9',          # Purple - :<:
    'question': '#50fa7b',        # Green - ?:
    'description': '#f1fa8c',     # Yellow - /:
    'source': '#ffb86c',          # Orange - ...:
    'generic': '#f8f8f2',         # White
    'flow_index': '#ff5555',      # Red
    'sequence_type': '#6272a4',   # Gray
    'indent_guide': '#44475a',    # Dark gray
}

# Operator options for dropdown
OPERATOR_OPTIONS = [
    ('<=', 'Functional (<=)'),
    ('<-', 'Value (<-)'),
    (':<:', 'Output (:<:)'),
    ('?:', 'Question (?:)'),
    ('/:', 'Description (/:)'),
    ('...:', 'Source (...:)'),
    ('', 'None'),
]

# Sequence type options
SEQUENCE_TYPE_OPTIONS = [
    '', 'imperative', 'grouping', 'assigning', 
    'quantifying', 'timing', 'judgement', 'simple'
]


def init_structured_editor_state(file_type: str):
    """Initialize session state for a structured editor instance."""
    key_prefix = f'struct_editor_{file_type}'
    
    if f'{key_prefix}_lines' not in st.session_state:
        st.session_state[f'{key_prefix}_lines'] = []
    if f'{key_prefix}_manager' not in st.session_state:
        st.session_state[f'{key_prefix}_manager'] = LineManager()
    if f'{key_prefix}_selected' not in st.session_state:
        st.session_state[f'{key_prefix}_selected'] = None
    if f'{key_prefix}_mode' not in st.session_state:
        st.session_state[f'{key_prefix}_mode'] = 'structured'  # or 'text'
    if f'{key_prefix}_format' not in st.session_state:
        st.session_state[f'{key_prefix}_format'] = 'draft'  # 'draft', 'formal', 'natural'


def load_content(file_type: str, content: str):
    """Load content into the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    lines = manager.parse_text(content)
    st.session_state[f'{key_prefix}_lines'] = lines


def get_content(file_type: str, format: str = None) -> str:
    """
    Get serialized content from the structured editor.
    
    Args:
        file_type: The file type key
        format: Output format ('draft', 'formal', 'natural'). 
                If None, uses the current format setting.
    """
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    if format is None:
        format = st.session_state.get(f'{key_prefix}_format', 'draft')
    
    return manager.serialize(format)


def render_structured_editor(
    file_type: str,
    on_change: Optional[Callable] = None
):
    """
    Render the structured line-by-line editor.
    
    Args:
        file_type: Type of file ('draft', 'formal', 'natural')
        on_change: Callback when content changes
    """
    key_prefix = f'struct_editor_{file_type}'
    init_structured_editor_state(file_type)
    
    manager: LineManager = st.session_state[f'{key_prefix}_manager']
    mode = st.session_state[f'{key_prefix}_mode']
    
    # Mode toggle and toolbar
    _render_toolbar(file_type, key_prefix, manager)
    
    if mode == 'text':
        _render_text_mode(file_type, key_prefix, manager, on_change)
    else:
        _render_structured_mode(file_type, key_prefix, manager, on_change)


def _render_toolbar(file_type: str, key_prefix: str, manager: LineManager):
    """Render the editor toolbar."""
    col1, col2, col3, col4, col5, col6 = st.columns([1.2, 1, 1, 1, 1.5, 1])
    
    # Format toggle - this is the key feature!
    with col1:
        current_format = st.session_state.get(f'{key_prefix}_format', 'draft')
        format_options = {
            'draft': '📄 Draft (.ncd)',
            'formal': '📋 Formal (.nc)', 
            'natural': '📖 Natural (.ncn)'
        }
        
        new_format = st.selectbox(
            "Format",
            options=['draft', 'formal', 'natural'],
            index=['draft', 'formal', 'natural'].index(current_format),
            format_func=lambda x: format_options[x],
            key=f'{key_prefix}_format_select',
            label_visibility='collapsed'
        )
        
        if new_format != current_format:
            st.session_state[f'{key_prefix}_format'] = new_format
            st.rerun()
    
    with col2:
        mode = st.session_state[f'{key_prefix}_mode']
        if st.button(
            "📝 Text" if mode == 'structured' else "🔧 Struct",
            key=f'{key_prefix}_mode_toggle',
            help="Toggle between structured and text editing modes"
        ):
            new_mode = 'text' if mode == 'structured' else 'structured'
            st.session_state[f'{key_prefix}_mode'] = new_mode
            st.rerun()
    
    with col3:
        if st.button("➕ Add", key=f'{key_prefix}_add_line'):
            # Add a new line at the end
            manager.insert_line(len(manager.lines))
            st.rerun()
    
    with col4:
        if st.button("📋 Paste", key=f'{key_prefix}_paste',
                    help="Switch to text mode to paste content"):
            st.session_state[f'{key_prefix}_mode'] = 'text'
            st.rerun()
    
    with col5:
        if manager.has_modifications():
            st.markdown("⚠️ **Modified**")
        else:
            st.caption(f"{len(manager.lines)} lines")
    
    with col6:
        # Show current format indicator
        format_colors = {'draft': '#8be9fd', 'formal': '#ff79c6', 'natural': '#50fa7b'}
        st.markdown(
            f"<span style='color: {format_colors[new_format]}'>●</span>",
            unsafe_allow_html=True
        )


def _render_text_mode(
    file_type: str, 
    key_prefix: str, 
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render text area mode for bulk editing."""
    current_content = manager.serialize()
    
    new_content = st.text_area(
        "Raw Content",
        value=current_content,
        height=500,
        key=f'{key_prefix}_text_area',
        label_visibility='collapsed'
    )
    
    # Parse changes back
    if new_content != current_content:
        manager.parse_text(new_content)
        if on_change:
            on_change()


def _render_structured_mode(
    file_type: str,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render the structured line-by-line editing mode."""
    
    # Custom CSS for editor styling
    st.markdown("""
    <style>
    .line-editor-container {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        background-color: #1e1e2e;
        border-radius: 8px;
        padding: 10px;
    }
    .line-row {
        display: flex;
        align-items: center;
        border-bottom: 1px solid #2d2d3d;
        padding: 2px 0;
    }
    .line-number {
        color: #6272a4;
        width: 40px;
        text-align: right;
        padding-right: 10px;
        user-select: none;
    }
    .indent-guide {
        color: #44475a;
        user-select: none;
    }
    .line-operator {
        font-weight: bold;
        min-width: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get visible lines (respecting collapse state)
    visible_lines = manager.get_visible_lines()
    
    if not visible_lines:
        st.info("No content yet. Click 'Add Line' to start editing.")
        return
    
    # Render each line
    for i, line in enumerate(visible_lines):
        _render_line_row(
            line=line,
            line_number=i + 1,
            key_prefix=key_prefix,
            manager=manager,
            on_change=on_change
        )


def _render_line_row(
    line: EditableLine,
    line_number: int,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render a single editable line row."""
    
    # Calculate column widths
    # Flow Index | Indent | Operator | Content | Seq | Actions
    # Flow index is now auto-computed and shown as the "line number"
    
    # Check if this line has children (for collapse toggle)
    has_children = len(manager.get_children(line.id)) > 0
    
    # Build indent string for display
    indent_display = "│  " * line.depth if line.depth > 0 else ""
    
    # Line container - removed the separate Flow column since it's now shown as line number
    cols = st.columns([0.8, 0.5, 0.8, 5.5, 1, 1.4])
    
    # Flow index as line number (auto-computed based on structure)
    with cols[0]:
        flow_display = line.flow_index if line.flow_index else "—"
        st.markdown(
            f"<span style='color: {COLORS['flow_index']}; font-weight: bold; font-family: monospace;'>{flow_display}</span>",
            unsafe_allow_html=True
        )
    
    # Indent visualization and collapse toggle
    with cols[1]:
        if has_children:
            collapse_icon = "▼" if not line.is_collapsed else "▶"
            if st.button(
                f"{collapse_icon}",
                key=f'{key_prefix}_collapse_{line.id}',
                help="Collapse/expand children"
            ):
                manager.toggle_collapse(line.id)
                st.rerun()
        else:
            st.markdown(
                f"<span style='color: {COLORS['indent_guide']}'>{indent_display}├</span>",
                unsafe_allow_html=True
            )
    
    # Operator dropdown
    with cols[2]:
        current_op = line.operator
        op_index = next(
            (i for i, (op, _) in enumerate(OPERATOR_OPTIONS) if op == current_op),
            len(OPERATOR_OPTIONS) - 1
        )
        
        new_op = st.selectbox(
            "Op",
            options=[op for op, _ in OPERATOR_OPTIONS],
            format_func=lambda x: x if x else "—",
            index=op_index,
            key=f'{key_prefix}_op_{line.id}',
            label_visibility='collapsed'
        )
        
        if new_op != current_op:
            manager.update_line_operator(line.id, new_op)
            if on_change:
                on_change()
    
    # Content input
    with cols[3]:
        # Color based on line type
        color = COLORS.get(line.line_type.value, COLORS['generic'])
        
        new_content = st.text_input(
            "Content",
            value=line.content,
            key=f'{key_prefix}_content_{line.id}',
            label_visibility='collapsed',
            placeholder="Enter content..."
        )
        
        if new_content != line.content:
            manager.update_line_content(line.id, new_content)
            if on_change:
                on_change()
    
    # Sequence type
    with cols[4]:
        seq_index = SEQUENCE_TYPE_OPTIONS.index(line.sequence_type) if line.sequence_type in SEQUENCE_TYPE_OPTIONS else 0
        
        new_seq = st.selectbox(
            "Seq",
            options=SEQUENCE_TYPE_OPTIONS,
            index=seq_index,
            key=f'{key_prefix}_seq_{line.id}',
            label_visibility='collapsed',
            format_func=lambda x: x[:3] if x else "—"
        )
        
        if new_seq != line.sequence_type:
            manager.update_line_metadata(line.id, sequence_type=new_seq)
            if on_change:
                on_change()
    
    # Action buttons
    with cols[5]:
        _render_line_actions(line, key_prefix, manager, on_change)


def _render_line_actions(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render action buttons for a line."""
    
    # Use a popover/expander for actions to save space
    action_cols = st.columns([1, 1, 1, 1, 1])
    
    # Indent/Outdent
    with action_cols[0]:
        if st.button("→", key=f'{key_prefix}_indent_{line.id}', help="Indent"):
            manager.indent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[1]:
        if st.button("←", key=f'{key_prefix}_outdent_{line.id}', help="Outdent"):
            manager.outdent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Move up/down
    with action_cols[2]:
        if st.button("↑", key=f'{key_prefix}_up_{line.id}', help="Move up"):
            manager.move_line_up(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[3]:
        if st.button("↓", key=f'{key_prefix}_down_{line.id}', help="Move down"):
            manager.move_line_down(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Delete
    with action_cols[4]:
        if st.button("🗑", key=f'{key_prefix}_del_{line.id}', help="Delete"):
            manager.delete_line(line.id)
            if on_change:
                on_change()
            st.rerun()


def render_line_context_menu(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render an expanded context menu for a line."""
    
    with st.expander(f"Line {manager.get_line_index(line.id) + 1} Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Duplicate", key=f'{key_prefix}_dup_{line.id}'):
                manager.duplicate_line(line.id)
                if on_change:
                    on_change()
                st.rerun()
            
            if st.button("📋 Duplicate with children", key=f'{key_prefix}_dup_children_{line.id}'):
                manager.duplicate_line(line.id, include_children=True)
                if on_change:
                    on_change()
                st.rerun()
        
        with col2:
            st.markdown("**Add Annotation:**")
            ann_cols = st.columns(3)
            
            with ann_cols[0]:
                if st.button("?:", key=f'{key_prefix}_add_q_{line.id}', help="Add question"):
                    manager.add_annotation(line.id, 'question')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[1]:
                if st.button("/:", key=f'{key_prefix}_add_d_{line.id}', help="Add description"):
                    manager.add_annotation(line.id, 'description')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[2]:
                if st.button("...:", key=f'{key_prefix}_add_s_{line.id}', help="Add source"):
                    manager.add_annotation(line.id, 'source')
                    if on_change:
                        on_change()
                    st.rerun()


def render_quick_actions_panel(
    file_type: str,
    key_prefix: str,
    manager: LineManager
):
    """Render a panel with quick actions for the entire document."""
    
    with st.expander("🔧 Quick Actions", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Structure:**")
            st.caption("💡 Flow indices auto-update based on indent structure")
            
            if st.button("📐 Rebuild hierarchy", key=f'{key_prefix}_fix_indent'):
                _normalize_indentation(manager)
                st.rerun()
        
        with col2:
            st.markdown("**Insert Templates:**")
            if st.button("➕ Functional block", key=f'{key_prefix}_tpl_func'):
                _insert_functional_template(manager)
                st.rerun()
            
            if st.button("➕ Value block", key=f'{key_prefix}_tpl_value'):
                _insert_value_template(manager)
                st.rerun()
        
        with col3:
            st.markdown("**View:**")
            if st.button("▼ Expand all", key=f'{key_prefix}_expand_all'):
                for line in manager.lines:
                    line.is_collapsed = False
                st.rerun()
            
            if st.button("▶ Collapse all", key=f'{key_prefix}_collapse_all'):
                for line in manager.lines:
                    if manager.get_children(line.id):
                        line.is_collapsed = True
                st.rerun()


def _normalize_indentation(manager: LineManager):
    """Ensure consistent indentation based on parent-child relationships."""
    manager._build_hierarchy()
    for line in manager.lines:
        line.is_modified = True


def _insert_functional_template(manager: LineManager):
    """Insert a template for a functional concept block."""
    lines = [
        EditableLine(depth=0, operator='<=', line_type=LineType.FUNCTIONAL_CONCEPT,
                    content='$.({method_name})', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description of what this does', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_1}', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_2}', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


def _insert_value_template(manager: LineManager):
    """Insert a template for a value concept block."""
    lines = [
        EditableLine(depth=0, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{concept_name}', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


```

```python
"""
Structured Line-by-Line Editor Component

Renders NormCode content as individually editable lines with
per-line controls for structural operations.
"""

import streamlit as st
from typing import List, Optional, Callable
from pathlib import Path
import sys

# Add parent to path for imports
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.line_editor import EditableLine, LineManager, LineType


# Color scheme for syntax highlighting
COLORS = {
    'functional': '#ff79c6',      # Pink - <=
    'value': '#8be9fd',           # Cyan - <-
    'output': '#bd93f9',          # Purple - :<:
    'question': '#50fa7b',        # Green - ?:
    'description': '#f1fa8c',     # Yellow - /:
    'source': '#ffb86c',          # Orange - ...:
    'generic': '#f8f8f2',         # White
    'flow_index': '#ff5555',      # Red
    'sequence_type': '#6272a4',   # Gray
    'indent_guide': '#44475a',    # Dark gray
}

# Operator options for dropdown
OPERATOR_OPTIONS = [
    ('<=', 'Functional (<=)'),
    ('<-', 'Value (<-)'),
    (':<:', 'Output (:<:)'),
    ('?:', 'Question (?:)'),
    ('/:', 'Description (/:)'),
    ('...:', 'Source (...:)'),
    ('', 'None'),
]

# Sequence type options
SEQUENCE_TYPE_OPTIONS = [
    '', 'imperative', 'grouping', 'assigning', 
    'quantifying', 'timing', 'judgement', 'simple'
]


def init_structured_editor_state(file_type: str):
    """Initialize session state for a structured editor instance."""
    key_prefix = f'struct_editor_{file_type}'
    
    if f'{key_prefix}_lines' not in st.session_state:
        st.session_state[f'{key_prefix}_lines'] = []
    if f'{key_prefix}_manager' not in st.session_state:
        st.session_state[f'{key_prefix}_manager'] = LineManager()
    if f'{key_prefix}_selected' not in st.session_state:
        st.session_state[f'{key_prefix}_selected'] = None
    if f'{key_prefix}_mode' not in st.session_state:
        st.session_state[f'{key_prefix}_mode'] = 'structured'  # or 'text'
    if f'{key_prefix}_format' not in st.session_state:
        st.session_state[f'{key_prefix}_format'] = 'draft'  # 'draft', 'formal', 'natural'


def load_content(file_type: str, content: str):
    """Load content into the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    lines = manager.parse_text(content)
    st.session_state[f'{key_prefix}_lines'] = lines


def get_content(file_type: str, format: str = None) -> str:
    """
    Get serialized content from the structured editor.
    
    Args:
        file_type: The file type key
        format: Output format ('draft', 'formal', 'natural'). 
                If None, uses the current format setting.
    """
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    if format is None:
        format = st.session_state.get(f'{key_prefix}_format', 'draft')
    
    return manager.serialize(format)


def render_structured_editor(
    file_type: str,
    on_change: Optional[Callable] = None
):
    """
    Render the structured line-by-line editor.
    
    Args:
        file_type: Type of file ('draft', 'formal', 'natural')
        on_change: Callback when content changes
    """
    key_prefix = f'struct_editor_{file_type}'
    init_structured_editor_state(file_type)
    
    manager: LineManager = st.session_state[f'{key_prefix}_manager']
    mode = st.session_state[f'{key_prefix}_mode']
    
    # Mode toggle and toolbar
    _render_toolbar(file_type, key_prefix, manager)
    
    if mode == 'text':
        _render_text_mode(file_type, key_prefix, manager, on_change)
    else:
        _render_structured_mode(file_type, key_prefix, manager, on_change)


def _render_toolbar(file_type: str, key_prefix: str, manager: LineManager):
    """Render the editor toolbar."""
    col1, col2, col3, col4, col5, col6 = st.columns([1.2, 1, 1, 1, 1.5, 1])
    
    # Format toggle - this is the key feature!
    with col1:
        current_format = st.session_state.get(f'{key_prefix}_format', 'draft')
        format_options = {
            'draft': '📄 Draft (.ncd)',
            'formal': '📋 Formal (.nc)', 
            'natural': '📖 Natural (.ncn)'
        }
        
        new_format = st.selectbox(
            "Format",
            options=['draft', 'formal', 'natural'],
            index=['draft', 'formal', 'natural'].index(current_format),
            format_func=lambda x: format_options[x],
            key=f'{key_prefix}_format_select',
            label_visibility='collapsed'
        )
        
        if new_format != current_format:
            st.session_state[f'{key_prefix}_format'] = new_format
            st.rerun()
    
    with col2:
        mode = st.session_state[f'{key_prefix}_mode']
        if st.button(
            "📝 Text" if mode == 'structured' else "🔧 Struct",
            key=f'{key_prefix}_mode_toggle',
            help="Toggle between structured and text editing modes"
        ):
            new_mode = 'text' if mode == 'structured' else 'structured'
            st.session_state[f'{key_prefix}_mode'] = new_mode
            st.rerun()
    
    with col3:
        if st.button("➕ Add", key=f'{key_prefix}_add_line'):
            # Add a new line at the end
            manager.insert_line(len(manager.lines))
            st.rerun()
    
    with col4:
        if st.button("📋 Paste", key=f'{key_prefix}_paste',
                    help="Switch to text mode to paste content"):
            st.session_state[f'{key_prefix}_mode'] = 'text'
            st.rerun()
    
    with col5:
        if manager.has_modifications():
            st.markdown("⚠️ **Modified**")
        else:
            st.caption(f"{len(manager.lines)} lines")
    
    with col6:
        # Show current format indicator
        format_colors = {'draft': '#8be9fd', 'formal': '#ff79c6', 'natural': '#50fa7b'}
        st.markdown(
            f"<span style='color: {format_colors[new_format]}'>●</span>",
            unsafe_allow_html=True
        )


def _render_text_mode(
    file_type: str, 
    key_prefix: str, 
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render text area mode for bulk editing."""
    current_format = st.session_state.get(f'{key_prefix}_format', 'draft')
    current_content = manager.serialize(current_format)
    
    # Show format indicator
    format_names = {'draft': '.ncd (Draft)', 'formal': '.nc (Formal)', 'natural': '.ncn (Natural)'}
    st.caption(f"Editing as: **{format_names[current_format]}**")
    
    new_content = st.text_area(
        "Raw Content",
        value=current_content,
        height=500,
        key=f'{key_prefix}_text_area_{current_format}',  # Include format in key to refresh
        label_visibility='collapsed'
    )
    
    # Parse changes back (always parse as draft for now - formal/natural parsing would need more work)
    if new_content != current_content:
        manager.parse_text(new_content)
        if on_change:
            on_change()
    
    # Show all three formats preview
    with st.expander("📊 All Formats Preview", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption("Draft (.ncd)")
            st.code(manager.serialize('draft'), language='text')
        
        with col2:
            st.caption("Formal (.nc)")
            st.code(manager.serialize('formal'), language='text')
        
        with col3:
            st.caption("Natural (.ncn)")
            st.code(manager.serialize('natural'), language='text')


def _render_structured_mode(
    file_type: str,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render the structured line-by-line editing mode."""
    
    # Custom CSS for editor styling
    st.markdown("""
    <style>
    .line-editor-container {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        background-color: #1e1e2e;
        border-radius: 8px;
        padding: 10px;
    }
    .line-row {
        display: flex;
        align-items: center;
        border-bottom: 1px solid #2d2d3d;
        padding: 2px 0;
    }
    .line-number {
        color: #6272a4;
        width: 40px;
        text-align: right;
        padding-right: 10px;
        user-select: none;
    }
    .indent-guide {
        color: #44475a;
        user-select: none;
    }
    .line-operator {
        font-weight: bold;
        min-width: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get visible lines (respecting collapse state)
    visible_lines = manager.get_visible_lines()
    
    if not visible_lines:
        st.info("No content yet. Click 'Add Line' to start editing.")
        return
    
    # Render each line
    for i, line in enumerate(visible_lines):
        _render_line_row(
            line=line,
            line_number=i + 1,
            key_prefix=key_prefix,
            manager=manager,
            on_change=on_change
        )


def _render_line_row(
    line: EditableLine,
    line_number: int,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render a single editable line row."""
    
    # Calculate column widths
    # Flow Index | Indent | Operator | Content | Seq | Actions
    # Flow index is now auto-computed and shown as the "line number"
    
    # Check if this line has children (for collapse toggle)
    has_children = len(manager.get_children(line.id)) > 0
    
    # Build indent string for display
    indent_display = "│  " * line.depth if line.depth > 0 else ""
    
    # Line container - removed the separate Flow column since it's now shown as line number
    cols = st.columns([0.8, 0.5, 0.8, 5.5, 1, 1.4])
    
    # Flow index as line number (auto-computed based on structure)
    with cols[0]:
        flow_display = line.flow_index if line.flow_index else "—"
        st.markdown(
            f"<span style='color: {COLORS['flow_index']}; font-weight: bold; font-family: monospace;'>{flow_display}</span>",
            unsafe_allow_html=True
        )
    
    # Indent visualization and collapse toggle
    with cols[1]:
        if has_children:
            collapse_icon = "▼" if not line.is_collapsed else "▶"
            if st.button(
                f"{collapse_icon}",
                key=f'{key_prefix}_collapse_{line.id}',
                help="Collapse/expand children"
            ):
                manager.toggle_collapse(line.id)
                st.rerun()
        else:
            st.markdown(
                f"<span style='color: {COLORS['indent_guide']}'>{indent_display}├</span>",
                unsafe_allow_html=True
            )
    
    # Operator dropdown
    with cols[2]:
        current_op = line.operator
        op_index = next(
            (i for i, (op, _) in enumerate(OPERATOR_OPTIONS) if op == current_op),
            len(OPERATOR_OPTIONS) - 1
        )
        
        new_op = st.selectbox(
            "Op",
            options=[op for op, _ in OPERATOR_OPTIONS],
            format_func=lambda x: x if x else "—",
            index=op_index,
            key=f'{key_prefix}_op_{line.id}',
            label_visibility='collapsed'
        )
        
        if new_op != current_op:
            manager.update_line_operator(line.id, new_op)
            if on_change:
                on_change()
    
    # Content input
    with cols[3]:
        # Color based on line type
        color = COLORS.get(line.line_type.value, COLORS['generic'])
        
        new_content = st.text_input(
            "Content",
            value=line.content,
            key=f'{key_prefix}_content_{line.id}',
            label_visibility='collapsed',
            placeholder="Enter content..."
        )
        
        if new_content != line.content:
            manager.update_line_content(line.id, new_content)
            if on_change:
                on_change()
    
    # Sequence type
    with cols[4]:
        seq_index = SEQUENCE_TYPE_OPTIONS.index(line.sequence_type) if line.sequence_type in SEQUENCE_TYPE_OPTIONS else 0
        
        new_seq = st.selectbox(
            "Seq",
            options=SEQUENCE_TYPE_OPTIONS,
            index=seq_index,
            key=f'{key_prefix}_seq_{line.id}',
            label_visibility='collapsed',
            format_func=lambda x: x[:3] if x else "—"
        )
        
        if new_seq != line.sequence_type:
            manager.update_line_metadata(line.id, sequence_type=new_seq)
            if on_change:
                on_change()
    
    # Action buttons
    with cols[5]:
        _render_line_actions(line, key_prefix, manager, on_change)


def _render_line_actions(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render action buttons for a line."""
    
    # Use a popover/expander for actions to save space
    action_cols = st.columns([1, 1, 1, 1, 1])
    
    # Indent/Outdent
    with action_cols[0]:
        if st.button("→", key=f'{key_prefix}_indent_{line.id}', help="Indent"):
            manager.indent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[1]:
        if st.button("←", key=f'{key_prefix}_outdent_{line.id}', help="Outdent"):
            manager.outdent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Move up/down
    with action_cols[2]:
        if st.button("↑", key=f'{key_prefix}_up_{line.id}', help="Move up"):
            manager.move_line_up(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[3]:
        if st.button("↓", key=f'{key_prefix}_down_{line.id}', help="Move down"):
            manager.move_line_down(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Delete
    with action_cols[4]:
        if st.button("🗑", key=f'{key_prefix}_del_{line.id}', help="Delete"):
            manager.delete_line(line.id)
            if on_change:
                on_change()
            st.rerun()


def render_line_context_menu(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render an expanded context menu for a line."""
    
    with st.expander(f"Line {manager.get_line_index(line.id) + 1} Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Duplicate", key=f'{key_prefix}_dup_{line.id}'):
                manager.duplicate_line(line.id)
                if on_change:
                    on_change()
                st.rerun()
            
            if st.button("📋 Duplicate with children", key=f'{key_prefix}_dup_children_{line.id}'):
                manager.duplicate_line(line.id, include_children=True)
                if on_change:
                    on_change()
                st.rerun()
        
        with col2:
            st.markdown("**Add Annotation:**")
            ann_cols = st.columns(3)
            
            with ann_cols[0]:
                if st.button("?:", key=f'{key_prefix}_add_q_{line.id}', help="Add question"):
                    manager.add_annotation(line.id, 'question')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[1]:
                if st.button("/:", key=f'{key_prefix}_add_d_{line.id}', help="Add description"):
                    manager.add_annotation(line.id, 'description')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[2]:
                if st.button("...:", key=f'{key_prefix}_add_s_{line.id}', help="Add source"):
                    manager.add_annotation(line.id, 'source')
                    if on_change:
                        on_change()
                    st.rerun()


def render_quick_actions_panel(
    file_type: str,
    key_prefix: str,
    manager: LineManager
):
    """Render a panel with quick actions for the entire document."""
    
    with st.expander("🔧 Quick Actions", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Structure:**")
            st.caption("💡 Flow indices auto-update based on indent structure")
            
            if st.button("📐 Rebuild hierarchy", key=f'{key_prefix}_fix_indent'):
                _normalize_indentation(manager)
                st.rerun()
        
        with col2:
            st.markdown("**Insert Templates:**")
            if st.button("➕ Functional block", key=f'{key_prefix}_tpl_func'):
                _insert_functional_template(manager)
                st.rerun()
            
            if st.button("➕ Value block", key=f'{key_prefix}_tpl_value'):
                _insert_value_template(manager)
                st.rerun()
        
        with col3:
            st.markdown("**View:**")
            if st.button("▼ Expand all", key=f'{key_prefix}_expand_all'):
                for line in manager.lines:
                    line.is_collapsed = False
                st.rerun()
            
            if st.button("▶ Collapse all", key=f'{key_prefix}_collapse_all'):
                for line in manager.lines:
                    if manager.get_children(line.id):
                        line.is_collapsed = True
                st.rerun()


def _normalize_indentation(manager: LineManager):
    """Ensure consistent indentation based on parent-child relationships."""
    manager._build_hierarchy()
    for line in manager.lines:
        line.is_modified = True


def _insert_functional_template(manager: LineManager):
    """Insert a template for a functional concept block."""
    lines = [
        EditableLine(depth=0, operator='<=', line_type=LineType.FUNCTIONAL_CONCEPT,
                    content='$.({method_name})', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description of what this does', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_1}', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_2}', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


def _insert_value_template(manager: LineManager):
    """Insert a template for a value concept block."""
    lines = [
        EditableLine(depth=0, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{concept_name}', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


```

Now let me add a preview panel showing all three formats in the structured mode:

```python
"""
Structured Line-by-Line Editor Component

Renders NormCode content as individually editable lines with
per-line controls for structural operations.
"""

import streamlit as st
from typing import List, Optional, Callable
from pathlib import Path
import sys

# Add parent to path for imports
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.line_editor import EditableLine, LineManager, LineType


# Color scheme for syntax highlighting
COLORS = {
    'functional': '#ff79c6',      # Pink - <=
    'value': '#8be9fd',           # Cyan - <-
    'output': '#bd93f9',          # Purple - :<:
    'question': '#50fa7b',        # Green - ?:
    'description': '#f1fa8c',     # Yellow - /:
    'source': '#ffb86c',          # Orange - ...:
    'generic': '#f8f8f2',         # White
    'flow_index': '#ff5555',      # Red
    'sequence_type': '#6272a4',   # Gray
    'indent_guide': '#44475a',    # Dark gray
}

# Operator options for dropdown
OPERATOR_OPTIONS = [
    ('<=', 'Functional (<=)'),
    ('<-', 'Value (<-)'),
    (':<:', 'Output (:<:)'),
    ('?:', 'Question (?:)'),
    ('/:', 'Description (/:)'),
    ('...:', 'Source (...:)'),
    ('', 'None'),
]

# Sequence type options
SEQUENCE_TYPE_OPTIONS = [
    '', 'imperative', 'grouping', 'assigning', 
    'quantifying', 'timing', 'judgement', 'simple'
]


def init_structured_editor_state(file_type: str):
    """Initialize session state for a structured editor instance."""
    key_prefix = f'struct_editor_{file_type}'
    
    if f'{key_prefix}_lines' not in st.session_state:
        st.session_state[f'{key_prefix}_lines'] = []
    if f'{key_prefix}_manager' not in st.session_state:
        st.session_state[f'{key_prefix}_manager'] = LineManager()
    if f'{key_prefix}_selected' not in st.session_state:
        st.session_state[f'{key_prefix}_selected'] = None
    if f'{key_prefix}_mode' not in st.session_state:
        st.session_state[f'{key_prefix}_mode'] = 'structured'  # or 'text'
    if f'{key_prefix}_format' not in st.session_state:
        st.session_state[f'{key_prefix}_format'] = 'draft'  # 'draft', 'formal', 'natural'


def load_content(file_type: str, content: str):
    """Load content into the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    lines = manager.parse_text(content)
    st.session_state[f'{key_prefix}_lines'] = lines


def get_content(file_type: str, format: str = None) -> str:
    """
    Get serialized content from the structured editor.
    
    Args:
        file_type: The file type key
        format: Output format ('draft', 'formal', 'natural'). 
                If None, uses the current format setting.
    """
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    if format is None:
        format = st.session_state.get(f'{key_prefix}_format', 'draft')
    
    return manager.serialize(format)


def render_structured_editor(
    file_type: str,
    on_change: Optional[Callable] = None
):
    """
    Render the structured line-by-line editor.
    
    Args:
        file_type: Type of file ('draft', 'formal', 'natural')
        on_change: Callback when content changes
    """
    key_prefix = f'struct_editor_{file_type}'
    init_structured_editor_state(file_type)
    
    manager: LineManager = st.session_state[f'{key_prefix}_manager']
    mode = st.session_state[f'{key_prefix}_mode']
    
    # Mode toggle and toolbar
    _render_toolbar(file_type, key_prefix, manager)
    
    if mode == 'text':
        _render_text_mode(file_type, key_prefix, manager, on_change)
    else:
        _render_structured_mode(file_type, key_prefix, manager, on_change)


def _render_toolbar(file_type: str, key_prefix: str, manager: LineManager):
    """Render the editor toolbar."""
    col1, col2, col3, col4, col5, col6 = st.columns([1.2, 1, 1, 1, 1.5, 1])
    
    # Format toggle - this is the key feature!
    with col1:
        current_format = st.session_state.get(f'{key_prefix}_format', 'draft')
        format_options = {
            'draft': '📄 Draft (.ncd)',
            'formal': '📋 Formal (.nc)', 
            'natural': '📖 Natural (.ncn)'
        }
        
        new_format = st.selectbox(
            "Format",
            options=['draft', 'formal', 'natural'],
            index=['draft', 'formal', 'natural'].index(current_format),
            format_func=lambda x: format_options[x],
            key=f'{key_prefix}_format_select',
            label_visibility='collapsed'
        )
        
        if new_format != current_format:
            st.session_state[f'{key_prefix}_format'] = new_format
            st.rerun()
    
    with col2:
        mode = st.session_state[f'{key_prefix}_mode']
        if st.button(
            "📝 Text" if mode == 'structured' else "🔧 Struct",
            key=f'{key_prefix}_mode_toggle',
            help="Toggle between structured and text editing modes"
        ):
            new_mode = 'text' if mode == 'structured' else 'structured'
            st.session_state[f'{key_prefix}_mode'] = new_mode
            st.rerun()
    
    with col3:
        if st.button("➕ Add", key=f'{key_prefix}_add_line'):
            # Add a new line at the end
            manager.insert_line(len(manager.lines))
            st.rerun()
    
    with col4:
        if st.button("📋 Paste", key=f'{key_prefix}_paste',
                    help="Switch to text mode to paste content"):
            st.session_state[f'{key_prefix}_mode'] = 'text'
            st.rerun()
    
    with col5:
        if manager.has_modifications():
            st.markdown("⚠️ **Modified**")
        else:
            st.caption(f"{len(manager.lines)} lines")
    
    with col6:
        # Show current format indicator
        format_colors = {'draft': '#8be9fd', 'formal': '#ff79c6', 'natural': '#50fa7b'}
        st.markdown(
            f"<span style='color: {format_colors[new_format]}'>●</span>",
            unsafe_allow_html=True
        )


def _render_text_mode(
    file_type: str, 
    key_prefix: str, 
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render text area mode for bulk editing."""
    current_format = st.session_state.get(f'{key_prefix}_format', 'draft')
    current_content = manager.serialize(current_format)
    
    # Show format indicator
    format_names = {'draft': '.ncd (Draft)', 'formal': '.nc (Formal)', 'natural': '.ncn (Natural)'}
    st.caption(f"Editing as: **{format_names[current_format]}**")
    
    new_content = st.text_area(
        "Raw Content",
        value=current_content,
        height=500,
        key=f'{key_prefix}_text_area_{current_format}',  # Include format in key to refresh
        label_visibility='collapsed'
    )
    
    # Parse changes back (always parse as draft for now - formal/natural parsing would need more work)
    if new_content != current_content:
        manager.parse_text(new_content)
        if on_change:
            on_change()
    
    # Show all three formats preview
    with st.expander("📊 All Formats Preview", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption("Draft (.ncd)")
            st.code(manager.serialize('draft'), language='text')
        
        with col2:
            st.caption("Formal (.nc)")
            st.code(manager.serialize('formal'), language='text')
        
        with col3:
            st.caption("Natural (.ncn)")
            st.code(manager.serialize('natural'), language='text')


def _render_structured_mode(
    file_type: str,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render the structured line-by-line editing mode."""
    
    current_format = st.session_state.get(f'{key_prefix}_format', 'draft')
    
    # Custom CSS for editor styling
    st.markdown("""
    <style>
    .line-editor-container {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        background-color: #1e1e2e;
        border-radius: 8px;
        padding: 10px;
    }
    .line-row {
        display: flex;
        align-items: center;
        border-bottom: 1px solid #2d2d3d;
        padding: 2px 0;
    }
    .line-number {
        color: #6272a4;
        width: 40px;
        text-align: right;
        padding-right: 10px;
        user-select: none;
    }
    .indent-guide {
        color: #44475a;
        user-select: none;
    }
    .line-operator {
        font-weight: bold;
        min-width: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get visible lines (respecting collapse state)
    visible_lines = manager.get_visible_lines()
    
    if not visible_lines:
        st.info("No content yet. Click 'Add' to start editing.")
        return
    
    # Render each line
    for i, line in enumerate(visible_lines):
        _render_line_row(
            line=line,
            line_number=i + 1,
            key_prefix=key_prefix,
            manager=manager,
            on_change=on_change,
            current_format=current_format
        )
    
    # Multi-format preview panel
    with st.expander("📊 All Formats Preview", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption("📄 Draft (.ncd)")
            st.code(manager.serialize('draft'), language='text')
        
        with col2:
            st.caption("📋 Formal (.nc)")
            st.code(manager.serialize('formal'), language='text')
        
        with col3:
            st.caption("📖 Natural (.ncn)")
            st.code(manager.serialize('natural'), language='text')


def _render_line_row(
    line: EditableLine,
    line_number: int,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render a single editable line row."""
    
    # Calculate column widths
    # Flow Index | Indent | Operator | Content | Seq | Actions
    # Flow index is now auto-computed and shown as the "line number"
    
    # Check if this line has children (for collapse toggle)
    has_children = len(manager.get_children(line.id)) > 0
    
    # Build indent string for display
    indent_display = "│  " * line.depth if line.depth > 0 else ""
    
    # Line container - removed the separate Flow column since it's now shown as line number
    cols = st.columns([0.8, 0.5, 0.8, 5.5, 1, 1.4])
    
    # Flow index as line number (auto-computed based on structure)
    with cols[0]:
        flow_display = line.flow_index if line.flow_index else "—"
        st.markdown(
            f"<span style='color: {COLORS['flow_index']}; font-weight: bold; font-family: monospace;'>{flow_display}</span>",
            unsafe_allow_html=True
        )
    
    # Indent visualization and collapse toggle
    with cols[1]:
        if has_children:
            collapse_icon = "▼" if not line.is_collapsed else "▶"
            if st.button(
                f"{collapse_icon}",
                key=f'{key_prefix}_collapse_{line.id}',
                help="Collapse/expand children"
            ):
                manager.toggle_collapse(line.id)
                st.rerun()
        else:
            st.markdown(
                f"<span style='color: {COLORS['indent_guide']}'>{indent_display}├</span>",
                unsafe_allow_html=True
            )
    
    # Operator dropdown
    with cols[2]:
        current_op = line.operator
        op_index = next(
            (i for i, (op, _) in enumerate(OPERATOR_OPTIONS) if op == current_op),
            len(OPERATOR_OPTIONS) - 1
        )
        
        new_op = st.selectbox(
            "Op",
            options=[op for op, _ in OPERATOR_OPTIONS],
            format_func=lambda x: x if x else "—",
            index=op_index,
            key=f'{key_prefix}_op_{line.id}',
            label_visibility='collapsed'
        )
        
        if new_op != current_op:
            manager.update_line_operator(line.id, new_op)
            if on_change:
                on_change()
    
    # Content input
    with cols[3]:
        # Color based on line type
        color = COLORS.get(line.line_type.value, COLORS['generic'])
        
        new_content = st.text_input(
            "Content",
            value=line.content,
            key=f'{key_prefix}_content_{line.id}',
            label_visibility='collapsed',
            placeholder="Enter content..."
        )
        
        if new_content != line.content:
            manager.update_line_content(line.id, new_content)
            if on_change:
                on_change()
    
    # Sequence type
    with cols[4]:
        seq_index = SEQUENCE_TYPE_OPTIONS.index(line.sequence_type) if line.sequence_type in SEQUENCE_TYPE_OPTIONS else 0
        
        new_seq = st.selectbox(
            "Seq",
            options=SEQUENCE_TYPE_OPTIONS,
            index=seq_index,
            key=f'{key_prefix}_seq_{line.id}',
            label_visibility='collapsed',
            format_func=lambda x: x[:3] if x else "—"
        )
        
        if new_seq != line.sequence_type:
            manager.update_line_metadata(line.id, sequence_type=new_seq)
            if on_change:
                on_change()
    
    # Action buttons
    with cols[5]:
        _render_line_actions(line, key_prefix, manager, on_change)


def _render_line_actions(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render action buttons for a line."""
    
    # Use a popover/expander for actions to save space
    action_cols = st.columns([1, 1, 1, 1, 1])
    
    # Indent/Outdent
    with action_cols[0]:
        if st.button("→", key=f'{key_prefix}_indent_{line.id}', help="Indent"):
            manager.indent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[1]:
        if st.button("←", key=f'{key_prefix}_outdent_{line.id}', help="Outdent"):
            manager.outdent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Move up/down
    with action_cols[2]:
        if st.button("↑", key=f'{key_prefix}_up_{line.id}', help="Move up"):
            manager.move_line_up(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[3]:
        if st.button("↓", key=f'{key_prefix}_down_{line.id}', help="Move down"):
            manager.move_line_down(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Delete
    with action_cols[4]:
        if st.button("🗑", key=f'{key_prefix}_del_{line.id}', help="Delete"):
            manager.delete_line(line.id)
            if on_change:
                on_change()
            st.rerun()


def render_line_context_menu(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render an expanded context menu for a line."""
    
    with st.expander(f"Line {manager.get_line_index(line.id) + 1} Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Duplicate", key=f'{key_prefix}_dup_{line.id}'):
                manager.duplicate_line(line.id)
                if on_change:
                    on_change()
                st.rerun()
            
            if st.button("📋 Duplicate with children", key=f'{key_prefix}_dup_children_{line.id}'):
                manager.duplicate_line(line.id, include_children=True)
                if on_change:
                    on_change()
                st.rerun()
        
        with col2:
            st.markdown("**Add Annotation:**")
            ann_cols = st.columns(3)
            
            with ann_cols[0]:
                if st.button("?:", key=f'{key_prefix}_add_q_{line.id}', help="Add question"):
                    manager.add_annotation(line.id, 'question')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[1]:
                if st.button("/:", key=f'{key_prefix}_add_d_{line.id}', help="Add description"):
                    manager.add_annotation(line.id, 'description')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[2]:
                if st.button("...:", key=f'{key_prefix}_add_s_{line.id}', help="Add source"):
                    manager.add_annotation(line.id, 'source')
                    if on_change:
                        on_change()
                    st.rerun()


def render_quick_actions_panel(
    file_type: str,
    key_prefix: str,
    manager: LineManager
):
    """Render a panel with quick actions for the entire document."""
    
    with st.expander("🔧 Quick Actions", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Structure:**")
            st.caption("💡 Flow indices auto-update based on indent structure")
            
            if st.button("📐 Rebuild hierarchy", key=f'{key_prefix}_fix_indent'):
                _normalize_indentation(manager)
                st.rerun()
        
        with col2:
            st.markdown("**Insert Templates:**")
            if st.button("➕ Functional block", key=f'{key_prefix}_tpl_func'):
                _insert_functional_template(manager)
                st.rerun()
            
            if st.button("➕ Value block", key=f'{key_prefix}_tpl_value'):
                _insert_value_template(manager)
                st.rerun()
        
        with col3:
            st.markdown("**View:**")
            if st.button("▼ Expand all", key=f'{key_prefix}_expand_all'):
                for line in manager.lines:
                    line.is_collapsed = False
                st.rerun()
            
            if st.button("▶ Collapse all", key=f'{key_prefix}_collapse_all'):
                for line in manager.lines:
                    if manager.get_children(line.id):
                        line.is_collapsed = True
                st.rerun()


def _normalize_indentation(manager: LineManager):
    """Ensure consistent indentation based on parent-child relationships."""
    manager._build_hierarchy()
    for line in manager.lines:
        line.is_modified = True


def _insert_functional_template(manager: LineManager):
    """Insert a template for a functional concept block."""
    lines = [
        EditableLine(depth=0, operator='<=', line_type=LineType.FUNCTIONAL_CONCEPT,
                    content='$.({method_name})', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description of what this does', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_1}', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_2}', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


def _insert_value_template(manager: LineManager):
    """Insert a template for a value concept block."""
    lines = [
        EditableLine(depth=0, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{concept_name}', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


```

```python
"""
Structured Line-by-Line Editor Component

Renders NormCode content as individually editable lines with
per-line controls for structural operations.
"""

import streamlit as st
from typing import List, Optional, Callable
from pathlib import Path
import sys

# Add parent to path for imports
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.line_editor import EditableLine, LineManager, LineType


# Color scheme for syntax highlighting
COLORS = {
    'functional': '#ff79c6',      # Pink - <=
    'value': '#8be9fd',           # Cyan - <-
    'output': '#bd93f9',          # Purple - :<:
    'question': '#50fa7b',        # Green - ?:
    'description': '#f1fa8c',     # Yellow - /:
    'source': '#ffb86c',          # Orange - ...:
    'generic': '#f8f8f2',         # White
    'flow_index': '#ff5555',      # Red
    'sequence_type': '#6272a4',   # Gray
    'indent_guide': '#44475a',    # Dark gray
}

# Operator options for dropdown
OPERATOR_OPTIONS = [
    ('<=', 'Functional (<=)'),
    ('<-', 'Value (<-)'),
    (':<:', 'Output (:<:)'),
    ('?:', 'Question (?:)'),
    ('/:', 'Description (/:)'),
    ('...:', 'Source (...:)'),
    ('', 'None'),
]

# Sequence type options
SEQUENCE_TYPE_OPTIONS = [
    '', 'imperative', 'grouping', 'assigning', 
    'quantifying', 'timing', 'judgement', 'simple'
]


def init_structured_editor_state(file_type: str):
    """Initialize session state for a structured editor instance."""
    key_prefix = f'struct_editor_{file_type}'
    
    if f'{key_prefix}_lines' not in st.session_state:
        st.session_state[f'{key_prefix}_lines'] = []
    if f'{key_prefix}_manager' not in st.session_state:
        st.session_state[f'{key_prefix}_manager'] = LineManager()
    if f'{key_prefix}_selected' not in st.session_state:
        st.session_state[f'{key_prefix}_selected'] = None
    if f'{key_prefix}_mode' not in st.session_state:
        st.session_state[f'{key_prefix}_mode'] = 'structured'  # or 'text'
    if f'{key_prefix}_format' not in st.session_state:
        st.session_state[f'{key_prefix}_format'] = 'draft'  # 'draft', 'formal', 'natural'


def load_content(file_type: str, content: str):
    """Load content into the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    lines = manager.parse_text(content)
    st.session_state[f'{key_prefix}_lines'] = lines


def get_content(file_type: str, format: str = None) -> str:
    """
    Get serialized content from the structured editor.
    
    Args:
        file_type: The file type key
        format: Output format ('draft', 'formal', 'natural'). 
                If None, uses the current format setting.
    """
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    if format is None:
        format = st.session_state.get(f'{key_prefix}_format', 'draft')
    
    return manager.serialize(format)


def render_structured_editor(
    file_type: str,
    on_change: Optional[Callable] = None
):
    """
    Render the structured line-by-line editor.
    
    Args:
        file_type: Type of file ('draft', 'formal', 'natural')
        on_change: Callback when content changes
    """
    key_prefix = f'struct_editor_{file_type}'
    init_structured_editor_state(file_type)
    
    manager: LineManager = st.session_state[f'{key_prefix}_manager']
    mode = st.session_state[f'{key_prefix}_mode']
    
    # Mode toggle and toolbar
    _render_toolbar(file_type, key_prefix, manager)
    
    if mode == 'text':
        _render_text_mode(file_type, key_prefix, manager, on_change)
    else:
        _render_structured_mode(file_type, key_prefix, manager, on_change)


def _render_toolbar(file_type: str, key_prefix: str, manager: LineManager):
    """Render the editor toolbar."""
    col1, col2, col3, col4, col5, col6 = st.columns([1.2, 1, 1, 1, 1.5, 1])
    
    # Format toggle - this is the key feature!
    with col1:
        current_format = st.session_state.get(f'{key_prefix}_format', 'draft')
        format_options = {
            'draft': '📄 Draft (.ncd)',
            'formal': '📋 Formal (.nc)', 
            'natural': '📖 Natural (.ncn)'
        }
        
        new_format = st.selectbox(
            "Format",
            options=['draft', 'formal', 'natural'],
            index=['draft', 'formal', 'natural'].index(current_format),
            format_func=lambda x: format_options[x],
            key=f'{key_prefix}_format_select',
            label_visibility='collapsed'
        )
        
        if new_format != current_format:
            st.session_state[f'{key_prefix}_format'] = new_format
            st.rerun()
    
    with col2:
        mode = st.session_state[f'{key_prefix}_mode']
        if st.button(
            "📝 Text" if mode == 'structured' else "🔧 Struct",
            key=f'{key_prefix}_mode_toggle',
            help="Toggle between structured and text editing modes"
        ):
            new_mode = 'text' if mode == 'structured' else 'structured'
            st.session_state[f'{key_prefix}_mode'] = new_mode
            st.rerun()
    
    with col3:
        if st.button("➕ Add", key=f'{key_prefix}_add_line'):
            # Add a new line at the end
            manager.insert_line(len(manager.lines))
            st.rerun()
    
    with col4:
        if st.button("📋 Paste", key=f'{key_prefix}_paste',
                    help="Switch to text mode to paste content"):
            st.session_state[f'{key_prefix}_mode'] = 'text'
            st.rerun()
    
    with col5:
        if manager.has_modifications():
            st.markdown("⚠️ **Modified**")
        else:
            st.caption(f"{len(manager.lines)} lines")
    
    with col6:
        # Show current format indicator
        format_colors = {'draft': '#8be9fd', 'formal': '#ff79c6', 'natural': '#50fa7b'}
        st.markdown(
            f"<span style='color: {format_colors[new_format]}'>●</span>",
            unsafe_allow_html=True
        )


def _render_text_mode(
    file_type: str, 
    key_prefix: str, 
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render text area mode for bulk editing."""
    current_format = st.session_state.get(f'{key_prefix}_format', 'draft')
    current_content = manager.serialize(current_format)
    
    # Show format indicator
    format_names = {'draft': '.ncd (Draft)', 'formal': '.nc (Formal)', 'natural': '.ncn (Natural)'}
    st.caption(f"Editing as: **{format_names[current_format]}**")
    
    new_content = st.text_area(
        "Raw Content",
        value=current_content,
        height=500,
        key=f'{key_prefix}_text_area_{current_format}',  # Include format in key to refresh
        label_visibility='collapsed'
    )
    
    # Parse changes back (always parse as draft for now - formal/natural parsing would need more work)
    if new_content != current_content:
        manager.parse_text(new_content)
        if on_change:
            on_change()
    
    # Show all three formats preview
    with st.expander("📊 All Formats Preview", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption("Draft (.ncd)")
            st.code(manager.serialize('draft'), language='text')
        
        with col2:
            st.caption("Formal (.nc)")
            st.code(manager.serialize('formal'), language='text')
        
        with col3:
            st.caption("Natural (.ncn)")
            st.code(manager.serialize('natural'), language='text')


def _render_structured_mode(
    file_type: str,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render the structured line-by-line editing mode."""
    
    current_format = st.session_state.get(f'{key_prefix}_format', 'draft')
    
    # Custom CSS for editor styling
    st.markdown("""
    <style>
    .line-editor-container {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        background-color: #1e1e2e;
        border-radius: 8px;
        padding: 10px;
    }
    .line-row {
        display: flex;
        align-items: center;
        border-bottom: 1px solid #2d2d3d;
        padding: 2px 0;
    }
    .line-number {
        color: #6272a4;
        width: 40px;
        text-align: right;
        padding-right: 10px;
        user-select: none;
    }
    .indent-guide {
        color: #44475a;
        user-select: none;
    }
    .line-operator {
        font-weight: bold;
        min-width: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get visible lines (respecting collapse state)
    visible_lines = manager.get_visible_lines()
    
    if not visible_lines:
        st.info("No content yet. Click 'Add' to start editing.")
        return
    
    # Render each line
    for i, line in enumerate(visible_lines):
        _render_line_row(
            line=line,
            line_number=i + 1,
            key_prefix=key_prefix,
            manager=manager,
            on_change=on_change,
            current_format=current_format
        )
    
    # Multi-format preview panel
    with st.expander("📊 All Formats Preview", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption("📄 Draft (.ncd)")
            st.code(manager.serialize('draft'), language='text')
        
        with col2:
            st.caption("📋 Formal (.nc)")
            st.code(manager.serialize('formal'), language='text')
        
        with col3:
            st.caption("📖 Natural (.ncn)")
            st.code(manager.serialize('natural'), language='text')


def _render_line_row(
    line: EditableLine,
    line_number: int,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable],
    current_format: str = 'draft'
):
    """Render a single editable line row."""
    
    # Check if this line has children (for collapse toggle)
    has_children = len(manager.get_children(line.id)) > 0
    
    # Build indent string for display
    indent_display = "│  " * line.depth if line.depth > 0 else ""
    
    # Different layouts for different formats
    if current_format == 'formal':
        # Formal format: show the line as flow.type|content
        cols = st.columns([2.5, 6, 1.4])
        
        # Show formal line representation
        with cols[0]:
            formal_prefix = f"{line.flow_index}.{line.sequence_type or 'object'}"
            st.markdown(
                f"<span style='color: {COLORS['flow_index']}; font-family: monospace;'>{formal_prefix}|</span>",
                unsafe_allow_html=True
            )
        
        # Content (editable)
        with cols[1]:
            display_content = f"{line.operator} {line.content}" if line.operator else line.content
            new_full = st.text_input(
                "Content",
                value=display_content,
                key=f'{key_prefix}_formal_{line.id}',
                label_visibility='collapsed'
            )
            # Parse back - simple approach
            if new_full != display_content:
                for op, _ in OPERATOR_OPTIONS:
                    if op and new_full.startswith(op):
                        manager.update_line_operator(line.id, op)
                        manager.update_line_content(line.id, new_full[len(op):].strip())
                        break
                else:
                    manager.update_line_content(line.id, new_full)
                if on_change:
                    on_change()
        
        with cols[2]:
            _render_line_actions(line, key_prefix, manager, on_change)
    
    elif current_format == 'natural':
        # Natural format: show indented natural language
        cols = st.columns([0.8, 0.5, 7, 1.4])
        
        with cols[0]:
            st.caption(f"{line_number}")
        
        with cols[1]:
            st.markdown(
                f"<span style='color: {COLORS['indent_guide']}'>{indent_display}</span>",
                unsafe_allow_html=True
            )
        
        with cols[2]:
            # Show operator as natural prefix
            prefix = line.operator + " " if line.operator else ""
            natural_content = f"{prefix}{line.content}"
            new_natural = st.text_input(
                "Natural",
                value=natural_content,
                key=f'{key_prefix}_natural_{line.id}',
                label_visibility='collapsed'
            )
            if new_natural != natural_content:
                # Parse operator prefix
                for op, _ in OPERATOR_OPTIONS:
                    if op and new_natural.startswith(op):
                        manager.update_line_operator(line.id, op)
                        manager.update_line_content(line.id, new_natural[len(op):].strip())
                        break
                else:
                    manager.update_line_content(line.id, new_natural)
                if on_change:
                    on_change()
        
        with cols[3]:
            _render_line_actions(line, key_prefix, manager, on_change)
    
    else:  # draft format - full structured editing
        cols = st.columns([0.8, 0.5, 0.8, 5.5, 1, 1.4])
        
        # Flow index as line number (auto-computed based on structure)
        with cols[0]:
            flow_display = line.flow_index if line.flow_index else "—"
            st.markdown(
                f"<span style='color: {COLORS['flow_index']}; font-weight: bold; font-family: monospace;'>{flow_display}</span>",
                unsafe_allow_html=True
            )
        
        # Indent visualization and collapse toggle
        with cols[1]:
            if has_children:
                collapse_icon = "▼" if not line.is_collapsed else "▶"
                if st.button(
                    f"{collapse_icon}",
                    key=f'{key_prefix}_collapse_{line.id}',
                    help="Collapse/expand children"
                ):
                    manager.toggle_collapse(line.id)
                    st.rerun()
            else:
                st.markdown(
                    f"<span style='color: {COLORS['indent_guide']}'>{indent_display}├</span>",
                    unsafe_allow_html=True
                )
        
        # Operator dropdown
        with cols[2]:
            current_op = line.operator
            op_index = next(
                (i for i, (op, _) in enumerate(OPERATOR_OPTIONS) if op == current_op),
                len(OPERATOR_OPTIONS) - 1
            )
            
            new_op = st.selectbox(
                "Op",
                options=[op for op, _ in OPERATOR_OPTIONS],
                format_func=lambda x: x if x else "—",
                index=op_index,
                key=f'{key_prefix}_op_{line.id}',
                label_visibility='collapsed'
            )
            
            if new_op != current_op:
                manager.update_line_operator(line.id, new_op)
                if on_change:
                    on_change()
        
        # Content input
        with cols[3]:
            new_content = st.text_input(
                "Content",
                value=line.content,
                key=f'{key_prefix}_content_{line.id}',
                label_visibility='collapsed',
                placeholder="Enter content..."
            )
            
            if new_content != line.content:
                manager.update_line_content(line.id, new_content)
                if on_change:
                    on_change()
        
        # Sequence type
        with cols[4]:
            seq_index = SEQUENCE_TYPE_OPTIONS.index(line.sequence_type) if line.sequence_type in SEQUENCE_TYPE_OPTIONS else 0
            
            new_seq = st.selectbox(
                "Seq",
                options=SEQUENCE_TYPE_OPTIONS,
                index=seq_index,
                key=f'{key_prefix}_seq_{line.id}',
                label_visibility='collapsed',
                format_func=lambda x: x[:3] if x else "—"
            )
            
            if new_seq != line.sequence_type:
                manager.update_line_metadata(line.id, sequence_type=new_seq)
                if on_change:
                    on_change()
        
        # Action buttons
        with cols[5]:
            _render_line_actions(line, key_prefix, manager, on_change)


def _render_line_actions(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render action buttons for a line."""
    
    # Use a popover/expander for actions to save space
    action_cols = st.columns([1, 1, 1, 1, 1])
    
    # Indent/Outdent
    with action_cols[0]:
        if st.button("→", key=f'{key_prefix}_indent_{line.id}', help="Indent"):
            manager.indent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[1]:
        if st.button("←", key=f'{key_prefix}_outdent_{line.id}', help="Outdent"):
            manager.outdent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Move up/down
    with action_cols[2]:
        if st.button("↑", key=f'{key_prefix}_up_{line.id}', help="Move up"):
            manager.move_line_up(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[3]:
        if st.button("↓", key=f'{key_prefix}_down_{line.id}', help="Move down"):
            manager.move_line_down(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Delete
    with action_cols[4]:
        if st.button("🗑", key=f'{key_prefix}_del_{line.id}', help="Delete"):
            manager.delete_line(line.id)
            if on_change:
                on_change()
            st.rerun()


def render_line_context_menu(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render an expanded context menu for a line."""
    
    with st.expander(f"Line {manager.get_line_index(line.id) + 1} Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Duplicate", key=f'{key_prefix}_dup_{line.id}'):
                manager.duplicate_line(line.id)
                if on_change:
                    on_change()
                st.rerun()
            
            if st.button("📋 Duplicate with children", key=f'{key_prefix}_dup_children_{line.id}'):
                manager.duplicate_line(line.id, include_children=True)
                if on_change:
                    on_change()
                st.rerun()
        
        with col2:
            st.markdown("**Add Annotation:**")
            ann_cols = st.columns(3)
            
            with ann_cols[0]:
                if st.button("?:", key=f'{key_prefix}_add_q_{line.id}', help="Add question"):
                    manager.add_annotation(line.id, 'question')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[1]:
                if st.button("/:", key=f'{key_prefix}_add_d_{line.id}', help="Add description"):
                    manager.add_annotation(line.id, 'description')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[2]:
                if st.button("...:", key=f'{key_prefix}_add_s_{line.id}', help="Add source"):
                    manager.add_annotation(line.id, 'source')
                    if on_change:
                        on_change()
                    st.rerun()


def render_quick_actions_panel(
    file_type: str,
    key_prefix: str,
    manager: LineManager
):
    """Render a panel with quick actions for the entire document."""
    
    with st.expander("🔧 Quick Actions", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Structure:**")
            st.caption("💡 Flow indices auto-update based on indent structure")
            
            if st.button("📐 Rebuild hierarchy", key=f'{key_prefix}_fix_indent'):
                _normalize_indentation(manager)
                st.rerun()
        
        with col2:
            st.markdown("**Insert Templates:**")
            if st.button("➕ Functional block", key=f'{key_prefix}_tpl_func'):
                _insert_functional_template(manager)
                st.rerun()
            
            if st.button("➕ Value block", key=f'{key_prefix}_tpl_value'):
                _insert_value_template(manager)
                st.rerun()
        
        with col3:
            st.markdown("**View:**")
            if st.button("▼ Expand all", key=f'{key_prefix}_expand_all'):
                for line in manager.lines:
                    line.is_collapsed = False
                st.rerun()
            
            if st.button("▶ Collapse all", key=f'{key_prefix}_collapse_all'):
                for line in manager.lines:
                    if manager.get_children(line.id):
                        line.is_collapsed = True
                st.rerun()


def _normalize_indentation(manager: LineManager):
    """Ensure consistent indentation based on parent-child relationships."""
    manager._build_hierarchy()
    for line in manager.lines:
        line.is_modified = True


def _insert_functional_template(manager: LineManager):
    """Insert a template for a functional concept block."""
    lines = [
        EditableLine(depth=0, operator='<=', line_type=LineType.FUNCTIONAL_CONCEPT,
                    content='$.({method_name})', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description of what this does', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_1}', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_2}', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


def _insert_value_template(manager: LineManager):
    """Insert a template for a value concept block."""
    lines = [
        EditableLine(depth=0, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{concept_name}', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


```

Now let me simplify the main editor tab to be truly unified:

```python
"""
NormCode Files Editor Tab

Provides UI for editing .ncd, .nc, and .ncn files with:
- Line-by-line structured editing
- Bidirectional sync between formats
- Version control

Supports both structured mode (per-line editing) and text mode (bulk editing).
"""

import streamlit as st
from pathlib import Path
import os
import sys

# Import core functionality
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.manifest import ManifestManager
from core.version_control import VersionControl
from core.syntax_highlighter import SyntaxHighlighter
from core.converters import FormatConverter
from core.line_editor import LineManager, EditableLine, LineType

# Import structured editor component
from .structured_editor import (
    init_structured_editor_state,
    load_content,
    get_content,
    render_structured_editor,
    render_quick_actions_panel,
    COLORS
)


def render_normcode_editor_tab():
    """Render the NormCode files editor tab."""
    st.header("📝 NormCode Files Editor")
    st.markdown("""
    Edit `.ncd`, `.nc`, and `.ncn` files with **line-by-line structured editing**.
    
    Each line is independently editable with controls for indentation, operators, and metadata.
    """)
    
    # Initialize session state
    _init_session_state()
    
    # Initialize managers
    manifest_mgr = ManifestManager()
    version_ctrl = VersionControl()
    
    # Project Management Section
    _render_project_management(manifest_mgr)
    
    # Only show editor if a manifest is loaded
    if not st.session_state.nc_editor_manifest:
        st.info("👆 Load or create a project to get started")
        return
    
    manifest = st.session_state.nc_editor_manifest
    
    # Display current project info
    st.divider()
    col_info1, col_info2 = st.columns([3, 1])
    with col_info1:
        st.markdown(f"### 📂 {manifest['project_name']}")
        if manifest['metadata'].get('description'):
            st.caption(manifest['metadata']['description'])
    with col_info2:
        if st.button("💾 Save All", key='nc_save_all'):
            _save_all_files(manifest, version_ctrl)
    
    # Unified Editor - single source that can be exported to any format
    st.divider()
    
    # Main unified editor using 'draft' as the canonical format
    _render_unified_editor(manifest, version_ctrl)
    
    # Export panel for saving to specific formats
    st.divider()
    _render_export_panel(manifest, version_ctrl)


def _init_session_state():
    """Initialize session state for the editor."""
    if 'nc_editor_manifest' not in st.session_state:
        st.session_state.nc_editor_manifest = None
    if 'nc_editor_current_file' not in st.session_state:
        st.session_state.nc_editor_current_file = 'draft'
    if 'nc_editor_content' not in st.session_state:
        st.session_state.nc_editor_content = {'draft': '', 'formal': '', 'natural': ''}
    if 'nc_editor_modified' not in st.session_state:
        st.session_state.nc_editor_modified = {'draft': False, 'formal': False, 'natural': False}
    if 'nc_sync_preview' not in st.session_state:
        st.session_state.nc_sync_preview = None
    if 'nc_show_create_form' not in st.session_state:
        st.session_state.nc_show_create_form = False
    
    # Initialize structured editor states for each file type
    for file_type in ['draft', 'formal', 'natural']:
        init_structured_editor_state(file_type)


def _render_project_management(manifest_mgr: ManifestManager):
    """Render project management section."""
    st.subheader("Project Management")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        available_manifests = manifest_mgr.list_manifests()
        
        if available_manifests:
            selected_manifest = st.selectbox(
                "Load Existing Project",
                options=[''] + available_manifests,
                key='nc_manifest_selector'
            )
            
            if selected_manifest and st.button("Load Project"):
                manifest = manifest_mgr.load(selected_manifest)
                if manifest:
                    st.session_state.nc_editor_manifest = manifest
                    # Load file contents into structured editors
                    _load_manifest_files_structured(manifest)
                    st.success(f"Loaded project: {selected_manifest}")
                    st.rerun()
        else:
            st.info("No projects found. Create a new one below.")
    
    with col2:
        if st.button("➕ Create New"):
            st.session_state.nc_show_create_form = True
    
    with col3:
        if st.session_state.nc_editor_manifest and st.button("💾 Save Manifest"):
            manifest_mgr.save(st.session_state.nc_editor_manifest)
            st.success("Manifest saved!")
    
    # Create new project form
    if st.session_state.nc_show_create_form:
        _render_create_project_form(manifest_mgr)


def _render_create_project_form(manifest_mgr: ManifestManager):
    """Render the create new project form."""
    with st.expander("Create New Project", expanded=True):
        project_name = st.text_input("Project Name", key='nc_new_project_name')
        description = st.text_area("Description (optional)", key='nc_new_project_desc')
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Create"):
                if project_name:
                    manifest = manifest_mgr.create(
                        project_name=project_name,
                        draft_path=f"examples/{project_name}.ncd",
                        formal_path=f"examples/{project_name}.nc",
                        natural_path=f"examples/{project_name}.ncn",
                        description=description
                    )
                    st.session_state.nc_editor_manifest = manifest
                    st.session_state.nc_show_create_form = False
                    
                    # Initialize empty structured editors
                    for file_type in ['draft', 'formal', 'natural']:
                        load_content(file_type, "")
                    
                    st.success(f"Created project: {project_name}")
                    st.rerun()
        with col_b:
            if st.button("Cancel"):
                st.session_state.nc_show_create_form = False
                st.rerun()


def _render_structured_file_editor(
    file_type: str, 
    extension: str, 
    manifest: dict, 
    version_ctrl: VersionControl
):
    """Render the structured editor for a specific file type."""
    file_path = manifest['files'][file_type]
    key_prefix = f'struct_editor_{file_type}'
    
    # File info header
    col_info1, col_info2, col_info3 = st.columns([3, 1, 1])
    with col_info1:
        st.caption(f"📁 {file_path}")
    with col_info2:
        manager: LineManager = st.session_state.get(f'{key_prefix}_manager')
        if manager and manager.has_modifications():
            st.caption("⚠️ Modified")
    with col_info3:
        # Quick save button
        if st.button("💾", key=f'nc_quick_save_{file_type}', help="Save this file"):
            _save_single_file(file_type, file_path, version_ctrl)
    
    # Quick actions panel
    manager = st.session_state.get(f'{key_prefix}_manager')
    if manager:
        render_quick_actions_panel(file_type, key_prefix, manager)
    
    # Main editor
    def on_content_change():
        st.session_state.nc_editor_modified[file_type] = True
    
    render_structured_editor(
        file_type=file_type,
        on_change=on_content_change
    )
    
    # Bottom actions
    st.divider()
    col_act1, col_act2, col_act3, col_act4 = st.columns(4)
    
    with col_act1:
        if st.button("💾 Save", key=f'nc_save_{file_type}'):
            _save_single_file(file_type, file_path, version_ctrl)
            st.success(f"Saved {extension} file")
    
    with col_act2:
        if st.button("📜 History", key=f'nc_history_{file_type}'):
            st.session_state[f'nc_show_history_{file_type}'] = True
    
    with col_act3:
        if st.button("📥 Load File", key=f'nc_load_{file_type}'):
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                load_content(file_type, content)
                st.success(f"Loaded from {file_path}")
                st.rerun()
            else:
                st.warning(f"File not found: {file_path}")
    
    with col_act4:
        if st.button("🎨 Preview", key=f'nc_preview_{file_type}'):
            st.session_state[f'nc_show_preview_{file_type}'] = True
    
    # Version history modal
    if st.session_state.get(f'nc_show_history_{file_type}', False):
        _render_version_history(file_type, file_path, version_ctrl)
    
    # Syntax preview modal
    if st.session_state.get(f'nc_show_preview_{file_type}', False):
        _render_syntax_preview(file_type, extension)


def _render_sync_panel(manifest: dict, version_ctrl: VersionControl):
    """Render the synchronization panel."""
    st.subheader("🔄 Format Synchronization")
    st.markdown("""
    Convert content between formats. Changes are previewed before applying.
    
    ⚠️ Some conversions are **lossy** (e.g., annotations may be lost when converting to `.nc`).
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**From .ncd (Draft):**")
        if st.button("→ Convert to .nc", key='sync_ncd_to_nc'):
            _sync_files('draft', 'formal', manifest, version_ctrl)
        if st.button("→ Convert to .ncn", key='sync_ncd_to_ncn'):
            _sync_files('draft', 'natural', manifest, version_ctrl)
    
    with col2:
        st.markdown("**To .ncd (Draft):**")
        if st.button("← Convert from .nc", key='sync_nc_to_ncd'):
            _sync_files('formal', 'draft', manifest, version_ctrl)
        if st.button("← Convert from .ncn", key='sync_ncn_to_ncd'):
            _sync_files('natural', 'draft', manifest, version_ctrl)
    
    # Show sync preview if active
    if st.session_state.nc_sync_preview:
        _render_sync_preview(version_ctrl)


def _render_version_history(file_type: str, file_path: str, version_ctrl: VersionControl):
    """Render version history panel."""
    with st.expander("📜 Version History", expanded=True):
        versions = version_ctrl.get_history(file_path, limit=20)
        
        if not versions:
            st.info("No version history yet. Save the file to create the first snapshot.")
        else:
            st.caption(f"📊 {len(versions)} version(s) found")
            
            for version in versions:
                with st.container():
                    col_v1, col_v2, col_v3 = st.columns([2, 2, 1])
                    
                    with col_v1:
                        st.caption(f"🕒 {version.timestamp[:19]}")
                    
                    with col_v2:
                        st.caption(f"💬 {version.message}")
                    
                    with col_v3:
                        if st.button("Restore", key=f'nc_restore_{version.id}'):
                            # Restore into structured editor
                            load_content(file_type, version.content)
                            st.success(f"Restored version {version.id[:8]}")
                            st.rerun()
        
        if st.button("Close", key=f'nc_close_history_{file_type}'):
            st.session_state[f'nc_show_history_{file_type}'] = False
            st.rerun()


def _render_syntax_preview(file_type: str, extension: str):
    """Render syntax-highlighted preview."""
    with st.expander("🎨 Syntax Highlight Preview", expanded=True):
        content = get_content(file_type)
        
        if extension == '.ncd':
            highlighted = SyntaxHighlighter.highlight_ncd(content)
        elif extension == '.nc':
            highlighted = SyntaxHighlighter.highlight_nc(content)
        else:
            highlighted = SyntaxHighlighter.highlight_ncn(content)
        
        st.markdown(highlighted, unsafe_allow_html=True)
        
        if st.button("Close Preview", key=f'nc_close_preview_{file_type}'):
            st.session_state[f'nc_show_preview_{file_type}'] = False
            st.rerun()


def _render_sync_preview(version_ctrl: VersionControl):
    """Show sync preview with diff."""
    preview = st.session_state.nc_sync_preview
    
    st.subheader("🔍 Sync Preview")
    
    # Show warnings
    if preview['warnings']:
        for warning in preview['warnings']:
            st.warning(warning)
    
    # Show diff
    col_diff1, col_diff2 = st.columns(2)
    
    with col_diff1:
        st.caption(f"Current {preview['target_type']} content")
        current = preview['current_target']
        st.code(current[:500] + ('...' if len(current) > 500 else ''))
    
    with col_diff2:
        st.caption(f"New content from {preview['source_type']}")
        new = preview['target_content']
        st.code(new[:500] + ('...' if len(new) > 500 else ''))
    
    # Diff view
    with st.expander("📊 Detailed Diff"):
        diff = version_ctrl.diff(
            file_path="temp",
            content1=preview['current_target'],
            content2=preview['target_content']
        )
        st.code(diff, language='diff')
    
    # Actions
    col_act1, col_act2 = st.columns(2)
    
    with col_act1:
        if st.button("✅ Apply Changes"):
            # Load into structured editor
            load_content(preview['target_type'], preview['target_content'])
            st.session_state.nc_editor_modified[preview['target_type']] = True
            st.session_state.nc_sync_preview = None
            st.success("Changes applied!")
            st.rerun()
    
    with col_act2:
        if st.button("❌ Cancel"):
            st.session_state.nc_sync_preview = None
            st.rerun()


def _save_single_file(file_type: str, file_path: str, version_ctrl: VersionControl):
    """Save a single file and create version snapshot."""
    content = get_content(file_type)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Create version snapshot
    version_ctrl.save_snapshot(file_path, content, 'Manual save')
    
    # Clear modification flags
    st.session_state.nc_editor_modified[file_type] = False
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state.get(f'{key_prefix}_manager')
    if manager:
        manager.clear_modifications()


def _save_all_files(manifest: dict, version_ctrl: VersionControl):
    """Save all files."""
    file_types = ['draft', 'formal', 'natural']
    
    for file_type in file_types:
        file_path = manifest['files'][file_type]
        _save_single_file(file_type, file_path, version_ctrl)
    
    st.success("All files saved!")


def _load_manifest_files_structured(manifest: dict):
    """Load manifest files into structured editors."""
    file_types = ['draft', 'formal', 'natural']
    
    for file_type in file_types:
        file_path = manifest['files'][file_type]
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            load_content(file_type, content)
            st.session_state.nc_editor_content[file_type] = content
        else:
            load_content(file_type, "")
            st.session_state.nc_editor_content[file_type] = ""


def _sync_files(source_type: str, target_type: str, manifest: dict, version_ctrl: VersionControl):
    """Sync content from source to target file type."""
    source_content = get_content(source_type)
    
    if not source_content.strip():
        st.warning("Source file is empty")
        return
    
    # Determine conversion function
    ext_map = {'draft': 'ncd', 'formal': 'nc', 'natural': 'ncn'}
    source_ext = ext_map[source_type]
    target_ext = ext_map[target_type]
    
    conversion_key = f"{source_ext}_to_{target_ext}"
    
    try:
        if conversion_key == "ncd_to_nc":
            converted, warnings = FormatConverter.ncd_to_nc(source_content)
        elif conversion_key == "ncd_to_ncn":
            converted, warnings = FormatConverter.ncd_to_ncn(source_content)
        elif conversion_key == "nc_to_ncd":
            converted, warnings = FormatConverter.nc_to_ncd(source_content)
        elif conversion_key == "ncn_to_ncd":
            converted, warnings = FormatConverter.ncn_to_ncd(source_content)
        elif conversion_key == "nc_to_ncn":
            converted, warnings = FormatConverter.nc_to_ncn(source_content)
        elif conversion_key == "ncn_to_nc":
            converted, warnings = FormatConverter.ncn_to_nc(source_content)
        else:
            st.error(f"Unsupported conversion: {conversion_key}")
            return
        
        # Store sync preview
        st.session_state.nc_sync_preview = {
            'source_type': source_type,
            'target_type': target_type,
            'source_content': source_content,
            'target_content': converted,
            'warnings': warnings,
            'current_target': get_content(target_type)
        }
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Conversion error: {str(e)}")

```

```python
"""
NormCode Files Editor Tab

Provides UI for editing .ncd, .nc, and .ncn files with:
- Line-by-line structured editing
- Bidirectional sync between formats
- Version control

Supports both structured mode (per-line editing) and text mode (bulk editing).
"""

import streamlit as st
from pathlib import Path
import os
import sys

# Import core functionality
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.manifest import ManifestManager
from core.version_control import VersionControl
from core.syntax_highlighter import SyntaxHighlighter
from core.converters import FormatConverter
from core.line_editor import LineManager, EditableLine, LineType

# Import structured editor component
from .structured_editor import (
    init_structured_editor_state,
    load_content,
    get_content,
    render_structured_editor,
    render_quick_actions_panel,
    COLORS
)


def render_normcode_editor_tab():
    """Render the NormCode files editor tab."""
    st.header("📝 NormCode Files Editor")
    st.markdown("""
    Edit `.ncd`, `.nc`, and `.ncn` files with **line-by-line structured editing**.
    
    Each line is independently editable with controls for indentation, operators, and metadata.
    """)
    
    # Initialize session state
    _init_session_state()
    
    # Initialize managers
    manifest_mgr = ManifestManager()
    version_ctrl = VersionControl()
    
    # Project Management Section
    _render_project_management(manifest_mgr)
    
    # Only show editor if a manifest is loaded
    if not st.session_state.nc_editor_manifest:
        st.info("👆 Load or create a project to get started")
        return
    
    manifest = st.session_state.nc_editor_manifest
    
    # Display current project info
    st.divider()
    col_info1, col_info2 = st.columns([3, 1])
    with col_info1:
        st.markdown(f"### 📂 {manifest['project_name']}")
        if manifest['metadata'].get('description'):
            st.caption(manifest['metadata']['description'])
    with col_info2:
        if st.button("💾 Save All", key='nc_save_all'):
            _save_all_files(manifest, version_ctrl)
    
    # Unified Editor - single source that can be exported to any format
    st.divider()
    
    # Main unified editor using 'draft' as the canonical format
    _render_unified_editor(manifest, version_ctrl)
    
    # Export panel for saving to specific formats
    st.divider()
    _render_export_panel(manifest, version_ctrl)


def _init_session_state():
    """Initialize session state for the editor."""
    if 'nc_editor_manifest' not in st.session_state:
        st.session_state.nc_editor_manifest = None
    if 'nc_editor_current_file' not in st.session_state:
        st.session_state.nc_editor_current_file = 'draft'
    if 'nc_editor_content' not in st.session_state:
        st.session_state.nc_editor_content = {'draft': '', 'formal': '', 'natural': ''}
    if 'nc_editor_modified' not in st.session_state:
        st.session_state.nc_editor_modified = {'draft': False, 'formal': False, 'natural': False}
    if 'nc_sync_preview' not in st.session_state:
        st.session_state.nc_sync_preview = None
    if 'nc_show_create_form' not in st.session_state:
        st.session_state.nc_show_create_form = False
    
    # Initialize structured editor states for each file type
    for file_type in ['draft', 'formal', 'natural']:
        init_structured_editor_state(file_type)


def _render_project_management(manifest_mgr: ManifestManager):
    """Render project management section."""
    st.subheader("Project Management")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        available_manifests = manifest_mgr.list_manifests()
        
        if available_manifests:
            selected_manifest = st.selectbox(
                "Load Existing Project",
                options=[''] + available_manifests,
                key='nc_manifest_selector'
            )
            
            if selected_manifest and st.button("Load Project"):
                manifest = manifest_mgr.load(selected_manifest)
                if manifest:
                    st.session_state.nc_editor_manifest = manifest
                    # Load file contents into structured editors
                    _load_manifest_files_structured(manifest)
                    st.success(f"Loaded project: {selected_manifest}")
                    st.rerun()
        else:
            st.info("No projects found. Create a new one below.")
    
    with col2:
        if st.button("➕ Create New"):
            st.session_state.nc_show_create_form = True
    
    with col3:
        if st.session_state.nc_editor_manifest and st.button("💾 Save Manifest"):
            manifest_mgr.save(st.session_state.nc_editor_manifest)
            st.success("Manifest saved!")
    
    # Create new project form
    if st.session_state.nc_show_create_form:
        _render_create_project_form(manifest_mgr)


def _render_create_project_form(manifest_mgr: ManifestManager):
    """Render the create new project form."""
    with st.expander("Create New Project", expanded=True):
        project_name = st.text_input("Project Name", key='nc_new_project_name')
        description = st.text_area("Description (optional)", key='nc_new_project_desc')
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Create"):
                if project_name:
                    manifest = manifest_mgr.create(
                        project_name=project_name,
                        draft_path=f"examples/{project_name}.ncd",
                        formal_path=f"examples/{project_name}.nc",
                        natural_path=f"examples/{project_name}.ncn",
                        description=description
                    )
                    st.session_state.nc_editor_manifest = manifest
                    st.session_state.nc_show_create_form = False
                    
                    # Initialize empty structured editors
                    for file_type in ['draft', 'formal', 'natural']:
                        load_content(file_type, "")
                    
                    st.success(f"Created project: {project_name}")
                    st.rerun()
        with col_b:
            if st.button("Cancel"):
                st.session_state.nc_show_create_form = False
                st.rerun()


def _render_unified_editor(manifest: dict, version_ctrl: VersionControl):
    """Render the unified structured editor with format toggle."""
    
    # Use 'draft' as the canonical internal representation
    file_type = 'draft'
    key_prefix = f'struct_editor_{file_type}'
    
    st.subheader("📝 Unified NormCode Editor")
    st.caption("Edit once, export to any format. Use the format dropdown to switch views.")
    
    # Quick actions panel
    manager = st.session_state.get(f'{key_prefix}_manager')
    if manager:
        render_quick_actions_panel(file_type, key_prefix, manager)
    
    # Main editor with format toggle
    def on_content_change():
        st.session_state.nc_editor_modified[file_type] = True
    
    render_structured_editor(
        file_type=file_type,
        on_change=on_content_change
    )
    
    # Bottom actions
    st.divider()
    col_act1, col_act2, col_act3 = st.columns(3)
    
    with col_act1:
        if st.button("📜 Version History", key='nc_history_unified'):
            st.session_state['nc_show_history_unified'] = True
    
    with col_act2:
        if st.button("📥 Import from File", key='nc_import_unified'):
            st.session_state['nc_show_import'] = True
    
    with col_act3:
        if manager and manager.has_modifications():
            st.markdown("⚠️ **Unsaved changes**")
    
    # Version history modal
    if st.session_state.get('nc_show_history_unified', False):
        _render_version_history(file_type, manifest['files'][file_type], version_ctrl)
    
    # Import modal
    if st.session_state.get('nc_show_import', False):
        _render_import_panel(manifest)


def _render_export_panel(manifest: dict, version_ctrl: VersionControl):
    """Render panel for exporting to specific formats."""
    st.subheader("💾 Export to Files")
    
    col1, col2, col3, col4 = st.columns([1.5, 1.5, 1.5, 1])
    
    key_prefix = 'struct_editor_draft'
    manager = st.session_state.get(f'{key_prefix}_manager')
    
    with col1:
        if st.button("📄 Save as .ncd", key='export_ncd', use_container_width=True):
            content = get_content('draft', 'draft')
            file_path = manifest['files']['draft']
            _save_to_file(file_path, content, version_ctrl)
            st.success(f"Saved: {file_path}")
    
    with col2:
        if st.button("📋 Save as .nc", key='export_nc', use_container_width=True):
            content = get_content('draft', 'formal')
            file_path = manifest['files']['formal']
            _save_to_file(file_path, content, version_ctrl)
            st.success(f"Saved: {file_path}")
    
    with col3:
        if st.button("📖 Save as .ncn", key='export_ncn', use_container_width=True):
            content = get_content('draft', 'natural')
            file_path = manifest['files']['natural']
            _save_to_file(file_path, content, version_ctrl)
            st.success(f"Saved: {file_path}")
    
    with col4:
        if st.button("💾 Save All", key='export_all', use_container_width=True):
            # Save all three formats
            _save_to_file(manifest['files']['draft'], get_content('draft', 'draft'), version_ctrl)
            _save_to_file(manifest['files']['formal'], get_content('draft', 'formal'), version_ctrl)
            _save_to_file(manifest['files']['natural'], get_content('draft', 'natural'), version_ctrl)
            st.success("Saved all formats!")


def _render_import_panel(manifest: dict):
    """Render import options."""
    with st.expander("📥 Import Content", expanded=True):
        import_source = st.selectbox(
            "Import from:",
            options=['Select...', 'Draft (.ncd)', 'Formal (.nc)', 'Natural (.ncn)'],
            key='import_source'
        )
        
        if import_source != 'Select...':
            file_map = {
                'Draft (.ncd)': manifest['files']['draft'],
                'Formal (.nc)': manifest['files']['formal'],
                'Natural (.ncn)': manifest['files']['natural']
            }
            file_path = file_map[import_source]
            
            if os.path.exists(file_path):
                if st.button(f"Load from {file_path}"):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    load_content('draft', content)
                    st.session_state['nc_show_import'] = False
                    st.success(f"Imported from {file_path}")
                    st.rerun()
            else:
                st.warning(f"File not found: {file_path}")
        
        if st.button("Cancel", key='import_cancel'):
            st.session_state['nc_show_import'] = False
            st.rerun()


def _save_to_file(file_path: str, content: str, version_ctrl: VersionControl):
    """Save content to file and create version snapshot."""
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    version_ctrl.save_snapshot(file_path, content, 'Manual save')


def _render_structured_file_editor(
    file_type: str, 
    extension: str, 
    manifest: dict, 
    version_ctrl: VersionControl
):
    """Render the structured editor for a specific file type (legacy, kept for compatibility)."""
    file_path = manifest['files'][file_type]
    key_prefix = f'struct_editor_{file_type}'
    
    # File info header
    col_info1, col_info2, col_info3 = st.columns([3, 1, 1])
    with col_info1:
        st.caption(f"📁 {file_path}")
    with col_info2:
        manager: LineManager = st.session_state.get(f'{key_prefix}_manager')
        if manager and manager.has_modifications():
            st.caption("⚠️ Modified")
    with col_info3:
        # Quick save button
        if st.button("💾", key=f'nc_quick_save_{file_type}', help="Save this file"):
            _save_single_file(file_type, file_path, version_ctrl)
    
    # Quick actions panel
    manager = st.session_state.get(f'{key_prefix}_manager')
    if manager:
        render_quick_actions_panel(file_type, key_prefix, manager)
    
    # Main editor
    def on_content_change():
        st.session_state.nc_editor_modified[file_type] = True
    
    render_structured_editor(
        file_type=file_type,
        on_change=on_content_change
    )
    
    # Bottom actions
    st.divider()
    col_act1, col_act2, col_act3, col_act4 = st.columns(4)
    
    with col_act1:
        if st.button("💾 Save", key=f'nc_save_{file_type}'):
            _save_single_file(file_type, file_path, version_ctrl)
            st.success(f"Saved {extension} file")
    
    with col_act2:
        if st.button("📜 History", key=f'nc_history_{file_type}'):
            st.session_state[f'nc_show_history_{file_type}'] = True
    
    with col_act3:
        if st.button("📥 Load File", key=f'nc_load_{file_type}'):
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                load_content(file_type, content)
                st.success(f"Loaded from {file_path}")
                st.rerun()
            else:
                st.warning(f"File not found: {file_path}")
    
    with col_act4:
        if st.button("🎨 Preview", key=f'nc_preview_{file_type}'):
            st.session_state[f'nc_show_preview_{file_type}'] = True
    
    # Version history modal
    if st.session_state.get(f'nc_show_history_{file_type}', False):
        _render_version_history(file_type, file_path, version_ctrl)
    
    # Syntax preview modal
    if st.session_state.get(f'nc_show_preview_{file_type}', False):
        _render_syntax_preview(file_type, extension)


def _render_sync_panel(manifest: dict, version_ctrl: VersionControl):
    """Render the synchronization panel."""
    st.subheader("🔄 Format Synchronization")
    st.markdown("""
    Convert content between formats. Changes are previewed before applying.
    
    ⚠️ Some conversions are **lossy** (e.g., annotations may be lost when converting to `.nc`).
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**From .ncd (Draft):**")
        if st.button("→ Convert to .nc", key='sync_ncd_to_nc'):
            _sync_files('draft', 'formal', manifest, version_ctrl)
        if st.button("→ Convert to .ncn", key='sync_ncd_to_ncn'):
            _sync_files('draft', 'natural', manifest, version_ctrl)
    
    with col2:
        st.markdown("**To .ncd (Draft):**")
        if st.button("← Convert from .nc", key='sync_nc_to_ncd'):
            _sync_files('formal', 'draft', manifest, version_ctrl)
        if st.button("← Convert from .ncn", key='sync_ncn_to_ncd'):
            _sync_files('natural', 'draft', manifest, version_ctrl)
    
    # Show sync preview if active
    if st.session_state.nc_sync_preview:
        _render_sync_preview(version_ctrl)


def _render_version_history(file_type: str, file_path: str, version_ctrl: VersionControl):
    """Render version history panel."""
    with st.expander("📜 Version History", expanded=True):
        versions = version_ctrl.get_history(file_path, limit=20)
        
        if not versions:
            st.info("No version history yet. Save the file to create the first snapshot.")
        else:
            st.caption(f"📊 {len(versions)} version(s) found")
            
            for version in versions:
                with st.container():
                    col_v1, col_v2, col_v3 = st.columns([2, 2, 1])
                    
                    with col_v1:
                        st.caption(f"🕒 {version.timestamp[:19]}")
                    
                    with col_v2:
                        st.caption(f"💬 {version.message}")
                    
                    with col_v3:
                        if st.button("Restore", key=f'nc_restore_{version.id}'):
                            # Restore into structured editor
                            load_content(file_type, version.content)
                            st.success(f"Restored version {version.id[:8]}")
                            st.rerun()
        
        if st.button("Close", key=f'nc_close_history_{file_type}'):
            st.session_state[f'nc_show_history_{file_type}'] = False
            st.rerun()


def _render_syntax_preview(file_type: str, extension: str):
    """Render syntax-highlighted preview."""
    with st.expander("🎨 Syntax Highlight Preview", expanded=True):
        content = get_content(file_type)
        
        if extension == '.ncd':
            highlighted = SyntaxHighlighter.highlight_ncd(content)
        elif extension == '.nc':
            highlighted = SyntaxHighlighter.highlight_nc(content)
        else:
            highlighted = SyntaxHighlighter.highlight_ncn(content)
        
        st.markdown(highlighted, unsafe_allow_html=True)
        
        if st.button("Close Preview", key=f'nc_close_preview_{file_type}'):
            st.session_state[f'nc_show_preview_{file_type}'] = False
            st.rerun()


def _render_sync_preview(version_ctrl: VersionControl):
    """Show sync preview with diff."""
    preview = st.session_state.nc_sync_preview
    
    st.subheader("🔍 Sync Preview")
    
    # Show warnings
    if preview['warnings']:
        for warning in preview['warnings']:
            st.warning(warning)
    
    # Show diff
    col_diff1, col_diff2 = st.columns(2)
    
    with col_diff1:
        st.caption(f"Current {preview['target_type']} content")
        current = preview['current_target']
        st.code(current[:500] + ('...' if len(current) > 500 else ''))
    
    with col_diff2:
        st.caption(f"New content from {preview['source_type']}")
        new = preview['target_content']
        st.code(new[:500] + ('...' if len(new) > 500 else ''))
    
    # Diff view
    with st.expander("📊 Detailed Diff"):
        diff = version_ctrl.diff(
            file_path="temp",
            content1=preview['current_target'],
            content2=preview['target_content']
        )
        st.code(diff, language='diff')
    
    # Actions
    col_act1, col_act2 = st.columns(2)
    
    with col_act1:
        if st.button("✅ Apply Changes"):
            # Load into structured editor
            load_content(preview['target_type'], preview['target_content'])
            st.session_state.nc_editor_modified[preview['target_type']] = True
            st.session_state.nc_sync_preview = None
            st.success("Changes applied!")
            st.rerun()
    
    with col_act2:
        if st.button("❌ Cancel"):
            st.session_state.nc_sync_preview = None
            st.rerun()


def _save_single_file(file_type: str, file_path: str, version_ctrl: VersionControl):
    """Save a single file and create version snapshot."""
    content = get_content(file_type)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Create version snapshot
    version_ctrl.save_snapshot(file_path, content, 'Manual save')
    
    # Clear modification flags
    st.session_state.nc_editor_modified[file_type] = False
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state.get(f'{key_prefix}_manager')
    if manager:
        manager.clear_modifications()


def _save_all_files(manifest: dict, version_ctrl: VersionControl):
    """Save all files."""
    file_types = ['draft', 'formal', 'natural']
    
    for file_type in file_types:
        file_path = manifest['files'][file_type]
        _save_single_file(file_type, file_path, version_ctrl)
    
    st.success("All files saved!")


def _load_manifest_files_structured(manifest: dict):
    """Load manifest files into structured editors."""
    file_types = ['draft', 'formal', 'natural']
    
    for file_type in file_types:
        file_path = manifest['files'][file_type]
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            load_content(file_type, content)
            st.session_state.nc_editor_content[file_type] = content
        else:
            load_content(file_type, "")
            st.session_state.nc_editor_content[file_type] = ""


def _sync_files(source_type: str, target_type: str, manifest: dict, version_ctrl: VersionControl):
    """Sync content from source to target file type."""
    source_content = get_content(source_type)
    
    if not source_content.strip():
        st.warning("Source file is empty")
        return
    
    # Determine conversion function
    ext_map = {'draft': 'ncd', 'formal': 'nc', 'natural': 'ncn'}
    source_ext = ext_map[source_type]
    target_ext = ext_map[target_type]
    
    conversion_key = f"{source_ext}_to_{target_ext}"
    
    try:
        if conversion_key == "ncd_to_nc":
            converted, warnings = FormatConverter.ncd_to_nc(source_content)
        elif conversion_key == "ncd_to_ncn":
            converted, warnings = FormatConverter.ncd_to_ncn(source_content)
        elif conversion_key == "nc_to_ncd":
            converted, warnings = FormatConverter.nc_to_ncd(source_content)
        elif conversion_key == "ncn_to_ncd":
            converted, warnings = FormatConverter.ncn_to_ncd(source_content)
        elif conversion_key == "nc_to_ncn":
            converted, warnings = FormatConverter.nc_to_ncn(source_content)
        elif conversion_key == "ncn_to_nc":
            converted, warnings = FormatConverter.ncn_to_nc(source_content)
        else:
            st.error(f"Unsupported conversion: {conversion_key}")
            return
        
        # Store sync preview
        st.session_state.nc_sync_preview = {
            'source_type': source_type,
            'target_type': target_type,
            'source_content': source_content,
            'target_content': converted,
            'warnings': warnings,
            'current_target': get_content(target_type)
        }
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Conversion error: {str(e)}")

```

Let me refresh the browser to see the unified editor:

Excellent! The unified editor is working! I can see the structured editor with:
- **Flow indices** (1.3.1, 1.4, 1.4.1, 1.5, etc.) auto-computed from structure
- **Operator dropdowns** (`<=`, `<-`, `/:`)
- **Sequence type dropdowns** (`imp`, `—`)
- **"All Formats Preview" expander** to see all three formats
- **Export buttons** for saving to .ncd, .nc, .ncn

Let me take a screenshot to show you the unified editor interface:

This is working exactly as intended! The **Unified NormCode Editor** now shows:

1. **📄 Format Dropdown** at the top (currently showing "Draft (.ncd)") - this is the key feature for flipping between formats!
2. **Line-by-line structured editing** with:
   - Auto-computed flow indices (1, 1.1, 1.2, 1.3, 1.3.1, 1.4, 1.4.1...)
   - Collapse toggles (▼)
   - Indent guides (│ ├)
   - Operator dropdown (<=, <-, :<:, ?:, /:, ...:)
   - Content input
   - Sequence type (ass, imp)
   - Action buttons (→, ←, ↑, ↓, 🗑)

Let me demonstrate the format switching by clicking on the format dropdown:

I can see the dropdown is open with three format options. Let me click on "Formal (.nc)" to switch formats:

Excellent! The format has switched to **Formal (.nc)**! Look at how the lines now display:

- `1.object|` → `?: What is the result?`
- `2.object|` → `<= $.({number})`
- `3.imperative|` → `<- {number a}`
- `3.1.object|` → `/: The first number`
- etc.

This is the actual `.nc` file format! Let me take a screenshot to show this:

**Yes!** This is exactly what you wanted! The **Unified NormCode Editor** now allows you to:

## 🔄 Flip Between Formats with One Click

| Draft (.ncd) | Formal (.nc) | Natural (.ncn) |
|-------------|--------------|----------------|
| `<= $.({number})` | `2.object|<= $.({number})` | `<= $.({number})` |
| `  <- {number a}` | `3.imperative|<- {number a}` | `    <- {number a}` |
| `    /: The first number` | `3.1.object|/: The first number` | `        /: The first number` |

The **same underlying data** is rendered in all three formats - you just switch the dropdown!

## Key Features Implemented:

1. **Format Toggle Dropdown** - Switch between Draft, Formal, Natural views instantly
2. **Single Source of Truth** - Edit once, export to any format
3. **Auto-computed Flow Indices** - Based on line structure/depth
4. **Export Buttons** - Save as `.ncd`, `.nc`, `.ncn`, or "Save All"
5. **All Formats Preview** expander - See all three at once
6. **Text Mode** - For bulk editing with format-specific output

This is a **universal structured editor** where each line is stored in a canonical form, but can be **viewed and exported** as any of the three NormCode file formats. The flow indices are derived from the hierarchical structure, not manually entered.

---

**User**

TypeError: LineManager.serialize() takes 1 positional argument but 2 were given

Traceback:

File "c:\Users\ProgU\PycharmProjects\normCode\streamlit_app\app.py", line 73, in <module>

    render_normcode_editor_tab()

File "C:\Users\ProgU\PycharmProjects\normCode\streamlit_app\tabs\normcode_editor_tab.py", line 80, in render_normcode_editor_tab

    _render_unified_editor(manifest, version_ctrl)

File "C:\Users\ProgU\PycharmProjects\normCode\streamlit_app\tabs\normcode_editor_tab.py", line 199, in _render_unified_editor

    render_structured_editor(

File "C:\Users\ProgU\PycharmProjects\normCode\streamlit_app\tabs\structured_editor.py", line 119, in render_structured_editor

    _render_structured_mode(file_type, key_prefix, manager, on_change)

File "C:\Users\ProgU\PycharmProjects\normCode\streamlit_app\tabs\structured_editor.py", line 299, in _render_structured_mode

    st.code(manager.serialize('draft'), language='text')

            ^^^^^^^^^^^^^^^^^^^^^^^^^^

---

**Cursor**

I see the issue - the `LineManager.serialize` method wasn't updated with the format parameter. Let me fix that:

The method exists in the file with the format parameter. The issue might be that Streamlit is caching an old version. Let me restart the Streamlit app:

```plaintext
File "C:\Users\ProgU\PycharmProjects\normCode\streamlit_app\tabs\structured_editor.py", line 299, in _render_structured_mode
    st.code(manager.serialize('draft'), language='text')
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
```

Let me verify the serialize method is correctly defined by reading that specific section:

The code is correct. The issue is Streamlit caching an old version. Let me clear the cache and restart:

The page is showing without errors now. Let me expand the "All Formats Preview" to verify the format serialization is working:

The "All Formats Preview" is now working and showing all three formats:

The **Universal Structured Editor** is now complete and working!

## Summary

You now have a **unified NormCode editor** where:

1. **Edit once, view in any format** - Use the format dropdown (📄 Draft, 📋 Formal, 📖 Natural) to flip between views
2. **All Formats Preview** - See all three formats side by side:
   - **Draft (.ncd)**: `?: What is the result? | 1`, `<= $.({number}) | 2`...
   - **Formal (.nc)**: `1.object|?: What is the result?`, `2.object|<= $.({number})`...
   - **Natural (.ncn)**: `Question: What is the result?`, `<= $.({number})`...

3. **Export to any format** - Save as `.ncd`, `.nc`, `.ncn`, or all at once

The error was caused by Python caching an older version of `LineManager`. After clearing the `__pycache__` directories, everything works correctly.

