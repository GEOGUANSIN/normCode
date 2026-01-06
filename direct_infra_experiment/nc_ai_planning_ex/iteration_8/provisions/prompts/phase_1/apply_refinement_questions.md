# Apply Refinement Questions

## Task

Apply the refinement questions to the given instruction and provide answers that fill in missing details. The goal is to transform a vague instruction into one that is **concrete enough for derivation**.

## Inputs

You will receive:
- `input_1` — The original natural language instruction (raw instruction content)
- `input_2` — The refinement questions to apply (refinement questions content)

---

## The Core Derivation Question

Every derivation answers one recursive question:

> **"What do I need to produce this?"**

For refinement, we need to ensure the instruction provides enough information to answer:
1. What's the final output?
2. What operation produces it?
3. What inputs does that operation need?
4. For each input: repeat

**Refinement fills in the gaps** so this recursion can proceed.

---

## The 7 Refinement Questions

For each question, determine if the instruction already answers it. If not, infer a reasonable answer.

### Question 1: WHAT is the final output?

**What to extract**:
- What exactly should be produced at the end?
- What format should it be in (text, JSON, file, etc.)?
- What fields/properties must it contain?

**Refinement example**:
- ❌ "Help the user" → ✅ "Produce a response message sent to the user"
- ❌ "Analyze it" → ✅ "Produce a sentiment score from 0-1 and a list of key themes"

---

### Question 2: WHAT are the inputs?

**What to extract**:
- What data/files/information are given at the start?
- What format are they in?
- Are there any constraints on input size/structure?

**Refinement example**:
- ❌ "Process the data" → ✅ "Process the customer reviews from reviews.json"
- ❌ "Analyze documents" → ✅ "Analyze PDF files in the /input folder"

---

### Question 3: HOW should the main transformation happen?

**What to extract**:
- What is the core logic or algorithm?
- Are there specific steps that must occur in order?
- What tools/capabilities are needed (LLM, file I/O, computation)?

**Refinement example**:
- ❌ "Make a decision" → ✅ "1. Evaluate conditions, 2. Generate applicable recommendations, 3. Synthesize final decision"
- ❌ "Clean the data" → ✅ "1. Remove nulls, 2. Normalize values, 3. Deduplicate"

---

### Question 4: Are there ITERATIONS needed?

**What to extract**:
- Does anything need to happen "for each" item in a collection?
- What is the collection being iterated over?
- What should be produced per iteration?

**Refinement example**:
- ❌ "Process the documents" → ✅ "For each document in the collection, extract a summary"
- ❌ "Handle user requests" → ✅ "For each request, until user disconnects, process and respond"

**Key patterns to recognize**:
- "for each X" → loop over collection X
- "for every X" → loop over collection X
- "process all X" → loop over collection X
- "keep doing until" → self-seeding loop with conditional append

---

### Question 5: Are there CONDITIONS or branching?

**What to extract**:
- Are there "if/then" decisions to make?
- What conditions trigger different paths?
- What happens in each branch?

**Refinement example**:
- ❌ "If appropriate, do X" → ✅ "If sentiment score > 0.7, classify as positive"
- ❌ "Make a decision" → ✅ "If bullish signals, recommend buy; if bearish, recommend sell; otherwise hold"

---

### Question 6: What INTERMEDIATE results are needed?

**What to extract**:
- What must be computed before the final output?
- Are there dependencies between intermediate steps?
- What should each intermediate step produce?

**Refinement example**:
- ❌ "Generate a report" → ✅ "First extract entities, then analyze sentiment per entity, then aggregate into report"
- ❌ "Understand and respond" → ✅ "1. Parse message into intent, 2. Execute intent, 3. Format response"

---

### Question 7: What could go WRONG and how to handle it?

**What to extract**:
- What errors or edge cases might occur?
- Should there be validation steps?
- Are there fallbacks or retries needed?

**Refinement example**:
- ❌ "Process the file" → ✅ "Read the file; if file is empty, return error message; otherwise process content"
- ❌ "Get the result" → ✅ "Try primary method; if it fails, use fallback value"

---

## Process

For each question:

1. **Check if the instruction already answers it clearly**
   - If yes, extract the explicit answer
   - Mark source as "explicit"

2. **If not explicit, try to infer from context**
   - What would a reasonable interpretation be?
   - Mark source as "inferred"
   - Note lower confidence

3. **If truly unknowable, mark as "unknown"**
   - Flag this as a critical gap
   - Suggest what information is needed

---

## Output Format

Return a JSON object:

