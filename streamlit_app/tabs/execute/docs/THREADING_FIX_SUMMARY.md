# Threading-Based User Input - Implementation Summary

## Problem Identified

The previous implementation had multiple critical issues:

1. **Trying to update Streamlit UI from background threads** - Streamlit UI elements (`st.info()`, `st.empty()`, etc.) cannot be called from background threads
2. **Infinite rerun loops** - Creating new orchestrators on every page rerun
3. **Missing ScriptRunContext errors** - Background threads didn't have proper Streamlit context for accessing `st.session_state`

## Solution Implemented

### Architecture

We now use a **pure threading-based approach** as recommended in `recom.md`:

1. **Background Thread** (Orchestrator Worker):
   - Runs the orchestrator synchronously
   - Blocks on `threading.Event` when user input is needed
   - Updates ONLY session state variables (no UI calls)
   - Has Streamlit `ScriptRunContext` added via `add_script_run_ctx()`

2. **Main Streamlit Thread** (UI):
   - Polls session state every 0.5 seconds
   - Reads execution state and renders UI
   - Shows user input forms when needed
   - Updates UI based on execution progress

### Key Changes

#### 1. User Input Tool (`user_input_tool.py`)
- Uses `threading.Event` to block worker thread
- Posts request to `st.session_state.user_input_request`
- Waits on `st.session_state.user_input_event`
- UI sets the event after user submits response
- Added 0.5s debug delay and logging at start of each call

#### 2. Execute Tab (`execute_tab.py`)
- **Early user input check**: Checks for pending user input requests at the very top of `render_execute_tab()` before any other rendering
- **Non-blocking execution**: Starts orchestrator in a background thread, not with blocking `asyncio.run()`
- **Polling loop**: Auto-reruns every 0.5s when execution is running
- **Session state only**: Background thread only updates session state, never calls Streamlit UI functions
- **Execution guards**: Prevents starting multiple executions with `is_executing` flag set BEFORE starting thread

#### 3. Execution Engine (`engine.py`)
- Added `ScriptRunContext` to worker thread
- Runs orchestrator via `asyncio.to_thread()` with proper context
- Worker thread can now access `st.session_state` safely

### Execution Flow

```
User clicks "Start Execution"
    ↓
Set is_executing=True
    ↓
Start background thread with ScriptRunContext
    ↓
Thread runs orchestrator synchronously
    ↓
┌─────────────────────────────────────┐
│ Main Thread (UI)                    │  Background Thread (Worker)
│                                     │
│ Rerun every 0.5s                    │  Running orchestrator...
│ Check session state:                │
│  - execution_state (phase, run_id)  │  Calls user_input()
│  - user_input_request               │       ↓
│  - execution_completed              │  Posts to session_state.user_input_request
│  - execution_error                  │       ↓
│                                     │  Calls event.wait() → BLOCKS
│ If user_input_request exists:      │       ↓
│   → Show form                       │  (waiting...)
│   → User submits                    │       ↓
│   → Write to user_input_response    │  (waiting...)
│   → Set event                       │       ↓
│                                     │  Event set! → UNBLOCKS
│                                     │       ↓
│                                     │  Reads user_input_response
│                                     │       ↓
│                                     │  Continues execution...
└─────────────────────────────────────┘
```

### Critical Implementation Details

1. **No UI calls from background thread**: The sync execution function ONLY updates session state variables
2. **ScriptRunContext propagation**: Context is captured in main thread and added to worker thread before starting
3. **User input form doesn't stop script**: Form is shown but page continues to poll (no `st.stop()`)
4. **Execution flag set early**: `is_executing=True` is set BEFORE starting thread to prevent race conditions
5. **Auto-polling with controlled rerun**: Main thread sleeps 0.5s then reruns to poll for updates

### Session State Variables

- `is_executing` (bool): True when orchestration is running
- `execution_thread` (Thread): Reference to background thread
- `execution_state` (ExecutionState): Current execution phase, run_id, metrics
- `execution_engine` (OrchestrationExecutionEngine): Engine instance for accessing metrics
- `execution_result` (dict): Final result when completed
- `execution_completed` (bool): Flag indicating successful completion
- `execution_error` (str): Error message if failed
- `user_input_request` (dict): Pending user input request
- `user_input_response` (dict): User's submitted response
- `user_input_event` (threading.Event): Event to unblock worker thread

### Debugging Features

- Extensive logging with `[MAIN]`, `[THREAD]`, `[WORKER]`, `[UI]` prefixes
- 0.5s delay at start of each user input tool call
- Debug logging shows vars and kwargs for every user input request

## Testing

To test:
1. Start execution
2. Page should auto-update every 0.5s showing progress
3. When user input is needed, form appears at top of page
4. Submit answer → worker thread unblocks and continues
5. Execution completes → success message shown

## Known Limitations

- Streamlit's architecture requires polling (can't push updates from background thread)
- User must wait for auto-rerun cycle to see updates (max 0.5s delay)
- If user navigates away during execution, thread continues but state may be lost on next full reload

## Future Improvements

- Add progress bar based on execution state metrics
- Show live file operations during execution
- Add "Cancel Execution" button that safely terminates thread
- Persist execution state to database for recovery after page reload

