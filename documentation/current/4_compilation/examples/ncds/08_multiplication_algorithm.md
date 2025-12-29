# Example 08: Digit-by-Digit Multiplication Algorithm

**Status**: 📝 Draft (derived from refined instruction, not yet compiled)

---

## Natural Language Instruction (Refined)

```
Multiply two numbers using the digit-by-digit algorithm:

1. For each digit position P in the multiplier (0 = rightmost):
   a. Get the multiplier digit D at position P
   b. Compute: multiplicand × D (single-digit multiplication with carry):
      - For each digit in multiplicand (with carry starting at 0):
        - product = multiplicand_digit × D + carry
        - result_digit = product mod 10
        - new_carry = product div 10
        - Append result_digit to partial product
        - Continue while multiplicand has digits OR carry > 0
   c. Shift result left by P positions (append P zeros to the right)
   d. Collect as partial product

2. Sum all partial products using digit-by-digit addition

Result: the product
```

---

## Derived `.ncds`

```ncds
/: ========================================
/: Example 08: Digit-by-Digit Multiplication
/: ========================================
/: Multiplies two numbers using nested loops
/: and partial product accumulation.
/: STATUS: Draft - derived from refined instruction
/:
/: Input: multiplicand, multiplier
/: Output: product

<- product
    <= sum all partial products
    /: Reuses addition algorithm to sum partial products
    <- all partial products
        <= for each multiplier digit position
        /: Outer loop over positions (0, 1, 2, ...) from right
        
            <= return shifted partial product per position
            
            <- shifted partial product
                <= shift partial result left by position
                /: Append 'position' zeros to the right
                <- partial result
                    <= multiply multiplicand by single digit with carry
                    /: Inner computation - multiplicand × one digit
                    
                    <- single digit multiplication result
                        <= for each multiplicand digit with carry state
                        /: Nested loop over multiplicand digits
                        
                            <= return result digit per multiplicand digit
                            
                            <- result digit
                                <= get remainder of digit product divided by 10
                                    <= after digit product
                                <- digit product
                            
                            <- digit product
                                <= compute multiplicand digit times multiplier digit plus carry
                                <- current multiplicand digit
                                    <= extract unit digit from current multiplicand
                                    <- current multiplicand
                                <- multiplier digit
                                    /: From outer loop - the single digit we're multiplying by
                                <- current carry
                            
                            <- multiplicand digits
                                <= append next multiplicand state
                                    <= if NOT all done
                                        <= if carry is 0
                                        <* carry is 0?
                                    <* all multiplicand digits processed?
                                <- next multiplicand state
                                    <= remove unit digit from current multiplicand
                                    <- current multiplicand
                                <- multiplicand digits
                                <- all multiplicand digits processed?
                                <- carry is 0?
                            
                            <- all multiplicand digits processed?
                                <= judge if current multiplicand is 0
                                    <= after next multiplicand state
                                <- next multiplicand state
                            
                            <- carry is 0?
                                <= judge if current carry is 0
                                    <= after next multiplicand state
                                <- current carry
                            
                            <- current carry
                                <= update carry from quotient
                                <- new carry
                                    <= get quotient of digit product divided by 10
                                        <= after digit product
                                    <- digit product
                        
                        <- multiplicand digits
                        <* current multiplicand from multiplicand digits
                        <^ carry with previous value starting at 0
                    
                    <- multiplicand
                
                <- position
            
            <- multiplier digit
                <= extract digit at position from multiplier
                <- multiplier
                <- position
        
        <- multiplier positions
            <= generate position indices from multiplier
            /: Creates [0, 1, 2, ...] for each digit position
            <- multiplier
        <* position in multiplier positions
    
    <- multiplicand
    <- multiplier
```

---

## Key Patterns Demonstrated

### 1. Triple-Level Nesting

```
Outer: for each multiplier position
  Middle: multiply multiplicand by single digit
    Inner: for each multiplicand digit with carry
```

This is one level deeper than the addition algorithm.

### 2. Composition (Reuse of Addition)

```ncds
<- product
    <= sum all partial products   ← This IS the addition algorithm
    <- all partial products
```

The final step reuses the addition algorithm from Example 07.

### 3. Position-Based Shifting

```ncds
<- shifted partial product
    <= shift partial result left by position
    <- partial result
    <- position
```

Each partial product is shifted based on which multiplier digit produced it.

### 4. Same Termination Pattern as Addition

```ncds
<= append next state
    <= if NOT all done
        <= if carry is 0
        <* carry is 0?
    <* all digits processed?
```

Loop continues while digits remain OR carry exists.

---

## Execution Trace Example

**Input**: 123 × 45

**Phase 1: Generate Partial Products**

```
Position 0 (digit 5):
  123 × 5:
    3 × 5 + 0 = 15 → digit=5, carry=1
    2 × 5 + 1 = 11 → digit=1, carry=1
    1 × 5 + 1 = 6  → digit=6, carry=0
    All done, carry=0 → STOP
  Partial: 615
  Shift by 0: 615

Position 1 (digit 4):
  123 × 4:
    3 × 4 + 0 = 12 → digit=2, carry=1
    2 × 4 + 1 = 9  → digit=9, carry=0
    1 × 4 + 0 = 4  → digit=4, carry=0
    All done, carry=0 → STOP
  Partial: 492
  Shift by 1: 4920

All partial products: [615, 4920]
```

**Phase 2: Sum Partial Products**

```
615 + 4920 = 5535
```

**Result**: 5535 ✓

---

## Comparison: Addition vs. Multiplication

| Aspect | Addition | Multiplication |
|--------|----------|----------------|
| Nesting depth | 2 levels | 3 levels |
| Per-digit operation | a + b + carry | a × b + carry |
| Outer loop | Digit positions | Multiplier positions |
| Inner loop | Numbers in pair | Multiplicand digits |
| Additional step | — | Position shifting |
| Final aggregation | Direct output | Sum partial products |

---

## Flow Structure

| Level | Concept | Loop/Operation |
|-------|---------|----------------|
| 1 | `{product}` | Sum all partial products |
| 1.1 | `{all partial products}` | For each multiplier position |
| 1.1.1 | `{shifted partial product}` | Shift by position |
| 1.1.1.1 | `{partial result}` | Multiply by single digit |
| 1.1.1.1.1 | `{result digit}` | For each multiplicand digit |
| 1.1.1.1.1.1 | `{digit product}` | Compute product + carry |
| 1.1.1.1.1.2 | `{new carry}` | Quotient (div 10) |
| 1.1.1.1.1.3 | `{result digit}` | Remainder (mod 10) |

---

## Atomic Operations (Python Scripts)

| Operation | Input | Output |
|-----------|-------|--------|
| `extract_digit_at_position` | number, position | single digit |
| `multiply_add` | a, b, carry | product |
| `mod_10` | number | remainder |
| `div_10` | number | quotient |
| `shift_left` | number, positions | shifted number |
| `is_zero` | number | boolean |
| `sum_list` | list of numbers | total (uses addition) |

---

## Why This Example Matters

1. **Demonstrates composition** — Reuses addition algorithm
2. **Shows deeper nesting** — 3 levels vs. 2 in addition
3. **Position-aware processing** — Shifting based on index
4. **Same patterns scale** — Carry-over, conditional termination work the same way

---

## Files

- **Example**: `documentation/current/4_compilation/examples/ncds/08_multiplication_algorithm.md`
- **NCDS**: `documentation/current/4_compilation/examples/ncds/08_multiplication_algorithm.ncds`
- **Related**: Example 07 (Addition Algorithm)

