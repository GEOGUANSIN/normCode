# NormCode Guide - Core Syntax

This document covers the fundamental syntax of NormCode, a semi-formal language for constructing a **plan of inferences**.

## Core Syntax: Concepts and Inferences

The fundamental unit of a Normcode plan is the **inference**. An inference is defined by a functional concept and its associated value concepts.

-   **Functional Concept (`<=`)**: This is the cornerstone of an inference. It "pins down" the inference by defining its core logic, function, or operation. Crucially, the functional concept is responsible for **invoking an agent's sequence** (e.g., `quantifying`, `imperative`), which is the underlying engine that executes the inference's logic.

-   **Value Concept (`<-`)**: This concept provides the concrete data for the inference. It specifies the inputs, outputs, parameters, or results that the functional concept operates on or produces.

The entire plan is represented in a hierarchical, vertical format. An inference begins with a root concept, followed by an indented functional concept (`<=`) that defines the operation. The value concepts (`<-`) are then supplied at the same or a more deeply nested level.

A line in Normcode can also have optional annotations for clarity and control:

`_concept_definition_ | _annotation_ // _comment_`

-   **`_concept_definition_`**: The core functional (`<=`) or value (`<-`) statement.
-   **`_annotation_`**: Optional metadata following the `|` symbol. This can be a **flow index** (e.g., `1.1.2`), an intended **data reference**, or the name of the invoked **agent's sequence**.
-   **`// _comment_`**: Human-readable comments.

**Example Structure of an Inference:**
```Normcode
_concept_to_infer_ // The overall goal of this inference
    <= _functional_concept_defining_the_operation_ | 
    quantifying // This invokes the 'quantifying' agent's sequence
    <- _input_value_concept_1_ // This is an input for the 
    operation
    <- _input_value_concept_2_
```
