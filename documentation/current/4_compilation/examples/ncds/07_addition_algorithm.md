# Example 07: Digit-by-Digit Addition Algorithm

**Status**: ✅ Working (verified against `infra/examples/add_examples/repo/`)

---

## Natural Language Instruction

```
Add two numbers using the digit-by-digit algorithm:

1. For each number pair (carrying over from previous iteration):
   a. For each number in the pair:
      - Extract the unit place digit
   b. Collect all unit place digits together
   c. Sum the digits plus the carry-over
   d. Compute the remainder (output digit = sum mod 10)
   e. Compute the quotient (new carry-over = sum / 10)
   f. For each number in the pair:
      - Remove the last digit (number / 10)
   g. Check if all numbers are now 0
   h. Check if carry-over is 0
   i. If NOT (all zero AND carry is zero):
      - Append the new number pair and continue
   j. Otherwise, the loop ends

2. Combine all the remainder digits to form the final sum
```

---

## Derived `.ncds` (Phase 1: Addition)

```ncds
/: Digit-by-Digit Addition Algorithm
/: Demonstrates nested loops, carry-over state, and conditional termination
/: STATUS: Working - verified against infra/examples/add_examples/repo/

<- new number pair
    <= for every number pair with carry-over state
    
        <= return the remainder per iteration
        
        <- remainder
            <= get the remainder of digit sum divided by 10
                <= after digit sum
            <- digit sum
        
        <- digit sum
            <= sum all unit place values and carry-over
            <- all unit place values of numbers
                <= collect unit place values across the pair
                <- unit place value
                    <= for every number in the pair
                    
                        <= return single unit place value
                        
                        <- single unit place value
                            <= get unit place digit of number
                            <- current number in pair
                    
                    <- current number pair
                    <* current number in pair
                <* current number pair
            <- current carry-over
        
        <- number pair
            <= append new number pair to collection
                <= if NOT all numbers are 0
                    <= if carry-over is 0
                    <* carry-over number is 0?
                <* all numbers are 0?
            <- number pair to append
                <= for every number in the pair (for removing digits)
                
                    <= return number with last digit removed
                    
                    <- number with last digit removed
                        <= remove unit place digit from number
                        <- current number for appending
                
                <- current number pair
                <* current number for appending
            <- number pair
            <- all numbers are 0?
            <- carry-over number is 0?
        
        <- all numbers are 0?
            <= judge if all numbers are 0
                <= after number pair to append
            <- number pair to append
        
        <- carry-over number is 0?
            <= judge if carry-over is 0
                <= after number pair to append
            <- current carry-over
        
        <- current carry-over
            <= update carry-over from quotient
            <- carry-over
                <= find quotient of digit sum divided by 10
                    <= after digit sum
                <- digit sum
    
    <- number pair
    <* current number pair from number pair
    <^ carry-over with previous value
```

---

## Derived `.ncds` (Phase 2: Combination)

```ncds
/: Combine digits into final sum
/: Takes remainders from addition and concatenates them

<- sum
    <= combine all number digits
    <- number digits
        <= collect all new number pair values
        <- new number pair
```

---

## Key Patterns Demonstrated

### 1. Nested Loops with Different Indices

```ncds
<= for every number pair    /: @(1) - outer loop
    <- unit place value
        <= for every number in pair   /: @(2) - inner loop for extraction
        ...
    <- number pair to append
        <= for every number in pair   /: @(3) - inner loop for removal
        ...
```

The outer loop `@(1)` iterates over number pairs. Two separate inner loops `@(2)` and `@(3)` iterate over numbers within each pair.

### 2. Carry-Over State Between Iterations

```ncds
<= for every number pair with carry-over state
    ...
<^ carry-over with previous value   /: %^({carry-over}*-1)
```

The carry-over from the previous iteration (`*-1`) is available in the current iteration.

**Initial value**: `{carry-over number}*1` is ground concept initialized to `0`.

### 3. Conditional Termination via Append Gating

```ncds
<- number pair
    <= append new number pair to collection
        <= if NOT all numbers are 0      /: @:! gate
            <= if carry-over is 0        /: @:' gate (nested)
            <* carry-over number is 0?
        <* all numbers are 0?
    <- number pair to append
    ...
```

The loop terminates when:
- All numbers become 0 (all digits processed)
- AND carry-over is 0 (no final carry)

### 4. Timing Dependencies

```ncds
<- remainder
    <= get the remainder of digit sum divided by 10
        <= after digit sum    /: @. timing - wait for digit sum
    <- digit sum
```

Operations explicitly wait for dependencies using `@after` (now `@.`).

### 5. Python Script Execution (Not LLM)

This plan uses `imperative_python` sequence, executing deterministic scripts:
- `op_sum.py` - adds numbers
- `op_get_digit.py` - extracts unit digit
- `op_remove_digit.py` - divides by 10
- `op_get_quotient.py` - integer division
- `op_get_remainder.py` - modulo 10
- `op_is_zero.py` - checks if zero

---

## Flow Structure Summary

### Addition Phase (Phase 1)

