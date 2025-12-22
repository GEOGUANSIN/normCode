# Reference System

**How NormCode stores and manipulates data in multi-dimensional tensors.**

---

## Overview

While **concepts** define the *meaning* of data in a NormCode plan, **References** provide the *structure* to hold and organize that data. Understanding References is essential to grasping how information flows through the execution.

**Key Points:**
- References are multi-dimensional tensors with named axes
- Data elements are often perceptual signs (pointers) not raw content
- References support rich operations (slicing, joining, cross products)
- The reference system enables explicit data isolation

---

## What Is a Reference?

A **Reference** is the container where a concept's information is stored.

### Core Properties

| Property | Description | Example |
|----------|-------------|---------|
| **Multi-dimensional** | Data organized as tensor (multi-dimensional array) | 3 students × 4 assignments × 2 semesters |
| **Named Axes** | Each dimension has a meaningful name | `['student', 'assignment', 'semester']` |
| **Shape** | Size of each dimension | `(3, 4, 2)` |
| **Elements** | Can be values, perceptual signs, or complex objects | `%{file_location}7f2(data/input.txt)` |
| **Skip Values** | Explicit representation of missing data | `@#SKIP#@` |

### Concept vs. Reference

```
┌───────────────────────────────────────────┐
│  CONCEPT: Semantic Identity               │
│  "What does this data mean?"              │
│  Example: {student grades}                │
├───────────────────────────────────────────┤
│  REFERENCE: Structural Container          │
│  "How is this data organized?"            │
│  Example: 3×4 tensor with axes            │
│           [student, assignment]           │
└───────────────────────────────────────────┘
```

**Key Insight**: Concepts give information its identity; References give it structure.

---

## Creating References

### Direct Construction

```python
from infra._core import Reference

# Create a 2D reference for student grades
grades = Reference(
    axes=['student', 'assignment'],
    shape=(3, 4),
    initial_value=0
)
```

### From Existing Data

```python
# Automatically infer shape from nested list
data = [[85, 90, 88, 92], 
        [78, 88, 85, 90], 
        [92, 95, 93, 98]]

grades = Reference.from_data(
    data, 
    axis_names=['student', 'assignment']
)
# Result: axes=['student', 'assignment'], shape=(3, 4)
```

### Handling Complex Elements

If data has more dimensions than axis names, inner dimensions become list elements:

```python
# 3D data: 3 students, 2 semesters, 4 assignments each
raw_data = [
    [[80, 85, 90, 88], [82, 87, 92, 90]],  # Student 0
    [[70, 75, 80, 78], [72, 77, 82, 80]],  # Student 1
    [[90, 95, 98, 96], [92, 97, 99, 98]]   # Student 2
]

# Only specify 2 axes → inner lists become elements
ref = Reference.from_data(
    raw_data, 
    axis_names=['student', 'semester']
)

# Result:
# - axes=['student', 'semester']
# - shape=(3, 2)
# - Each element is a list: [80, 85, 90, 88]
```

This is crucial for handling complex objects like dictionaries or nested structures.

---

## Perceptual Signs

### The Pointer System

References often don't store raw data directly. Instead, they store **perceptual signs**—formatted strings that tell the agent *how* to retrieve the actual data.

### Format

```
%{Norm}ID(Signifier)
```

| Component | Description | Example |
|-----------|-------------|---------|
| **Norm** | Perception strategy (which tool to use) | `file_location`, `prompt_location` |
| **ID** | Unique hex identifier for tracking | `7f2`, `a1b` |
| **Signifier** | The actual pointer (path, key, etc.) | `data/input.txt` |

### Examples

```python
# File pointer
"%{file_location}7f2(data/input.txt)"

# Prompt template pointer
"%{prompt_location}3c4(prompts/summarize.txt)"

# Save path (where to write result)
"%{save_path}8d1(output/result.json)"

# Direct prompt content
"%{prompt}5e9(Summarize this document)"

# Truth value (for propositions)
"%{truth_value}2a3(True)"
```

