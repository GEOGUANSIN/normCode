# 🤝 Human-in-the-Loop Feature - v1.4.0

## Overview

The Streamlit Orchestrator app now supports **Human-in-the-Loop (HITL)** execution, allowing the orchestrator to pause and request user input during execution, then seamlessly resume after the user provides their response.

This enables interactive workflows where:
- Users can review and approve AI-generated content
- Users can provide domain knowledge or corrections
- Users can make decisions at critical points in the orchestration
- Users can edit or refine intermediate results

## What's New

### ✅ StreamlitInputTool

A custom user input tool that integrates seamlessly with Streamlit's session state and rerun mechanism. This replaces the default CLI/GUI-based `UserInputTool` when running in the Streamlit app.

**Key Features:**
- **Non-blocking**: Works with Streamlit's top-to-bottom execution model
- **Native UI**: Shows Streamlit widgets (text inputs, text areas, etc.)
- **State Preservation**: Saves orchestrator state during pauses
- **Multiple Interaction Types**: Supports text input, text editing, confirmations, and more

### ✅ Automatic Integration

The app automatically injects `StreamlitInputTool` into the `Body` object for every execution, enabling HITL without any configuration needed.

### ✅ Pause & Resume

When the orchestrator needs user input:
1. Execution pauses automatically
2. A checkpoint is saved (preserves all progress)
3. UI form appears with the prompt/question
4. User provides input and clicks "Submit & Resume"
5. Execution continues from exactly where it paused

## How It Works

### Architecture

```
┌─────────────────────────────────────────────┐
│  User clicks "Start Execution"              │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  Orchestrator begins running                │
│  (with StreamlitInputTool injected)         │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  Agent executes inferences normally         │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
         ╔════════════════════════╗
         ║  Need user input?      ║
         ╚════════╦═══════════════╝
                  │
        ┌─────────┴─────────┐
        │ NO                │ YES
        ▼                   ▼
┌──────────────┐   ┌────────────────────────┐
│ Continue     │   │ Raise                  │
│ execution    │   │ NeedsUserInteraction   │
└──────────────┘   └────────┬───────────────┘
                             │
                             ▼
                   ┌─────────────────────────┐
                   │ App catches exception   │
                   │ Saves orchestrator      │
                   │ Shows input form        │
                   └────────┬────────────────┘
                             │
                             ▼
                   ┌─────────────────────────┐
                   │ User provides input     │
                   │ Clicks "Submit & Resume"│
                   └────────┬────────────────┘
                             │
                             ▼
                   ┌─────────────────────────┐
                   │ Input stored in         │
                   │ session_state           │
                   │ App reruns              │
                   └────────┬────────────────┘
                             │
                             ▼
                   ┌─────────────────────────┐
                   │ Orchestrator resumes    │
                   │ Tool finds input        │
                   │ Execution continues     │
                   └─────────────────────────┘
```

### Under the Hood

**1. Tool Injection (app.py)**
```python
body = Body(llm_name=llm_model, base_dir=body_base_dir)
body.user_input = StreamlitInputTool()  # Inject custom tool
```

**2. Exception Handling**
```python
try:
    orchestrator.run()
except NeedsUserInteraction as interaction:
    # Save state
    st.session_state.orchestrator_state = orchestrator
    st.session_state.current_interaction = interaction
    st.rerun()  # Show input form
```

**3. Input Collection**
```python
if st.session_state.waiting_for_input:
    with st.form("user_interaction_form"):
        user_input = st.text_input(interaction['prompt'])
        if st.form_submit_button("Submit & Resume"):
            st.session_state.pending_user_inputs[interaction_id] = user_input
            orchestrator.run()  # Resume
```

## Usage

### For Repository Creators

To add user interaction to your repository, use the appropriate inference sequence:

**Example: Text Input**
```json
{
  "concept_to_infer": "{user feedback}",
  "inference_sequence": "imperative_input",
  "working_interpretation": {
    "user_prompt": "Please review the generated summary and provide your feedback:"
  }
}
```

**Example: Text Editing**
```json
{
  "concept_to_infer": "{edited content}",
  "inference_sequence": "imperative_edit",
  "value_concepts": ["{initial content}"],
  "working_interpretation": {
    "user_prompt": "Review and edit the content below:",
    "initial_text_concept": "{initial content}"
  }
}
```

