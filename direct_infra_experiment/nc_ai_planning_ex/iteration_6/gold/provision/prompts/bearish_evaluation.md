# Bearish Signal Evaluation Prompt

Evaluate whether the overall signal is BEARISH (recommending a SELL action).

## Input
**Validated Signal Bundle**: $input_1

**Theoretical Framework**: $input_2

## Decision Rule

A signal is BEARISH if and only if:
1. The `overall_signal` in the quantitative analysis is "bearish", AND
2. The `bearish_count` exceeds `bullish_count`, AND
3. The narrative sentiment `overall_score` is negative (< 0)

**IMPORTANT**:
- Overbought RSI with strong upward momentum is NOT bearish - it's bullish with caution
- A signal cannot be both bullish AND bearish - they are mutually exclusive
- If the `overall_signal` says "bullish", this evaluation MUST return `false`
- Only return `true` if the `overall_signal` explicitly says "bearish"

## Evaluation Steps

1. Check quantitative signals:
   - Look at `summary.overall_signal` - is it "bearish"?
   - Compare `bearish_count` vs `bullish_count`

2. Check narrative signals (if present):
   - Look at `overall_score` - is it negative?
   - Look at themes - are they bearish (hawkish policy, strong dollar, etc.)?

3. Make final determination:
   - If overall_signal is "bearish" AND bearish_count > bullish_count → **TRUE**
   - Otherwise → **FALSE**

## Output
Return a JSON object with an "answer" field containing a boolean:
```json
{
  "answer": true
}
```

**CRITICAL**: 
- Return `true` ONLY if the signals clearly indicate a SELL situation
- If `overall_signal` is "bullish" or "neutral", return `false`
- The answer MUST be a boolean (`true` or `false`), not a string
