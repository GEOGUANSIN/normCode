# Methodology: Simulating Blueprint Execution in a Compiled System

This document outlines the philosophy and implementation technique for making a multi-agent system, which is compiled from a NormCode blueprint, produce an execution trace that seemingly adheres to the blueprint inference-by-inference.

## 1. Core Philosophy: NormCode as a Verifiable Blueprint

The fundamental philosophy is to treat a NormCode plan not as a script to be interpreted by a generic runtime engine, but as a **formal, design-time blueprint** for a purpose-built software system. The goal is to "compile" the logic from a single, specific NormCode plan into a highly efficient and deterministic multi-agent system.

## 2. The Challenge: Bridging Design and Runtime

A key challenge arises from this philosophy: If the system is pre-compiled for efficiency, how can we verify that its runtime behavior faithfully executes the logic of the original blueprint? A standard application log (`"Starting task X..."`) is insufficient as it doesn't directly reference the blueprint's structure.

## 3. The "Pseudo-Running" Technique

The "trick" to making the multi-agent system *seemingly* adhere to the blueprint inference-by-inference lies in a single, powerful technique:

**We create a structured execution trace that runs in parallel to the actual computation, using the blueprint's own structure as the schema for the log.**

This is achieved through a combination of three implementation details:

### 3.1. The Controller as a Manual, Blueprint-Aware Interpreter

The `ControllerAgent` is not a generic orchestrator; its code is a **direct, hard-coded translation of the NormCode's control flow**.

-   The `while` loop in the `run` method **is** the `*every({number pair})` inference at quantifier `@(1)`.
-   The nested `for` loops **are** the `*every({number pair})` inferences at quantifiers `@(2)` and `@(3)`.

The controller is manually "interpreting" the blueprint's flow, which is the foundational layer of the technique.

### 3.2. The `ExecutionState` as a NormCode-Aware "Logbook"

The `ExecutionState` class is the core of the mechanism. It is not a generic log; it is a **NormCode-aware data structure**. Its purpose is to store results not by an internal program variable name, but by the **semantic location within the blueprint**.

After every computational step, the `ControllerAgent`'s secondary responsibility is to record the result back into this "logbook."

### 3.3. Hyper-Specific, Context-Rich Keys

This is the secret sauce of the implementation. The keys used to store data in the `ExecutionState` are not simple strings; they are **hyper-specific and context-rich identifiers** that fuse the blueprint's static structure with the runtime's dynamic state.

### 4. A Concrete Example

Consider this key from the `addition_system`'s trace:

```json
  "1.1.2.4.2.1.2 (q1:1, q2:1)": {
    "{single unit place value}": 3
  }
```

This key precisely and unambiguously tells us:
-   **`1.1.2.4.2.1.2`**: This result corresponds *exactly* to the `imperative` inference for `{single unit place value}` in the NormCode blueprint.
-   **`q1:1`**: This happened during the **1st cycle** of the main `*every` loop (quantifier `@(1)`).
-   **`q2:1`**: This happened during the **1st cycle** of the *nested* `*every` loop responsible for extracting digits (quantifier `@(2)`).

## 5. Summary of the Trick

In essence, the technique is to **separate the computation from the reporting**.

-   **Computation:** The system uses efficient, simple Python variables (`number_pair`, `carry_over`, etc.) to perform the actual calculations.
-   **Reporting:** After every single computational step, the controller performs a second action: it creates a detailed, context-rich key based on the blueprint and stores the result in the `ExecutionState` object.

The final JSON output is not a dump of the program's internal memory. It is the fully assembled `ExecutionState` "logbook"—a carefully constructed narrative that uses the blueprint's own language and structure to tell the story of the execution, making it appear as if the blueprint itself was the engine. This provides a powerful method for verification, debugging, and ensuring transparency between the design and the final implementation.
