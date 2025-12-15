# Paradigm Summary for Gold Investment Decision Plan

This document summarizes the paradigms required by `example_syntax_coherence.ncd`.

---

## Design Principles

1. **Paradigms output `o_Normal`** — raw data wrapped in standard format
2. **Truth value wrapping is handled by TIA** (in judgement sequence), not the paradigm
3. **Template differences ≠ paradigm differences** — same paradigm, different prompts
4. **Complex multi-tool flows → plan composition** — use sequential inferences, not mega-paradigms

---

## The 4 Paradigms

### PARADIGM 1: `h_FileData-c_LoadParse-o_Normal`

| Field | Value |
|-------|-------|
| **Purpose** | Load file from path, parse as JSON, return normal data |
| **Used by** | 1.1, 1.2, 1.3, 1.4 |
| **Inputs** | `h_input`: file_location perceptual sign |
| **Tools** | `file_system.read()`, `formatter_tool.parse_json()`, `formatter_tool.wrap()` |
| **Output** | `o_Normal` — dict in memory |

**Flow:**
```
file_location → read file → parse JSON → wrap as Normal → output
```

---

### PARADIGM 2: `v_Prompt-h_Data-c_ThinkJSON-o_Normal`

| Field | Value |
|-------|-------|
| **Purpose** | Fill prompt template with data, call LLM with thinking, extract JSON answer |
| **Used by** | 1.5.2, 1.6, 1.7, 1.9, 1.9.1.1, 1.9.1.2, 1.9.1.3 |
| **Inputs** | `v_input`: prompt_location (vertical), `h_input`: in-memory data (horizontal) |
| **Tools** | `prompt_tool.read()`, `llm.generate()`, `formatter_tool.parse_json()`, `formatter_tool.wrap()` |
| **Output** | `o_Normal` — JSON dict from LLM |

**Flow:**
```
prompt_location → read template → fill with h_data → LLM generate → parse JSON → extract answer → wrap as Normal → output
```

**Note:** For judgement sequences (1.6, 1.7), the TIA step converts the boolean output to `%{truth_value}(...)`.

---

### PARADIGM 3: `v_Script-h_Data-c_Execute-o_Normal`

| Field | Value |
|-------|-------|
| **Purpose** | Execute Python script on in-memory data |
| **Used by** | 1.5.1, 1.9.1.1.x, 1.9.1.2.x (position sizing) |
| **Inputs** | `v_input`: script_location (vertical), `h_input`: in-memory data (horizontal) |
| **Tools** | `file_system.read()`, `python_interpreter.function_execute()`, `formatter_tool.wrap()` |
| **Output** | `o_Normal` — script return value |

**Flow:**
```
script_location → read script → execute with h_data as params → wrap as Normal → output
```

---

### PARADIGM 4: `h_Data-c_PassThrough-o_Normal`

| Field | Value |
|-------|-------|
| **Purpose** | Pass through data unchanged (for pure assertions) |
| **Used by** | 1.8 (neutral signal evaluation — assertion only, no LLM) |
| **Inputs** | `h_input`: in-memory data |
| **Tools** | `formatter_tool.wrap()` |
| **Output** | `o_Normal` — same data, wrapped |

**Flow:**
```
h_data → wrap as Normal → output
```

**Note:** The actual assertion logic (`<For Each {signal} where ALL {status_type} False>`) is handled by TIA, not the paradigm. The paradigm just passes the data through.

---

## Provision Mapping

| Flow | Functional Concept | Paradigm | V_Input | H_Input |
|------|-------------------|----------|---------|---------|
| 1.1 | `:%(composition):{paradigm}(retrieve price data...)` | `h_FileData-c_LoadParse-o_Normal` | — | `provision/data/price_data.json` |
| 1.2 | `:%(composition):{paradigm}(retrieve news data...)` | `h_FileData-c_LoadParse-o_Normal` | — | `provision/data/news_data.json` |
| 1.3 | `:%(composition):{paradigm}(obtain theoretical framework...)` | `h_FileData-c_LoadParse-o_Normal` | — | `provision/data/theoretical_framework.json` |
| 1.4 | `:%(composition):{paradigm}(collect investor constraints...)` | `h_FileData-c_LoadParse-o_Normal` | — | `provision/data/investor_risk_profile.json` |
| 1.5.1 | `:%(composition):(compute price-based indicators from {1}...)` | `v_Script-h_Data-c_Execute-o_Normal` | `provision/scripts/technical_analysis.py` | in-memory |
| 1.5.2 | `:%(composition):(extract sentiment and themes from {1}...)` | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | `provision/prompts/sentiment_extraction.md` | in-memory |
| 1.6 | `:%(composition):({1}... exceeds predictions...) <For Each...>` | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | `provision/prompts/bullish_evaluation.md` | in-memory |
| 1.7 | `:%(composition):({1}... falls below predictions...) <For Each...>` | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | `provision/prompts/bearish_evaluation.md` | in-memory |
| 1.8 | `:%(composition):({1}...) <For Each {signal} where ALL {status_type} False>` | `h_Data-c_PassThrough-o_Normal` | — | in-memory |
| 1.9 | `:%(composition):(synthesize final decision from {1}...)` | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | `provision/prompts/final_synthesis.md` | in-memory |
| 1.9.1.1 | `:%(composition):(generate buy recommendation...)` | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | `provision/prompts/buy_recommendation.md` | in-memory |
| 1.9.1.1.x | `:%(composition):(compute position size...)` | `v_Script-h_Data-c_Execute-o_Normal` | `provision/scripts/position_sizing.py` | in-memory |
| 1.9.1.2 | `:%(composition):(generate sell recommendation...)` | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | `provision/prompts/sell_recommendation.md` | in-memory |
| 1.9.1.2.x | `:%(composition):(compute position size...)` | `v_Script-h_Data-c_Execute-o_Normal` | `provision/scripts/position_sizing.py` | in-memory |
| 1.9.1.3 | `:%(composition):(generate hold recommendation...)` | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | `provision/prompts/hold_recommendation.md` | in-memory |

