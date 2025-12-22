"""
Display Helpers Module - Pre-built components for sandbox display code.

This module provides a clean API for paradigm designers to build
interaction UIs without needing to know Streamlit internals.

Usage in display code:
    from display_helpers import display, interact
    
    display.title("Review This Code")
    display.code_block(context["code"], language="python")
    display.instruction("Please review and approve.")
    
    interact.text_editor(initial_value=context["code"], label="Edit below:")
"""

import streamlit as st
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


@dataclass
class InteractionSpec:
    """Specification for the interaction input the user needs."""
    type: str = "text_input"
    label: str = "Your response:"
    initial_value: Any = ""
    options: List[str] = field(default_factory=list)
    height: int = 150
    help_text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "label": self.label,
            "initial_value": self.initial_value,
            "options": self.options,
            "height": self.height,
            "help_text": self.help_text,
        }


class DisplayHelpers:
    """
    Pre-built display components for sandbox code.
    
    These helpers provide a clean, consistent API for common UI patterns.
    """
    
    def title(self, text: str, icon: str = ""):
        """Display a main title/header."""
        if icon:
            st.header(f"{icon} {text}")
        else:
            st.header(text)
    
    def subtitle(self, text: str):
        """Display a subtitle/subheader."""
        st.subheader(text)
    
    def text(self, content: str):
        """Display plain text or markdown."""
        st.markdown(content)
    
    def code_block(
        self, 
        code: str, 
        language: str = "python",
        title: Optional[str] = None,
        line_numbers: bool = False
    ):
        """
        Display a code block with optional title.
        
        Args:
            code: The code to display
            language: Programming language for syntax highlighting
            title: Optional title above the code block
            line_numbers: Whether to show line numbers (visual only)
        """
        if title:
            st.markdown(f"**{title}**")
        
        if line_numbers:
            lines = code.split('\n')
            numbered = '\n'.join(f"{i+1:3d} | {line}" for i, line in enumerate(lines))
            st.code(numbered, language=language)
        else:
            st.code(code, language=language)
    
    def instruction(self, text: str, type: str = "info"):
        """
        Display an instruction or message box.
        
        Args:
            text: The instruction text
            type: One of "info", "warning", "error", "success"
        """
        if type == "info":
            st.info(text)
        elif type == "warning":
            st.warning(text)
        elif type == "error":
            st.error(text)
        elif type == "success":
            st.success(text)
        else:
            st.info(text)
    
    def data_preview(
        self, 
        data: Any, 
        title: Optional[str] = None,
        format: str = "auto"
    ):
        """
        Display data in an appropriate format.
        
        Args:
            data: The data to display (dict, list, or primitive)
            title: Optional title above the data
            format: "auto", "json", "table", or "raw"
        """
        if title:
            st.markdown(f"**{title}**")
        
        if format == "json" or (format == "auto" and isinstance(data, (dict, list))):
            st.json(data)
        elif format == "table":
            st.dataframe(data)
        else:
            st.write(data)
    
    def metrics_row(self, metrics: Dict[str, Any]):
        """
        Display a row of metric cards.
        
        Args:
            metrics: Dict of {label: value} pairs
        """
        cols = st.columns(len(metrics))
        for col, (label, value) in zip(cols, metrics.items()):
            with col:
                st.metric(label, value)
    
    def divider(self):
        """Display a horizontal divider."""
        st.divider()
    
    def columns(self, contents: List[str], widths: Optional[List[int]] = None):
        """
        Display content in columns.
        
        Args:
            contents: List of markdown strings for each column
            widths: Optional list of relative widths
        """
        if widths:
            cols = st.columns(widths)
        else:
            cols = st.columns(len(contents))
        
        for col, content in zip(cols, contents):
            with col:
                st.markdown(content)
    
    def expandable(self, title: str, content: str, expanded: bool = False):
        """
        Display content in an expandable section.
        
        Args:
            title: The expander title
            content: Markdown content inside
            expanded: Whether to start expanded
        """
        with st.expander(title, expanded=expanded):
            st.markdown(content)
    
    def file_content(
        self, 
        content: str, 
        filename: str,
        language: Optional[str] = None
    ):
        """
        Display file content with filename header.
        
        Args:
            content: The file content
            filename: Name to display
            language: Language for syntax highlighting (auto-detected if None)
        """
        # Auto-detect language from extension
        if language is None:
            ext = filename.split('.')[-1] if '.' in filename else ''
            lang_map = {
                'py': 'python', 'js': 'javascript', 'ts': 'typescript',
                'json': 'json', 'md': 'markdown', 'yaml': 'yaml',
                'yml': 'yaml', 'html': 'html', 'css': 'css',
                'sql': 'sql', 'sh': 'bash', 'bash': 'bash',
            }
            language = lang_map.get(ext, 'text')
        
        st.markdown(f"📄 **`{filename}`**")
        st.code(content, language=language)


