# Paradigm Summary for Gold Investment Decision Plan

This document summarizes the paradigms required by the inference repositories.

---

## Design Principles

1. **Paradigms output `o_Normal`** — raw data wrapped in standard format
2. **Truth value wrapping is handled by TIA** (in judgement sequence), not the paradigm
3. **Template differences ≠ paradigm differences** — same paradigm, different prompts
4. **Complex multi-tool flows → plan composition** — use sequential inferences, not mega-paradigms

---

## The 4 Paradigms

### PARADIGM 1: `h_Data-c_PassThrough-o_Normal`

| Field | Value |
|-------|-------|
| **Purpose** | Pass through data unchanged (handles perceptual signs via MVP) |
| **Used by** | 1.2, 1.3, 1.4, 1.5 (data loading via perceptual signs), 1.9 (neutral assertion) |
| **Inputs** | `h_input`: in-memory data (perceptual signs are perceived by MVP) |
| **Tools** | `formatter_tool.get()`, `formatter_tool.wrap()` |
| **Output** | `o_Normal` — same data, wrapped |

**Flow:**
```
h_data → extract input_1 → wrap as Normal → output
```

**Note:** For data loading, the ground concepts contain perceptual signs like `%{file_location}...` 
which are perceived by MVP (using PerceptionRouter) before being passed to the paradigm.

---

### PARADIGM 2: `h_FileData-c_LoadParse-o_Normal`

| Field | Value |
|-------|-------|
| **Purpose** | Load file from path, parse as JSON, return normal data |
| **Used by** | Alternative for explicit file loading (if perceptual signs not used) |
| **Inputs** | `h_input`: file_location string path |
| **Tools** | `file_system.read()`, `formatter_tool.parse_json()`, `formatter_tool.wrap()` |
| **Output** | `o_Normal` — dict in memory |

**Flow:**
```
file_location → read file → extract content → parse JSON → wrap as Normal → output
```

---

### PARADIGM 3: `v_Prompt-h_Data-c_ThinkJSON-o_Normal`

| Field | Value |
|-------|-------|
| **Purpose** | Fill prompt template with data, call LLM with thinking, extract JSON answer |
| **Used by** | 1.6.3, 1.7, 1.8, 1.10, 1.10.3.2, 1.10.3.3, 1.10.3.4 |
| **Inputs** | `v_input`: prompt_location (vertical), `h_input`: in-memory data (horizontal) |
| **Tools** | `prompt_tool.read()`, `llm.generate()`, `formatter_tool.parse_json()`, `formatter_tool.wrap()` |
| **Output** | `o_Normal` — JSON dict from LLM |

**Flow:**
```
prompt_location → strip perceptual sign → read template → create template_fn
→ fill with h_data → LLM generate → clean code → parse JSON → extract answer 
→ wrap as Normal → output
```

**Note:** For judgement sequences (1.7, 1.8), the TIA step converts the boolean output to `%{truth_value}(...)`.

---

### PARADIGM 4: `v_Script-h_Data-c_Execute-o_Normal`

| Field | Value |
|-------|-------|
| **Purpose** | Execute Python script on in-memory data |
| **Used by** | 1.6.2 (technical analysis) |
| **Inputs** | `v_input`: script_location (vertical), `h_input`: in-memory data (horizontal) |
| **Tools** | `file_system.read()`, `python_interpreter.create_function_executor()`, `formatter_tool.wrap()` |
| **Output** | `o_Normal` — script return value |

**Flow:**
```
script_location → strip sign → read script → extract content → create executor(main)
→ collect inputs → execute with h_data → wrap as Normal → output
```

---

## Provision Mapping (Matches inference_repo.json)

