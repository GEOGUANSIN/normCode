"""
Display Sandbox Tab - Testing ground for user-injected UI code.

This tab allows paradigm designers to test custom Streamlit display code
that will be executed within an interaction container. The concept is:

1. USER provides display code (the "Ground") - custom UI using helpers
2. USER specifies interaction type in the same code block
3. INFRA executes the code and renders the interaction

This gives paradigm designers maximum flexibility while keeping
the interaction flow controlled by the infrastructure.
"""

import streamlit as st
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def render_sandbox_tab():
    """Render the Display Sandbox testing tab."""
    st.header("🧪 Display Sandbox")
    st.caption("Test custom display code with integrated interaction specification")
    
    # Initialize sandbox-specific session state
    _init_sandbox_state()
    
    # Layout: Three columns - Code editor, Preview, Documentation
    col_editor, col_preview = st.columns([1, 1])
    
    with col_editor:
        _render_code_editor()
    
    with col_preview:
        _render_sandbox_preview()
    
    st.divider()
    
    # Documentation section (collapsible)
    _render_documentation()


def _init_sandbox_state():
    """Initialize session state for sandbox testing."""
    if "sandbox_display_code" not in st.session_state:
        st.session_state.sandbox_display_code = _get_default_display_code()
    
    if "sandbox_context" not in st.session_state:
        st.session_state.sandbox_context = {
            "title": "Review This Code",
            "code": "def hello():\n    print('Hello, World!')",
            "instruction": "Please review the code above and provide feedback.",
            "data": {"rows": 100, "columns": 5},
        }
    
    if "sandbox_last_response" not in st.session_state:
        st.session_state.sandbox_last_response = None
    
    if "sandbox_error" not in st.session_state:
        st.session_state.sandbox_error = None
    
    if "sandbox_interaction_spec" not in st.session_state:
        st.session_state.sandbox_interaction_spec = None


def _get_default_display_code() -> str:
    """Return default example display code using helpers."""
    return '''# Display Code - Use helpers to build your UI
# Available: display.*, interact.*, context

display.title(context.get("title", "Untitled"), icon="📝")

display.code_block(
    context["code"], 
    language="python",
    title="Code to Review"
)

display.instruction(context["instruction"])

if "data" in context:
    display.data_preview(context["data"], title="Data Summary")

display.divider()

# Specify the interaction you need
interact.text_input(
    label="Your feedback:",
    initial_value="",
    help_text="Enter your review comments"
)
'''


