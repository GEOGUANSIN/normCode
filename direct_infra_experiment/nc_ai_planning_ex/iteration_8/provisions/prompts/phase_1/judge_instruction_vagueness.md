# Judge Instruction Vagueness

## Task

Determine whether the given instruction is **vague or underspecified** and needs refinement before it can be converted to a NormCode plan.

## Input

You will receive:
- `input_1` — The original natural language instruction (raw instruction content)

---

## The Derivation Problem

Natural language is ambiguous and unstructured. For example:

> "Analyze the sentiment of customer reviews after filtering out spam and duplicates."

**Questions that need answering before derivation**:
- What are the data entities? (reviews, sentiment scores, spam markers)
- What are the operations? (filter spam, remove duplicates, analyze sentiment)
- What's the dependency order? (filter first, then deduplicate, then analyze)
- Which concepts depend on which? (sentiment analysis needs clean reviews)

**Derivation resolves these ambiguities** by creating explicit structure. But it can only do so if the instruction provides enough information.

---

## Evaluation Criteria

### An instruction is **VAGUE** if any of the following are true:

1. **Missing final output**: No clear description of what should be produced
   - ❌ "Help the user" (what is produced?)
   - ✅ "Produce a response message sent to the user"

2. **Missing inputs**: No clear description of what data is available
   - ❌ "Analyze it" (what is "it"?)
   - ✅ "Analyze the customer reviews from the database"

3. **Ambiguous steps**: Steps are described at too high a level
   - ❌ "Process the data" (how?)
   - ✅ "1. Parse message, 2. Extract intent, 3. Identify entities"

4. **Missing iteration details**: Mentions "for each" without specifying the collection
   - ❌ "Handle messages" (which messages? how?)
   - ✅ "For each incoming message, process it and respond"

5. **Unclear conditions**: Mentions "if" without clear criteria
   - ❌ "If appropriate, do X" (what makes it appropriate?)
   - ✅ "If sentiment score > 0.7, classify as positive"

6. **Missing termination**: Open-ended without clear end state
   - ❌ "Keep going until done" (what is "done"?)
   - ✅ "Until user says 'quit'"

7. **Implicit loops or state**: Requires iteration/state tracking without mentioning it
   - ❌ "Calculate the total" (of what? accumulated how?)
   - ✅ "For each number, add to running total"

### An instruction is **CLEAR** (derivable as-is) if:

1. Final output is specified (format, structure, what it contains)
2. Inputs are enumerated (what data exists at the start)
3. Each step describes a concrete action (verbs are specific)
4. Loops specify what to iterate over
5. Conditions have clear true/false criteria
6. Dependencies between steps are evident
7. Termination is explicit for any repeating process

---

## The Key Test

Ask yourself: **"Could I write a dependency tree from this?"**

To write a dependency tree, you need to know:
- The goal (root of the tree)
- Operations that produce each intermediate result
- What inputs each operation requires
- Control flow (loops, conditions)

If any of these are ambiguous, the instruction is **vague**.

---

## Output Format

Return a JSON object:

```json
{
  "thinking": "Your step-by-step analysis of the instruction against each criterion",
  "is_vague": true | false,
  "reasons": [
    "List of specific vagueness issues found",
    "Or empty array if the instruction is clear"
  ],
  "missing_elements": {
    "final_output": true | false,
    "inputs": true | false,
    "steps": true | false,
    "iteration": true | false,
    "conditions": true | false,
    "termination": true | false
  },
  "confidence": 0.0-1.0
}
```

---

## Examples

### Example 1: Vague Instruction

**Instruction**: "Analyze the documents and generate a report"

**Analysis**:
```json
{
  "thinking": "This instruction has several issues: 1) 'documents' - which documents? what format? 2) 'analyze' - what kind of analysis? 3) 'report' - what structure? what should it contain?",
  "is_vague": true,
  "reasons": [
    "No specification of document format or source",
    "Report structure undefined",
    "Analysis criteria unclear",
    "No intermediate steps specified"
  ],
  "missing_elements": {
    "final_output": true,
    "inputs": true,
    "steps": true,
    "iteration": false,
    "conditions": false,
    "termination": false
  },
  "confidence": 0.95
}
```

### Example 2: Clear Instruction

**Instruction**: "For each PDF file in the input folder, extract the text content, summarize it in 3 sentences, and append the summary to output.txt"

**Analysis**:
```json
{
  "thinking": "This instruction is concrete: 1) Input: PDF files in input folder, 2) Iteration: for each PDF, 3) Steps: extract text → summarize to 3 sentences → append, 4) Output: appended to output.txt",
  "is_vague": false,
  "reasons": [],
  "missing_elements": {
    "final_output": false,
    "inputs": false,
    "steps": false,
    "iteration": false,
    "conditions": false,
    "termination": false
  },
  "confidence": 0.95
}
```

### Example 3: Partially Vague

**Instruction**: "Build a chatbot that helps users with their questions"

**Analysis**:
```json
{
  "thinking": "Some elements are clear (it's a chatbot, it responds to questions) but critical details are missing: 1) What triggers each interaction? 2) When does it end? 3) How should it 'help'? 4) What's the response format?",
  "is_vague": true,
  "reasons": [
    "No specification of what 'helps' means - just answers? executes commands?",
    "Missing: when does the session end?",
    "Missing: what's the response format?",
    "Implicit loop (chat session) needs to be explicit"
  ],
  "missing_elements": {
    "final_output": true,
    "inputs": false,
    "steps": true,
    "iteration": true,
    "conditions": false,
    "termination": true
  },
  "confidence": 0.85
}
```

---

## Now Evaluate

Instruction to evaluate:

$input_1