| Flow | Concept to Infer | Paradigm | V_Input | H_Input |
|------|-----------------|----------|---------|---------|
| 1.2 | `[price data]` | `h_Data-c_PassThrough-o_Normal` | — | `{simulated data: price data}` (perceptual sign) |
| 1.3 | `[news data]` | `h_Data-c_PassThrough-o_Normal` | — | `{simulated data: news data}` (perceptual sign) |
| 1.4 | `{theoretical framework}` | `h_Data-c_PassThrough-o_Normal` | — | `{simulated data: theoretical framework}` (perceptual sign) |
| 1.5 | `{investor risk profile}` | `h_Data-c_PassThrough-o_Normal` | — | `{simulated data: investor risk profile}` (perceptual sign) |
| 1.6 | `{validated signal}` | (grouping) | — | `{quantitative signal}`, `{narrative signal}` |
| 1.6.2 | `{quantitative signal}` | `v_Script-h_Data-c_Execute-o_Normal` | `provision/scripts/technical_analysis.py` | `[price data]` |
| 1.6.3 | `{narrative signal}` | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | `provision/prompts/sentiment_extraction.md` | `[news data]` |
| 1.7 | `<signals surpass theoretical expectations>` | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | `provision/prompts/bullish_evaluation.md` | `{validated signal}`, `{theoretical framework}` |
| 1.8 | `<signals deviate from theoretical expectations>` | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | `provision/prompts/bearish_evaluation.md` | `{validated signal}`, `{theoretical framework}` |
| 1.9 | `<signals are neutral>` | `h_Data-c_PassThrough-o_Normal` | — | `<signal status>` (assertion only) |
| 1.9.2 | `<signal status>` | (grouping) | — | `<signals surpass...>`, `<signals deviate...>` |
| 1.10 | `{investment decision}` | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | `provision/prompts/final_synthesis.md` | `[all recommendations]`, `{investor risk profile}` |
| 1.10.3 | `[all recommendations]` | (grouping) | — | `{bullish recommendation}`, `{bearish recommendation}`, `{neutral recommendation}` |
| 1.10.3.2 | `{bullish recommendation}` | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | `provision/prompts/buy_recommendation.md` | `{validated signal}`, `{investor risk profile}` |
| 1.10.3.3 | `{bearish recommendation}` | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | `provision/prompts/sell_recommendation.md` | `{validated signal}`, `{investor risk profile}` |
| 1.10.3.4 | `{neutral recommendation}` | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | `provision/prompts/hold_recommendation.md` | `{validated signal}` |

---

## Timing Gates

The recommendation branches use timing gates to conditionally execute:

| Flow | Timing Gate | Condition |
|------|-------------|-----------|
| 1.10.3.2.1 | `@:' (<signals surpass theoretical expectations>)` | Execute if bullish |
| 1.10.3.3.1 | `@:' (<signals deviate from theoretical expectations>)` | Execute if bearish |
| 1.10.3.4.1 | `@:' (<signals are neutral>)` | Execute if neutral |

---

## Resource Files

### Data Files
- `provision/data/price_data.json` - Simulated gold price OHLCV data
- `provision/data/news_data.json` - Simulated financial news articles
- `provision/data/theoretical_framework.json` - Investment thesis framework
- `provision/data/investor_risk_profile.json` - Demo investor constraints

### Prompt Files
- `provision/prompts/sentiment_extraction.md` - Extract sentiment from news
- `provision/prompts/bullish_evaluation.md` - Evaluate bullish signals
- `provision/prompts/bearish_evaluation.md` - Evaluate bearish signals
- `provision/prompts/buy_recommendation.md` - Generate buy recommendation
- `provision/prompts/sell_recommendation.md` - Generate sell recommendation
- `provision/prompts/hold_recommendation.md` - Generate hold recommendation
- `provision/prompts/final_synthesis.md` - Synthesize final decision

### Script Files
- `provision/scripts/technical_analysis.py` - Compute price-based indicators
- `provision/scripts/position_sizing.py` - Calculate position sizes

---

## Template Variable Format

All prompts use Python `string.Template` syntax:
- `$input_1` - First horizontal input
- `$input_2` - Second horizontal input (if provided)
- Variables are filled by `template.safe_substitute(variables)` during execution
