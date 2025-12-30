# Example 06: Investment Decision with Conditional Branches

**Status**: ✅ Working (verified against `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/repos/`)

---

## Natural Language Instruction

```
Make an investment decision by:

1. Retrieve price data from market sources
2. Retrieve news data from text sources  
3. Obtain a theoretical framework from domain experts
4. Collect investor constraints (risk tolerance, position size, stop-loss, horizon)

5. Compute quantitative signals from price data (technical indicators)
6. Extract narrative signals from news data (sentiment and themes)
7. Combine quantitative and narrative signals into validated signals

8. Evaluate if signals surpass theoretical expectations (bullish)
9. Evaluate if signals fall below theoretical expectations (bearish)
10. Determine which signals are neutral (neither bullish nor bearish)

11. For bullish signals: generate buy recommendation with position sizing
12. For bearish signals: generate sell recommendation with position sizing
13. For neutral signals: generate hold recommendation
14. Bundle all recommendations together

15. Synthesize final investment decision from all recommendations, 
    constrained by investor risk profile
```

---

## Derived `.ncds`

```ncds
/: Investment Decision with Conditional Branching
/: Multi-source analysis with judgement-based conditional execution
/: STATUS: Working - verified against gold repos

<- investment decision
    <= select investment decision as final output
    
    <- price data
        <= retrieve price data from market sources
        <- simulated data: price data
    
    <- news data
        <= retrieve news data from text sources
        <- simulated data: news data
    
    <- theoretical framework
        <= obtain theoretical framework from domain experts
        <- simulated data: theoretical framework
    
    <- investor risk profile
        <= collect investor constraints
        <- simulated data: investor risk profile
    
    <- validated signal
        <= collect quantitative signal and narrative signal together
        <- quantitative signal
            <= compute price-based indicators
            <- price data
        <- narrative signal
            <= extract sentiment and themes
            <- news data
    
    <- signals surpass theoretical expectations?
        <= judge if validated signal exceeds predictions of theoretical framework
        <- validated signal
        <- theoretical framework
    
    <- signals deviate from theoretical expectations?
        <= judge if validated signal falls below predictions of theoretical framework
        <- validated signal
        <- theoretical framework
    
    <- signals are neutral?
        <= evaluate which signals are neither bullish nor bearish
        <- signal status
            <= collect bullish and bearish evaluations together
            <- signals surpass theoretical expectations?
            <- signals deviate from theoretical expectations?
    
    <- investment decision
        <= synthesize final decision from all recommendations constrained by investor risk profile
        <- all recommendations
            <= bundle bullish, bearish, and neutral recommendations
            <- bullish recommendation
                <= generate buy recommendation with position sizing
                    <= if signals surpass theoretical expectations
                    <* signals surpass theoretical expectations?
                <- validated signal
                <- investor risk profile
            <- bearish recommendation
                <= generate sell recommendation with position sizing
                    <= if signals deviate from theoretical expectations
                    <* signals deviate from theoretical expectations?
                <- validated signal
                <- investor risk profile
            <- neutral recommendation
                <= generate hold recommendation
                    <= if signals are neutral
                    <* signals are neutral?
                <- validated signal
        <- investor risk profile
```

---

## Key Patterns Demonstrated

### 1. Multiple Parallel Data Sources
Four independent data retrieval branches:
```ncds
<- price data
    <= retrieve price data from market sources
    <- simulated data: price data
<- news data
    <= retrieve news data from text sources
    <- simulated data: news data
<- theoretical framework
    <= obtain theoretical framework from domain experts
    <- simulated data: theoretical framework
<- investor risk profile
    <= collect investor constraints
    <- simulated data: investor risk profile
```

### 2. Signal Extraction and Grouping
Process different data sources into signals, then combine:
```ncds
<- validated signal
    <= collect quantitative signal and narrative signal together
    <- quantitative signal
        <= compute price-based indicators
        <- price data
    <- narrative signal
        <= extract sentiment and themes
        <- news data
```
Uses `&[#]` (group across) to flatten into unified signal collection.

### 3. Judgement-Based Evaluation
Multiple boolean evaluations on the same data:
```ncds
<- signals surpass theoretical expectations?   /: Proposition <>
    <= judge if validated signal exceeds predictions of theoretical framework
    <- validated signal
    <- theoretical framework

<- signals deviate from theoretical expectations?  /: Proposition <>
    <= judge if validated signal falls below predictions of theoretical framework
    <- validated signal
    <- theoretical framework
```
These produce per-signal boolean masks (e.g., `[True, False, True]`).

### 4. Derived Neutral Evaluation
Neutral is computed from the combination of bullish and bearish:
```ncds
<- signals are neutral?
    <= evaluate which signals are neither bullish nor bearish
    <- signal status
        <= collect bullish and bearish evaluations together
        <- signals surpass theoretical expectations?
        <- signals deviate from theoretical expectations?
```
Uses assertion: `<For Each {signal} where ALL {status_type} False>`.

### 5. Conditional Recommendation Generation
Each recommendation branch is gated by its corresponding condition:
```ncds
<- bullish recommendation
    <= generate buy recommendation with position sizing
        <= if signals surpass theoretical expectations    /: @:' timing gate
        <* signals surpass theoretical expectations?      /: condition context
    <- validated signal
    <- investor risk profile
```
Only runs for signals where the condition is True.

### 6. Recommendation Bundling and Synthesis
All conditional branches bundled together, then synthesized:
```ncds
<- all recommendations
    <= bundle bullish, bearish, and neutral recommendations
    <- bullish recommendation
    <- bearish recommendation
    <- neutral recommendation

<- investment decision
    <= synthesize final decision from all recommendations constrained by investor risk profile
    <- all recommendations
    <- investor risk profile
```

