# NormCode Gold Investment System - Debugging Session Summary
**Date**: December 14, 2025  
**System**: Gold Investment Decision System (NormCode Framework)  
**Status**: Partial Success (15/17 inferences completing, 88.2% success rate)

---

## Executive Summary

We successfully debugged a complex orchestration deadlock in the NormCode framework by:
1. **Enabling dev mode** to expose silent errors that were being converted to skip values
2. **Fixing paradigm-tool mismatches** where paradigms expected methods that didn't exist
3. **Resolving composition context access issues** where bound functions weren't properly handling closures
4. **Fixing data type mismatches** where JSON strings weren't being parsed before passing to scripts

**Current Status**: 15/17 inferences complete. Remaining issues are axis/shape mismatches in bullish/bearish recommendation inferences.

---

## Problems Discovered and Fixes Applied

### 1. **Silent Error Handling (CRITICAL)**
**Problem**: Errors in `Reference` operations were being silently caught and converted to `@#SKIP#@` values, causing deadlocks without clear error messages.

**Fix**: 
- Modified `infra/_core/_reference.py` to add a `dev_mode` class variable
- When `dev_mode=True`, exceptions are raised instead of being converted to skip values
- Enabled in `_executor.py` by calling `set_dev_mode(True)` before orchestration
- Exposed via `infra/_core/__init__.py` public API

**Files Modified**:
- `infra/_core/_reference.py`
- `infra/_core/__init__.py`
- `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/_executor.py`

---

### 2. **Missing PromptTool Method**
**Problem**: Paradigm `v_Prompt-h_Data-c_ThinkJSON-o_Normal` called `prompt_tool.create_template_function()`, but this method didn't exist.

**Error**: `AttributeError: 'PromptTool' object has no attribute 'create_template_function'`

**Fix**: 
- Added `create_template_function()` method to `PromptTool` class
- Creates a closure function that has the template embedded
- Function accepts both positional dict and keyword arguments
- Enables composition to call template rendering without re-accessing parent meta

**Files Modified**:
- `infra/_agent/_models/_prompt.py`

**Code Added**:
```python
def create_template_function(self, template: Template):
    """Create a function that fills the template with provided variables."""
    def template_fn(*args, **kwargs):
        if args:
            if len(args) == 1 and isinstance(args[0], dict):
                variables = args[0]
            else:
                raise TypeError(f"Expected a single dict argument, got {len(args)} arguments")
        else:
            variables = kwargs
        return str(template.safe_substitute(variables))
    return template_fn
```

---

### 3. **Script Paradigm Composition Context Issue**
**Problem**: The `v_Script-h_Data-c_Execute-o_Normal` paradigm tried to reference `script_code` inside the composition plan, but composition contexts are isolated and can't access parent meta.

**Error**: `Key 'raw_script_path' not found in context` → `Key 'script_code' not found in context`

**Root Cause**: Composition tool builds its own context starting with only `__initial_input__`. MetaValues from parent context aren't automatically available inside composition.

**Fix**: 
- Added `create_function_executor()` method to `PythonInterpreterTool` 
- Creates a closure function with `script_code` and `function_name` already bound
- Function is created BEFORE entering composition, then called inside with only horizontal data
- Follows the same pattern as `template_fn` in prompt paradigm

**Files Modified**:
- `infra/_agent/_models/_python_interpreter.py`
- `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/provision/paradigm/v_Script-h_Data-c_Execute-o_Normal.json`

**Code Added**:
```python
def create_function_executor(self, script_code: str, function_name: str):
    """Creates a bound function that executes a specific function from the script."""
    def executor_fn(function_params: Dict[str, Any]) -> Any:
        return self.function_execute(script_code, function_name, function_params)
    return executor_fn
```

---

### 4. **Missing Input Concept in Inference Repository**
**Problem**: Inference 1.5.2 (narrative signal extraction) was missing `{theoretical framework}` as a value concept, even though the prompt template required it.

**Symptom**: Template had unfilled placeholders: `${theoretical_framework}` remained as literal string