### The Perception Process

When an agent needs the actual data (during MVP step):

```
1. Agent reads element: "%{file_location}7f2(data/input.txt)"
2. PerceptionRouter decodes the sign
3. Norm "file_location" → use FileSystem faculty
4. FileSystem reads 'data/input.txt'
5. Element is replaced with actual file content
6. Agent can now process the data
```

**Why this matters**: NormCode can pass around lightweight pointers until the moment data is actually needed, reducing memory overhead and enabling lazy evaluation.

---

## Specialized Element Types

Different concept types have different element conventions:

### Value Concepts (Objects, Collections)

**Objects `{}`**: Typically perceptual signs
```python
{document} → %{file_location}7f2(reports/doc1.pdf)
{result} → %{save_path}3c4(output/result.json)
```

**Relations `[]`**: Often complex structures
```python
[files] → [
    %{file_location}a1b(doc1.txt),
    %{file_location}c2d(doc2.txt),
    %{file_location}e3f(doc3.txt)
]
```

**Grouped Data**: Dictionaries from `&in` grouping
```python
{combined_input} → {
    'user query': 'What is the capital?',
    'context': 'France is a country in Europe...'
}
```

### Proposition Concepts

**Propositions `<>`**: Truth values for branching
```python
<is valid> → %{truth_value}2a3(True)
<check failed> → %{truth_value}7c8(False)
```

### Functional Concepts

**Imperatives `({})`**: Vertical inputs (prompts, scripts)
```python
::(extract key points) → %{prompt_location}5e9(prompts/extract.txt)
::(run python script) → %{script_location}8f2(scripts/analyze.py)
```

**Judgements `<{}>`**: Same as imperatives, plus assertion conditions
```python
<{validation}> → %{prompt}4d5(Check if format is valid)
```

### Subject Concepts

**Agents `:S:`**: Body configuration
```python
:agent: → {
    'mode': 'composition',
    'body': 'default',
    'tools': ['llm', 'file_system', 'python_executor']
}
```

---

## Basic Operations

### Get and Set

Access and modify data using **named axes**:

```python
# Set a specific value
grades.set(95, student=0, assignment=1)

# Get a specific value
score = grades.get(student=0, assignment=1)  # Returns 95

# Get entire row (all assignments for student 0)
student_grades = grades.get(student=0)
# Returns Reference with axes=['assignment'], shape=(4,)

# Get entire column (all students for assignment 1)
assignment_grades = grades.get(assignment=1)
# Returns Reference with axes=['student'], shape=(3,)
```

### Partial Indexing

When you index fewer axes than the reference has, you get a sub-reference:

```python
# 3D reference: student × semester × assignment
full_ref = Reference(axes=['student', 'semester', 'assignment'], shape=(3, 2, 4))

# Index only student 0
student_ref = full_ref.get(student=0)
# Result: Reference with axes=['semester', 'assignment'], shape=(2, 4)
```

### Copying

```python
# Deep copy—changes don't affect original
backup = grades.copy()
```

### Tensor Access

```python
# Raw nested list (includes skip values)
raw_data = grades.tensor

# Clean data (skip values removed)
clean_data = grades.get_tensor(ignore_skip=True)

# Check if reference has valid data
has_data = bool(clean_data)  # False if empty or all skips
```

---

## Reshaping Operations

### Slice

Extract a subset of axes, aggregating others:

```python
# Original: 3 students × 2 semesters × 4 assignments
full_grades = Reference(
    axes=['student', 'semester', 'assignment'],
    shape=(3, 2, 4)
)

# Slice to just student × assignment (collapse semesters)
sliced = full_grades.slice('student', 'assignment')
# Result: axes=['student', 'assignment'], shape=(3, 4)
# Each element aggregates across semesters
```

