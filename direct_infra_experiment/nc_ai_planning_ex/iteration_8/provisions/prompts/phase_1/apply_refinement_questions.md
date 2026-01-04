# Apply Refinement Questions

## Task

Apply each of the 7 refinement questions to the given instruction and provide answers that fill in missing details.

## Inputs

You will receive:
- `$input_1` — The original natural language instruction (raw instruction content)
- `$input_2` — The 7 refinement questions to apply (refinement questions content)

## Process

For each refinement question:
1. Check if the instruction already answers it
2. If yes, extract the answer
3. If no, infer a reasonable answer based on context
4. Mark whether the answer was explicit or inferred

## Output Format

Return a JSON array of question-answer pairs:

```json
{
  "thinking": "Your analysis of the instruction",
  "answers": [
    {
      "question_number": 1,
      "question": "WHAT is the final output?",
      "answer": "Your detailed answer",
      "source": "explicit" | "inferred",
      "confidence": 0.0-1.0
    },
    {
      "question_number": 2,
      "question": "WHAT are the inputs?",
      "answer": "Your detailed answer",
      "source": "explicit" | "inferred", 
      "confidence": 0.0-1.0
    },
    // ... continue for all 7 questions
  ]
}
```

## Guidelines

- **Be specific**: "A JSON object with fields X, Y, Z" is better than "some data"
- **Infer conservatively**: Only infer what's reasonably implied
- **Mark uncertainty**: Use lower confidence for uncertain inferences
- **Preserve intent**: Don't change the user's core goal

## Instruction to Refine

$input_1

## Refinement Questions

$input_2