**Fix**: 
- Added `{theoretical framework}` to `value_concepts` array
- Added `"{theoretical framework}": 2` to `value_order` mapping

**Files Modified**:
- `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/repos/inference_repo.json`

---

### 5. **Prompt Variable Name Mismatch**
**Problem**: Sentiment extraction prompt used `${news_data}` and `${theoretical_framework}`, but MVP step generates `input_1`, `input_2`, etc.

**Fix**: Updated prompt template to use the standardized `${input_1}`, `${input_2}` naming convention

**Files Modified**:
- `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/provision/prompts/sentiment_extraction.md`

---

### 6. **Missing main() Function in Script**
**Problem**: Script paradigm expected a `main()` function, but `technical_analysis.py` only had `compute_indicators()`

**Fix**: Added `main()` wrapper function that calls `compute_indicators()`

**Files Modified**:
- `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/provision/scripts/technical_analysis.py`

---

### 7. **Boolean Judgement Paradigm Format Mismatch**
**Problem**: Judgement prompts (`bullish_evaluation.md`, `bearish_evaluation.md`) asked for plain `true`/`false`, but paradigm expected `{"answer": true/false}`

**Error**: `AttributeError: 'bool' object has no attribute 'get'` when trying to extract "answer" field from boolean

**Fix**: Updated both evaluation prompts to return JSON format with "answer" field

**Files Modified**:
- `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/provision/prompts/bullish_evaluation.md`
- `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/provision/prompts/bearish_evaluation.md`

**Updated Format**:
```json
{
  "answer": true  // or false
}
```

---

### 8. **JSON String Not Parsed for Script Inputs (CRITICAL)**
**Problem**: When perceptual signs containing JSON were unwrapped and passed to Python scripts, they remained as **strings** instead of being parsed into **dicts**.

**Error**: `'str' object has no attribute 'get'` in `technical_analysis.py` when calling `price_data.get("data", [])`

**Root Cause**: The `collect_script_inputs()` function passed values through without checking if they were JSON strings that should be parsed.

**Impact**: This caused the quantitative signal generation (1.5.1) to fail silently in earlier runs, which then propagated through grouping and caused downstream shape mismatches.

**Fix**: 
- Modified `collect_script_inputs()` in FormatterTool to auto-parse JSON strings
- Maintains backward compatibility by catching parse errors and using raw string if parsing fails

**Files Modified**:
- `infra/_agent/_models/_formatter_tool.py`

**Code Added**:
```python
def collect_script_inputs(self, all_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Collects input_* keys and parses JSON strings automatically."""
    script_inputs = {}
    for key, value in all_inputs.items():
        if key.startswith("input_"):
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    script_inputs[key] = parsed
                except (json.JSONDecodeError, ValueError):
                    script_inputs[key] = value  # Use as-is if not JSON
            else:
                script_inputs[key] = value
    return script_inputs
```

---

## Current Execution Status

### ✅ Successfully Completing (15 inferences)

**Phase 1: Data Collection**
- ✅ 1.1: `[price data]` - File load
- ✅ 1.2: `[news data]` - File load
- ✅ 1.3: `{theoretical framework}` - File load
- ✅ 1.4: `{investor risk profile}` - File load

**Phase 2: Signal Generation**
- ✅ 1.5.1: `{quantitative signal}` - Script execution (technical_analysis.py)
- ✅ 1.5.2: `{narrative signal}` - LLM sentiment extraction
- ✅ 1.5: `{validated signal}` - Grouping (quantitative + narrative + framework)

**Phase 3: Signal Evaluation**
- ✅ 1.6: `<signals surpass theoretical expectations>` - Judgement (condition_not_met)
- ✅ 1.7: `<signals deviate from theoretical expectations>` - Judgement (condition_not_met)
- ✅ 1.8.1: `<signal status>` - Grouping boolean statuses
- ✅ 1.8: `<signals are neutral>` - Judgement (condition_not_met)

