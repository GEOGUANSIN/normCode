# Deprecated NormCode Patterns

This document tracks deprecated syntax patterns from older NormCode versions to help with migration and understanding legacy code.

---

## Flow Index Marking (DEPRECATED)

### Issue: Flow Index on Functional Concept

**Status**: ❌ **DEPRECATED** (older versions)

**Problem**: In some older NormCode versions, the flow index was marked on the functional concept (`<=`) instead of the concept to infer (`<-` or `:<:`). This made the functional concept's flow index serve as the inference identifier.

### Deprecated Pattern

```ncd
:<:{result}
    <= ::(compute) | ?{flow_index}: 1 | /: DEPRECATED: flow_index identifies inference
    <- {input A}
        <= ::(process A) | ?{flow_index}: 1.1 | /: DEPRECATED
        <- {raw A}
    <- {input B}
        <= ::(process B) | ?{flow_index}: 1.2 | /: DEPRECATED
        <- {raw B}
```

**Why deprecated**:
- Inconsistent with the principle that each concept should have its own address
- Makes it harder to identify which concept is being inferred
- Breaks the symmetry of flow index generation

---

### Current Pattern (CORRECT)

```ncd
:<:{result} | ?{flow_index}: 1
    <= ::(compute) | ?{flow_index}: 1.1
    <- {input A} | ?{flow_index}: 1.1.1
        <= ::(process A) | ?{flow_index}: 1.1.1.1
        <- {raw A} | ?{flow_index}: 1.1.1.1.1
    <- {input B} | ?{flow_index}: 1.1.2
        <= ::(process B) | ?{flow_index}: 1.1.2.1
        <- {raw B} | ?{flow_index}: 1.1.2.1.1
```

**Why correct**:
- Every concept line gets its own flow index
- The concept to infer is clearly marked with its flow index
- Consistent depth-based indexing
- Easy to trace which concept is at which step

---

## Migration Guide

### If You Encounter Deprecated Flow Indices

When you see:
```ncd
<- {result}
    <= ::(operation) | ?{flow_index}: 1.2.3
```

Update to:
```ncd
<- {result} | ?{flow_index}: 1.2.3
    <= ::(operation) | ?{flow_index}: 1.2.3.1
```

**Steps**:
1. Move the `?{flow_index}:` annotation from the functional concept to the concept to infer
2. Regenerate all child flow indices based on the new parent
3. Ensure every concept line has its own flow index

---

## Identification in Legacy Code

### How to Spot Deprecated Pattern

Look for:
- ✅ Functional concepts (`<=`) with `?{flow_index}:` but value concepts without
- ✅ Comments like "inference 1.2.3" referring to a functional concept's index
- ✅ Inconsistent flow index sequences (gaps in numbering)

### Example of Deprecated Code

```ncd
:<:{final report}
    <= ::(generate report) | ?{flow_index}: 1 | /: This identifies the inference
    <- {data}
        <= ::(process data) | ?{flow_index}: 2 | /: Another inference
        <- {raw data}
```

**Problems**:
- Flow indices jump from 1 to 2 (no hierarchical structure)
- Value concepts lack flow indices
- Inference identification relies on functional concepts

---

## Other Deprecated Patterns

### Old Operator Syntax (Pre-Unified Modifiers)

**Status**: ✅ **Supported but legacy**

Older operator syntax before unified modifiers:

| Operator | Old Syntax | Current Syntax |
|----------|-----------|----------------|
| Identity | `$=({source})` | `$= %>({source})` |
| Group In | `&in` + separate concepts | `&[{}] %>[{items}] %+({axis})` |
| Group Across | `&across({x}:{y})` | `&[#] %>[{items}] %+({axis})` |
| Loop | `*every(...)@(N)^[...]` | `*. %>(...) %@(N) %^(...)` |

See [Syntactic Operators](syntactic_operators.md#mapping-old-syntax-to-new) for complete mapping.

---

## Summary

| Pattern | Status | Action |
|---------|--------|--------|
| Flow index on functional concept | ❌ Deprecated | Move to concept to infer |
| Old operator syntax | ⚠️ Legacy | Update to unified modifiers when possible |
| `#` comments in NormCode | ❌ Never valid | Use `\|` or `/:` |

---

## References

- **Current syntax**: [NCD Format](ncd_format.md)
- **Operator migration**: [Syntactic Operators](syntactic_operators.md)
- **Annotation syntax**: [Annotation Check](_ANNOTATION_CHECK.md)

---

**Last Updated**: Grammar section documentation  
**Status**: Active deprecation tracking
