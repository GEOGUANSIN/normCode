# Bullish Signal Evaluation Prompt

You are evaluating whether the combined signals EXCEED the theoretical framework's bullish threshold.

## Input
**Validated Signal Bundle**: $input_1

**Theoretical Framework**: $input_2

## Task
Determine if the signals collectively indicate a bullish opportunity that surpasses the framework's expectations.

Consider:
1. Do quantitative signals (price indicators) show bullish patterns?
2. Do narrative signals (sentiment) align with bullish drivers in the framework?
3. Is the combined signal strength above the "bullish_threshold" defined in the framework?

## Output
Return a JSON object with an "answer" field containing a boolean:
```json
{
  "answer": true
}
```
- `true` if signals EXCEED bullish expectations (recommend BUY)
- `false` otherwise