**Special case—no axes**: Wrap entire tensor as one element
```python
wrapped = grades.slice()
# Result: axes=['_none_axis'], shape=(1,)
# grades.tensor stored as single element
```

### Append

Add data along a specified axis:

```python
# Pattern 1: Extend along container axis (add rows)
target = Reference.from_data(
    [[1, 2], [3, 4]], 
    axis_names=['row', 'col']
)
new_row = Reference.from_data([5, 6], axis_names=['col'])

result = target.append(new_row, by_axis='row')
# Result: [[1, 2], [3, 4], [5, 6]]

# Pattern 2: Extend along element axis (add columns)
new_cols = Reference.from_data([7, 8], axis_names=['extra'])

result = target.append(new_cols, by_axis='col')
# Result: [[1, 2, 7, 8], [3, 4, 7, 8]]
# new_cols broadcast to each row
```

---

## Combining References

These operations combine multiple References—the foundation for syntactic sequences.

### Cross Product

Aligns References by shared axes and combines elements:

```python
from infra._core import cross_product

# Grades and attendance share 'student' axis
grades = Reference(axes=['student'], shape=(3,))
grades.tensor = [85, 90, 78]

attendance = Reference(axes=['student'], shape=(3,))
attendance.tensor = [0.9, 0.95, 0.85]

# Combine into [grade, attendance] pairs
combined = cross_product([grades, attendance])

# Result:
# axes=['student'], shape=(3,)
# combined.get(student=0) = [85, 0.9]
# combined.get(student=1) = [90, 0.95]
```

**With non-shared axes**:
```python
grades = Reference(axes=['student'], shape=(3,))
assignments = Reference(axes=['assignment'], shape=(4,))

combined = cross_product([grades, assignments])
# Result: axes=['student', 'assignment'], shape=(3, 4)
# Each element is [grade, assignment]
```

**Key Behavior**:
- Shared axes must have matching shapes
- Non-shared axes create new dimensions
- If any input has skip at position → result is skip

### Join

Stacks References with *same shape* along a new axis:

```python
from infra._core import join

# Two 2×3 references
ref1 = Reference.from_data([[1, 2, 3], [4, 5, 6]], axis_names=['row', 'col'])
ref2 = Reference.from_data([[7, 8, 9], [10, 11, 12]], axis_names=['row', 'col'])

# Stack along new 'version' axis
joined = join([ref1, ref2], new_axis_name='version')

# Result: axes=['version', 'row', 'col'], shape=(2, 2, 3)
# joined.get(version=0) → ref1
# joined.get(version=1) → ref2
```

**Use cases**:
- Collecting results from multiple runs
- Grouping alternative solutions
- Building collections with new dimension

### Cross Action

Applies functions from one Reference to values from another:

```python
from infra._core import cross_action

# Reference of functions
funcs = Reference(axes=['operation'], shape=(2,))
funcs.set(lambda x: [x * 2], operation=0)
funcs.set(lambda x: [x + 10], operation=1)

# Reference of values
values = Reference(axes=['item'], shape=(3,))
values.tensor = [1, 2, 3]

# Apply each function to each value
result = cross_action(funcs, values, new_axis_name='result')

# Result: axes=['operation', 'item', 'result']
# result.get(operation=0, item=0) = [2]   # 1 * 2
# result.get(operation=0, item=1) = [4]   # 2 * 2
# result.get(operation=1, item=0) = [11]  # 1 + 10
```

**This is the core of TVA (Tool Value Actuation)**: functions prepared by MFP are applied to values perceived by MVP.

### Element Action

Applies a function element-wise across aligned References:

```python
from infra._core import element_action

A = Reference.from_data([[1, 2], [3, 4]], axis_names=['x', 'y'])
B = Reference.from_data([[10, 20], [30, 40]], axis_names=['x', 'y'])

def add(a, b):
    return a + b

result = element_action(add, [A, B])
# Result: [[11, 22], [33, 44]]
```

