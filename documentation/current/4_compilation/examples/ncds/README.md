# NormCode Derivation Examples

This directory contains verified `.ncds` examples paired with their natural language instructions.

---

## Purpose

These examples demonstrate:
1. How to express natural language intent as `.ncds` structure
2. Common patterns that translate cleanly to executable plans
3. The relationship between instruction → `.ncds` → compiled repos

---

## Examples Index

| # | Name | Complexity | Key Patterns |
|---|------|------------|--------------|
| **00** | [Simple Linear](00_simple_linear.md) | ⭐ Basic | Linear chain, data isolation |
| **01** | [Chat Session](01_chat_session.md) | ⭐⭐⭐ Advanced | Self-seeding loop, blocking I/O, conditional append |
| **02** | [Multi-Input](02_multi_input.md) | ⭐⭐ Intermediate | Parallel branches, synthesis |
| **03** | [Iteration](03_iteration.md) | ⭐⭐ Intermediate | Loop over collection, aggregation |
| **04** | [Conditional](04_conditional.md) | ⭐⭐ Intermediate | Timing gates, judgement, selection |
| **05** | [Grouping](05_grouping.md) | ⭐⭐ Intermediate | Bundling results, structured output |
| **06** | [Investment Decision](06_investment_decision.md) | ⭐⭐⭐ Advanced | Multi-source, judgement branches, axis-aware conditionals |
| **06** | (Chinese: `06_investment_decision_chinese.ncds`) | ⭐⭐⭐ Advanced | Same as above, in Chinese (中文) |
| **07** | [Addition Algorithm](07_addition_algorithm.md) | ⭐⭐⭐⭐ Expert | Nested loops, carry-over state, dual termination, Python scripts |
| **08** | [Multiplication Algorithm](08_multiplication_algorithm.md) | ⭐⭐⭐⭐⭐ Expert | Triple nesting, composition, position shifting |

---

## File Structure

Each example has:
- `XX_name.md` — Detailed explanation with instruction and patterns
- `XX_name.ncds` — Standalone `.ncds` file

---

## Pattern Reference

### Basic Patterns

| Pattern | Natural Language | `.ncds` Structure |
|---------|------------------|-------------------|
| **Linear chain** | "A then B" | B depends on A (A is child) |
| **Multiple inputs** | "Combine A and B" | A and B are sibling children |
| **Selection** | "Use A or B" | Both as children, select operator |

### Loop Patterns

| Pattern | Natural Language | `.ncds` Structure |
|---------|------------------|-------------------|
| **For each** | "For each X do Y" | `<= for every X`, `<* X` |
| **Self-seeding** | "Keep going until done" | Empty init + conditional append |
| **Accumulation** | "Collect all results" | `<= append X to Y` in loop |

### Control Flow Patterns

| Pattern | Natural Language | `.ncds` Structure |
|---------|------------------|-------------------|
| **Conditional** | "If X then Y" | `<= if X`, `<* X` |
| **Negated conditional** | "If NOT X then Y" | `<= if NOT X`, `<* X` |
| **Judgement** | "Check if X" | `<= judge if X` (produces `<>`) |

### Advanced Patterns

| Pattern | Natural Language | `.ncds` Structure |
|---------|------------------|-------------------|
| **Multiple judgements** | "If bullish do A, if bearish do B" | Separate branches with own timing gates |
| **Axis-aware grouping** | "Combine signals from different sources" | `<= collect X and Y together` creates axis |
| **Per-element evaluation** | "For each signal, check if..." | Judgement produces boolean mask |
| **Derived condition** | "Neutral = not bullish AND not bearish" | Evaluate from grouped status |
| **Conditional bundling** | "Bundle only the applicable recommendations" | Each branch gated, then grouped |

### I/O Patterns

| Pattern | Natural Language | `.ncds` Structure |
|---------|------------------|-------------------|
| **External input** | "Wait for user input" | `<= read user input` (`:>:`) |
| **External output** | "Send response to user" | `<= send response` (`:():`) |
| **Blocking** | "Wait until..." | I/O operation blocks iteration |

### Algorithmic Patterns (Non-LLM)

| Pattern | Natural Language | `.ncds` Structure |
|---------|------------------|-------------------|
| **Nested loops** | "For each X, for each Y in X" | Multiple `<*` at different depths with indices `@(N)` |
| **Carry-over state** | "With carry from previous" | `<^ carry with previous` (`%^()`) |
| **Dual termination** | "Stop when A AND B" | Two `<*` judgements gating append |
| **State initialization** | "Start with 0" | Ground concept with `reference_data: ["%(0)"]` |
| **Timing dependency** | "After X is computed" | `<= after X` (`@.`) |
| **Python execution** | "Compute exactly" | `imperative_python` sequence (not LLM) |

---

## Usage

### For Learning Derivation

1. Read the natural language instruction
2. Study the `.ncds` structure
3. Trace the bottom-up execution
4. Understand which patterns apply

### For LLM-Assisted Derivation

Include these examples in prompts to help LLMs generate correct `.ncds`:

```
Given these examples of instruction → .ncds conversion:

[Include relevant examples]

Now convert this instruction to .ncds:
[Your instruction]
```

### For Testing Compilation

Each example can be used to test the derivation → formalization pipeline:

```bash
# Example workflow (when tooling is available)
python compile.py examples/ncds/01_chat_session.ncds --to ncd
```

---

## Status Legend

| Status | Meaning |
|--------|---------|
| ✅ Working | Verified against compiled repos |
| ✅ Reference | Standard pattern, not end-to-end tested |
| 🔄 Draft | Needs review |

---

## Adding New Examples

1. Create `XX_name.md` with:
   - Natural language instruction
   - Derived `.ncds`
   - Explanation of patterns
   - Status indicator

2. Create `XX_name.ncds` with:
   - Comment header indicating status
   - The standalone `.ncds` content

3. Update this README's index

---

## Related Documentation

- [Derivation](../derivation.md) — Phase 1 specification
- [Formalization](../formalization.md) — Phase 2: `.ncds` → `.ncd`
- [Examples (Grammar)](../../1_intro/examples.md) — More pattern examples

