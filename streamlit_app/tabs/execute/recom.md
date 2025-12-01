
## Goal

Expose the internal activity of a **black-box orchestrator runner** in the existing **Streamlit UI** whenever it uses a **file tool**.

Constraints:

* The orchestrator runner is already implemented and treated as a black box.
* The orchestrator runner receives the **file tool via an attribute** (or constructor argument).
* The Streamlit app already exists and should not be heavily refactored.
* We can change:

  * The **file tool implementation**, and/or
  * **Wrap** the file tool with a decorator before passing it into the orchestrator runner.

---

## High-Level Idea

We do **not** modify the orchestrator runner.

Instead we:

1. **Instrument the file tool** (via decorator or callback hook) so that every time the orchestrator runner calls it, a **progress event** is emitted.
2. Emit those events into a **thread-safe queue** stored in `st.session_state`.
3. On each Streamlit rerun, the app:

   * Drains the queue,
   * Appends the new messages to a persistent list in `session_state`,
   * Renders them in the UI (log view, progress section, etc.).

This way:

* The orchestrator runner continues to call the file tool as usual.
* The UI gets a stream of “file tool activity” without needing to know about the orchestrator’s internals.

---

## Architecture

### 1. Progress channel: queue in `st.session_state`

In the Streamlit app startup logic (or a shared initialization module), ensure we have:

* `st.session_state.file_tool_queue` – `queue.Queue()` for cross-thread communication.
* `st.session_state.file_tool_messages` – list of strings to display in the UI.

The queue is **thread-safe**, so it can be safely written from the orchestrator runner’s worker thread.

### 2. Instrumented file tool (decorator approach)

We keep the existing file tool API unchanged, but wrap it before passing it into the orchestrator runner.

**Core idea:**

* A decorator `instrument_file_tool` that:

  * Logs “before” and “after” each file tool call,
  * Optionally logs errors,
  * Writes these logs into `st.session_state.file_tool_queue`.

In pseudocode:

```python
def instrument_file_tool(file_tool_fn):
    def wrapper(*args, **kwargs):
        q = st.session_state.file_tool_queue
        q.put(f"[file_tool] starting {file_tool_fn.__name__} args={args} kwargs={kwargs}")
        try:
            result = file_tool_fn(*args, **kwargs)
            q.put(f"[file_tool] finished {file_tool_fn.__name__}")
            return result
        except Exception as e:
            q.put(f"[file_tool] ERROR in {file_tool_fn.__name__}: {e}")
            raise
    return wrapper
```

This wrapper is then passed into the orchestrator runner instead of the raw file tool.

### 3. Injecting the wrapped file tool into the orchestrator runner

Wherever we currently construct or configure the orchestrator runner:

* Take the existing file tool object/function.
* Wrap it using `instrument_file_tool`.
* Assign the wrapped version to the orchestrator runner’s file tool attribute.

Example patterns:

* If the orchestrator is a class:

  ```python
  raw_file_tool = FileTool(...)
  wrapped_file_tool = instrument_file_tool(raw_file_tool)

  orchestrator = OrchestratorRunner(...)
  orchestrator.file_tool = wrapped_file_tool
  ```

* If the orchestrator is a function that takes the file tool as a parameter:

  ```python
  orchestrator_runner(
      file_tool=instrument_file_tool(raw_file_tool),
      ...
  )
  ```

The orchestrator doesn’t know the difference; it just calls `file_tool(...)` as before.

### 4. Streamlit: consuming and rendering file tool activity

In the existing Streamlit app code:

* At the top of each run, **drain the queue** into a persistent list:

  ```python
  while not st.session_state.file_tool_queue.empty():
      msg = st.session_state.file_tool_queue.get_nowait()
      st.session_state.file_tool_messages.append(msg)
  ```

* Render the messages somewhere in the UI (e.g., a collapsible log pane, a status section):

  ```python
  st.subheader("File tool activity")
  for msg in st.session_state.file_tool_messages:
      st.write("•", msg)
  ```

* Ensure the app triggers reruns while the orchestrator runner is active (you may already have this):

  * Either via user actions (buttons like “Refresh” / “Next step”), or
  * Via an auto-refresh mechanism (e.g. periodic reruns).

Each rerun picks up **new messages** from the queue and shows them to the user.

---

## Alternative: Global callback hook on the file tool

If modifying the file tool’s source is acceptable, you can avoid decorators and instead:

1. Add a **global or static callback** that the Streamlit layer can register:

   ```python
   # inside the file tool module

   _file_tool_callback = None

   def set_file_tool_callback(cb):
       global _file_tool_callback
       _file_tool_callback = cb

   def _report(msg):
       if _file_tool_callback:
           _file_tool_callback(msg)
   ```

2. Call `_report(...)` inside the file tool implementation wherever meaningful (start, per file, end, errors).

3. In the Streamlit app, set that callback once:

   ```python
   def file_tool_cb(msg: str):
       st.session_state.file_tool_queue.put(msg)

   set_file_tool_callback(file_tool_cb)
   ```

Any orchestrator runner that uses this file tool will automatically emit events the UI can display.

---

## Why this approach

* **No changes to the orchestrator runner**
  We respect it as a black box. All instrumentation is outside it.

* **File tool keeps its public contract**
  We wrap or augment it without breaking its signature, so existing orchestrator logic continues to work.

* **Thread-safe and Streamlit-friendly**
  File tool activity is emitted from the worker thread into a queue; the Streamlit main thread consumes and renders it during normal reruns.

* **Incremental adoption**
  The decorator/hook can be introduced gradually and extended (e.g., richer events: timestamps, file paths, durations, etc.) without touching orchestrator code.

---

If you’d like, this can be extended with a small event schema (e.g., `{"type": "copy", "src": "...", "dst": "...", "status": "start|end|error"}`) instead of raw strings, to support more structured UI elements like progress bars or per-file status tables.
