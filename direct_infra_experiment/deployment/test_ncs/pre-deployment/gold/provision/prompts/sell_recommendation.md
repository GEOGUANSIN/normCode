# Sell Recommendation Generation Prompt

Generate a SELL recommendation based on the bearish signals detected.

## Input
**Validated Signal Bundle**: $input_1

**Investor Risk Profile**: $input_2

## Task
1. Synthesize the bearish signals into a coherent exit/short rationale
2. Consider the investor's risk constraints
3. The position sizing will be calculated separately by the position sizing script

## Output Format
Return a JSON object with an "answer" field containing the recommendation:
```json
{
  "answer": {
    "action": "SELL",
    "rationale": "<detailed explanation of why signals support selling>",
    "confidence": <float between 0.0 and 1.0>,
    "key_drivers": [<list of main bearish drivers>],
    "risk_factors": [<list of risks if NOT selling>],
    "suggested_exit": "<exit strategy description>"
  }
}
```