### For App Users

1. **Upload Repository**: Upload a repository that includes user interaction inferences
2. **Start Execution**: Click "▶️ Start Execution" as normal
3. **Wait for Prompt**: The app will pause and show a form when input is needed
4. **Provide Input**: Enter your response in the text field
5. **Resume**: Click "✅ Submit & Resume" to continue execution
6. **Repeat**: If multiple interactions are needed, repeat steps 3-5

## Supported Interaction Types

### 1. Text Input
Simple single-line text input.

**UI:**
```
Your response:
[_________________________]

[✅ Submit & Resume]  [❌ Cancel Execution]
```

**Use Cases:**
- Asking for names, labels, or short answers
- Collecting numerical inputs
- Simple confirmations (via text)

### 2. Text Editor
Multi-line text editing with initial content.

**UI:**
```
Edit the text below:
╔═══════════════════════════════════════╗
║ Initial text appears here...          ║
║ User can modify it as needed.         ║
║                                       ║
╚═══════════════════════════════════════╝

[✅ Submit & Resume]  [❌ Cancel Execution]
```

**Use Cases:**
- Reviewing and editing AI-generated content
- Refining descriptions or summaries
- Correcting errors in generated text

### 3. Confirmation (Future)
Yes/No confirmation dialogs.

**UI:**
```
Please confirm:
○ Yes  ○ No

[✅ Submit & Resume]  [❌ Cancel Execution]
```

**Use Cases:**
- Approving actions
- Confirming destructive operations
- Binary decisions

## Example Workflow

### Scenario: Content Generation with Human Review

**Repository:**
```json
{
  "concepts": [
    {"concept_name": "{topic}", "is_ground_concept": true},
    {"concept_name": "{draft content}"},
    {"concept_name": "{reviewed content}"},
    {"concept_name": "{final content}"}
  ],
  "inferences": [
    {
      "flow_index": "1",
      "concept_to_infer": "{draft content}",
      "inference_sequence": "imperative_python",
      "value_concepts": ["{topic}"],
      "working_interpretation": {
        "script_location": "generate_content.py"
      }
    },
    {
      "flow_index": "2",
      "concept_to_infer": "{reviewed content}",
      "inference_sequence": "imperative_edit",
      "value_concepts": ["{draft content}"],
      "working_interpretation": {
        "user_prompt": "Review and improve the generated content:",
        "initial_text_concept": "{draft content}"
      }
    },
    {
      "flow_index": "3",
      "concept_to_infer": "{final content}",
      "inference_sequence": "imperative_python",
      "value_concepts": ["{reviewed content}"],
      "working_interpretation": {
        "script_location": "finalize_content.py"
      }
    }
  ]
}
```

**Execution Flow:**
1. User uploads repository with topic="Machine Learning"
2. Orchestrator generates draft content using AI
3. **[PAUSE]** App shows text editor with draft content
4. User reviews and improves the content
5. User clicks "Submit & Resume"
6. **[RESUME]** Orchestrator finalizes the content
7. Final content is displayed in Results tab

## Benefits

### 🎯 Precision
- Humans can correct AI mistakes in real-time
- Domain expertise can be injected at key decision points
- Quality control at every critical step

### 🚀 Efficiency
- No need to restart execution after reviewing results
- Iterative refinement without re-running everything
- Checkpoint saves ensure no work is lost

### 🎨 Flexibility
- Mix automated and manual steps seamlessly
- Adapt workflows on-the-fly based on intermediate results
- Support complex approval workflows

### 💡 Transparency
- Users see exactly what the AI generates before it's used
- Full visibility into the orchestration process
- Ability to intervene when needed

## Technical Details

### Session State Management

The feature uses the following session state keys:

```python
st.session_state = {
    # Core interaction state
    'waiting_for_input': bool,          # Is execution paused?
    'current_interaction': dict,        # Details about current request
    'orchestrator_state': dict,         # Saved orchestrator for resumption
    'pending_user_inputs': dict,        # {interaction_id: user_value}
    
    # Existing state (unchanged)
    'last_run': dict,
    'execution_log': list,
    'loaded_config': dict,
    ...
}
```