class InteractionBuilder:
    """
    Builder for specifying what interaction input is needed.
    
    The paradigm designer calls these methods to specify the input type.
    The sandbox reads the resulting spec and renders the appropriate widget.
    """
    
    def __init__(self):
        self._spec: Optional[InteractionSpec] = None
    
    def text_input(
        self, 
        label: str = "Your response:",
        initial_value: str = "",
        help_text: str = ""
    ) -> InteractionSpec:
        """Request a single-line text input."""
        self._spec = InteractionSpec(
            type="text_input",
            label=label,
            initial_value=initial_value,
            help_text=help_text
        )
        return self._spec
    
    def text_editor(
        self,
        label: str = "Edit text:",
        initial_value: str = "",
        height: int = 200,
        help_text: str = ""
    ) -> InteractionSpec:
        """Request a multi-line text editor."""
        self._spec = InteractionSpec(
            type="text_editor",
            label=label,
            initial_value=initial_value,
            height=height,
            help_text=help_text
        )
        return self._spec
    
    def confirm(
        self,
        label: str = "Please confirm:",
        help_text: str = ""
    ) -> InteractionSpec:
        """Request a yes/no confirmation."""
        self._spec = InteractionSpec(
            type="confirm",
            label=label,
            help_text=help_text
        )
        return self._spec
    
    def select(
        self,
        options: List[str],
        label: str = "Select an option:",
        help_text: str = ""
    ) -> InteractionSpec:
        """Request a selection from options."""
        self._spec = InteractionSpec(
            type="select",
            label=label,
            options=options,
            help_text=help_text
        )
        return self._spec
    
    def multi_select(
        self,
        options: List[str],
        label: str = "Select options:",
        help_text: str = ""
    ) -> InteractionSpec:
        """Request multiple selections from options."""
        self._spec = InteractionSpec(
            type="multi_select",
            label=label,
            options=options,
            help_text=help_text
        )
        return self._spec
    
    def get_spec(self) -> Optional[InteractionSpec]:
        """Get the current interaction specification."""
        return self._spec


# Singleton instances for use in display code
display = DisplayHelpers()
interact = InteractionBuilder()


# Documentation for the sandbox UI
HELPER_DOCUMENTATION = """
## Available Helpers

### Display Components (`display.*`)

| Method | Description |
|--------|-------------|
| `display.title(text, icon="")` | Main header with optional emoji icon |
| `display.subtitle(text)` | Subheader |
| `display.text(content)` | Plain text or markdown |
| `display.code_block(code, language="python", title=None)` | Syntax-highlighted code |
| `display.instruction(text, type="info")` | Message box (info/warning/error/success) |
| `display.data_preview(data, title=None, format="auto")` | Display data as JSON/table |
| `display.metrics_row({"Label": value, ...})` | Row of metric cards |
| `display.divider()` | Horizontal line |
| `display.file_content(content, filename)` | File with name header |
| `display.expandable(title, content)` | Collapsible section |

### Interaction Types (`interact.*`)

| Method | Description |
|--------|-------------|
| `interact.text_input(label, initial_value="")` | Single-line text input |
| `interact.text_editor(label, initial_value="", height=200)` | Multi-line text editor |
| `interact.confirm(label)` | Yes/No confirmation |
| `interact.select(options, label)` | Dropdown selection |
| `interact.multi_select(options, label)` | Multiple selection |

### Context Variable

The `context` dict contains data passed from the paradigm:
```python
context["title"]       # Title text
context["code"]        # Code content
context["instruction"] # Instructions
context["data"]        # Any data
```

### Constraints

❌ **Not Allowed:**
- `import` statements (use provided helpers)
- File system access
- Network requests
- Infinite loops

✅ **Allowed:**
- All `display.*` helpers
- All `interact.*` helpers  
- `context` dictionary access
- Basic Python (loops, conditionals, string formatting)
"""

QUICK_REFERENCE = """
```python
# Basic template
display.title(context.get("title", "Untitled"))
display.code_block(context["code"], language="python")
display.instruction(context["instruction"])

interact.text_input("Your feedback:")
```
"""

