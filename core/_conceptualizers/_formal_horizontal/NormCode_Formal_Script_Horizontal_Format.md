# NormCode Formal Script Horizontal Format

## Overview

This document provides a comprehensive guide to writing NormCode formal scripts using the **horizontal layout format**. The horizontal format expresses all elements in a single line with explicit opening and closing markers, making it suitable for compact representation and automated processing.

## Core Principles

### Horizontal Layout Structure

The horizontal format uses a **linear representation** where all elements are expressed in a single line with explicit scope boundaries. This format is **semantically equivalent** to the vertical layout but differs in visual presentation.

### Scope Boundary Markers

**Opening Markers**: `|index|` - Begin an element's scope
**Closing Markers**: `|/index|` - End an element's scope
**Content**: The actual NormCode content between opening and closing markers

## Basic Syntax

### Element Structure

```NormCode
|index|content|/index|
```

Where:
- `index` is the hierarchical index number (optional but recommended)
- `content` is the NormCode element content
- `|/index|` closes the element's scope

### Indexing System

The horizontal format uses a **hierarchical indexing system** for precise element reference:

- **Root Level**: Single digit (1, 2, 3, ...)
- **Nested Levels**: Dot notation (1.1, 1.2, 1.1.1, 1.1.2, ...)
- **Sibling Elements**: Increment last number (1.1, 1.2, 1.3, ...)
- **Child Elements**: Add new level (1.1.1, 1.1.2, ...)

## Core Operators in Horizontal Format

### Functional Operator: `<=`

Establishes **functional relationships** and **definitions**:

```NormCode
|1|_concept_ |1.1|<= _primary_functional_ |/1.1||/1|
```

### Value Operator: `<-`

Establishes **value relationships** derived from functional relationships:

```NormCode
|1|_concept_ |1.1|<= _primary_functional_ |/1.1| |1.2|<- _derived_value_ |/1.2||/1|
```

## Assignment Operators

### Entity Assignment: `$=`

```NormCode
|1|_entity_ |1.1|$= _definition_ |/1.1||/1|
```

### Specification Assignment: `$.`

```NormCode
|1|_entity_ |1.1|$. _specification_ |/1.1||/1|
```

### Composition Assignment: `$::`

```NormCode
|1|_entity_ |1.1|$:: _composition_ |/1.1||/1|
```

### Abstraction Assignment: `$%`

```NormCode
|1|_entity_ |1.1|$% _abstraction_ |/1.1||/1|
```

## Sequencing Operators

### Conditional Sequencing: `@If`

```NormCode
|1|_process_ |1.1|@If _condition_ |1.1.1|<= _antecedent_ |/1.1.1||/1.1||/1|
```

### Consequence Sequencing: `@onlyIf`

```NormCode
|1|_process_ |1.1|@onlyIf _consequence_ |1.1.1|<= _implication_ |/1.1.1||/1.1||/1|
```

### Imperative Sequencing: `@by`

```NormCode
|1|_process_ |1.1|@by _method_ |1.1.1|<= _procedure_ |/1.1.1||/1.1||/1|
```

### Temporal Sequencing: `@after`, `@before`, `@with`

```NormCode
|1|_process_ |1.1|@after _preceding_action_ |/1.1| |1.2|@before _following_action_ |/1.2| |1.3|@with _concurrent_action_ |/1.3||/1|
```

### Loop Sequencing: `@while`, `@until`, `@afterstep`

```NormCode
|1|_process_ |1.1|@while _condition_ |/1.1| |1.2|@until _termination_ |/1.2| |1.3|@afterstep _step_action_ |/1.3||/1|
```

## Grouping Operators

### Inclusion Grouping: `&in`

```NormCode
|1|_collection_ |1.1|&in _container_ |1.1.1|<= _membership_ |/1.1.1||/1.1||/1|
```

### Cross-Reference Grouping: `&across`

```NormCode
|1|_relationship_ |1.1|&across _domains_ |1.1.1|<= _cross_domain_ |/1.1.1||/1.1||/1|
```

### Set Grouping: `&set`

```NormCode
|1|_set_ |1.1|&set _elements_ |1.1.1|<= _set_members_ |/1.1.1||/1.1||/1|
```

### Pair Grouping: `&pair`

```NormCode
|1|_pair_ |1.1|&pair _first_second_ |1.1.1|<= _pair_relationship_ |/1.1.1||/1.1||/1|
```

## Quantification Operators

### Universal Quantification: `*every`

```NormCode
|1|_universal_ |1.1|*every _domain_ |1.1.1|<= _universal_property_ |/1.1.1||/1.1||/1|
```

### Existential Quantification: `*some`

```NormCode
|1|_existential_ |1.1|*some _domain_ |1.1.1|<= _existential_property_ |/1.1.1||/1.1||/1|
```

### Count Quantification: `*count`

```NormCode
|1|_counted_ |1.1|*count _quantity_ |1.1.1|<= _count_condition_ |/1.1.1||/1.1||/1|
```

## Advanced Operators

### Entity-to-Position Mapping: `$.()`

```NormCode
|1|_entity_ |1.1|$.() _position_mapping_ |1.1.1|<= _mapping_function_ |/1.1.1||/1.1||/1|
```

### Compositional Relationship: `::()`

```NormCode
|1|_composition_ |1.1|::() _part_whole_ |1.1.1|<= _compositional_structure_ |/1.1.1||/1.1||/1|
```

### Component Relationship: `S.^()`

```NormCode
|1|_subject_ |1.1|S.^() _component_ |1.1.1|<= _component_relationship_ |/1.1.1||/1.1||/1|
```

### Subject-Predicate Grouping: `S.<...>`

