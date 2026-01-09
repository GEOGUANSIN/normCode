# Synthesize Refined Instruction

## Task

Combine the answers to the 7 refinement questions into a **single, clear, comprehensive instruction** that is suitable for NormCode derivation.

## Input

You will receive:
- `input_1` — Array of question-answer pairs from refinement (refinement answers)

---

## Goal

Transform vague intent into a **derivable instruction**—one that directly maps to the five core NormCode patterns:

| Pattern | What It Represents |
|---------|-------------------|
| **Linear Chain** | Transform A into B |
| **Multiple Inputs** | Combine A and B to produce C |
| **Iteration** | For each X, produce Y |
| **Conditional** | Do A if condition is true |
| **Grouping** | Bundle A, B, C together |

The synthesized instruction should make it obvious which patterns apply.

---

## Rules of Thumb for Paraphrasing

Apply these rules to convert inferred answers into concrete language:

### Rule 1: Make implicit loops explicit

| Vague | Refined |
|-------|---------|
| "Process the documents" | "For each document in the collection, extract summary" |
| "Handle user requests" | "For each request, until user disconnects, process and respond" |
| "Iterate until done" | "For each item, append to results if condition X holds" |

**Key phrase**: "For each X in Y, do Z"

---

### Rule 2: Name the data explicitly

| Vague | Refined |
|-------|---------|
| "Analyze it" | "Analyze the price data to produce quantitative signals" |
| "Get the result" | "Compute the sentiment score from the review text" |
| "Process the input" | "Parse the user message into a structured command" |

**Key pattern**: Use specific nouns with clear types

---

### Rule 3: Make conditions concrete

| Vague | Refined |
|-------|---------|
| "If appropriate" | "If sentiment score > 0.7" |
| "When ready" | "After all signals are computed" |
| "Unless there's a problem" | "If validation fails, use fallback value" |

**Key pattern**: Conditions should have clear true/false criteria

---

### Rule 4: Identify what triggers iteration

| Vague | Refined |
|-------|---------|
| "Keep going" | "Append new item to collection; loop continues while collection grows" |
| "Listen for messages" | "Block waiting for user input; each input triggers one iteration" |
| "Process continuously" | "For each item in stream, as items arrive" |

**Key pattern**: Self-seeding loops terminate via conditional append

---

### Rule 5: Decompose compound operations

| Vague | Refined |
|-------|---------|
| "Understand the user" | "1. Parse message, 2. Extract intent, 3. Identify entities" |
| "Make a decision" | "1. Evaluate conditions, 2. Generate applicable recommendations, 3. Synthesize final decision" |
| "Clean the data" | "1. Remove nulls, 2. Normalize values, 3. Deduplicate" |

**Key pattern**: Break down verbs into ordered steps

---

### Rule 6: Distinguish LLM vs deterministic operations

| Needs LLM | Needs Script/Computation |
|-----------|--------------------------|
| "Determine sentiment" | "Compute sum of digits" |
| "Generate response" | "Parse JSON" |
| "Judge if user wants to quit" | "Check if number equals zero" |
| "Extract themes from text" | "Divide by 10" |

**Key insight**: LLM for ambiguous reasoning; scripts for deterministic computation

---

## Requirements for the Synthesized Instruction

The synthesized instruction MUST:

1. **Be self-contained**: All necessary information in one document
2. **Be unambiguous**: No vague terms like "process" or "handle"
3. **Specify all I/O**: Clear inputs and outputs with formats
4. **Detail all steps**: Concrete actions, not abstract goals
5. **Clarify iterations**: Explicit "for each X in Y" patterns
6. **Clarify conditions**: Explicit "if X then Y else Z" patterns
7. **Show dependencies**: What needs what to complete

---

## Synthesis Process

1. **Start with the goal** (from Question 1: Final output)
   - What is produced at the end?
   - What format is it in?

2. **Identify the inputs** (from Question 2: Inputs)
   - What data exists at the start?
   - These become "ground concepts"

3. **Map the transformation** (from Question 3: How)
   - What steps convert inputs to outputs?
   - Order them by dependency

4. **Add iteration structure** (from Question 4: Iterations)
   - Wrap appropriate steps in "for each" patterns
   - Identify the collection being iterated