**Index-aware variant**:
```python
def labeled_add(a, b, index_dict):
    x, y = index_dict['x'], index_dict['y']
    return f"[{x},{y}]: {a + b}"

result = element_action(labeled_add, [A, B], index_awareness=True)
# Result: [["[0,0]: 11", "[0,1]: 22"], ["[1,0]: 33", "[1,1]: 44"]]
```

---

## Skip Values and Error Handling

### The Skip Value

Missing or invalid data is represented by the special string `@#SKIP#@`.

### Propagation Rules

| Operation | Behavior |
|-----------|----------|
| `cross_product` with any skip input | Result element is skip |
| `cross_action` on skip function or value | Result is skip |
| `element_action` with any skip input | Result element is skip |
| `join` with any skip at position | Result element is skip |
| `get()` on missing index | Returns skip |

### Working with Skips

```python
# Check for valid data
clean_data = ref.get_tensor(ignore_skip=True)
has_valid_data = bool(clean_data)

# Manually set skip
ref.set('@#SKIP#@', student=1, assignment=2)

# Skip propagates through operations
ref1 = Reference(axes=['x'], shape=(2,))
ref1.tensor = [1, '@#SKIP#@']

ref2 = Reference(axes=['x'], shape=(2,))
ref2.tensor = [10, 20]

combined = cross_product([ref1, ref2])
# Result: [[1, 10], '@#SKIP#@']
```

**Why skips matter**: They allow the execution to continue even when some data is missing, with explicit tracking of what failed.

---

## Axes and Indeterminacy

### Named Dimensions

Axes represent **dimensions of indeterminacy**—aspects along which data varies.

**Example**: A concept like "a student's grade" has indeterminacy in:
- Which student? → `student` axis
- Which assignment? → `assignment` axis
- Which semester? → `semester` axis

### Axis Semantics

| Axis Pattern | Meaning | Example |
|--------------|---------|---------|
| **Entity identifier** | Which instance | `student`, `document`, `item` |
| **Time/sequence** | When or what order | `semester`, `iteration`, `version` |
| **Category/type** | What kind | `signal_type`, `method`, `source` |
| **Structural** | Loop or group index | `loop_index`, `_none_axis` |

### Axis Operations

**Alignment**: Cross product aligns by shared axis names
```python
# Both have 'student' axis → aligned
ref1: axes=['student', 'course']
ref2: axes=['student', 'semester']
cross_product([ref1, ref2])
→ axes=['student', 'course', 'semester']
```

**Aggregation**: Slice removes axes (collapses)
```python
# Collapse 'semester' axis
ref.slice('student', 'course')
→ aggregates across semesters
```

**Extension**: Join or append adds axes
```python
# Add 'version' axis
join([ref1, ref2], new_axis_name='version')
```

---

## Reference Lifecycle

### 1. Creation (Initialization)

```
Concept declared in .ncd
      ↓
Compiler creates entry in ConceptRepo
      ↓
Reference initialized (empty or with initial value)
```

### 2. Population (Inference Execution)

```
Parent inference retrieves input References (IR step)
      ↓
Syntactic operations reshape References
      ↓
Semantic operations perceive and process
      ↓
Result stored as Reference (OR step)
```

### 3. Retrieval (Child Inferences)

```
Child inference declares parent as input
      ↓
IR step retrieves parent's Reference
      ↓
Child uses Reference as input
```

### 4. Perception (Transmutation)

```
MVP step encounters perceptual sign
      ↓
PerceptionRouter decodes sign
      ↓
Appropriate faculty retrieves actual data
      ↓
Sign replaced with data in Reference
      ↓
Agent operates on actual data
```

---

## Advanced Patterns

### Building Tensors Dynamically

**Loop accumulation** (using `$+` continuation):

