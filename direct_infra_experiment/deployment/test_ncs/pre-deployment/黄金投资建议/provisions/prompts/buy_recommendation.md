# Buy Recommendation Generation Prompt

Generate a BUY recommendation based on the bullish signals detected.

## Input
**Validated Signal Bundle**: $input_1

**Investor Risk Profile**: $input_2

## Task
1. Synthesize the bullish signals into a coherent investment rationale
2. Consider the investor's risk constraints
3. The position sizing will be calculated separately by the position sizing script

## Output Format
Return a JSON object with an "answer" field containing the recommendation:
```json
{
  "answer": {
    "action": "BUY",
    "rationale": "<detailed explanation of why signals support buying>",
    "confidence": <float between 0.0 and 1.0>,
    "key_drivers": [<list of main bullish drivers>],
    "risk_factors": [<list of risks to monitor>],
    "suggested_entry": "<entry strategy description>"
  }
}
```

