# Example 02: Multi-Input Processing

**Status**: ✅ Reference pattern

---

## Natural Language Instruction

```
Generate an investment recommendation by analyzing both quantitative signals 
and qualitative narrative, then combining them with a theoretical framework.
```

---

## Derived `.ncds`

```ncds
/: Investment recommendation with multiple analysis paths

<- investment recommendation
    <= synthesize final recommendation
    <- quantitative signal
        <= analyze the numerical data for trends
        <- price data
    <- narrative signal
        <= extract sentiment from news articles
        <- news articles
    <- theoretical framework
        <= apply valuation model
        <- company fundamentals
```

---

## Explanation

Multiple independent analyses feed into a single synthesis step.

**Execution order**:
1. Three parallel branches can execute independently:
   - `analyze the numerical data for trends` on `price data`
   - `extract sentiment from news articles` on `news articles`
   - `apply valuation model` on `company fundamentals`
2. Once all three complete → `synthesize final recommendation`

**Key insight**: The synthesis step sees ONLY the three processed signals, not the raw data sources. This prevents context pollution from mixing raw price data with news text.

---

## Patterns Demonstrated

1. **Multiple sibling inputs**: Three value concepts at the same level
2. **Parallel execution**: Independent branches can run concurrently
3. **Synthesis point**: Multiple results combined into one
4. **Data isolation**: Synthesizer never sees raw sources