### Interaction IDs

Each user interaction request has a unique, deterministic ID generated from:
- The prompt text
- The context/kwargs

This ensures that the same request (e.g., in a retry scenario) maps to the same ID, preventing duplicate prompts.

### Checkpoint Integration

When execution pauses for user input:
1. Current cycle and inference count are saved
2. Checkpoint is written to database
3. If app crashes or is closed, execution can resume from this checkpoint
4. User can even load the checkpoint later and continue from the pause point

### Error Handling

If an error occurs during resumed execution:
- Waiting state is cleared
- User is returned to normal execution UI
- Error is logged normally
- Checkpoint remains valid for retry

## Migration Guide

### From v1.3.1 to v1.4.0

**No changes required for existing repositories!**

The HITL feature is **fully backward compatible**:
- Repositories without user interactions work exactly as before
- The `StreamlitInputTool` is a drop-in replacement for the default tool
- All existing features (Fresh Run, Resume, Fork) continue to work

**To add HITL to existing repositories:**
1. Add user interaction inferences to your repository JSON
2. Upload and execute as normal
3. App will automatically handle pauses and resumes

## Future Enhancements

Planned for future releases:

- [ ] **File Upload Interactions**: Allow users to upload files during execution
- [ ] **Multi-Select**: Choose from a list of options
- [ ] **Data Table Editing**: Edit tabular data inline
- [ ] **Conditional Branching**: Different execution paths based on user choices
- [ ] **Interaction History**: View log of all user interactions in a run
- [ ] **Batch Approvals**: Approve/reject multiple items at once
- [ ] **Timeout Handling**: Auto-continue after X minutes if no response

## Troubleshooting

### "Execution keeps pausing at the same point"

**Cause**: Input not being saved properly to session state

**Solution**: Check that you're clicking "Submit & Resume", not just refreshing the page

### "Lost my input after app refresh"

**Cause**: Browser refresh clears session state

**Solution**: Avoid refreshing during paused execution. Use the "Submit & Resume" button instead.

### "Can't resume execution after providing input"

**Cause**: Orchestrator state may not have been saved

**Solution**: Ensure database path is configured and checkpointing is enabled

### "Exception: NeedsUserInteraction not caught"

**Cause**: Exception handling may be disabled or modified

**Solution**: Check app.py for proper exception handling around `orchestrator.run()`

## Examples

See `streamlit_app/examples/` for sample repositories that demonstrate HITL:

- `content_review_example.json` - AI generates content, user reviews/edits
- `decision_tree_example.json` - User makes decisions at branch points
- `validation_example.json` - User validates AI classifications

## API Reference

### StreamlitInputTool

```python
class StreamlitInputTool:
    def __init__(self, session_state_key: str = "pending_user_inputs"):
        """Initialize the tool with a session state key."""
        
    def create_input_function(self, prompt_key: str = "prompt_text") -> Callable:
        """Create a function for simple text input."""
        
    def create_text_editor_function(self, 
                                   prompt_key: str = "prompt_text",
                                   initial_text_key: str = "initial_text") -> Callable:
        """Create a function for multi-line text editing."""
        
    def create_interaction(self, **config) -> Callable:
        """Create a generic interaction function."""
        
    def provide_input(self, interaction_id: str, value: Any):
        """Manually provide input for an interaction."""
        
    def clear_all_inputs(self):
        """Clear all pending inputs."""
```

### NeedsUserInteraction

```python
class NeedsUserInteraction(Exception):
    def __init__(self, 
                 prompt: str,
                 interaction_id: str,
                 interaction_type: str = "text_input",
                 **kwargs):
        """
        Args:
            prompt: The question/prompt to show the user
            interaction_id: Unique identifier for this interaction
            interaction_type: Type of interaction (text_input, text_editor, etc.)
            **kwargs: Additional context or configuration
        """
```

---

**Version**: 1.4.0  
**Release Date**: 2025-11-30  
**Status**: ✅ Production Ready  
**Backward Compatible**: ✅ Yes  
**Requires**: Streamlit, NormCode Orchestrator v1.3.1+, Database checkpointing

**Enjoy seamless human-in-the-loop orchestration!** 🤝🚀

