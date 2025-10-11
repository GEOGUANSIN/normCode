# Normcode Concepts and Sequences: An Explanation

This document breaks down how Normcode's concepts and sequences work, using the multi-digit addition example from `infra/examples/add_examples/ex_add_complete.py` as a case study.

## 1. Introduction to Normcode and Sequences

**Normcode** is a specialized language designed to represent complex data processing and reasoning tasks in a structured, hierarchical way. It uses a set of special characters and keywords called **concepts** to define operations.

These operations are organized into **sequences**, which are pre-defined pipelines for executing a specific type of logic. Each line in a Normcode script is typically annotated with the sequence that handles its execution (e.g., `| 1. quantifying`).

Based on the `infra/_agent/_sequences` directory, common sequences include:
-   `simple`: Basic data retrieval and output.
-   `grouping`: Operations for grouping or collecting data.
-   `quantifying`: Manages loops and iterative operations over data collections.
-   `assigning`: Handles variable assignments and updates.
-   `imperative`: Executes complex commands, often by invoking external tools or language models.
-   `judgement`: Performs evaluations and returns a boolean-like assessment.
-   `timing`: Controls conditional execution and flow control (e.g., if/while).

Each sequence is composed of a series of steps (e.g., `IWI` - Input Working Interpretation, `IR` - Input References, `QR` - Quantifying References, etc.) that form a processing pipeline.

## 2. Analysis of the Addition Example

The example code in `ex_add_complete.py` implements a multi-digit addition algorithm. It's designed to handle numbers of any length by iterating through them digit by digit, calculating the sum and a carry-over, and repeating until all digits are processed.

Let's break down the Normcode snippet step by step.

### Level 1: The `quantifying` Sequence (The Main Loop)

```normcode
{new number pair} | 1. quantifying
    <= *every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>] | 1.1. assigning
```

-   **`{new number pair} | 1. quantifying`**: This is the entry point of the entire process. It declares that the ultimate goal is to produce a `{new number pair}` (which will be the final sum) and that the overall logic will be managed by a `quantifying` sequence. This is appropriate because addition is an iterative (looping) process over the digits.

-   **`<= *every({number pair}) ... | 1.1. assigning`**: This line, handled by an `assigning` sequence, defines the main loop of the algorithm.
    -   **`*every({number pair})`**: The `*every` concept is a quantifier. It signals an iteration over the items in the `{number pair}` collection. This loop will continue as long as the conditions inside it are met (i.e., there are still digits to add or a carry-over exists).
    -   The rest of the line sets up the loop's state, tracking the evolving `{number pair}` and initializing a `{carry-over number}`.

### Level 1.1.2: The `imperative` Sequence (Calculating the Digit Sum)

```normcode
<- {digit sum} | 1.1.2. imperative
    <= ::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)
    ...
```

-   **`<- {digit sum} | 1.1.2. imperative`**: This block's purpose is to calculate the `{digit sum}` for the current column of digits. It uses an `imperative` sequence because it involves a complex, command-like action.
-   **`<= ::(sum ...)`**: The `::` concept marks an imperative command. The text inside the parentheses is a natural language instruction that is likely sent to a language model or a specialized tool. It commands the system to sum the digits from the current place value (`[all {unit place value} of numbers]`) and the current `{carry-over number}`.

### Level 1.1.2.4: The `grouping` Sequence (Getting the Digits)

Nested within the imperative block, this part gathers the digits to be added.

```normcode
<- [all {unit place value} of numbers]<:{1}> | 1.1.2.4. grouping
    <= &across({unit place value}:{number pair}*1)
    ...
```

-   **`<- [all {unit place value} of numbers] ... | 1.1.2.4. grouping`**: A `grouping` sequence is used here to collect multiple pieces of data into a single collection.
-   **`<= &across(...)`**: The `&across` concept is a grouping operator. It iterates across the two numbers in the current `{number pair}` and extracts the `{unit place value}` (the rightmost digit) from each one. The result is a collection of digits that can then be summed.

### Level 1.1.3 & 1.1.3.1: `assigning` and `timing` Sequences (Loop Control)

This section is responsible for updating the state for the next loop iteration and checking if the loop should terminate.

```normcode
<- {number pair}<$={1}> | 1.1.3. assigning
    <= $+({number pair to append}:{number pair})%:[{number pair}] | 1.1.3.1. timing
        <= @if!(<all number is 0>) | 1.1.3.1.1. timing
            <= @if(<carry-over number is 0>)
```

-   **`<- {number pair}<$={1}> | 1.1.3. assigning`**: This `assigning` sequence updates the `{number pair}` by removing the last digit from each number, preparing for the next iteration.
-   **`| 1.1.3.1. timing`**: The update logic is wrapped in a `timing` sequence, which handles conditional flow.
-   **`<= @if!(<all number is 0>)` and `@if(<carry-over number is 0>)`**: These lines use `timing` concepts. `@if` and `@if!` are conditional operators. This logic states that the loop should continue if the numbers are **not** all zero OR if the carry-over is **not** zero. This ensures the loop runs until the entire addition is complete.

### Level 1.1.3.3: The `judgement` Sequence (Checking for Zero)

To implement the loop's exit condition, the code needs to determine if the numbers have been reduced to zero.

```normcode
<- <all number is 0> | 1.1.3.3. judgement
    <= :%(True):<{1}<$({number})%_> is 0> | 1.1.3.3.1. timing
```

-   **`<- <all number is 0> | 1.1.3.3. judgement`**: This block uses a `judgement` sequence to make a determination. Its goal is to produce a boolean-like result for the condition `<all number is 0>`.
-   **`<= :%(True):<... is 0>`**: The `<...>` syntax is used for judgements. This expression evaluates whether the input `{number}` is `0` and returns a `True` or `False` value, which is then used by the `timing` sequence (`@if!`) to control the loop.

## Conclusion

This example demonstrates how Normcode combines different **concepts** and orchestrates them using **sequences** to build a complex algorithm. Each sequence has a specialized role, from managing loops (`quantifying`) to executing commands (`imperative`) and controlling logic flow (`timing`, `judgement`). The hierarchical structure allows for building sophisticated logic from these fundamental building blocks.
