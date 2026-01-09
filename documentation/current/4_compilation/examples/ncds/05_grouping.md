# Example 05: Grouping Multiple Results

**Status**: ✅ Reference pattern

---

## Natural Language Instruction

```
Collect the user's query, the database results, and the generated summary 
together as a single response bundle.
```

---

## Derived `.ncds`

```ncds
/: Bundle multiple results into a single structured output

<- response bundle
    <= bundle the query, results, and summary together
    <- user query
    <- database results
        <= query the database
        <- user query
    <- generated summary
        <= summarize the results
        <- database results
```

---

## Explanation

This pattern groups multiple concepts into a single structured output using the `&[{}]` (group in) operator.

**Structure breakdown**:
- `<= bundle ... together`: Grouping operation — collects children into a dict-like structure
- Three value concepts at the same level become labeled entries

**Resulting structure**:
```json
{
  "{user query}": "...",
  "{database results}": [...],
  "{generated summary}": "..."
}
```

**Execution**:
1. Receive `user query` (input)
2. Run `query the database` → `database results`
3. Run `summarize the results` → `generated summary`
4. Bundle all three → `response bundle`

---

## Patterns Demonstrated

1. **Grouping operator**: `bundle X, Y, Z together` → `&[{}]`
2. **Labeled structure**: Each input keeps its name as a key
3. **Mixed dependencies**: Some inputs are raw, some are derived
4. **Syntactic operation**: Grouping is FREE (no LLM call)

---

## Variant: Flat Collection

If you want a flat list instead of labeled dict:

```ncds
/: Collect into a flat list

<- all signals
    <= collect all signals into a list
    <- signal A
    <- signal B
    <- signal C
```

This uses `&[#]` (group across) instead of `&[{}]` (group in).

| Grouping Type | Natural Language | Result |
|---------------|------------------|--------|
| `&[{}]` (group in) | "bundle together", "combine as structure" | `{A: ..., B: ..., C: ...}` |
| `&[#]` (group across) | "collect into list", "gather all" | `[..., ..., ...]` |