| Flow Index | Concept | Sequence | Description |
|------------|---------|----------|-------------|
| `1` | `{new number pair}` | quantifying | Outer loop |
| `1.1` | loop return | assigning | Return remainder |
| `1.1.2` | `{digit sum}` | imperative_python | Sum digits + carry |
| `1.1.2.4` | `[all unit place values]` | grouping | Collect digits |
| `1.1.2.4.2` | `{unit place value}` | quantifying | Inner loop @(2) |
| `1.1.2.4.2.1` | inner return | assigning | Return digit |
| `1.1.2.4.2.1.2` | `{single unit place value}` | imperative_python | Extract digit |
| `1.1.3` | `{number pair}` | assigning | Append (continuation) |
| `1.1.3.1` | timing gate | timing | `@if!(<all is 0>)` |
| `1.1.3.1.1` | nested timing | timing | `@if(<carry is 0>)` |
| `1.1.3.2` | `{number pair to append}` | quantifying | Inner loop @(3) |
| `1.1.3.2.1` | inner return | assigning | Return truncated number |
| `1.1.3.2.1.2` | `{number with last digit removed}` | imperative_python | Remove digit |
| `1.1.3.3` | `<all number is 0>` | judgement_python | Check termination |
| `1.1.3.4` | `<carry-over is 0>` | judgement_python | Check carry |
| `1.1.3.4.2` | `{carry-over number}*1` | grouping | Update carry state |
| `1.1.3.4.2.2` | `{carry-over number}*1` | imperative_python | Compute quotient |
| `1.1.4` | `{remainder}` | imperative_python | Compute remainder |

### Combination Phase (Phase 2)

| Flow Index | Concept | Sequence | Description |
|------------|---------|----------|-------------|
| `1` | `{sum}` | imperative_python | Combine digits |
| `1.1` | `{number digits}` | grouping | Collect all remainders |

---

## Execution Trace Example

**Input**: Add 123 + 98

```
Iteration 1: [123, 98], carry=0
  - Extract digits: [3, 8]
  - Sum: 3 + 8 + 0 = 11
  - Remainder: 11 % 10 = 1  ← first output digit
  - Quotient: 11 / 10 = 1   ← new carry
  - Remove digits: [12, 9]
  - All zero? No → Append [12, 9]

Iteration 2: [12, 9], carry=1
  - Extract digits: [2, 9]
  - Sum: 2 + 9 + 1 = 12
  - Remainder: 12 % 10 = 2  ← second output digit
  - Quotient: 12 / 10 = 1   ← new carry
  - Remove digits: [1, 0]
  - All zero? No → Append [1, 0]

Iteration 3: [1, 0], carry=1
  - Extract digits: [1, 0]
  - Sum: 1 + 0 + 1 = 2
  - Remainder: 2 % 10 = 2   ← third output digit
  - Quotient: 2 / 10 = 0    ← new carry
  - Remove digits: [0, 0]
  - All zero? Yes, carry=0? Yes → STOP

Phase 2: Combine [1, 2, 2] → 221
Final result: 221
```

---

## Syntax Mapping (Old → New)

This example uses older syntax. Here's the mapping:

| Old Syntax | New Syntax | Meaning |
|------------|------------|---------|
| `*every({X})%:[{Y}]@(N)` | `*. %>({X}) %:({Y}) %@(N)` | Loop over X by Y at index N |
| `^[{carry}<*1>]` | `%^({carry}<$({carry})*-1>)` | Carry state from previous |
| `&across({X}:{Y})` | `&[#] %>({X}) %:({Y})` | Group across Y |
| `@if(<cond>)` | `@:' (<cond>)` | Execute if true |
| `@if!(<cond>)` | `@:! (<cond>)` | Execute if NOT true |
| `@after({dep})` | `@. ({dep})` | Execute after dependency |
| `$+({src}:{dest})` | `$+ %>({dest}) %<({src})` | Append src to dest |
| `$.({X})` | `$. %>({X})` | Specification select |

---

## Files

- **Addition repos**: `infra/examples/add_examples/repo/addition_*.json`
- **Combination repos**: `infra/examples/add_examples/repo/combination_*.json`
- **Input**: `infra/examples/add_examples/repo/addition_inputs.json`
- **Scripts**: `generated_scripts/op_*.py`
- **Prompts**: `generated_prompts/op_*_prompt.txt`

---

## Key Concepts Used

| Concept | Type | Description |
|---------|------|-------------|
| `{number pair}` | `{}` | Collection of number pairs to add |
| `{number pair}*1` | `{}` | Current pair in outer loop @(1) |
| `{number pair}*1*2` | `{}` | Current number in inner loop @(2) |
| `{number pair}*1*3` | `{}` | Current number in inner loop @(3) |
| `{carry-over number}*1` | `{}` | Current carry-over (loop state) |
| `{digit sum}` | `{}` | Sum of digits + carry |
| `{remainder}` | `{}` | Output digit (sum mod 10) |
| `{unit place value}` | `{}` | Extracted digit from number |
| `[all unit place values]` | `[]` | Grouped digits from pair |
| `{number with last digit removed}` | `{}` | Number after removing unit digit |
| `{number pair to append}` | `{}` | New pair for next iteration |
| `<all number is 0>` | `<>` | Termination check |
| `<carry-over number is 0>` | `<>` | Carry check |
| `{new number pair}` | `{}` | Final result (all remainders) |

---

## Why This Example Matters

This is the most algorithmically complex NormCode example, demonstrating:

1. **Nested iteration** - Multiple loop levels with different indices
2. **State accumulation** - Carry-over persists across iterations
3. **Dual termination conditions** - Both data exhaustion AND state check
4. **Non-LLM execution** - Pure Python scripts for deterministic math
5. **Multiple inner loops** - Same data processed differently in separate loops
6. **Timing dependencies** - Explicit sequencing with `@after`

It proves NormCode can express traditional algorithms, not just LLM workflows.

