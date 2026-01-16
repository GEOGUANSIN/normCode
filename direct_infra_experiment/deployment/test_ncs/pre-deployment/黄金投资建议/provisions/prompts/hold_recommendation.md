# Hold Recommendation Generation Prompt

Generate a HOLD recommendation based on neutral/mixed signals.

## Input
**Validated Signal Bundle**: $input_1

## Task
1. Explain why the signals do not support a directional trade
2. Identify what would need to change for a buy or sell signal
3. Suggest monitoring actions

## Output Format
Return a JSON object with an "answer" field containing the recommendation:
```json
{
  "answer": {
    "action": "HOLD",
    "rationale": "<explanation of neutral signal interpretation>",
    "confidence": <float between 0.0 and 1.0>,
    "wait_for": [<list of conditions that would trigger action>],
    "monitoring_points": [<what to watch>]
  }
}
```