```NormCode
|1|_subject_ |1.1|S.<predicate> |1.1.1|<= _predicate_relationship_ |/1.1.1||/1.1||/1|
```

## Question Type Mapping

### "What" Questions (Assignment)

```NormCode
|1|_what_entity_ |1.1|$= _definition_ |/1.1| |1.2|$. _specification_ |/1.2| |1.3|$:: _composition_ |/1.3| |1.4|$% _abstraction_ |/1.4||/1|
```

### "How" Questions (Imperative Sequencing)

```NormCode
|1|_how_process_ |1.1|@by _method_ |/1.1| |1.2|@after _sequence_ |/1.2| |1.3|@before _prerequisite_ |/1.3| |1.4|@with _concurrent_ |/1.4||/1|
```

### "When" Questions (Judgement Sequencing)

```NormCode
|1|_when_condition_ |1.1|@If _antecedent_ |/1.1| |1.2|@onlyIf _consequence_ |/1.2| |1.3|@while _loop_condition_ |/1.3| |1.4|@until _termination_ |/1.4||/1|
```

## Complex Examples

### Multi-Level Inference Structure

```NormCode
|1|_inferred_concept_ |1.1|<= _primary_functional_ |1.1.1|<= _secondary_functional_ |1.1.1.1|<= _tertiary_functional_ |/1.1.1.1| |1.1.1.2|<- _value_for_tertiary_ |/1.1.1.2||/1.1.1| |1.1.2|<- _value_for_secondary_ |/1.1.2||/1.1| |1.2|<- _derived_value_ |1.2.1|<= _functional_for_derived_ |/1.2.1| |1.2.2|<- _values_for_derived_ |/1.2.2||/1.2||/1|
```

### Process with Multiple Conditions

```NormCode
|1|_process_execution_ |1.1|@by _main_method_ |1.1.1|<= _procedure_steps_ |/1.1.1||/1.1| |1.2|@If _condition_met_ |1.2.1|<= _antecedent_check_ |/1.2.1||/1.2| |1.3|@onlyIf _expected_outcome_ |1.3.1|<= _consequence_validation_ |/1.3.1||/1.3| |1.4|@with _supporting_action_ |1.4.1|<= _concurrent_process_ |/1.4.1||/1.4||/1|
```

### Entity with Multiple Relationships

```NormCode
|1|_complex_entity_ |1.1|$= _core_definition_ |/1.1| |1.2|$:: _compositional_parts_ |1.2.1|<= _part_whole_relationship_ |/1.2.1||/1.2| |1.3|&in _container_context_ |1.3.1|<= _membership_condition_ |/1.3.1||/1.3| |1.4|*every _universal_property_ |1.4.1|<= _universal_condition_ |/1.4.1||/1.4||/1|
```

## Best Practices

### 1. Consistent Indexing

Always use consistent indexing patterns:
- Start with single digits for root elements
- Use dot notation for nesting
- Increment numbers for siblings
- Maintain hierarchical relationships

### 2. Proper Scope Closure

Ensure every opening marker has a corresponding closing marker:
- `|1|` must have `|/1|`
- `|1.1|` must have `|/1.1|`
- Check for balanced opening/closing pairs

### 3. Logical Grouping

Group related elements under common parents:
- Functional relationships under primary functionals
- Value relationships under their functional parents
- Sequencing elements under process definitions

### 4. Readability

Use spacing and formatting for readability:
- Add spaces between major sections
- Align related elements
- Use consistent indentation in your editor

### 5. Validation

Validate your horizontal format by:
- Checking for balanced markers
- Verifying hierarchical relationships
- Testing semantic equivalence with vertical format

## Conversion Guidelines

### From Vertical to Horizontal

1. **Identify root elements** and assign index numbers
2. **Map nested elements** using dot notation
3. **Add opening markers** `|index|` before each element
4. **Add closing markers** `|/index|` after each element's scope
5. **Maintain semantic relationships** between elements

### From Horizontal to Vertical

1. **Parse opening markers** to identify element hierarchy
2. **Use indentation** to represent nesting levels
3. **Remove index numbers** (optional in vertical format)
4. **Maintain logical structure** and relationships

## Common Patterns

### Template Pattern

```NormCode
|1|_template_ |1.1|<= _template_structure_ |1.1.1|{placeholder}? |/1.1.1||/1.1| |1.2|<- _concrete_instance_ |1.2.1|<reference_mapping> |/1.2.1||/1.2||/1|
```

### Reference Pattern

```NormCode
|1|_reference_ |1.1|<= _reference_structure_ |1.1.1|<source_target> |/1.1.1||/1.1| |1.2|<- _bidirectional_link_ |1.2.1|<= _link_properties_ |/1.2.1||/1.2||/1|
```

### Validation Pattern

```NormCode
|1|_validation_ |1.1|<= _validation_criteria_ |/1.1| |1.2|<- _validation_result_ |1.2.1|<= _result_properties_ |/1.2.1||/1.2||/1|
```

## Conclusion

The horizontal format provides a compact, linear representation of NormCode formal scripts that is semantically equivalent to the vertical format. By mastering the indexing system, scope boundaries, and operator syntax, you can create precise and unambiguous formal representations suitable for automated processing and systematic analysis.

Key advantages of the horizontal format:
- **Compact representation** for complex structures
- **Explicit scope boundaries** for clear element relationships
- **Indexing system** for precise element reference
- **Automated processing** compatibility
- **Semantic equivalence** with vertical format

This format is particularly useful for:
- Database storage and retrieval
- Automated parsing and validation
- Compact documentation
- Cross-referencing and linking
- Systematic analysis workflows 