**Phase 4: Conditional Recommendations**
- ✅ 1.9.1.1.1: Timing condition for bullish
- ✅ 1.9.1.2.1: Timing condition for bearish
- ✅ 1.9.1.3.1: Timing condition for neutral
- ✅ 1.9.1.3: `{neutral recommendation}` - LLM generation (HOLD)

### ❌ Currently Failing (2 inferences)

- ❌ 1.9.1.1: `{bullish recommendation}` - **Shape mismatch: 2 vs 1**
- ❌ 1.9.1.2: `{bearish recommendation}` - **Shape mismatch: 2 vs 1**

**Blocked Downstream**:
- ⏸️ 1.9.1: `[all recommendations]` - Grouping (waiting for bullish/bearish)
- ⏸️ 1.9: `{investment decision}` - Final synthesis (waiting for all recommendations)
- ⏸️ 1: Assignment to target concept (waiting for decision)

---

## Remaining Issue: Axis Shape Mismatch

### Error Details
```
Shape mismatch for shared axis '_none_axis': 2 vs 1
```

### Root Cause Analysis

**Inputs to failing inferences**:
- `{validated signal}`: Has **2 elements** (quantitative + narrative signals)
  - According to concept_repo: `axis_name: "signal"`
  - But grouping output shows: `axes: ['_none_axis'], shape: (1,)` with **array of 2 items inside single cell**
  - Tensor: `[[item1, item2, item3]]` (quantitative, narrative, framework)
  
- `{investor risk profile}`: Has **1 element** (single loaded file)
  - According to concept_repo: `axis_name: "_none_axis"`
  - Shape: `(1,)`

**Why neutral works but bullish/bearish fail**:
- Neutral recommendation uses only `{validated signal}` (1 input)
- Bullish/bearish use `{validated signal}` + `{investor risk profile}` (2 inputs)
- When combining 2 inputs, the system tries to align axes but encounters shape mismatch

### Suspected Grouping Issue

The grouping step (1.5) is configured to group 3 concepts:
```json
"by_axis_concepts": [
  "{quantitative signal}",
  "{narrative signal}", 
  "{theoretical framework}"
]
```

**Expected behavior**: Create a new axis (e.g., "signal") with 3 elements

**Actual behavior** (from logs):
```
Reference Axes: ['_none_axis']
Reference Shape: (1,)
Reference Tensor: [[item1, item2, item3]]  ← All 3 items in a single _none_axis cell
```

**Hypothesis**: The grouping is creating a **list** inside a single cell on `_none_axis`, rather than creating a new axis dimension. This causes downstream axis alignment issues when trying to combine with other concepts.

---

## Questions for Further Investigation

1. **Grouping behavior**: Why is the grouping placing all items in a single `_none_axis` cell instead of creating a new "signal" axis?

2. **Axis inheritance**: Should `{validated signal}` inherit the `axis_name: "signal"` from its concept_repo definition, or does grouping override this?

3. **Axis alignment**: When MVP combines multiple inputs with different axes, what's the expected behavior for axis alignment and broadcasting?

4. **Value selectors**: Should we use `value_selectors` in the working_interpretation to explicitly handle axis mismatches?

---

## Files Modified During Session

### Infrastructure Core
1. `infra/_core/_reference.py` - Added dev_mode
2. `infra/_core/__init__.py` - Exposed set_dev_mode

### Agent Models (Tools)
3. `infra/_agent/_models/_prompt.py` - Added create_template_function()
4. `infra/_agent/_models/_python_interpreter.py` - Added create_function_executor()
5. `infra/_agent/_models/_formatter_tool.py` - Auto-parse JSON in collect_script_inputs()

### Paradigms
6. `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/provision/paradigm/v_Script-h_Data-c_Execute-o_Normal.json` - Complete rewrite to use bound executor functions

### Repositories
7. `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/repos/inference_repo.json` - Added missing {theoretical framework} to inference 1.5.2

### Prompts
8. `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/provision/prompts/sentiment_extraction.md` - Fixed variable names
9. `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/provision/prompts/bullish_evaluation.md` - Added "answer" wrapper
10. `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/provision/prompts/bearish_evaluation.md` - Added "answer" wrapper

