# Derivation v2

**The Core**: Transforming intent into executable structure.

---

## What Is Derivation?

Derivation is the process of converting **what you want** into **how to compute it**.

```
Intent (natural language) → Structure (dependency tree) → Executable (NormCode)
```

**The key insight**: Every computation is a tree of dependencies. Derivation builds that tree.

---

## The Derivation Question

Given any intent, derivation answers one recursive question:

> **"What do I need to produce this?"**

Applied recursively:
1. What's the final output?
2. What operation produces it?
3. What inputs does that operation need?
4. For each input: go back to step 2

**This recursion builds the tree.**

---

## The Tree Structure

Every derivation produces a tree with three node types:

| Node Type | Symbol | Question It Answers |
|-----------|--------|---------------------|
| **Value** | `<-` | "What data exists here?" |
| **Function** | `<=` | "What operation produces it?" |
| **Context** | `<*` | "What controls or scopes this?" |

**Reading direction**: Write top-down (goal first), execute bottom-up (leaves first).

---

## The Five Core Patterns

Every derivation uses combinations of these patterns:

### Pattern 1: Linear Chain
**Intent**: "Transform A into B"

```
B ← [operation] ← A
```

```ncds
<- B
    <= transform A into B
    <- A
```

### Pattern 2: Multiple Inputs
**Intent**: "Combine A and B to produce C"

```
C ← [operation] ← A
                ← B
```

```ncds
<- C
    <= combine A and B
    <- A
    <- B
```

### Pattern 3: Iteration
**Intent**: "For each X, produce Y"

```
all Y ← [for each] ← Y (per item)
                   ← X (collection)
```

```ncds
<- all Y
    <= for each X
    <- Y
        <= produce Y from X
        <- current X
    <* X collection
```

**Key**: `<*` marks the loop base (what we iterate over).

### Pattern 4: Conditional
**Intent**: "Do A if condition is true"

```
result ← [operation] ← inputs
                     ← condition (controls execution)
```

```ncds
<- result
    <= do A
        <= if condition
        <* condition
    <- inputs
```

**Key**: `<*` marks the condition that gates execution.

### Pattern 5: Grouping
**Intent**: "Bundle A, B, C together"

```
bundle ← [group] ← A
                 ← B
                 ← C
```

```ncds
<- bundle
    <= group A, B, and C
    <- A
    <- B
    <- C
```

---

## Before Derivation: Instruction Refinement

Not all instructions can be directly derived. Vague or incomplete instructions need **refinement** before they become derivable.

### The Refinement Questions

Ask these questions to make an instruction concrete:

| Question | What It Reveals | Example Refinement |
|----------|-----------------|-------------------|
| **"What's the final output?"** | The goal/root concept | "Help the user" → "Produce a response message" |
| **"What data exists at the start?"** | Ground concepts (inputs) | "Analyze it" → "Analyze the customer reviews from the database" |
| **"Does this repeat?"** | Loop structure | "Handle messages" → "For each incoming message, process it" |
| **"What triggers each step?"** | Iteration driver | "Keep chatting" → "Wait for user input, then respond" |
| **"When does it end?"** | Termination condition | "Until done" → "Until user says 'quit'" |
| **"What conditions affect behavior?"** | Branching/gating | "Make a decision" → "If bullish, buy; if bearish, sell; otherwise hold" |
| **"What's one atomic step?"** | Operation granularity | "Understand and respond" → "1. Parse intent, 2. Execute command, 3. Generate response" |

---

### Rules of Thumb for Paraphrasing

**Rule 1: Make implicit loops explicit**

| Vague | Refined |
|-------|---------|
| "Process the documents" | "For each document in the collection, extract summary" |
| "Handle user requests" | "For each request, until user disconnects, process and respond" |
| "Iterate until done" | "For each item, append to results if condition X holds" |

**Rule 2: Name the data**

| Vague | Refined |
|-------|---------|
| "Analyze it" | "Analyze the price data to produce quantitative signals" |
| "Get the result" | "Compute the sentiment score from the review text" |
| "Process the input" | "Parse the user message into a structured command" |

**Rule 3: Make conditions concrete**

| Vague | Refined |
|-------|---------|
| "If appropriate" | "If sentiment score > 0.7" |
| "When ready" | "After all signals are computed" |
| "Unless there's a problem" | "If validation fails, use fallback value" |

**Rule 4: Identify what triggers iteration**

| Vague | Refined |
|-------|---------|
| "Keep going" | "Append new item to collection; loop continues while collection grows" |
| "Listen for messages" | "Block waiting for user input; each input triggers one iteration" |
| "Process continuously" | "For each item in stream, as items arrive" |

**Rule 5: Decompose compound operations**

| Vague | Refined |
|-------|---------|
| "Understand the user" | "1. Parse message, 2. Extract intent, 3. Identify entities" |
| "Make a decision" | "1. Evaluate conditions, 2. Generate applicable recommendations, 3. Synthesize final decision" |
| "Clean the data" | "1. Remove nulls, 2. Normalize values, 3. Deduplicate" |

**Rule 6: Identify what an LLM can/cannot do**

| Needs LLM | Needs Script |
|-----------|--------------|
| "Determine sentiment" | "Compute sum of digits" |
| "Generate response" | "Parse JSON" |
| "Judge if user wants to quit" | "Check if number equals zero" |
| "Extract themes from text" | "Divide by 10" |