```ncd
<- {all summaries}
    <= *. %>({documents}) %<({summary})
    <- {summary}
        <= $+ %<({accumulated summaries}) %^({summary}*-1)
        <- {new summary}
            <= ::(summarize document)
            <- {document}*1
        <- {accumulated summaries}*-1
```

Each iteration appends new summary to accumulated reference.

### Multi-Source Selection

**Assigning with fallbacks** (using `$.` specification):

```ncd
<- {final answer}
    <= $. %<({final answer})
    <- {validated answer}
        <= @if <validation passed>
        <- {computed answer}
    <- {fallback answer}
        <= @if! <validation passed>
        <- {default value}
```

Assigner selects first valid reference.

### Nested Grouping

**Grouping for semantic operations**:

```ncd
<- {analysis}
    <= ::(analyze with context)
    <- {bundled input}
        <= &in
        <- {user query}
        <- {retrieved documents}
        <- {system context}
```

Grouper creates dictionary: `{'user query': ..., 'retrieved documents': ..., 'system context': ...}`

---

## Implementation Notes

### Python Classes

| Class | File | Purpose |
|-------|------|---------|
| `Reference` | `infra/_core/_reference.py` | Main reference implementation |
| `PerceptionRouter` | `infra/_agent/_models/_perception_router.py` | Transmutes signs to data |
| `FormatterTool` | `infra/_agent/_models/_formatter_tool.py` | Creates perceptual signs |

### Key Methods

```python
# Reference class
ref.get(axis=index, ...)           # Retrieve elements
ref.set(value, axis=index, ...)    # Set elements
ref.slice(*axes)                   # Project onto axes
ref.append(other, by_axis)         # Extend along axis
ref.copy()                         # Deep copy

# Module functions
from infra._core import (
    cross_product,      # Align and combine
    join,               # Stack along new axis
    cross_action,       # Apply functions to values
    element_action      # Element-wise operation
)
```

---

## Debugging References

### Common Issues

**Empty Reference**:
```python
# Check if reference has data
clean_data = ref.get_tensor(ignore_skip=True)
if not clean_data:
    print("Reference is empty or all skips")
```

**Wrong Shape**:
```python
# Inspect structure
print(f"Axes: {ref.axes}")
print(f"Shape: {ref.shape}")
print(f"Tensor: {ref.tensor}")
```

**Perceptual Sign Not Resolved**:
```python
# Check if sign is still a string
element = ref.get(student=0)
if isinstance(element, str) and element.startswith('%{'):
    print("Sign not perceived yet")
```

**Cross Product Fails**:
```python
# Check axis compatibility
print(f"Ref1 axes: {ref1.axes}, shape: {ref1.shape}")
print(f"Ref2 axes: {ref2.axes}, shape: {ref2.shape}")
# Shared axes must have matching shapes
```

---

## Summary

### Key Takeaways

| Concept | Insight |
|---------|---------|
| **References are tensors** | Multi-dimensional containers with named axes |
| **Elements are often signs** | Pointers, not raw data, until perception |
| **Operations are compositional** | Slice, join, cross product build complex structures |
| **Skips propagate** | Explicit handling of missing data |
| **Isolation is structural** | Each concept has its own Reference |

### The Reference Promise

**NormCode's data isolation relies on References**:

1. Each concept has exactly one Reference
2. Inferences receive References as inputs (not raw access)
3. Operations transform References explicitly
4. Result References stored and tracked
5. No hidden state or global variables

**Result**: You can inspect exactly what each inference saw and produced—it's all in the References.

---

## Next Steps

- **[Agent Sequences](agent_sequences.md)** - How sequences manipulate References
- **[Orchestrator](orchestrator.md)** - How the orchestrator manages References
- **[References and Axes (Grammar)](../2_grammar/references_and_axes.md)** - Detailed syntax

---

**Ready to see References in action?** Continue to [Agent Sequences](agent_sequences.md) to understand how each sequence type uses References.
