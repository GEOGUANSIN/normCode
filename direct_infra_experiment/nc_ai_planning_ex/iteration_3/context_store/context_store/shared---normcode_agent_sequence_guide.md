# NormCode Guide - Agent's Sequences

Agent's sequences are the **operational realization** of inferences - they are the pre-defined pipelines that execute the actual logic when a functional concept invokes them. Each agent's sequence represents a specific pattern of processing steps that transform inputs into outputs.

When a functional concept (like `*every`, `::`, or `&across`) is encountered in a NormCode script, it triggers the corresponding agent's sequence, which then executes a series of standardized processing steps to realize the inference's logic.

## Available Agent's Sequences

| Sequence Name | Pattern                               | Purpose                                                       | Use Case                                                    |
|---------------|---------------------------------------|---------------------------------------------------------------|-------------------------------------------------------------|
| Simple        | `(IWI-IR-OR-OWI)`                     | Basic data retrieval and output operations                    | Usually as dummy for testing                                |
| Grouping      | `(IWI-IR-GR-OR-OWI)`                  | Handles data collection and grouping operations               | Collecting related data items using `&across` and `&in`   |
| Quantifying   | `(IWI-IR-GR-QR-OR-OWI)`               | Manages loops and iterative operations over data collections  | Iterating over collections using `*every` operator          |
| Assigning     | `(IWI-IR-AR-OR-OWI)`                  | Manages variable assignments and state updates                | Variable assignment using `$=`, `$+`, `$.`, `$%` operators   |
| Imperative    | `(IWI-IR-MFP-MVP-TVA-TIP-MIA-OR-OWI)` | Executes complex commands, often with external tools or models| Complex operations using `::` imperative operators          |
| Judgement     | `(IWI-IR-MFP-MVP-TVA-TIP-MIA-OR-OWI)` | Evaluates conditions and returns boolean-like assessments     | Conditional evaluations using `<>` judgement operators      |
| Timing        | `(IWI-T-OWI)`                         | Controls conditional execution and flow control               | Conditional logic using `@if`, `@if!`, `@after` operators |

This architecture ensures that every inference in NormCode has a well-defined operational realization through these standardized agent's sequences.
