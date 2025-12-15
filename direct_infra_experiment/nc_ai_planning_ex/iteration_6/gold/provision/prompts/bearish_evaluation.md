# Bearish Signal Evaluation Prompt

You are evaluating whether the combined signals DEVIATE NEGATIVELY from the theoretical framework's expectations.

## Input
**Validated Signal Bundle**: $input_1

**Theoretical Framework**: $input_2

## Task
Determine if the signals collectively indicate a bearish condition that falls below the framework's expectations.

Consider:
1. Do quantitative signals (price indicators) show bearish patterns?
2. Do narrative signals (sentiment) indicate bearish conditions?
3. Is the combined signal weakness below the "bearish_threshold" defined in the framework?

## Output
Return a JSON object with an "answer" field containing a boolean:
```json
{
  "answer": true
}
```
- `true` if signals indicate bearish conditions (recommend SELL)
- `false` otherwise

