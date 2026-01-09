# Example 00: Simple Linear Workflow

**Status**: ✅ Reference pattern

---

## Natural Language Instruction

```
Summarize a document by first cleaning it and then extracting key points.
```

---

## Derived `.ncds`

```ncds
/: Simple document summarization pipeline

<- document summary
    <= summarize this text
    <- clean text
        <= extract main content, removing headers
        <- raw document
```

---

## Explanation

This is the simplest NormCode pattern: a linear chain of operations.

**Execution order** (bottom-up):
1. Start with `raw document` (input)
2. Run `extract main content, removing headers` → produces `clean text`
3. Run `summarize this text` → produces `document summary`

**Key insight**: The summarization step **cannot see** `raw document`. It only receives `clean text`. This is data isolation in action.

---

## Structure After Formalization

```ncd
:<:{document summary} | ?{flow_index}: 1
    <= ::(summarize this text) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {clean text} | ?{flow_index}: 1.2
        <= ::(extract main content, removing headers) | ?{flow_index}: 1.2.1 | ?{sequence}: imperative
        <- {raw document} | ?{flow_index}: 1.2.1.1
```

---

## Patterns Demonstrated

1. **Linear dependency chain**: Each step depends on the previous
2. **Data isolation**: Summarizer never sees raw document
3. **Two LLM calls**: Both operations are imperatives (semantic)