5. **Add conditional logic** (from Question 5: Conditions)
   - Insert "if/then" where branches exist
   - Make conditions explicit

6. **Identify intermediate concepts** (from Question 6: Intermediates)
   - Name each intermediate result
   - Show data flow between steps

7. **Add error handling** (from Question 7: Errors)
   - Add validation steps if needed
   - Specify fallback behavior

---

## Output Format

Return a JSON object:

```json
{
  "thinking": "How you're combining the answers and applying paraphrasing rules",
  "result": {
    "refined_instruction": "The complete, refined instruction as a single coherent text. This should be a multi-line string that reads naturally and can be directly used for derivation.",
    "structure": {
      "goal": "The final output being produced",
      "inputs": ["List of input data/concepts"],
      "outputs": ["List of output data/concepts"],
      "iterations": [
        {
          "collection": "What is iterated over",
          "per_item": "What is produced per item"
        }
      ],
      "conditions": [
        {
          "condition": "The condition being checked",
          "if_true": "What happens if true",
          "if_false": "What happens if false (optional)"
        }
      ],
      "steps": [
        "Ordered list of main operations"
      ]
    },
    "patterns_used": ["linear", "multi-input", "iteration", "conditional", "grouping"]
  }
}
```

**Important**: Put all data in the `result` field. The `thinking` field is for your reasoning only.

---

## Example

### Refinement Answers Input

```json
{
  "answers": [
    {"question_number": 1, "answer": "A response message sent to the user in text format"},
    {"question_number": 2, "answer": "User's message (text) and chat history"},
    {"question_number": 3, "answer": "1. Receive message, 2. Understand intent, 3. Generate response, 4. Send"},
    {"question_number": 4, "answer": "For each user message in session, process and respond"},
    {"question_number": 5, "answer": "End session if user says goodbye"},
    {"question_number": 6, "answer": "Parsed intent, generated response before sending"},
    {"question_number": 7, "answer": "Handle unintelligible input with clarification request"}
  ]
}
```

### Synthesized Output

```json
{
  "thinking": "The instruction describes a chat session loop. Applying Rule 1 (explicit loops): 'for each user message'. Applying Rule 4 (trigger): 'blocking wait for input'. Applying Rule 3 (conditions): 'if user wants to end session'. Applying Rule 5 (decompose): breaking 'understand' into parse+intent steps.",
  "result": {
    "refined_instruction": "Chat Session Handler:\n\nINPUT:\n- User message (text string from user)\n- Chat history (list of previous message-response pairs)\n\nOUTPUT:\n- Response message (text string to send to user)\n- Updated chat history\n\nPROCESS:\nFor each user message (blocking wait until received):\n  1. Parse the user message to extract the intent\n  2. Check if the user wants to end the session (e.g., says 'goodbye', 'quit', 'exit')\n  3. If session should end:\n     - Generate a farewell response\n     - Stop the loop (do not append to ongoing messages)\n  4. If session should continue:\n     - Generate an appropriate response based on the intent and chat history\n     - Append the message-response pair to chat history\n     - Continue to next iteration\n\nERROR HANDLING:\n- If message cannot be understood, respond with a clarification request\n- The clarification request counts as a valid response (session continues)\n\nTERMINATION:\n- Loop ends when user indicates they want to end the session\n- Session state is preserved in chat history",
    "structure": {
      "goal": "Send appropriate response to user and maintain chat session",
      "inputs": ["user message", "chat history"],
      "outputs": ["response message", "updated chat history"],
      "iterations": [
        {
          "collection": "ongoing messages (self-seeding)",
          "per_item": "one response per user message"
        }
      ],
      "conditions": [
        {
          "condition": "user wants to end session",
          "if_true": "generate farewell, stop loop",
          "if_false": "generate response, continue loop"
        }
      ],
      "steps": [
        "parse user message",
        "check if user wants to end",
        "generate response based on intent",
        "append to chat history (conditional)",
        "send response"
      ]
    },
    "patterns_used": ["iteration", "conditional", "linear"]
  }
}
```

---

## Refinement Answers to Synthesize

$input_1