---

### The Refinement Process

1. **Start with the raw instruction**
   > "Build a chatbot that helps users"

2. **Apply refinement questions**
   - Final output? → "A response message sent to the user"
   - Data at start? → "User's message, chat history"
   - Does it repeat? → Yes, per message
   - Triggers? → User sends message
   - Ends when? → User says to quit
   - Conditions? → Different responses based on intent
   - Atomic steps? → Read input, understand intent, generate response, send response

3. **Write refined instruction**
   > "For each user message (blocking until received):
   > 1. Understand the message as a command
   > 2. Execute the command
   > 3. Generate a response based on the result
   > 4. Send the response to the user
   > 5. If the user wants to end the session, stop; otherwise continue"

4. **Now derive** — The refined instruction maps directly to patterns

---

### Common Refinement Patterns

| Raw Intent | Likely Pattern | Refinement Needed |
|------------|----------------|-------------------|
| "Do X for each Y" | Iteration | Identify Y (the collection) |
| "Keep doing X" | Self-seeding loop | Identify termination condition |
| "X then Y then Z" | Linear chain | Verify order is correct |
| "X or Y depending on Z" | Conditional | Make Z a concrete boolean |
| "Combine/merge/bundle" | Grouping | Identify what's being grouped |
| "Wait for X" | Blocking I/O | Identify the blocking operation |
| "Track/remember X" | State/carry-over | Identify what state persists |

---

## The Derivation Algorithm

### Step 1: Identify the Goal
**Question**: "What is the final output?"

This becomes the root of your tree.

```ncds
<- [final output]
```

### Step 2: Identify the Operation
**Question**: "What operation produces this output?"

This becomes the first child.

```ncds
<- [final output]
    <= [operation that produces it]
```

### Step 3: Identify the Inputs
**Question**: "What does this operation need?"

These become siblings under the operation.

```ncds
<- [final output]
    <= [operation]
    <- [input 1]
    <- [input 2]
```

### Step 4: Recurse
**For each input that isn't a base value**: Go back to Step 2.

```ncds
<- [final output]
    <= [operation]
    <- [input 1]
        <= [operation that produces input 1]
        <- [deeper input]
    <- [input 2]
```

### Step 5: Identify Control
**Question**: "Is there iteration or conditioning?"

Add context markers (`<*`) for:
- Loop bases (what collection are we iterating?)
- Conditions (what boolean gates this?)

---

## Worked Example

**Intent**: 
> "For each customer review, extract sentiment, then summarize all sentiments into a report."

### Step 1: Goal
```ncds
<- sentiment report
```

### Step 2: Operation
```ncds
<- sentiment report
    <= summarize all sentiments
```

### Step 3: Inputs
```ncds
<- sentiment report
    <= summarize all sentiments
    <- all sentiments
```

### Step 4: Recurse on "all sentiments"
This is a collection produced by iteration:

```ncds
<- sentiment report
    <= summarize all sentiments
    <- all sentiments
        <= for each review
        <- sentiment
            <= extract sentiment
            <- current review
        <* reviews
```

### Step 5: Verify Control
- `<* reviews` marks what we iterate over
- No conditions in this example

**Final Result**:
```ncds
<- sentiment report
    <= summarize all sentiments
    <- all sentiments
        <= for each review
        <- sentiment
            <= extract sentiment
            <- current review
        <* reviews
```

---

## Pattern Recognition Guide

When you see this intent... → Use this pattern:

| Intent Pattern | Derivation Pattern |
|----------------|-------------------|
| "Transform X into Y" | Linear chain |
| "Combine X and Y" | Multiple inputs |
| "For each X, do Y" | Iteration |
| "If X, then Y" | Conditional |
| "Bundle X, Y, Z" | Grouping |
| "Keep doing X until Y" | Iteration + conditional append |
| "Choose between X and Y" | Conditional branches |

---

## What Derivation Does NOT Do

Derivation focuses on **structure**, not **execution details**:

| Derivation Does | Derivation Does NOT |
|-----------------|---------------------|
| Build dependency tree | Assign flow indices |
| Identify operations | Determine sequence types |
| Express data flow | Configure execution |
| Recognize patterns | Add semantic types |

Those details are added in **Formalization** (the next phase).

---

## The Derivation Promise

A correct derivation guarantees:

1. **All outputs are reachable** — Every concept has a path to its inputs
2. **All inputs are used** — No orphaned data
3. **Execution order is clear** — Bottom-up traversal is unambiguous
4. **Intent is preserved** — The structure does what was asked

---

## Summary

**Derivation is dependency analysis.**

1. Ask: "What do I need to produce this?"
2. Build the tree recursively
3. Mark control (loops, conditions) with `<*`
4. Result: A structure ready for formalization

**The three markers**:
- `<-` What exists (data)
- `<=` What happens (operations)  
- `<*` What controls (context)

**The five patterns**: Linear, Multiple Inputs, Iteration, Conditional, Grouping.

Everything else is combinations of these.

---

## Next

See [Examples](examples/ncds/README.md) for worked derivations from real plans.

See [Formalization](formalization.md) for the next compilation phase.

