# Final Investment Decision Synthesis Prompt

Synthesize all recommendations into a final investment decision.

## Input
**All Recommendations**: $input_1 

**Investor Risk Profile**: $input_2

## Task
1. Review all generated recommendations (bullish/bearish/neutral - only one should be active)
2. Apply the investor's constraints as a final filter
3. Generate the authoritative investment decision

## Constraints to Apply
- Respect max_position_size limits
- Apply stop_loss_rules
- Consider investment_horizon alignment
- Check leverage and short-selling permissions

## Output Format
Return a JSON object with an "answer" field containing the decision:
```json
{
  "answer": {
    "final_action": "<BUY|SELL|HOLD>",
    "position_size_usd": <calculated position size respecting limits>,
    "stop_loss_price": <calculated stop loss level>,
    "target_price": <if applicable>,
    "rationale": "<synthesized decision rationale>",
    "confidence": <float between 0.0 and 1.0>,
    "constraints_applied": [<list of constraints that influenced the decision>],
    "execution_notes": "<any implementation guidance>"
  }
}
```