---

## Plan Restructuring Required

For steps 1.9.1.1 and 1.9.1.2 (buy/sell with position sizing), the `.ncd` should decompose into sequential inferences:

```ncd
<- {bullish recommendation}
    <= &[{}] %>[{buy rationale}, {buy position size}]
    <- {buy rationale}
        <= :%(composition):{paradigm}(generate buy rationale)
           | %{norm_input}: v_Prompt-h_Data-c_ThinkJSON-o_Normal
        <- {validated signal}
        <- {investor risk profile}
    <- {buy position size}
        <= :%(composition):{paradigm}(compute position size)
           | %{norm_input}: v_Script-h_Data-c_Execute-o_Normal
        <- {buy rationale}
        <- {investor risk profile}
```

The **plan** handles the LLM → Script composition, not a mega-paradigm.

---

## NCD Comment Block (Copy-Paste Ready)

```ncd
||═══════════════════════════════════════════════════════════════════════════════
|| PARADIGM SUMMARY (Simplified — 4 Paradigms)
||═══════════════════════════════════════════════════════════════════════════════
||
|| Design Principles:
||   - Paradigms output o_Normal (raw data)
||   - Truth value wrapping → TIA step in judgement sequence
||   - Template differences ≠ paradigm differences
||   - Complex flows → plan composition (sequential inferences)
||
|| ┌─────────────────────────────────────────────────────────────────────────────┐
|| │ PARADIGM 1: h_FileData-c_LoadParse-o_Normal                                 │
|| ├─────────────────────────────────────────────────────────────────────────────┤
|| │ Purpose:  Load file from path, parse as JSON, return normal data           │
|| │ Used by:  1.1, 1.2, 1.3, 1.4                                                │
|| │ Inputs:   h_input (file_location perceptual sign)                          │
|| │ Tools:    file_system.read(), formatter_tool.parse_json()                  │
|| │ Output:   o_Normal — dict in memory                                        │
|| └─────────────────────────────────────────────────────────────────────────────┘
||
|| ┌─────────────────────────────────────────────────────────────────────────────┐
|| │ PARADIGM 2: v_Prompt-h_Data-c_ThinkJSON-o_Normal                            │
|| ├─────────────────────────────────────────────────────────────────────────────┤
|| │ Purpose:  Prompt + data → LLM (with thinking) → JSON → normal data         │
|| │ Used by:  1.5.2, 1.6, 1.7, 1.9, 1.9.1.1, 1.9.1.2, 1.9.1.3                   │
|| │ Inputs:   v_input (prompt_location), h_input (in-memory data)              │
|| │ Tools:    prompt_tool.read(), llm.generate(), formatter_tool.parse_json()  │
|| │ Output:   o_Normal — JSON dict from LLM                                    │
|| │ Note:     For judgements, TIA converts bool → %{truth_value}(...)          │
|| └─────────────────────────────────────────────────────────────────────────────┘
||
|| ┌─────────────────────────────────────────────────────────────────────────────┐
|| │ PARADIGM 3: v_Script-h_Data-c_Execute-o_Normal                              │
|| ├─────────────────────────────────────────────────────────────────────────────┤
|| │ Purpose:  Execute Python script on in-memory data                          │
|| │ Used by:  1.5.1, 1.9.1.1.x, 1.9.1.2.x (position sizing)                     │
|| │ Inputs:   v_input (script_location), h_input (in-memory data)              │
|| │ Tools:    file_system.read(), python_interpreter.function_execute()        │
|| │ Output:   o_Normal — script return value                                   │
|| └─────────────────────────────────────────────────────────────────────────────┘
||
|| ┌─────────────────────────────────────────────────────────────────────────────┐
|| │ PARADIGM 4: h_Data-c_PassThrough-o_Normal                                   │
|| ├─────────────────────────────────────────────────────────────────────────────┤
|| │ Purpose:  Pass through data unchanged (for pure assertions)                │
|| │ Used by:  1.8 (neutral evaluation — assertion only, no LLM)                │
|| │ Inputs:   h_input (in-memory data)                                         │
|| │ Tools:    formatter_tool.wrap()                                            │
|| │ Output:   o_Normal — same data, wrapped                                    │
|| │ Note:     Assertion logic handled by TIA, not paradigm                     │
|| └─────────────────────────────────────────────────────────────────────────────┘
||
||═══════════════════════════════════════════════════════════════════════════════
```
