# Bullish Signal Evaluation Prompt

Evaluate whether the overall signal is BULLISH (recommending a BUY action).

## Input
**Validated Signal Bundle**: $input_1

**Theoretical Framework**: $input_2

## Decision Rule

A signal is BULLISH if and only if:
1. The `overall_signal` in the quantitative analysis is "bullish", AND
2. The `bullish_count` exceeds `bearish_count`, AND  
3. The narrative sentiment `overall_score` is positive (> 0)

**IMPORTANT**: 
- Overbought RSI (> 70) with upward momentum is STILL bullish (just with caution) - NOT bearish
- A signal cannot be both bullish AND bearish - they are mutually exclusive
- If the `overall_signal` says "bullish", this evaluation should return `true`

## Evaluation Steps

1. Check quantitative signals:
   - Look at `summary.overall_signal` - is it "bullish"?
   - Compare `bullish_count` vs `bearish_count`
   
2. Check narrative signals (if present):
   - Look at `overall_score` - is it positive?
   - Look at `confidence` - is it reasonable (> 0.3)?

3. Make final determination:
   - If overall_signal is "bullish" AND bullish_count > bearish_count → **TRUE**
   - Otherwise → **FALSE**

## Output
Return a JSON object with an "answer" field containing a boolean:
```json
{
  "answer": true
}
```

**CRITICAL**: 
- Return `true` if the signals indicate a BUY opportunity
- Return `false` otherwise
- The answer MUST be a boolean (`true` or `false`), not a string
