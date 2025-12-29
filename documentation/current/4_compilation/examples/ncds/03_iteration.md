# Example 03: Iteration Over Collections

**Status**: ✅ Reference pattern

---

## Natural Language Instruction

```
For each document in the collection, extract key entities and collect all results.
```

---

## Derived `.ncds`

```ncds
/: Extract entities from each document in a collection

<- all extracted entities
    <= for every document in the list
    
        <= return the extracted entities per document
        
        <- extracted entities
            <= extract key entities and themes
            <- current document
    
    <- documents
    <* current document from documents
```

---

## Explanation

This pattern iterates over a collection, processing each item and collecting results.

**Structure breakdown**:
- `<- all extracted entities`: Final collection (loop output)
- `<= for every document in the list`: Loop operator (`*.`)
- `<= return the extracted entities per document`: What each iteration produces
- `<- extracted entities`: Per-iteration result
- `<= extract key entities and themes`: The semantic operation
- `<- current document`: Reference to current loop element
- `<- documents`: The base collection to iterate over
- `<* current document from documents`: Context concept marking the loop variable

**Execution**:
1. For each `current document` in `documents`
2. Extract entities → `extracted entities`
3. Collect all results → `all extracted entities`

---

## Patterns Demonstrated

1. **Loop structure**: `<= for every X` creates a quantifier loop
2. **Loop variable**: `<* current document` is the context concept
3. **Per-iteration return**: Nested `<= return` specifies what to collect
4. **Result aggregation**: All iteration results collected automatically

