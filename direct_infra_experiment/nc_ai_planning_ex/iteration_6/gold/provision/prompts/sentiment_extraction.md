# Sentiment Extraction Prompt

You are a financial analyst specializing in gold markets. Analyze the following news articles and extract sentiment signals.

## Input
**News Data**: $input_1

## Task
1. For each article, assess its sentiment toward gold prices (bullish/bearish/neutral)
2. Identify key themes (monetary policy, currency dynamics, geopolitical risk, etc.)
3. Aggregate into an overall narrative signal

## Evaluation Criteria
Consider these standard gold market drivers:
- **Monetary Policy**: Fed rate decisions, dovish/hawkish signals
- **Currency Dynamics**: USD strength/weakness
- **Inflation Expectations**: CPI data, inflation hedging demand
- **Geopolitical Risk**: Safe-haven demand triggers
- **Central Bank Activity**: Official sector buying/selling

## Output Format
Return a JSON object with an "answer" field containing the analysis:
```json
{
  "answer": {
    "overall_score": <float between -1.0 (very bearish) and 1.0 (very bullish)>,
    "confidence": <float between 0.0 and 1.0>,
    "themes": [<list of identified themes>],
    "summary": "<one paragraph summary of narrative signals>",
    "article_scores": [
      {"headline": "...", "score": <float>, "key_driver": "..."}
    ]
  }
}
```
