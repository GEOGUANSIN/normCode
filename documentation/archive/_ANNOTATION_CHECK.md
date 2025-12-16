# NormCode Annotation Syntax Verification

**Date**: Grammar Section Review  
**Issue**: Ensure correct annotation syntax in all NormCode examples

---

## ✅ Correct NormCode Annotation Syntax

### 1. Normal Annotations (with `|`)

```ncd
<- {concept} | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <= ::(operation) | ?{sequence}: imperative | /:Description of operation
    <- {input} | ?{flow_index}: 1.1.1
```

**Components**:
- `|` - Separates annotation from concept
- `?{...}:` - Syntactical comments (flow_index, sequence, natural_language)
- `%{...}:` - Referential comments (paradigm, location_string)

> **Important**: Flow indices (`?{flow_index}:`) should be marked on the **concept to infer** (the value concept `<-` or output marker `:<:`), not on the functional concept. Older versions sometimes marked it on the functional concept—this is deprecated.

### 2. Meta Annotations (with `/:`)

```ncd
<- {result} /: This is the final result concept
    <= ::(compute) /: This computes the result
    <- {input} /: This is the input data
```

**Purpose**: Human-readable descriptions marking concepts as complete.

---

## ❌ INCORRECT Syntax (Do Not Use)

### Using `#` for comments

```ncd
<- {result}    # WRONG: Don't use # in NormCode
    <= ::(compute)    # WRONG: This is Python-style comment
```

**Why wrong**: `#` is not part of NormCode annotation syntax. Use `|` or `/:` instead.

---

## 📊 Verification Results

### Files Checked
- ✅ `ncd_format.md`
- ✅ `semantic_concepts.md`
- ✅ `syntactic_operators.md`
- ✅ `references_and_axes.md`
- ✅ `complete_syntax_reference.md`

### Changes Made

1. **ncd_format.md**:
   - ✅ Flow index example updated to use `| ?{flow_index}:` syntax
   - ✅ All NormCode examples now use proper annotations

2. **syntactic_operators.md**:
   - ✅ Selection operator examples updated to use `/:` for descriptions

3. **complete_syntax_reference.md**:
   - ✅ Flow index example updated to use `| ?{flow_index}:` syntax

4. **references_and_axes.md**:
   - ✅ Verified all `#` uses are in Python code blocks (correct)
   - ✅ No incorrect `#` usage in NormCode blocks

---

## 🔍 Special Cases (Acceptable)

### 1. Python Code Blocks

```python
# This is fine - Python uses # for comments
grades.get(student=0, assignment=1)  # Returns 95
result = cross_product([ref1, ref2])  # Combine references
```

**Status**: ✅ **Correct** - Python comments should use `#`

### 2. Pseudo-code Structure Annotations

```python
students: [
    [ //: class = "A"    # Illustrative comment showing structure
        [ //: nationality = "American"
            John Doe,
        ]
    ]
]
```

**Status**: ✅ **Acceptable** - These are illustrative comments in Python blocks showing tensor structure, not actual NormCode syntax

### 3. Markdown Headers

```markdown
## Section Title
### Subsection
```

**Status**: ✅ **Correct** - Markdown uses `#` for headers, not related to NormCode

---

## 📝 Summary of NormCode Annotation Rules

| Context | Syntax | Example | Status |
|---------|--------|---------|--------|
| **Normal annotation** | `\| text` | `<- {x} \| ?{flow_index}: 1.1` | ✅ Use |
| **Meta/description** | `/: text` | `<- {x} /: This is X` | ✅ Use |
| **Syntactical comment** | `\| ?{...}: value` | `\| ?{sequence}: imperative` | ✅ Use |
| **Referential comment** | `\| %{...}: value` | `\| %{paradigm}: composition` | ✅ Use |
| **Python comment** | `# text` | `grades.get()  # Returns 95` | ✅ In Python only |
| **NormCode comment** | `# text` | `<- {x}  # comment` | ❌ Never use |

---

## ✅ Verification Complete

All NormCode examples in the grammar documentation now use correct annotation syntax:
- `|` for normal annotations
- `/:` for meta annotations/descriptions
- NO use of `#` in NormCode blocks

**Status**: Grammar section annotation syntax is correct and consistent.

---

## Reference

From `shared---normcode_formalism_basic.md`:

> A line in Normcode can also have optional comments for clarity, control, and metadata:
>
> `_concept_definition_ (optionally new line) | _comment_`
>
> - **`_concept_definition_`**: The core functional (`<=`), value (`<-`), or context (`<*`) statement.
> - **`_comment_`**: Optional metadata or description following the `|` symbol.
