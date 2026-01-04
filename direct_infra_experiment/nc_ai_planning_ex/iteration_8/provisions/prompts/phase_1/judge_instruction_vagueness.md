# Judge Instruction Vagueness

## Task

Determine whether the given instruction is vague or underspecified and needs refinement before it can be converted to a NormCode plan.

## Input

You will receive:
- `$input_1` — The original natural language instruction (raw instruction content)

## Evaluation Criteria

An instruction is **VAGUE** if any of the following are true:
1. **Missing final output**: No clear description of what should be produced
2. **Missing inputs**: No clear description of what data is available
3. **Ambiguous steps**: Steps are described at too high a level (e.g., "process the data")
4. **Missing iteration details**: Mentions "for each" without specifying the collection
5. **Unclear conditions**: Mentions "if" without clear criteria
6. **Missing intermediate steps**: Large logical gaps between steps

An instruction is **CLEAR** if:
1. Final output is specified (format, structure)
2. Inputs are enumerated
3. Each step describes a concrete action
4. Loops specify what to iterate over
5. Conditions have clear true/false criteria
6. Dependencies between steps are evident

## Output Format

Return a JSON object:

```json
{
  "thinking": "Your step-by-step analysis of the instruction against each criterion",
  "is_vague": true/false,
  "reasons": ["List of specific vagueness issues found, or empty if clear"],
  "confidence": 0.0-1.0
}
```

## Examples

### Vague Instruction
"Analyze the documents and generate a report"
→ is_vague: true
→ reasons: ["No specification of document format", "Report structure undefined", "Analysis criteria unclear"]

### Clear Instruction
"For each PDF file in the input folder, extract the text content, summarize it in 3 sentences, and append the summary to output.txt"
→ is_vague: false
→ reasons: []

## Now Evaluate

Instruction to evaluate:

$input_1

