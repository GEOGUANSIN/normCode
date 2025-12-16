# Syntax Updates Tracking

This document tracks potential updates needed to align grammar documentation with the latest implementations in `shared---normcode_activation.md` and `shared---normcode_syntatical_concepts_reconstruction.md`.

---

## Status: Grammar Section Completeness

### ✅ Already Documented

1. **Unified Modifier System** (`%>`, `%<`, `%:`, `%^`, `%@`)
   - Fully documented in `syntactic_operators.md`
   - Examples throughout all documents

2. **Create Axis Modifier** (`%+`)
   - Documented in grouping operators section
   - Examples for both `&[{}]` and `&[#]`
   - Usage: `%+({axis_name})` to explicitly name new axes

3. **Per-Reference Grouping Mode**
   - Both legacy and per-reference modes documented
   - Examples show `%+(recommendation)` and `%+(signal)` usage

4. **Iteration Version Markers** (`*1`, `*-1`, `*0`)
   - Documented in looping operator section
   - Semantics explained

5. **Protection Markers** (`<$!{axis}>`)
   - Documented in grouping section
   - Used to prevent axis collapse

---

## 🔍 Areas to Verify/Enhance

### 1. Selection Operators (`$-`) - Extended Syntax

**Current Status**: Basic documentation exists

**From activation.md**:
```ncd
$- %>({collection}) %^(<$*0>)           # Select first item
$- %>({collection}) %^(<$*-1>)          # Select last item
$- %>({dict}) %^(<$({my_key})%>)        # Select by key
$- %>({list}) %^(<$*#>)                 # Unpack all
```

**Enhancement Needed**:
- ✅ Already documented in syntactic_operators.md lines 190-205
- Could add more examples in complete_syntax_reference.md

---

### 2. Instance Markers (`<$()%>`) - More Context

**Current Status**: Basic explanation in semantic_concepts.md

**From activation.md examples**:
```ncd
{prompt}<$({instruction distillation prompt})%>  # Marks a "prompt" role
{1}<$({input files})%>                           # Position 1, typed as "input files"
```

**Enhancement Needed**:
- ✅ Already explained in semantic_concepts.md (abstraction formalization section)
- Could add more practical examples

---

### 3. Paradigm Syntax in Functional Concepts

**Current Status**: Mentioned but not fully detailed

**From activation.md**:
```ncd
:%(composition):({prompt}<$(...)%>: {1}<$(...)%>)
```

**Enhancement Needed**:
- Add more examples of paradigm specification syntax
- Document the `:%(paradigm):` pattern more explicitly
- Could go in semantic_concepts.md or a new advanced section

---

### 4. Perception Norms and Perceptual Signs

**Current Status**: Documented in references_and_axes.md

**From activation.md**:
```ncd
%{file_location}7f2(data/input.txt)
%{literal}zero(0)
```

**Enhancement Needed**:
- ✅ Already documented in references_and_axes.md
- Examples are present

---

### 5. Value Order and Bindings

**Current Status**: Mentioned throughout

**From activation.md** - working_interpretation extraction:
```python
"value_order": {
    "{validated signal}": 1,
    "{theoretical framework}": 2
}
```

**Enhancement Needed**:
- Already shown in examples with `<:{1}>`, `<:{2}>` markers
- Could add section on how compiler determines value order

---

### 6. Branch Selectors

**From activation.md**:
```ncd
$- %>({input files}) %^(<$({original prompt})%>)
```

**Status**: 
- Documented as key selection in syntactic_operators.md
- Could add more complex selector examples

---

## 📝 Recommended Additions

### 1. Add Glossary of Auxiliary Syntax

Create a quick reference for all the inline annotations:
- `<$!{...}>` - Protection
- `<$*N>` - Iteration version
- `<$({key})%>` - Key/instance marker
- `<$={N}>` - Identity marker
- `<:{N}>` - Value placement
- `<$*#>` - Unpack all

**Status**: ✅ Already in complete_syntax_reference.md (Inline Annotations section)

---

### 2. Legacy vs. New Syntax Migration Guide

Document the transition from old syntax to new:

| Feature | Old Syntax | New Syntax |
|---------|-----------|------------|
| Group In | `&in` + separate values | `&[{}] %>[...]` |
| Group Across | `&across({x}:{y})` | `&[#] %>({y}) %:({x})` |
| Create Axis | Implicit | `%+({axis_name})` explicit |
| Loop | `*every(...)%:[...]@(N)^[...]` | `*. %>(...) %:(...) %^(...) %@(N)` |

**Status**: ✅ Already in syntactic_operators.md (Old → New mapping section)

---

### 3. Advanced Example: Full Working Interpretation

Show a complete example with:
- The `.ncd` syntax
- The extracted `working_interpretation` dict
- The runtime execution

**Status**: Could be added to execution section when that's created

---

## 🎯 Priority Updates (If Needed)

### High Priority
- ✅ None - Core syntax is documented

### Medium Priority
1. Add more examples of paradigm specification syntax
2. Expand on perception norms (if not already sufficient)
3. Add complex selector examples

### Low Priority
1. Migration guide refinements
2. More visual diagrams
3. Advanced usage patterns

---

## 📊 Overall Assessment

**Grammar section completeness: ~95%**

The core syntax is fully documented. The main additions from the activation and reconstruction docs are:

1. ✅ **`%+` modifier** - Already documented
2. ✅ **Per-reference grouping** - Already documented
3. ✅ **Selection operators** - Already documented
4. ✅ **Unified modifiers** - Fully documented
5. ✅ **Inline annotations** - Already documented

**Minor enhancements that could be made**:
- More examples of paradigm specification (`:%(paradigm):`)
- More complex selector patterns
- Link to activation/compilation examples (when those sections are created)

**Conclusion**: The grammar documentation is comprehensive and up-to-date with the latest syntax. No critical updates are needed before proceeding to the next section.

---

## Next Steps

1. Review this assessment with the user
2. Make any requested priority updates
3. Proceed to Phase 4 (Execution Section) or Phase 5 (Compilation Section)

---

**Last Updated**: During Phase 3 completion
**Reviewed Against**: 
- `shared---normcode_activation.md`
- `shared---normcode_syntatical_concepts_reconstruction.md`
