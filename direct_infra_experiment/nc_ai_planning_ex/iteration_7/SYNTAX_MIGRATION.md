# NormCode Syntax Migration Guide: iteration_6 → iteration_7

This document describes the syntax changes between the old format (iteration_6) and the new format (iteration_7) based on the updated NormCode documentation.

---

## Overview of Changes

The primary changes are:
1. **Flow indices moved from prefix to suffix** with explicit annotation
2. **Sequence types use explicit annotations** instead of embedded prefixes
3. **Comment system formalized** with three categories
4. **Operator notation updated** for clarity

---

## 1. Flow Index Format

### Old Format (iteration_6)
```
1.output|:<:({result files})
1.1.grouping|<= &across
1.2.object|<- {Phase 1}
```

### New Format (iteration_7)
```ncd
:<:{result files} | ?{flow_index}: 1
    <= &[#] | ?{flow_index}: 1.1 | ?{sequence}: grouping
    <- {Phase 1} | ?{flow_index}: 1.2
```

**Key change**: Flow index moved from `PREFIX|` to `| ?{flow_index}: VALUE`

---

## 2. Sequence Type Annotation

### Old Format
```
1.1.grouping|<= &across
1.2.2.1.imperative_::{%(composition)}|<= (...)
```

### New Format
```ncd
<= &[#] | ?{flow_index}: 1.1 | ?{sequence}: grouping
<= ::(...) | ?{flow_index}: 1.2.2.1 | ?{sequence}: imperative
```

**Key change**: Sequence type extracted to `| ?{sequence}: TYPE`

---

## 3. Comment Categories

The new format uses three distinct comment prefixes:

| Prefix | Type | Purpose | Example |
|--------|------|---------|---------|
| `?{...}:` | Syntactical | Structure metadata | `?{flow_index}: 1.2.3` |
| `%{...}:` | Referential | Data configuration | `%{paradigm}: python_script` |
| `/:` | Description | Human-readable note | `/: This computes X` |

### Annotation Lines (Multi-line metadata)
Annotations on separate lines start with `|%{...}:`:
```ncd
<- {instruction block file} | ?{flow_index}: 1.2.2
    |%{file_location}: 1.1_instruction_block.md
    |%{ref_axes}: [_none_axis]
```

---

## 4. Operator Changes

### Grouping Operators

| Old | New | Purpose |
|-----|-----|---------|
| `&across` | `&[#]` | Collect items into ordered list |
| `&in` | `&[{}]` | Group into labeled dictionary |

### Assigning Operators

| Old | New | Purpose |
|-----|-----|---------|
| `$.({type})` | `$. %<[{item1}, {item2}]` | Select from candidates |
| `$=` | `$=` | Identity assignment (unchanged) |

### Timing Operators

| Old | New | Purpose |
|-----|-----|---------|
| `@if(<cond>)` | `@:' %>(<condition>)` | Execute if condition true |
| `@if!(<cond>)` | `@:! %>(<condition>)` | Execute if condition false |
| `@after({event})` | `@. %>({dependency})` | Wait for dependency |

---

## 5. Concept Markers

### Root/Output Marker
```
Old: :<:({concept})
New: :<:{concept}
```

### Value Bindings
```
Old: <- {concept}<$={1}><:{1}>
New: <- {concept}<:{1}> | ?{flow_index}: X.X.X
```

### Instance Markers
```
Old: <$({concept})%>
New: <$({concept})%>  (unchanged)
```

---

## 6. Paradigm Annotations

### Old Format
```
1.2.2.1.imperative_::{%(composition)}|<= ({prompt}<$({...})%>)
```

### New Format
```ncd
<= ::({prompt}<$({...})%>) | ?{flow_index}: 1.2.2.1 | ?{sequence}: imperative
    |%{paradigm}: h_PromptTemplate_SavePath-c_GenerateThinkJson-Extract-Save-o_FileLocation
    |%{h_input_norm}: file_location
```

---

## 7. File Format Extensions

| Format | Old Extension | New Extension | Purpose |
|--------|---------------|---------------|---------|
| Draft (authoring) | `.ncd` with annotations | `.ncds` | Easy authoring format |
| Formalized | `.nc` | `.ncd` | Formal executable syntax |
| Natural language | `.ncn` | `.ncn` | Human-readable companion |
| Hybrid editor | N/A | `.ncdn` | Combined NCD + NCN view |

---

## 8. Complete Example Comparison

### Old Format (iteration_6)
```
1.2.object|<- {Phase 1: Confirmation of Instruction}
1.2.1.assigning|<= $.([{1.1_instruction_block.md}, {1.2_initial_context_registerd.json}])
1.2.2.object_%{file_location}:1.1_instruction_block.md|<- {1.1_instruction_block.md}
1.2.2.1.imperative_::{%(composition)}|<= ({prompt}<$({instruction distillation prompt})%>: {1}<$({input files})%>)
```

### New Format (iteration_7)
```ncd
<- {Phase 1: Confirmation of Instruction} | ?{flow_index}: 1.2
    <= $. %<[{1.1_instruction_block.md}, {1.2_initial_context_registered.json}] | ?{flow_index}: 1.2.1 | ?{sequence}: assigning
    <- {1.1_instruction_block.md} | ?{flow_index}: 1.2.2
        |%{file_location}: 1.1_instruction_block.md
        <= ::({prompt}<$({instruction distillation prompt})%>; {1}<$({input files})%>) | ?{flow_index}: 1.2.2.1 | ?{sequence}: imperative
            |%{paradigm}: h_PromptTemplate_SavePath-c_GenerateThinkJson-Extract-Save-o_FileLocation
```

---

## Quick Reference: Annotation Prefixes

```
| ?{...}:    Syntactical (flow_index, sequence, natural_language)
| %{...}:   Referential (paradigm, file_location, prompt_location, ref_axes)
| /:        Description (human-readable summary)
| ...:      Source text (un-decomposed, needs further decomposition)
| ?:        Question (guiding decomposition)
```

