# NormCode Terminology Clarification

## Overview

This document clarifies the terminology used in NormCode by comparing the formal definitions in README.md with the practical usage in the in-question analysis algorithm. It identifies areas of alignment and potential discrepancies.

## Core Terminology Alignment

### 1. Fundamental Concepts

**README Definition:**
- **Concepts**: Fundamental units with Representation, Sense, and Reference
- **Beings**: What concepts refer to in the real world
- **Objects**: Concepts representing entities, things, or defined elements
- **Judgements**: Concepts representing conditional relationships or evaluative statements
- **Imperatives**: Concepts representing actions, processes, or procedural instructions

**Algorithm Usage:**
- Uses "entities" and "objects" interchangeably
- Focuses on "processes" rather than "imperatives"
- Emphasizes "relationships" rather than "judgements"

**Clarification Needed:**
- Should standardize on "imperatives" vs "processes"
- Clarify distinction between "judgements" and "relationships"
- Define when to use "beings" vs "concepts"

### 2. Syntactic Operators

**README Definition:**
- **Assignment**: `$=`, `$.`, `$::`, `$_..._?`, `$%`
- **Sequencing**: `@If`, `@OnlyIf`, `@IfOnlyIf`, `@after`, `@by`, `@before`, `@with`, `@while`, `@afterstep`, `@until`
- **Grouping**: `&in`, `&across`, `&set`, `&pair`
- **Quantification**: `*every`, `*some`, `*count`

**Algorithm Usage:**
- Uses `$=`, `$::`, `@by`, `@onlyIf`, `@If` consistently
- Introduces `&in()` for component relationships
- Uses `$.()` for entity-to-position mapping
- Uses `::()` for compositional relationships
- Uses `$%` for abstraction operations

**Discrepancies Identified:**
- Algorithm uses `@onlyIf` while README uses `@OnlyIf` (capitalization)
- Algorithm introduces `$.()` which isn't explicitly defined in README
- Algorithm uses `::()` for composition, not defined in README grouping operators
- Algorithm uses `$%` for abstraction, which should be added to README definition

### 3. Question Types and Conditions

**README Definition:**
- **"What"**: Assignment conditions (`$=`, `$.`, `$::`, `$%`)
- **"How"**: Imperative sequence conditions (`@by`, `@after`, `@before`, `@with`)
- **"When"**: Judgement sequence conditions (`@If`, `@OnlyIf`, `@IfOnlyIf`) or object looping (`@while`, `@afterstep`, `@until`)

**Algorithm Usage:**
- **"What"**: Entity definition (`$=`) and step identification (`$=`)
- **"How"**: Main process analysis (`@by`)
- **"When"**: Consequence analysis (`@onlyIf`) and antecedent analysis (`@If`)

**Alignment Status:**
- ✅ "What" for assignment/definition aligns
- ✅ "How" for imperative sequence aligns
- ✅ "When" for judgement sequence aligns
- ⚠️ Algorithm doesn't cover all sequencing operators from README

## Specific Terminology Issues

### 1. Operator Naming Inconsistencies

| README | Algorithm | Issue |
|--------|-----------|-------|
| `@OnlyIf` | `@onlyIf` | Capitalization difference |
| `@If` | `@If` | ✅ Consistent |
| `@by` | `@by` | ✅ Consistent |
| `$=` | `$=` | ✅ Consistent |
| `$::` | `$::` | ✅ Consistent |
| `$%` | `$%` | ✅ Consistent |

### 2. Undefined Operators in Algorithm

The algorithm uses several operators not explicitly defined in README:

- `$.()` - Entity-to-position mapping
- `::()` - Compositional relationship
- `S.^()` - Component relationship under subject
- `S.<...>` - Subject-predicate grouping

### 3. Missing Algorithm Coverage

The algorithm doesn't cover these README-defined operators:

- **Assignment**: `$.` (specification)
- **Sequencing**: `@after`, `@before`, `@with`, `@while`, `@afterstep`, `@until`
- **Grouping**: `&across`, `&set`, `&pair`
- **Quantification**: `*every`, `*some`, `*count`

## Recommended Terminology Standardization

### 1. Operator Naming Convention

**Recommendation**: Use lowercase for all operators to maintain consistency
- `@onlyIf` instead of `@OnlyIf`
- `@if` instead of `@If` (if not already lowercase)

### 2. Missing Operator Definitions

**Add to README or Algorithm**:
```markdown
### Additional Operators Used in Analysis

- `$.()` - Entity-to-position mapping (maps concrete entities to template positions)
- `::()` - Compositional relationship (shows part-of relationships)
- `S.^()` - Component relationship under subject (groups components under a subject)
- `S.<...>` - Subject-predicate grouping (groups predicates under a subject)
```

### 3. Concept Type Clarification

**Standardize on**:
- **Imperatives** (not "processes") for action concepts
- **Judgements** (not "relationships") for conditional concepts
- **Objects** for entity concepts
- **Beings** when referring to real-world referents

### 4. Question Type Mapping

**Complete the mapping**:
- **"What"**: All assignment operations (`$=`, `$.`, `$::`, `$%`)
- **"How"**: All imperative sequencing (`@by`, `@after`, `@before`, `@with`)
- **"When"**: All judgement sequencing (`@If`, `@onlyIf`, `@ifOnlyIf`) and object looping (`@while`, `@until`, `@afterstep`)

## Implementation Recommendations

### 1. Update Algorithm Coverage

Extend the algorithm to handle all README-defined operators:

```markdown
### 7. Extended Sequencing Analysis
- **@after**: Future imperative sequencing
- **@before**: Past imperative sequencing  
- **@with**: Current imperative sequencing
- **@while**: Object loop while condition
- **@until**: Object loop until condition
- **@afterstep**: Object loop after step
```

### 2. Add Missing Question Types

```markdown
### 7. Specification Analysis (`$what?` with `$.`)
### 8. Abstraction Analysis (`$what?` with `$%`)
### 9. Future Sequencing Analysis (`$how?` with `@after`)
### 10. Past Sequencing Analysis (`$how?` with `@before`)
### 11. Current Sequencing Analysis (`$how?` with `@with`)
### 12. Loop Analysis (`$when?` with `@while`, `@until`, `@afterstep`)
```

### 3. Standardize Notation

Ensure consistent use of:
- Curly braces `{...}` for objects/concepts
- Question marks `{...}?` for placeholders
- Angle brackets `<...>` for reference mappings
- Parentheses `(...)` for operators and groupings

## Conclusion

The algorithm and README are largely aligned in their core concepts and approach. The main areas needing clarification are:

1. **Operator naming consistency** (capitalization)
2. **Definition of additional operators** used in the algorithm
3. **Complete coverage** of all README-defined operators in the algorithm
4. **Standardization** of concept type terminology

These clarifications will ensure that both the theoretical framework (README) and practical implementation (algorithm) use consistent terminology and provide complete coverage of the NormCode system. 