### Scripts
11. `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/provision/scripts/technical_analysis.py` - Added main() wrapper

### Executor
12. `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/_executor.py` - Enabled dev_mode

---

## Key Technical Insights

### Paradigm Design Pattern: Bound Functions via Closure
Both the **Prompt paradigm** and **Script paradigm** now follow this pattern:

1. **Vertical setup (before composition)**:
   - Read the template/script file
   - Extract the content
   - Create a **bound function** with content embedded via closure

2. **Composition (with horizontal data)**:
   - Call the bound function with horizontal data only
   - No need to pass vertical data again (already bound)
   - Avoids composition context access issues

**This is the correct pattern for v_X-h_Y-c_Z paradigms in NormCode.**

### Composition Tool Context Isolation
The composition tool (`CompositionTool.compose()`) creates an **isolated execution context**:
- Starts with only `{'__initial_input__': initial_input}`
- Step outputs are added to context as they execute
- **Cannot access parent sequence's meta** directly
- All needed values must be:
  - Bound into functions via closure (vertical data)
  - Passed through `__initial_input__` (horizontal data)
  - Generated within the composition itself

### Data Type Handling
**Perceptual signs** store data as strings (JSON or otherwise). When passing to:
- **LLM prompts**: Use as-is (string templates)
- **Python scripts**: Parse JSON strings to Python dicts/lists first
- **Composition functions**: Depends on what the function expects

---

## Remaining Issues to Resolve

### Issue: Axis Shape Mismatch in Recommendations

**Failing Inferences**: 1.9.1.1 (bullish), 1.9.1.2 (bearish)

**Error**: `Shape mismatch for shared axis '_none_axis': 2 vs 1`

**Inputs**:
- `{validated signal}`: Contains [quantitative, narrative, framework] bundled in single `_none_axis` cell
- `{investor risk profile}`: Single element on `_none_axis`

**Observation**: 
The grouping step (1.5) is supposed to create a "signal" axis but instead creates a flat list within a single `_none_axis` cell. This prevents proper axis alignment when combining with other concepts.

**Potential Solutions**:
1. Fix grouping to properly create dimensional axes instead of nested lists
2. Add value_selectors to handle axis broadcasting
3. Restructure the data flow to ensure compatible shapes
4. Modify concept_repo axis definitions to align properly

### Secondary Issue: "answer" Field Extraction

**Observation**: The neutral recommendation prompt returns the full JSON object directly:
```json
{
  "action": "HOLD",
  "rationale": "...",
  "confidence": 0.65,
  ...
}
```

But the paradigm tries to extract an "answer" field, resulting in `None`. The prompt should either:
- Wrap the response: `{"answer": {"action": "HOLD", ...}}`
- Or the paradigm should use the full `parsed_json` instead of extracting "answer"

---

## Test Execution Command

```powershell
python direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/_executor.py
```

**Arguments available**:
- `--llm`: LLM model name (default: "demo")
- `--max-cycles`: Maximum orchestration cycles
- `--resume`: Resume from checkpoint
- `--run-id`: Specific run ID to resume
- `--mode`: Execution mode

---

## Next Steps

1. **Investigate grouping implementation**: Check `infra/_agent/_sequences/grouping.py` and `infra/_agent/_steps/grouping/` to understand why it's creating nested lists instead of dimensional axes

2. **Fix axis creation**: Ensure grouping creates proper axis dimensions when `by_axis_concepts` are specified

3. **Test axis alignment**: Verify that MVP can properly combine concepts with different axes (e.g., "signal" axis vs "_none_axis")

4. **Fix recommendation prompts**: Ensure all prompts return data in the expected format (with or without "answer" wrapper as needed)

5. **Complete execution**: Once axis issues are resolved, the full orchestration should complete and produce `{investment decision}`

---

## Success Metrics

**Current**: 15/17 inferences (88.2% success)  
**Target**: 20/20 inferences (100% completion)  
**Final Goal**: `{investment decision}` concept populated with actionable recommendation

---

**End of Summary**