```json
{
  "thinking": "Your analysis of the instruction and what's missing",
  "answers": [
    {
      "question_number": 1,
      "question_short": "Final output?",
      "question_full": "WHAT is the final output?",
      "answer": "Your detailed answer describing the output",
      "source": "explicit" | "inferred" | "unknown",
      "confidence": 0.0-1.0,
      "evidence": "Quote or reasoning from the instruction"
    },
    {
      "question_number": 2,
      "question_short": "Inputs?",
      "question_full": "WHAT are the inputs?",
      "answer": "Your detailed answer describing the inputs",
      "source": "explicit" | "inferred" | "unknown",
      "confidence": 0.0-1.0,
      "evidence": "Quote or reasoning from the instruction"
    },
    {
      "question_number": 3,
      "question_short": "Transformation?",
      "question_full": "HOW should the main transformation happen?",
      "answer": "Your detailed answer describing the steps",
      "source": "explicit" | "inferred" | "unknown",
      "confidence": 0.0-1.0,
      "evidence": "Quote or reasoning from the instruction"
    },
    {
      "question_number": 4,
      "question_short": "Iterations?",
      "question_full": "Are there ITERATIONS needed?",
      "answer": "Your detailed answer about loops",
      "source": "explicit" | "inferred" | "unknown",
      "confidence": 0.0-1.0,
      "evidence": "Quote or reasoning from the instruction"
    },
    {
      "question_number": 5,
      "question_short": "Conditions?",
      "question_full": "Are there CONDITIONS or branching?",
      "answer": "Your detailed answer about conditions",
      "source": "explicit" | "inferred" | "unknown",
      "confidence": 0.0-1.0,
      "evidence": "Quote or reasoning from the instruction"
    },
    {
      "question_number": 6,
      "question_short": "Intermediates?",
      "question_full": "What INTERMEDIATE results are needed?",
      "answer": "Your detailed answer about intermediate steps",
      "source": "explicit" | "inferred" | "unknown",
      "confidence": 0.0-1.0,
      "evidence": "Quote or reasoning from the instruction"
    },
    {
      "question_number": 7,
      "question_short": "Error handling?",
      "question_full": "What could go WRONG and how to handle it?",
      "answer": "Your detailed answer about error cases",
      "source": "explicit" | "inferred" | "unknown",
      "confidence": 0.0-1.0,
      "evidence": "Quote or reasoning from the instruction"
    }
  ],
  "critical_gaps": [
    "List of questions that could not be answered even with inference"
  ],
  "overall_refinement_needed": true | false
}
```

---

## Example

**Instruction**: "Build a chatbot that helps users"

**Analysis**:

```json
{
  "thinking": "This instruction is vague. I need to infer most details from the general concept of a chatbot.",
  "answers": [
    {
      "question_number": 1,
      "question_short": "Final output?",
      "question_full": "WHAT is the final output?",
      "answer": "A response message sent to the user in text format",
      "source": "inferred",
      "confidence": 0.7,
      "evidence": "Chatbots typically produce text responses"
    },
    {
      "question_number": 2,
      "question_short": "Inputs?",
      "question_full": "WHAT are the inputs?",
      "answer": "User's message (text) and possibly chat history",
      "source": "inferred",
      "confidence": 0.8,
      "evidence": "'helps users' implies receiving user input"
    },
    {
      "question_number": 3,
      "question_short": "Transformation?",
      "question_full": "HOW should the main transformation happen?",
      "answer": "1. Receive user message, 2. Understand intent, 3. Generate appropriate response, 4. Send response",
      "source": "inferred",
      "confidence": 0.6,
      "evidence": "Standard chatbot flow, but 'helps' is vague - could mean many things"
    },
    {
      "question_number": 4,
      "question_short": "Iterations?",
      "question_full": "Are there ITERATIONS needed?",
      "answer": "Yes - for each user message in the session, process and respond. This is a self-seeding loop.",
      "source": "inferred",
      "confidence": 0.9,
      "evidence": "Chatbots inherently involve multiple message exchanges"
    },
    {
      "question_number": 5,
      "question_short": "Conditions?",
      "question_full": "Are there CONDITIONS or branching?",
      "answer": "Likely: different response types based on intent. Possibly: end session if user says goodbye.",
      "source": "inferred",
      "confidence": 0.5,
      "evidence": "Not specified, but common in chatbots"
    },
    {
      "question_number": 6,
      "question_short": "Intermediates?",
      "question_full": "What INTERMEDIATE results are needed?",
      "answer": "Parsed intent from user message, possibly entity extraction, generated response before sending",
      "source": "inferred",
      "confidence": 0.6,
      "evidence": "Standard NLU pipeline, but not specified"
    },
    {
      "question_number": 7,
      "question_short": "Error handling?",
      "question_full": "What could go WRONG and how to handle it?",
      "answer": "Unknown - no error handling specified. Should probably handle: unintelligible input, empty messages, connection issues.",
      "source": "unknown",
      "confidence": 0.3,
      "evidence": "No mention of error cases"
    }
  ],
  "critical_gaps": [
    "What specific types of 'help' should the chatbot provide?",
    "When should the session end?",
    "Error handling strategy"
  ],
  "overall_refinement_needed": true
}
```

---

## Now Apply

### Instruction to Refine

$input_1

### Refinement Questions Reference

$input_2
