# The NormCode Methodology: A Practical Summary

## The High-Level Idea

At its core, NormCode is a methodology for turning a complex plan, described in natural language, into a **verifiable, purpose-built multi-agent system**.

Think of it as the software equivalent of an architectural blueprint for a building. You don't just give a builder a vague idea of "a house" and let them figure it out. Instead, you create a detailed blueprint that specifies every room, every wire, and every pipe. The builder then follows that blueprint exactly.

NormCode does the same for software. The goal is to eliminate the ambiguity between a high-level design and the final code, ensuring the finished product is a **faithful, "hard-coded" implementation of the original plan**.

---

## The Practical Workflow: From Idea to Verifiable Trace

The entire process can be broken down into three concrete, practical phases:

### Phase 1: The Blueprinting (Design Time)

This is where you act as the architect.

*   **What you start with:** A task described in plain English (e.g., "Sum two numbers," or "Define the conditions for love").
*   **What you do:** You follow the recursive translation process to decompose the English text into a formal NormCode plan. You break the problem down into logical steps (inferences), assigning operators (`*every`, `@if`, `::`) to define the logic, flow, and actions.
*   **What you end up with:** A `.nc` file (like `addition_system/.nc` or `love_system/love_cleaned.nc`). **This is your architectural blueprint.** It doesn't *run*; it *describes* the system's structure, state, and logic in a formal way.

### Phase 2: The "Compilation" (Development Time)

This is where you put on your hard hat and act as the builder, following the blueprint.

*   **What you start with:** The `.nc` blueprint file.
*   **What you do:** You manually translate the blueprint's structure into a concrete multi-agent system in a language like Python. This is a surprisingly direct translation:
    *   **Agents & Tools:** Functional concepts like `::(sum ...)` in the blueprint tell you to create an `ImperativeAgent` with a `sum()` tool. A concept like `::<is a valid user>` tells you to create a `JudgementAgent` with a tool for validation.
    *   **State:** Object concepts like `{carry-over number}` in the blueprint become the variables your central `ControllerAgent` needs to manage.
    *   **Logic:** The blueprint's structure *is* the controller's logic. A `*every` operator becomes a `while` loop. An `@if` operator becomes an `if/else` statement. The numbered flow index (`1.1`, `1.2.1`) dictates the nesting and sequence of your code.
*   **What you end up with:** A set of Python files (`agents/`, `tools/`, `main.py`) that form a complete, purpose-built application. The system's logic is not dynamic or self-derived; it is a direct, hard-coded implementation of the blueprint.

### Phase 3: The Execution & Verification (Runtime)

This is the final inspection, where you prove the building was built to spec.

*   **What you start with:** Your compiled multi-agent system and some initial input data.
*   **What you do:** You run `main.py`. The `ControllerAgent` executes its hard-coded logic, calling the worker agents to perform their specific tasks.
*   **The "Trick":** As the system performs its actual computations, the Controller also maintains a separate "logbook" called the `ExecutionState`. After every single step, it logs the result not with a simple timestamp, but with a **hyper-specific key that comes directly from the blueprint's structure** (e.g., `"1.1.2.4.2.1.2 (q1:1, q2:1)"`).
*   **What you end up with:** A final JSON output. This isn't just a log; it is the fully assembled `ExecutionState` logbook. It's a carefully constructed narrative that tells the story of the execution using the blueprint's own language, making it a **powerful and verifiable trace** that proves the final code ran exactly as designed in the blueprint.
