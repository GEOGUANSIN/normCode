
## Goal

Expose and handle calls to a **black-box orchestrator runner’s `user_input` tool** through the existing **Streamlit UI**, so that:

* When the orchestrator calls `user_input(...)`,
* The question is surfaced in the UI,
* The user answers via Streamlit,
* The answer is passed back into the orchestrator as the return value of `user_input(...)`.

Constraints:

* The **orchestrator runner is a black box** (already implemented).
* The orchestrator expects a **synchronous `user_input` function** (e.g. `answer = user_input(prompt)`).
* The orchestrator receives the `user_input` tool **via an attribute** (or constructor argument).
* The **Streamlit app already exists**.
* We are allowed to:

  * Change / wrap the **`user_input` tool**,
  * Wire it into the orchestrator when we construct it.

---

## High-Level Idea

We do **not** modify the orchestrator runner.

Instead we:

1. **Instrument the `user_input` tool** so that every call:

   * Publishes a “question” event into shared state,
   * Blocks the worker thread until an answer is supplied.
2. Use **Streamlit UI** to:

   * Detect pending questions,
   * Render the question(s) to the user,
   * Collect the user’s answer,
   * Write the answer back into shared state.
3. Unblock the instrumented `user_input` wrapper so it can return the answer to the orchestrator.

So from the orchestrator’s point of view nothing changes:

```python
answer = user_input("Please confirm the path:")
```

But under the hood, that call now routes through Streamlit.

---

## Architecture

We need **two-way communication** between:

* The **worker thread** running the orchestrator, and
* The **Streamlit main thread** driving the UI.

We’ll use `st.session_state` to hold:

* A **single active request** (or a queue, if we need many),
* A **response slot**,
* A **synchronization primitive** (`threading.Event`) so the worker can wait for an answer.

### 1. Shared state in `st.session_state`

At Streamlit startup:

```python
import threading
import streamlit as st

if "user_input_request" not in st.session_state:
    # e.g. {"id": 1, "prompt": "…"} or None if no active request
    st.session_state.user_input_request = None

if "user_input_response" not in st.session_state:
    # e.g. {"id": 1, "answer": "…"} or None if no answer ready
    st.session_state.user_input_response = None

if "user_input_event" not in st.session_state:
    # Worker waits on this; UI sets it when answer is ready
    st.session_state.user_input_event = threading.Event()

if "user_input_next_id" not in st.session_state:
    st.session_state.user_input_next_id = 1
```

We assume **one active `user_input` at a time** for simplicity.
If you need multiple concurrent requests, this can be generalized to a dict/queue keyed by IDs.

### 2. Instrumented `user_input` tool (wrapper)

We keep the original `user_input` API but wrap it before giving it to the orchestrator.

```python
import time
import streamlit as st

def instrument_user_input(user_input_fn):
    """
    Wraps a user_input function so that calls are routed through Streamlit.
    If user_input_fn is just a placeholder, the wrapper can ignore it and
    implement the behavior entirely itself.
    """
    def wrapper(prompt: str, *args, **kwargs) -> str:
        # Allocate a new request id
        request_id = st.session_state.user_input_next_id
        st.session_state.user_input_next_id += 1

        # Create the request object
        st.session_state.user_input_request = {
            "id": request_id,
            "prompt": prompt,
            # optional: extra metadata
            "args": args,
            "kwargs": kwargs,
        }

        # Clear any old response + reset event
        st.session_state.user_input_response = None
        st.session_state.user_input_event.clear()

        # Block this worker thread until UI provides an answer
        # (the UI will set st.session_state.user_input_response and set the event)
        event = st.session_state.user_input_event
        event.wait()  # worker blocks here

        # When unblocked, read the response
        resp = st.session_state.user_input_response
        if not resp or resp.get("id") != request_id:
            # Defensive fallback; in normal operation these should match
            raise RuntimeError("user_input response mismatch or missing")

        answer = resp["answer"]
        return answer

    return wrapper
```