---

## Flow Structure Summary

| Flow Index | Concept | Sequence | Description |
|------------|---------|----------|-------------|
| `1` | `:<:({investment decision})` | assigning | Final output |
| `1.2` | `[price data]` | imperative | Load from file |
| `1.3` | `[news data]` | imperative | Load from file |
| `1.4` | `{theoretical framework}` | imperative | Load from file |
| `1.5` | `{investor risk profile}` | imperative | Load from file |
| `1.6` | `{validated signal}` | grouping | Combine signals |
| `1.6.2` | `{quantitative signal}` | imperative | Python script |
| `1.6.3` | `{narrative signal}` | imperative | LLM extraction |
| `1.7` | `<signals surpass>` | judgement | Bullish eval |
| `1.8` | `<signals deviate>` | judgement | Bearish eval |
| `1.9` | `<signals neutral>` | judgement | Neutral eval |
| `1.9.2` | `<signal status>` | grouping | Bundle evals |
| `1.10` | `{investment decision}` | imperative | LLM synthesis |
| `1.10.3` | `[all recommendations]` | grouping | Bundle recs |
| `1.10.3.2` | `{bullish recommendation}` | imperative | Gated by 1.7 |
| `1.10.3.2.1` | timing gate | timing | `@:'` if bullish |
| `1.10.3.3` | `{bearish recommendation}` | imperative | Gated by 1.8 |
| `1.10.3.3.1` | timing gate | timing | `@:'` if bearish |
| `1.10.3.4` | `{neutral recommendation}` | imperative | Gated by 1.9 |
| `1.10.3.4.1` | timing gate | timing | `@:'` if neutral |

---

## Paradigms Used

| Operation | Paradigm | Description |
|-----------|----------|-------------|
| Data retrieval | `h_Data-c_PassThrough-o_Normal` | Load file, pass through |
| Quantitative signal | `v_Script-h_Data-c_Execute-o_Normal` | Execute Python script |
| Narrative signal | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | LLM with thinking |
| Judgements | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | LLM evaluation |
| Recommendations | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | LLM generation |
| Final synthesis | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | LLM synthesis |

---

## Signal Axis Handling

This plan demonstrates **axis-aware operations**:

1. **Create axis**: `&[#] %>[{quantitative signal}, {narrative signal}] %+(signal)`
   - Creates `[signal]` axis from two sources

2. **Per-signal judgement**: `<For Each {validated signal} True>`
   - Evaluates each signal independently
   - Produces boolean mask matching signal axis

3. **Protected axis in grouping**: `%^<$!={signal}>`
   - Preserves signal axis when grouping status types

4. **Conditional execution on axis**: Timing gates apply per-signal
   - Only signals where condition is True proceed
   - Result is filtered/masked appropriately

---

## Language Variants

This plan exists in both English and Chinese, demonstrating that NormCode is **language-agnostic** for concept names.

### Concept Name Mapping

| English | Chinese (中文) |
|---------|---------------|
| `{investment decision}` | `{投资决策}` |
| `[price data]` | `[价格数据]` |
| `[news data]` | `[新闻数据]` |
| `{theoretical framework}` | `{理论框架}` |
| `{investor risk profile}` | `{投资者风险偏好}` |
| `{validated signal}` | `{验证信号}` |
| `{quantitative signal}` | `{量化信号}` |
| `{narrative signal}` | `{叙事信号}` |
| `<signals surpass theoretical expectations>` | `<信号超出理论预期>` |
| `<signals deviate from theoretical expectations>` | `<信号偏离理论预期>` |
| `<signals are neutral>` | `<信号中性>` |
| `<signal status>` | `<信号状态>` |
| `[all recommendations]` | `[所有建议]` |
| `{bullish recommendation}` | `{看涨建议}` |
| `{bearish recommendation}` | `{看跌建议}` |
| `{neutral recommendation}` | `{中性建议}` |

### Operation Mapping

| English | Chinese (中文) |
|---------|---------------|
| retrieve price data from market sources | 从市场来源获取价格数据 |
| retrieve news data from text sources | 从文本来源获取新闻数据 |
| obtain theoretical framework from domain experts | 从领域专家获取理论框架 |
| collect investor constraints | 收集投资者约束 |
| compute price-based indicators | 根据价格数据计算价格指标 |
| extract sentiment and themes | 从新闻数据提取情绪和主题 |
| judge if signal exceeds predictions | 判断验证信号是否超出理论框架的预测 |
| judge if signal falls below predictions | 判断验证信号是否低于理论框架的预测 |
| generate buy recommendation | 生成带仓位管理的买入建议 |
| generate sell recommendation | 生成带仓位管理的卖出建议 |
| generate hold recommendation | 生成持有建议 |
| synthesize final decision | 综合所有建议得出最终决策 |

### Timing Gate Keywords

| English | Chinese (中文) |
|---------|---------------|
| if signals surpass theoretical expectations | 如果信号超出理论预期 |
| if signals deviate from theoretical expectations | 如果信号偏离理论预期 |
| if signals are neutral | 如果信号中性 |

---

## Files

**English version:**
- **`.ncds`**: `06_investment_decision.ncds`
- **Source repos**: `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/repos/gold_en.*`

**Chinese version (中文版):**
- **`.ncds`**: `06_investment_decision_chinese.ncds`
- **Source repos**: `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/repos/gold_chinese.*`

**Shared:**
- **Paradigms**: Standard composition paradigms
- **Provisions**: `provision/prompts/` (English) and `provision/prompts_chinese/` (Chinese)

