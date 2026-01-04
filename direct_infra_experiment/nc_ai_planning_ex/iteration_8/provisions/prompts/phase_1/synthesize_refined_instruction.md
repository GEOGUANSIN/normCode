# Synthesize Refined Instruction

## Task

Combine the answers to the 7 refinement questions into a single, clear, comprehensive instruction suitable for NormCode derivation.

## Input

You will receive:
- `$input_1` — Array of question-answer pairs from refinement (refinement answers)

## Requirements

The synthesized instruction must:
1. **Be self-contained**: All necessary information in one document
2. **Be unambiguous**: No vague terms like "process" or "handle"
3. **Specify all I/O**: Clear inputs and outputs with formats
4. **Detail all steps**: Concrete actions, not abstract goals
5. **Clarify iterations**: Explicit "for each X in Y" patterns
6. **Clarify conditions**: Explicit "if X then Y else Z" patterns
7. **Show dependencies**: What needs what to complete

## Output Format

Return a JSON object:

```json
{
  "thinking": "How you're combining the answers",
  "refined_instruction": "The complete, refined instruction as a single coherent text",
  "structure": {
    "inputs": ["List of input concepts"],
    "outputs": ["List of output concepts"],
    "iterations": ["List of iteration patterns"],
    "conditions": ["List of conditional patterns"],
    "key_operations": ["List of main operations"]
  }
}
```

## Example

Given answers about:
- Output: "Summary report in JSON format"
- Inputs: "List of text files"
- Iteration: "For each text file"
- Steps: "Extract content, summarize, aggregate"

Synthesized instruction:
```
For each text file in the input list:
  1. Read the file content as plain text
  2. Summarize the content to 3 key points
  3. Add summary to the results collection

After all files are processed:
  4. Combine all summaries into a single JSON report
  5. Write the report to output.json

Input: [text files] - a list of file paths to .txt files
Output: {summary report} - a JSON object with structure:
  - file_count: number
  - summaries: array of {filename, key_points}
```

## Refinement Answers to Synthesize

$input_1

