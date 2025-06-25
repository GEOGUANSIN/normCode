# NormCode Formal Script Inference Syntax

## Overview

NormCode is a formal notation system for representing semantic relationships, logical structures, and procedural instructions. This document provides a comprehensive explanation of the syntax elements used in NormCode formal scripts to model inference and systematic plan of inference, with particular focus on the core operators `<=` and `<-`.

## Core Inference Operators

### Functional Operator: `<=`
The `<=` operator establishes **functional relationships** and **definitions**. It creates the primary inference ground by specifying what function or operation applies to an element.

### Value Operator: `<-`
The `<-` operator establishes **value relationships** of the above functional. It indicates that one element follows from or is derived from another, creating inference chains.

## Inference Layout Formats


### Vertical Layout

```NormCode
_inferred_1_
    <= _primary_functional_1_
        <= _primary_functional_2_
        <- _value_for_2_
        ....
    <- _value_3_
        <= _primary_functional_for_3_
        <- _values_for_3_
        ....
    ....
```

### Line Indexing System

NormCode supports an **optional line indexing system** that allows precise reference to any element in the inference structure. This enables cross-referencing, debugging, and documentation of specific inference steps.


#### Indexing Format

Each line can optionally start with a hierarchical index number:

```NormCode
1|_inferred_1_
    1|<= _primary_functional_1_
        1|<= _primary_functional_2_
        2|<- _value_for_2_
        ....
    2|<- _value_3_
        1|<= _primary_functional_for_3_
        2|<- _values_for_3_
        ....
    ....
```

#### Indexing Rules

1. **Root Level**: Starts with single digit (1, 2, 3, ...)
2. **Nested Levels**: Use dot notation (1.1, 1.2, 1.1.1, 1.1.2, ...)
3. **Sibling Elements**: Increment the last number (1.1, 1.2, 1.3, ...)
4. **Child Elements**: Add new level (1.1.1, 1.1.2, ...)
5. **Optional**: Indexes can be omitted for simpler structures

#### Reference Examples

- `1` refers to the root element `_inferred_1_`
- `1.1` refers to `<= _primary_functional_2_for_1_`
- `1.1.1` refers to `<= _primary_functional_for_2_`
- `1.1.2` refers to `<- _value_for_2_`
- `1.2` refers to `<- _value_3_`
- `1.2.1` refers to `<= _primary_functional_for_3_`
- `1.2.2` refers to `<- _values_for_3_`


### Layout Equivalence

**Important**: The horizontal and vertical layouts are **equivalent representations** of the same inference structure. They differ only in visual presentation, not in semantic meaning.

#### Indexing in Horizontal Layout

The horizontal layout can also use indexing, where all indexes need to be written in full in a closer `|_index_| _line_ |_index_|` format, for example:

```NormCode
|1|_inferred_1_ |1.1|<= _primary_functional_2_for_1_ |1.1.1|<= _primary_functional_for_2_ |/1.1.1||1.1.2|<- _value_for_2_ |/1.1.2| |/1.1| |1.2|<- _value_3_ |1.2.1|<= _primary_functional_for_3_ |/1.2.1||1.2.2|<- _values_for_3_ |/1.2.2||/1.2||/1|
```

#### Horizontal Layout Indexing Explanation

The horizontal format uses a `|index|content|/index|` pattern where:

**Opening Indexes (`|index|`):**
- `|1|` - Root element (`_inferred_1_`)
- `|1.1|` - First child of root (`<= _primary_functional_2_for_1_`)
- `|1.1.1|` - First child of 1.1 (`<= _primary_functional_for_2_`)
- `|1.1.2|` - Second child of 1.1 (`<- _value_for_2_`)
- `|1.2|` - Second child of root (`<- _value_3_`)
- `|1.2.1|` - First child of 1.2 (`<= _primary_functional_for_3_`)
- `|1.2.2|` - Second child of 1.2 (`<- _values_for_3_`)

**Closing Indexes (`|/index|`):**
Each opening index has a corresponding closing index that marks the end of that element's scope:
- `|/1.1.1|` - Closes the 1.1.1 element
- `|/1.1.2|` - Closes the 1.1.2 element
- `|/1.1|` - Closes the 1.1 element (and all its children)
- `|/1.2.1|` - Closes the 1.2.1 element
- `|/1.2.2|` - Closes the 1.2.2 element
- `|/1.2|` - Closes the 1.2 element (and all its children)
- `|/1|` - Closes the root element

**Hierarchical Structure:**
This creates a tree structure:
```
1 (_inferred_1_)
├── 1.1 (<= _primary_functional_2_for_1_)
│   ├── 1.1.1 (<= _primary_functional_for_2_)
│   └── 1.1.2 (<- _value_for_2_)
└── 1.2 (<- _value_3_)
    ├── 1.2.1 (<= _primary_functional_for_3_)
    └── 1.2.2 (<- _values_for_3_)
```

The closing indexes ensure proper nesting and scope boundaries, making it clear which elements are children of which parent elements in the horizontal format.

#### Vertical Layout Translation

The same inference structure in vertical layout format:

```NormCode
1|_inferred_1_
    1.1|<= _primary_functional_2_for_1_
        1.1.1|<= _primary_functional_for_2_
        1.1.2|<- _value_for_2_
    1.2|<- _value_3_
        1.2.1|<= _primary_functional_for_3_
        1.2.2|<- _values_for_3_
```

**One-to-One Correspondence:**
- `|1|_inferred_1_` ↔ `1|_inferred_1_`
- `|1.1|<= _primary_functional_2_for_1_` ↔ `1.1|<= _primary_functional_2_for_1_`
- `|1.1.1|<= _primary_functional_for_2_` ↔ `1.1.1|<= _primary_functional_for_2_`
- `|1.1.2|<- _value_for_2_` ↔ `1.1.2|<- _value_for_2_`
- `|1.2|<- _value_3_` ↔ `1.2|<- _value_3_`
- `|1.2.1|<= _primary_functional_for_3_` ↔ `1.2.1|<= _primary_functional_for_3_`
- `|1.2.2|<- _values_for_3_` ↔ `1.2.2|<- _values_for_3_`

The closing indexes in horizontal format (`|/1.1.1|`, `|/1.1.2|`, etc.) are represented by indentation levels in vertical format, demonstrating that both layouts encode identical semantic relationships.
