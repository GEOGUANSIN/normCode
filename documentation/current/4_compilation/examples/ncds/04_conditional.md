# Example 04: Conditional Execution

**Status**: ✅ Reference pattern

---

## Natural Language Instruction

```
Validate the draft output. If validation fails, apply corrections. 
Return either the original (if valid) or the corrected version.
```

---

## Derived `.ncds`

```ncds
/: Validation with conditional correction

<- final output
    <= select the first valid result
    <- corrected output
        <= apply corrections to fix issues
            <= if validation did NOT pass
            <* validation passed?
        <- draft output
        <- validation errors
    <- draft output
        <= generate initial draft
        <- input data
    <- validation passed?
        <= check if output meets requirements
        <- draft output
        <- requirements

<- validation errors
    <= extract the specific errors found
        <= if validation did NOT pass
        <* validation passed?
    <- draft output
    <- requirements
```

---

## Explanation

This pattern uses conditional execution (timing operators) to only run certain operations when conditions are met.

**Structure breakdown**:
- `<= select the first valid result`: Selection operator (`$.`) picks first non-skip value
- `<= if validation did NOT pass`: Timing gate (`@:!`) - only runs when condition is FALSE
- `<* validation passed?`: The condition being checked (context concept)

**Execution**:
1. Generate `draft output`
2. Check if `validation passed?` (judgement)
3. If validation passed: `corrected output` is SKIPPED
4. If validation failed: `apply corrections` runs
5. `select the first valid result` picks whichever is available

---

## Patterns Demonstrated

1. **Conditional timing**: `<= if X` / `<= if NOT X` gates execution
2. **Judgement concept**: `validation passed?` is a proposition (`<>`)
3. **Selection operator**: Picks first available (non-skip) value
4. **Context reference**: `<* validation passed?` links condition to gated operation