def _render_code_editor():
    """Render the code editor section."""
    st.subheader("📝 Display Code")
    
    # Use a version counter to force text_area to re-render when templates change
    if "sandbox_version" not in st.session_state:
        st.session_state.sandbox_version = 0
    
    # Code editor - key includes version to force refresh on template change
    new_code = st.text_area(
        "Write your display code using helpers",
        value=st.session_state.sandbox_display_code,
        height=350,
        key=f"sandbox_code_input_{st.session_state.sandbox_version}",
        help="Use display.* for UI components and interact.* to specify input type"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Run Code", use_container_width=True, type="primary"):
            st.session_state.sandbox_display_code = new_code
            st.session_state.sandbox_error = None
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.sandbox_display_code = _get_default_display_code()
            st.session_state.sandbox_context = {
                "title": "Review This Code",
                "code": "def hello():\n    print('Hello, World!')",
                "instruction": "Please review the code above and provide feedback.",
                "data": {"rows": 100, "columns": 5},
            }
            st.session_state.sandbox_last_response = None
            st.session_state.sandbox_error = None
            st.session_state.sandbox_version += 1  # Force text_area refresh
            st.rerun()
    
    # Context editor (collapsible)
    with st.expander("📦 Context Data", expanded=False):
        st.caption("Edit the context dictionary available to your code")
        import json
        try:
            context_json = json.dumps(st.session_state.sandbox_context, indent=2)
        except Exception:
            context_json = "{}"
        
        new_context_json = st.text_area(
            "Context (JSON)",
            value=context_json,
            height=150,
            key=f"sandbox_context_input_{st.session_state.sandbox_version}",
            label_visibility="collapsed"
        )
        
        if st.button("💾 Update Context", use_container_width=True):
            try:
                st.session_state.sandbox_context = json.loads(new_context_json)
                st.success("Context updated!")
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
    
    # Quick templates
    with st.expander("📚 Templates", expanded=False):
        template_col1, template_col2 = st.columns(2)
        
        with template_col1:
            if st.button("📊 Data Review", use_container_width=True):
                st.session_state.sandbox_display_code = _get_data_review_template()
                st.session_state.sandbox_context = {
                    "title": "Data Quality Review",
                    "metrics": {"Rows": 1000, "Columns": 5, "Missing": 23},
                    "sample": [[1, 2, 3], [4, 5, 6]],
                    "instruction": "Review the data and approve for processing."
                }
                st.session_state.sandbox_version += 1  # Force text_area refresh
                st.rerun()
            
            if st.button("📝 Code Editor", use_container_width=True):
                st.session_state.sandbox_display_code = _get_code_edit_template()
                st.session_state.sandbox_context = {
                    "title": "Edit Generated Code",
                    "code": "# Generated code\ndef process(x):\n    return x * 2",
                    "instruction": "Review and modify the code as needed."
                }
                st.session_state.sandbox_version += 1  # Force text_area refresh
                st.rerun()
        
        with template_col2:
            if st.button("🔀 Selection", use_container_width=True):
                st.session_state.sandbox_display_code = _get_selection_template()
                st.session_state.sandbox_context = {
                    "title": "Choose Strategy",
                    "options": ["Fast", "Balanced", "Thorough"],
                    "descriptions": {
                        "Fast": "Quick processing, lower accuracy",
                        "Balanced": "Good balance of speed and accuracy", 
                        "Thorough": "Slow but most accurate"
                    },
                    "instruction": "Select the processing strategy."
                }
                st.session_state.sandbox_version += 1  # Force text_area refresh
                st.rerun()
            
            if st.button("✅ Confirmation", use_container_width=True):
                st.session_state.sandbox_display_code = _get_confirm_template()
                st.session_state.sandbox_context = {
                    "title": "Confirm Action",
                    "action": "Delete all temporary files",
                    "warning": "This action cannot be undone!",
                    "details": ["temp_001.txt", "temp_002.txt", "cache/"]
                }
                st.session_state.sandbox_version += 1  # Force text_area refresh
                st.rerun()


def _render_sandbox_preview():
    """Render the sandbox preview area where display code executes."""
    st.subheader("👁️ Preview")
    
    # Create a container for the sandbox
    sandbox_container = st.container(border=True)
    
    with sandbox_container:
        # Execute the display code and get the interaction spec
        interaction_spec = _execute_display_code(
            st.session_state.sandbox_display_code,
            st.session_state.sandbox_context
        )
        
        # Show any errors
        if st.session_state.sandbox_error:
            st.error(f"⚠️ **Error in display code:**\n```\n{st.session_state.sandbox_error}\n```")
        
        # Render the interaction input based on the spec from the code
        if interaction_spec:
            st.divider()
            _render_interaction_from_spec(interaction_spec)
        elif not st.session_state.sandbox_error:
            st.divider()
            st.warning("⚠️ No interaction specified. Add `interact.*` call to your code.")
    
    # Show last response
    if st.session_state.sandbox_last_response is not None:
        st.success(f"**Last Response:** `{st.session_state.sandbox_last_response}`")


def _execute_display_code(code: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Execute user-provided display code in a sandboxed environment.
    
    Returns the interaction specification if one was defined.
    """
    try:
        # Import helpers
        from tools.display_helpers import DisplayHelpers, InteractionBuilder
        
        # Create fresh instances for this execution
        display = DisplayHelpers()
        interact = InteractionBuilder()
        
        # Create a restricted namespace for execution
        exec_globals = {
            "__builtins__": {
                # Allow safe built-ins
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sorted": sorted,
                "reversed": reversed,
                "min": min,
                "max": max,
                "sum": sum,
                "abs": abs,
                "round": round,
                "print": print,
                "isinstance": isinstance,
                "type": type,
                "getattr": getattr,
                "hasattr": hasattr,
            }
        }
        
        exec_locals = {
            "display": display,
            "interact": interact,
            "context": context.copy(),
        }
        
        # Execute the display code
        exec(code, exec_globals, exec_locals)
        
        # Clear any previous error
        st.session_state.sandbox_error = None
        
        # Get the interaction spec if one was defined
        spec = interact.get_spec()
        if spec:
            st.session_state.sandbox_interaction_spec = spec.to_dict()
            return spec.to_dict()
        
        return None
        
    except Exception as e:
        st.session_state.sandbox_error = str(e)
        logger.error(f"Sandbox execution error: {e}")
        return None


def _render_interaction_from_spec(spec: Dict[str, Any]):
    """Render the interaction input based on the specification."""
    interaction_type = spec.get("type", "text_input")
    label = spec.get("label", "Your response:")
    initial_value = spec.get("initial_value", "")
    options = spec.get("options", [])
    height = spec.get("height", 150)
    help_text = spec.get("help_text", "")
    
    st.markdown("**🎯 Interaction Input**")
    
    with st.form(key="sandbox_interaction_form"):
        # Render appropriate input based on type
        if interaction_type == "text_editor":
            user_input = st.text_area(
                label,
                value=initial_value,
                height=height,
                help=help_text if help_text else None,
                key="sandbox_editor_input"
            )
        elif interaction_type == "confirm":
            user_input = st.radio(
                label,
                options=[True, False],
                format_func=lambda x: "✅ Yes" if x else "❌ No",
                help=help_text if help_text else None,
                key="sandbox_confirm_input"
            )
        elif interaction_type == "select":
            user_input = st.selectbox(
                label,
                options=options,
                help=help_text if help_text else None,
                key="sandbox_select_input"
            )
        elif interaction_type == "multi_select":
            user_input = st.multiselect(
                label,
                options=options,
                help=help_text if help_text else None,
                key="sandbox_multiselect_input"
            )
        else:  # Default: text_input
            user_input = st.text_input(
                label,
                value=initial_value,
                help=help_text if help_text else None,
                key="sandbox_text_input"
            )
        
        submitted = st.form_submit_button("✅ Submit", type="primary", use_container_width=True)
        
        if submitted:
            st.session_state.sandbox_last_response = user_input


def _render_documentation():
    """Render the documentation/help section."""
    with st.expander("📖 Helper Reference", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### Display Components (`display.*`)
            
            | Method | Description |
            |--------|-------------|
            | `title(text, icon="")` | Main header |
            | `subtitle(text)` | Subheader |
            | `text(content)` | Markdown text |
            | `code_block(code, language, title)` | Code with syntax highlighting |
            | `instruction(text, type)` | Message box (info/warning/error/success) |
            | `data_preview(data, title)` | Display data as JSON |
            | `metrics_row({"Label": val})` | Metric cards |
            | `divider()` | Horizontal line |
            | `file_content(content, filename)` | File display |
            | `expandable(title, content)` | Collapsible section |
            """)
        
        with col2:
            st.markdown("""
            ### Interaction Types (`interact.*`)
            
            | Method | Description |
            |--------|-------------|
            | `text_input(label, initial_value)` | Single-line input |
            | `text_editor(label, initial_value, height)` | Multi-line editor |
            | `confirm(label)` | Yes/No choice |
            | `select(options, label)` | Dropdown |
            | `multi_select(options, label)` | Multiple choice |
            
            ### Constraints
            
            ❌ No `import` statements  
            ❌ No file/network access  
            ✅ Use `display.*` helpers  
            ✅ Use `interact.*` for input  
            ✅ Access `context` dict  
            """)
        
        st.markdown("---")
        st.markdown("### Quick Example")
        st.code('''# Minimal working example
display.title("My Task", icon="🎯")
display.instruction("Please complete this task.")
interact.text_input("Your answer:")
''', language="python")


# Template functions
def _get_data_review_template() -> str:
    return '''# Data Review Template
display.title(context.get("title", "Data Review"), icon="📊")

# Show metrics if available
if "metrics" in context:
    display.metrics_row(context["metrics"])

display.divider()

# Show sample data
if "sample" in context:
    display.data_preview(context["sample"], title="Sample Data")

display.instruction(context.get("instruction", "Review and approve."))

# Request confirmation
interact.confirm(label="Approve this data for processing?")
'''


def _get_code_edit_template() -> str:
    return '''# Code Editor Template
display.title(context.get("title", "Code Editor"), icon="📝")

display.code_block(
    context.get("code", "# No code provided"),
    language="python",
    title="Current Code"
)

display.instruction(
    context.get("instruction", "Edit the code below."),
    type="info"
)

# Request code editing
interact.text_editor(
    label="Edit the code:",
    initial_value=context.get("code", ""),
    height=250
)
'''


def _get_selection_template() -> str:
    return '''# Selection Template
display.title(context.get("title", "Make a Selection"), icon="🔀")

# Show option descriptions
if "descriptions" in context:
    display.subtitle("Available Options")
    for opt, desc in context["descriptions"].items():
        display.text(f"**{opt}**: {desc}")

display.divider()
display.instruction(context.get("instruction", "Select an option."))

# Request selection
interact.select(
    options=context.get("options", ["Option A", "Option B"]),
    label="Your choice:"
)
'''


def _get_confirm_template() -> str:
    return '''# Confirmation Template
display.title(context.get("title", "Confirm Action"), icon="⚠️")

display.instruction(
    f"**Action:** {context.get('action', 'Unknown action')}",
    type="warning"
)

if "warning" in context:
    display.instruction(context["warning"], type="error")

if "details" in context:
    display.expandable(
        "View Details",
        "\\n".join(f"- {d}" for d in context["details"])
    )

display.divider()

# Request confirmation
interact.confirm(label="Are you sure you want to proceed?")
'''
