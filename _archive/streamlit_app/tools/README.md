# Human-in-the-Loop Tools for Streamlit App

This directory contains custom tools that integrate the NormCode orchestration engine with Streamlit's UI framework, enabling seamless human-in-the-loop interactions.

## Overview

The `StreamlitInputTool` replaces the default CLI/GUI-based `UserInputTool` with a Streamlit-native implementation that:

1. **Pauses execution** when user input is needed
2. **Shows UI elements** (text inputs, text editors, etc.) in the web interface
3. **Resumes execution** after the user provides input
4. **Maintains state** across Streamlit reruns using session state

## Architecture

### How It Works

```
Orchestrator Running
        ↓
Agent needs user input
        ↓
StreamlitInputTool.create_input_function() called
        ↓
Checks session state for existing input
        ↓
    ╔═══════════════════════════════════╗
    ║ Input Found?                      ║
    ╠═══════════════════════════════════╣
    ║ YES → Return value immediately    ║
    ║ NO  → Raise NeedsUserInteraction  ║
    ╚═══════════════════════════════════╝
        ↓ (if NO)
Exception caught in app.py
        ↓
Save orchestrator state to session_state
        ↓
Display UI form for user input
        ↓
User submits response
        ↓
Store response in session_state
        ↓
Rerun app (st.rerun())
        ↓
Resume orchestrator.run()
        ↓
Tool finds input in session_state
        ↓
Execution continues
```

### Key Components

1. **`NeedsUserInteraction` Exception**
   - Custom exception that signals the need for user input
   - Contains: prompt, interaction_id, interaction_type, and additional kwargs

2. **`StreamlitInputTool` Class**
   - Mimics the interface of `infra._agent._models.UserInputTool`
   - Methods:
     - `create_input_function()` - Simple text input
     - `create_text_editor_function()` - Multi-line text editing
     - `create_interaction()` - Generic interaction handler

3. **App Integration (app.py)**
   - Injects `StreamlitInputTool` into `Body`
   - Catches `NeedsUserInteraction` exceptions
   - Displays UI forms for user input
   - Manages state across reruns

## Usage

### In Repository Definitions

If you're creating a repository that requires user input, use the `imperative_input` sequence in your inferences:

```json
{
  "concept_to_infer": "{user feedback}",
  "inference_sequence": "imperative_input",
  "working_interpretation": {
    "user_prompt": "Please provide your feedback on the analysis:"
  }
}
```

### Supported Interaction Types

1. **Text Input** (default)
   ```python
   # In your agent sequence implementation:
   input_fn = body.user_input.create_input_function()
   user_response = input_fn(prompt_text="What is your name?")
   ```

2. **Text Editor**
   ```python
   editor_fn = body.user_input.create_text_editor_function()
   edited_text = editor_fn(
       prompt_text="Review and edit the generated content:",
       initial_text="Original content here..."
   )
   ```

3. **Generic Interaction**
   ```python
   interaction_fn = body.user_input.create_interaction(
       interaction_type="confirm",
       prompt_key="prompt_text"
   )
   result = interaction_fn(prompt_text="Proceed with this action?")
   ```

## Session State Keys

The tool uses the following session state keys:

- `pending_user_inputs` - Dictionary of {interaction_id: value} for pending inputs
- `orchestrator_state` - Saved orchestrator state during pause
- `waiting_for_input` - Boolean flag indicating if execution is paused
- `current_interaction` - Details about the current interaction request

## Example Flow

### Initial Execution

```python
# User clicks "Start Execution"
orchestrator.run()
  ↓
# Agent calls user_input tool
body.user_input.create_input_function()(prompt_text="Enter your name:")
  ↓
# No input found in session_state
raise NeedsUserInteraction(
    prompt="Enter your name:",
    interaction_id="abc123...",
    interaction_type="text_input"
)
```

### UI Display

```python
# app.py catches the exception
except NeedsUserInteraction as interaction:
    # Save orchestrator to session_state
    st.session_state.orchestrator_state = orchestrator
    st.session_state.waiting_for_input = True
    st.session_state.current_interaction = interaction
    
    # Rerun to display input form
    st.rerun()
```

### User Input

```streamlit
# On next rerun, app.py shows:
with st.form("user_interaction_form"):
    user_input = st.text_input("Enter your name:")
    submit = st.form_submit_button("Submit & Resume")
    
    if submit:
        # Store input
        st.session_state.pending_user_inputs["abc123..."] = user_input
        # Resume execution
        orchestrator.run()
```

### Resumption

```python
# On next rerun, orchestrator continues
orchestrator.run()
  ↓
# Agent calls user_input tool again
body.user_input.create_input_function()(prompt_text="Enter your name:")
  ↓
# Input found in session_state!
return "John Doe"  # Execution continues normally
```

## Benefits

1. **No Blocking** - Streamlit scripts run top-to-bottom; this pattern works with that model
2. **Seamless UX** - User sees native Streamlit UI elements, not external dialogs
3. **State Persistence** - Checkpoints ensure no work is lost
4. **Type Flexibility** - Supports text, multi-line, confirmations, and more
5. **Resumable** - Can pause and resume at any point in the orchestration

## Limitations

1. **Stateful** - Requires session state management
2. **Single User** - Designed for single-user sessions (standard for Streamlit)
3. **Checkpoint Required** - Best used with database checkpointing enabled

## Future Enhancements

- [ ] File upload interactions
- [ ] Multi-select interactions
- [ ] Rich text editing (with markdown support)
- [ ] Interactive data table editing
- [ ] Conditional branching based on user choices

## Testing

To test the human-in-the-loop functionality:

1. Create a repository with `imperative_input` inferences
2. Upload to the Streamlit app
3. Start execution
4. Observe the pause when input is needed
5. Provide input through the UI
6. Verify execution resumes correctly

See `streamlit_app/docs/` for example repositories that use this feature.

---

**Version**: 1.4.0 (Human-in-the-Loop)  
**Compatible with**: NormCode Orchestrator v1.3.1+  
**Requires**: Streamlit session state, checkpoint database