Notes:

* The wrapper **does not need to call the original `user_input_fn` at all**, unless you want a fallback / default (e.g., for tests).
* The important behavior is:

  * Write `user_input_request`,
  * Wait on `user_input_event`,
  * Read `user_input_response`,
  * Return `answer`.

### 3. Injecting the wrapped user_input into the orchestrator runner

Where we construct the orchestrator runner, we pass in the **wrapped** tool:

```python
from user_tools import user_input  # original, or dummy default
from instrumentation import instrument_user_input
from orchestrator_module import OrchestratorRunner

wrapped_user_input = instrument_user_input(user_input)

orchestrator = OrchestratorRunner(...)
orchestrator.user_input_tool = wrapped_user_input  # or whatever attribute is used
```

The orchestrator continues to call `self.user_input_tool(prompt, ...)` as before; now that call goes through the wrapper.

### 4. Streamlit UI: showing questions and sending answers back

In the existing Streamlit app code, we add UI for pending `user_input` requests.

At the top of the app (after init):

```python
st.title("Orchestrator UI")

request = st.session_state.user_input_request
response = st.session_state.user_input_response
event = st.session_state.user_input_event
```

If there is a pending request, render it:

```python
if request is not None and response is None:
    st.subheader("Orchestrator question")
    st.write(request["prompt"])

    user_answer = st.text_input("Your answer:", key="user_input_answer")

    if st.button("Submit answer"):
        # Store the response and signal the worker
        st.session_state.user_input_response = {
            "id": request["id"],
            "answer": user_answer,
        }
        event.set()  # Unblock the worker thread waiting in wrapper()
        # Optionally force a rerun so the UI reflects that the question is no longer pending
        st.experimental_rerun()

elif request is not None and response is not None:
    # Optional: show the last answered question & answer
    st.write("Last question answered:")
    st.write(request["prompt"])
    st.write("Answer:", response["answer"])
else:
    st.write("No pending questions from orchestrator.")
```

Meanwhile, separately, you have whatever controls you already use to **start the orchestrator runner** in a background thread; that part doesn’t need to change much.

---

## Behavior Summary

1. Orchestrator calls:

   ```python
   answer = user_input("Please choose a target environment:")
   ```

2. Because we injected the wrapper:

   * `wrapper("Please choose a target environment:")` runs in the orchestrator’s worker thread.
   * It:

     * Creates a new `user_input_request` in `session_state`,
     * Clears old response,
     * Calls `event.wait()` and **blocks**.

3. On the next Streamlit rerun:

   * The app sees `user_input_request` is set and `user_input_response` is `None`.
   * It shows the prompt and a text input / button.

4. The user types an answer and clicks **“Submit answer”**:

   * The app writes `user_input_response = {"id": ..., "answer": ...}`,
   * Calls `user_input_event.set()`.

5. The worker thread unblocks:

   * `event.wait()` returns.
   * The wrapper reads the response, returns the answer string to the orchestrator.

6. Orchestrator continues as if it had just gotten the result from a synchronous `user_input` call.

---

## Why this works with our constraints

* **Orchestrator remains a black box**
  We never change its code; we only control the tool it receives.

* **Streamlit remains the only UI**
  All user interaction is in the Streamlit app; the worker just waits for answers.

* **API compatibility**
  The orchestrator still sees `user_input(prompt) -> str`.

* **Thread-safe & Streamlit-compatible**

  * Worker blocks on a `threading.Event`, not on Streamlit.
  * Streamlit main thread never blocks waiting for the worker; it just reads/writes `session_state`.

Final Recommendation for Developers

Refreshing every 0.5 seconds is safe and recommended.
Just ensure thread creation, state initialization, and orchestrator start logic are placed inside if blocks guarded by session_state flags.
The worker communicates via queues/events, which remain stable across reruns.