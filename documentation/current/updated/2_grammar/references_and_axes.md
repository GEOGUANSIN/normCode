# References and Axes

**Understanding how data is stored and manipulated in NormCode's tensor-based reference system.**

---

## Overview

While concepts define the *meaning* of data in a NormCode plan, the actual information is stored in a **Reference**. References are multi-dimensional tensors with named axes that model the **indeterminacies** inherent in expressions like "a student", "a number", or "a file".

This system enables **context-agnostic operations**: you can write code that operates on "a student" without knowing the surrounding context (school, class, nationality), and that context can change without modifying your operations.

---

## Part 1: References

### What is a Reference?

A **Reference** is the container where information for a concept is kept. Specifically, **semantical concepts** (like `{object}`, `[]`, or `<>`) have an associated Reference, as they represent data-holding entities.

**Key Characteristics**:

| Property | Description |
|----------|-------------|
| **Multi-dimensional** | A Reference is a tensor—it can hold data across multiple dimensions (axes) |
| **Named Axes** | Each dimension has a name (e.g., `student`, `assignment`), not just an index |
| **Shape** | The size of each dimension defines the `shape` (e.g., `(3, 4)` for 3 students × 4 assignments) |
| **Skip Values** | Missing or invalid data is represented by a special skip value (`@#SKIP#@`) |

**In short**: A `Concept` gives information its meaning within the plan, while a `Reference` provides the structure to hold and organize that information.

---

### The Elements: Perceptual Signs

While a Reference provides the container structure (tensor), the *elements* inside that tensor are often not raw data but **Perceptual Signs**—specially formatted strings that tell the Agent *how* to find or interpret the data.

#### The Format

A Perceptual Sign follows this strict syntax:

```
%{Norm}ID(Signifier)
```

- **`Norm`**: (Optional) The "Norm of Perception"—which faculty/tool the agent should use
  - *Examples*: `file_location`, `prompt_location`, `save_path`
- **`ID`**: A unique, short hexadecimal identifier (e.g., `a1b`) used to track lineage
- **`Signifier`**: The payload or pointer (e.g., a file path `data/input.txt`)

**Example**:
```
%{file_location}7f2(data/input.txt)
```
*Meaning*: "This element points to a file. Use the FileSystem faculty to read 'data/input.txt' to get the actual object."

#### The Act of Perception

When an Agent "perceives" a Reference (during the **MVP** step of a semantic sequence), it **transmutes** the sign into the actual object:

1. **Decode**: Parse the string `%{file_location}...(data/input.txt)`
2. **Select Faculty**: The norm `file_location` maps to the Agent's `FileSystem` faculty
3. **Transmute**: Execute `file_system.read('data/input.txt')` and replace the sign with the actual content

This mechanism allows NormCode to be **lightweight**—passing around small pointers (Signs) instead of heavy data—until the exact moment the data is needed.

---

### Specialized Element Types

Elements vary depending on the concept type:

#### A. Relational Elements (Complex Data)

For **Relation concepts (`[]`)** or grouped data:
- **Lists**: `[{'name': 'A'}, {'name': 'B'}]` — Produced by `&across` grouping
- **Dictionaries**: `{'user query': '...', 'context': '...'}` — Produced by `&in` grouping

#### B. Truth Value Elements (Propositions)

For **Proposition concepts (`<>`)**, elements represent boolean states:
- `%{truth_value}(True)`
- `%{truth_value}(False)`

Used by the `Timer` for branching (`@if`).

#### C. Functional Reference Elements (Vertical Inputs)

For **Functional concepts (`({})`, `<{}>`)**, the Reference holds the operation definition:
- **Direct Prompts**: `%{prompt}...` — Raw text of a prompt
- **Prompt Locations**: `%{prompt_location}...` — Pointer to a template file
- **Script Locations**: `%{script_location}...` — Pointer to a Python script

Read during the **MFP** (Model Function Perception) step.

#### D. Subject Reference Elements (Agents)

For **Subject concepts (`:S:`)**, the Reference holds the actor configuration:
- **Body + Config**: Dictionary specifying the `AgentFrame` mode and `Body` (toolset)

---

### Creating References

#### Direct Construction

```python
from infra._core import Reference

# A 2D reference: 3 students × 4 assignments
grades = Reference(
    axes=['student', 'assignment'],
    shape=(3, 4),
    initial_value=0
)
```

#### From Existing Data

```python
# Automatically infer shape from nested list structure
data = [[85, 90], [78, 88], [92, 95]]
grades = Reference.from_data(data, axis_names=['student', 'assignment'])
# Result: axes=['student', 'assignment'], shape=(3, 2)
```

#### Tensor with List Elements

If you provide fewer axis names than the data's dimensions (rank), the "extra" inner dimensions are preserved as list elements inside the tensor:

```python
# 3D data: 3 students, 2 semesters, each with a list of scores
raw_data = [
    [[80, 85], [90, 95]], 
    [[70, 75], [80, 85]], 
    [[60, 65], [70, 75]]
]
# We only specify 2 axes. The inner lists become the elements.
complex_ref = Reference.from_data(raw_data, axis_names=['student', 'semester'])
```

---

## Part 2: Axes

### What Are Axes?

Axes of reference are **frozen modes of presentation** that model the **indeterminacies** inherent in expressions like "a student", "a number pair", or "a file".

When we say "a student" in a specific context, we encounter many dimensions of indeterminacy: class, school, nationality, gender, age, etc. These dimensions form the **axes** of a tensor-like structure.

---

### From Determinate to Indeterminate Reference

#### Determinate Reference (Flat List)

When we fully reveal all students in a context, we get a flat list:

```python
{student} = [
    {class: "A", school: "School A", nationality: "American", name: "John Doe"},
    {class: "A", school: "School B", nationality: "British", name: "Jane Smith"},
    {class: "C", school: "School C", nationality: "American", name: "Jim Beam"},
    {class: "C", school: "School C", nationality: ["British", "American"], name: "Fallon Doe"},
]
```

#### Indeterminate Reference (Tensor Structure)

When we use an **indeterminate reference** (we don't know which exact student), the data organizes into a nested tensor:

```python
Possible values:
  class: ["A", "C"]
  school: ["School A", "School B", "School C"]
  nationality: ["American", "British"]

axes: [school, class, nationality, student]
      ↑ self-provided axis: student
      ↑ dependent axes: school, class, nationality

students: [
    [ //: school = "School A"
        [ //: class = "A"
            [ //: nationality = "American"
                John Doe,
            ],
            [ //: nationality = "British"
            ]
        ],
        [ //: class = "C"
            [ //: nationality = "American"
            ],
            [ //: nationality = "British"
                Jane Smith,
            ]
        ]
    ],
    [ //: school = "School B"
        ...
    ],
    [ //: school = "School C"
        [ //: class = "C"
            [ //: nationality = "American"
                Jim Beam, Fallon Doe,
            ],
            [ //: nationality = "British"
                Fallon Doe,
            ]
        ]
    ],
]
```

---

### Why This Design is Useful

This structure enables **context-agnostic operations**:

- Apply an operation to "a student" (singular) using `element_action` or `cross_action`
- The operation doesn't need to know the surrounding context (school, class, nationality)
- The context can change over time without modifying the operation
- The formality of the context structure can evolve independently

---

### Types of Axes

#### Self-Provided Axis

The concept's own dimension of plurality:
- `{student}` provides the "student" axis
- `{school}` provides the "school" axis

#### Dependent Axes

Axes inherited from context or other concepts:
- When discussing students, "school", "class", and "nationality" are dependent axes

#### The `_none_axis` Case

If a concept has no inherent plurality (a singular, certain value), it uses `_none_axis` as a degenerate axis with shape `(1,)`.

**Rule**: Each self-provided axis should be **unique** within a NormCode plan. If a concept cannot guarantee uniqueness, it should use `_none_axis`.

---

### Axis Accumulation Through Inference

Consider this inference:

```ncd
<- {parent}
    <= ::(find parent)
    <- {student}
```

The `{parent}` concept can accumulate axes because:
1. There are usually **multiple parents** per student → introduces a "parent" axis
2. The **student's axes** (school, class, nationality) become dependent axes of `parent`
3. If `find parent` has multiple interpretations (biological vs. legal) → may contribute its own axis

**Result**: `{parent}` axes might become `[school, class, nationality, student, parent_type, parent]`

When the operation is **certain** (no ambiguity), its contribution is `_none_axis` (effectively invisible).

---

## Part 3: Basic Reference Operations

### Get and Set

Access and modify data using **named axes**:

```python
# Set a specific value
grades.set(95, student=0, assignment=1)

# Get a specific value
score = grades.get(student=0, assignment=1)  # Returns 95

# Get an entire row (all assignments for student 0)
student_grades = grades.get(student=0)  # Returns [85, 95, ...]
```

### Copying

Create an independent copy of a Reference:

```python
grades_backup = grades.copy()  # Deep copy—changes don't affect original
```

### Tensor Access

Direct access to the underlying nested list structure:

```python
raw_data = grades.tensor  # The full nested list with skip values
clean_data = grades.get_tensor(ignore_skip=True)  # Skip values removed
```

---

## Part 4: Reshaping Operations

### Slice

Extract a subset of axes, preserving data alignment:

```python
# Original: axes=['student', 'semester', 'assignment'], shape=(3, 2, 4)
full_grades = Reference(...)

# Slice to just student × assignment (aggregate across semesters)
sliced = full_grades.slice('student', 'assignment')
# Result: axes=['student', 'assignment'], shape=(3, 4)
```

**Special case—no axes:** Creates a single-element container:
```python
wrapped = grades.slice()
# Result: axes=['_none_axis'], shape=(1,) — entire tensor stored as one element
```

### Append

Add data along a specified axis:

```python
# Pattern 1: Add new elements to a container axis
target = Reference.from_data([[1, 2], [3, 4]], axis_names=['B', 'A'])
source = Reference.from_data([5, 6], axis_names=['C'])
result = target.append(source, by_axis='B')
# Result: [[1, 2], [3, 4], [5, 6]] — new row added

# Pattern 2: Extend existing elements (broadcast)
result = target.append(source, by_axis='A')
# Result: [[1, 2, 5, 6], [3, 4, 5, 6]] — values appended to each row
```

---

## Part 5: Combining References

These functions combine multiple References into new structures. They are the building blocks for **Grouping** and **Looping** sequences.

### Cross Product

Aligns References by shared axes and combines their elements:

```python
from infra._core import cross_product

# Reference A: student grades
grades = Reference(axes=['student', 'semester'], shape=(3, 2))

# Reference B: student attendance
attendance = Reference(axes=['student', 'semester'], shape=(3, 2))

# Combine: each element becomes [grade, attendance] pair
combined = cross_product([grades, attendance])
# Result: axes=['student', 'semester'], each element is a list [grade, attendance]
```

**Key behavior**:
- Shared axes are aligned (must have matching shapes)
- Non-shared axes are added to the result
- If any input has a skip value at a position, the result is skip

### Join

Stacks References with the *same shape* along a new axis:

```python
from infra._core import join

ref1 = Reference.from_data([[1, 2], [3, 4]], axis_names=['B', 'A'])
ref2 = Reference.from_data([[5, 6], [7, 8]], axis_names=['B', 'A'])

joined = join([ref1, ref2], new_axis_name='C')
# Result: axes=['C', 'B', 'A'], shape=(2, 2, 2)
# joined.tensor = [[[1,2],[3,4]], [[5,6],[7,8]]]
```

### Cross Action

Applies functions from one Reference to values from another:

```python
from infra._core import cross_action

# Reference A: holds functions
funcs = Reference(axes=['op'], shape=(2,))
funcs.set(lambda x: [x * 2], op=0)
funcs.set(lambda x: [x + 10], op=1)

# Reference B: holds values
values = Reference(axes=['item'], shape=(3,))
values.tensor = [1, 2, 3]

# Apply each function to each value
result = cross_action(funcs, values, new_axis_name='result')
# Result: axes=['op', 'item', 'result']
# result.get(op=0, item=0) = [2]   (1 * 2)
# result.get(op=1, item=2) = [13]  (3 + 10)
```

**This is the core of the TVA (Tool Value Actuation) step** in semantic sequences—functions prepared by MFP are applied to values perceived by MVP.

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
    return f"({index_dict['x']},{index_dict['y']}): {a + b}"

result = element_action(labeled_add, [A, B], index_awareness=True)
```

---

## Part 6: Grouping with Axes

### Group In (`&[{}]`) — Annotated Collapse

```ncd
<- {students in a school}
    <= &[{}] %>[{student}, {school}] %:[{school}]
    <- {student}
    <- {school}
    <* {school}
```

**Effect**: The `{school}` axis is collapsed, but each element is **annotated** with its school:

```python
axes: [class, nationality, student]  ← school axis dropped

students: [
    [ //: class = "A"
        [ //: nationality = "American"
            {student: John Doe, school: School A}
        ],
        ...
    ],
    [ //: class = "C"
        [ //: nationality = "American"
            {student: Jim Beam, school: School C},
            {student: Fallon Doe, school: School C}
        ],
        [ //: nationality = "British"
            {student: Jane Smith, school: School A},
            {student: Fallon Doe, school: School C}
        ]
    ]
]
```

---

### Group Across (`&[#]`) — Flattened Collapse

```ncd
<- {students across schools}
    <= &[#] %>[{student}] %:[{school}]
    <- {student}
    <* {school}
```

**Effect**: The `{school}` axis is collapsed, and values are **flattened** into raw elements:

```python
axes: [class, nationality, student]  ← school axis dropped

students: [
    [ //: class = "A"
        [ //: nationality = "American"
            John Doe,
        ],
        ...
    ],
    [ //: class = "C"
        [ //: nationality = "American"
            Jim Beam, Fallon Doe
        ],
        [ //: nationality = "British"
            Jane Smith, Fallon Doe
        ]
    ]
]
```

---

### Group In with Protected Axes

```ncd
<- {students and parents for each nationality}
    <= &[{}] %>[{student}, {parent}] %:[{student}<$!={nationality}>]
    <- {student}
    <- {parent}
    <* {nationality}
```

**Effect**: The `{student}` axis is collapsed, but `{nationality}` is **protected** (kept):

```python
axes: [nationality]  ← only nationality preserved

students: [
    [ //: nationality = "American"
        [ //: element list - not an axis
            {student: John Doe, parent: [Kim Doe, Lowe Doe]},
            {student: Jim Beam, parent: [Kim Beam, Lowe Beam]},
            {student: Fallon Doe, parent: [Kim Doe, Lowe Doe]},
        ]
    ],
    [ //: nationality = "British"
        [ //: element list - not an axis
            {student: Jane Smith, parent: [Kim Smith, Lowe Smith]},
            {student: Fallon Doe, parent: [Kim Doe, Lowe Doe]},
        ]
    ]
]
```

---

## Part 7: Assigning with Axes

### Selection (`$-`) — Extract Elements

```ncd
<- {parents for students with a nationality}
    <= $- %>[{student} and {parent}]<%:({nationality})> %^<$*#><$({parent})%>
    <- {students and parents for each student with a nationality}
```

**Result**:
```python
axes: [nationality]

parents: [
    [ //: nationality = "American"
        [ //: element list - not an axis
            Kim Doe, Lowe Doe, Kim Beam, Lowe Beam
        ],
    ],
    [ //: nationality = "British"
        [ //: element list - not an axis
            Kim Smith, Lowe Smith, Kim Doe, Lowe Doe
        ]
    ]
]
```

---

### Continuation (`$+`) — Simple Append

**Use Case**: Adding a new student to an existing collection

```ncd
<- {updated students with nationality}
    <= $+ %>({current students}) %<({new student}) %:({student})
    <- {current students}
    <- {new student}
```

**Before** (current students):
```python
axes: [nationality, student]
shape: (2, 3)

students: [
    [ //: nationality = "American"
        John Doe, Jim Beam, Fallon Doe
    ],
    [ //: nationality = "British"
        Jane Smith, Fallon Doe
    ]
]
```

**After** (append along `student` axis):
```python
axes: [nationality, student]
shape: (2, 4)  ← student axis grew from 3 to 4

all_students: [
    [ //: nationality = "American"
        John Doe, Jim Beam, Fallon Doe, Alice Wang
    ],
    [ //: nationality = "British"
        Jane Smith, Fallon Doe, Bob Chen
    ]
]
```

---

### Continuation (`$+`) — Element-wise Append

**Use Case**: Adding test scores to each student

```ncd
<- {students with all test scores}
    <= $+ %>({current students}) %<({new test scores}) %:({test})
    <- {current students test scores}
    <- {new test scores}
```

**Before**:
```python
axes: [nationality, student, test]
shape: (2, 2, 2)  ← 2 tests per student

students_with_tests: [
    [ //: nationality = "American"
        [ //: student = John Doe
            [Test1: 85, Test2: 90]  ← tests axis
        ],
        [ //: student = Jim Beam
            [Test1: 78, Test2: 82]
        ]
    ]
]
```

**After** (append along `test` axis):
```python
axes: [nationality, student, test]
shape: (2, 2, 3)  ← test axis grew from 2 to 3

students_with_all_tests: [
    [ //: nationality = "American"
        [ //: student = John Doe
            [Test1: 85, Test2: 90, Test3: 87]  ← appended to each student
        ],
        [ //: student = Jim Beam
            [Test1: 78, Test2: 82, Test3: 80]
        ]
    ]
]
```

---

### Continuation (`$+`) — Broadcast Append

**Use Case**: Adding a common property to all students

```ncd
<- {students with school info}
    <= $+ %>({students}) %<({school info}) %:({school})
    <- {students}
    <- {school info}
```

**Effect**: Same info added to each student (broadcast).

---

## Part 8: Skip Values and Error Handling

The skip value (`@#SKIP#@`) propagates through operations:

| Scenario | Behavior |
|----------|----------|
| `cross_product` with any skip input | Result element is skip |
| `cross_action` on skip function or value | Result is skip |
| `element_action` with any skip input | Result element is skip |
| `get()` on missing index | Returns skip |

**Checking for valid data**:
```python
clean_data = reference.get_tensor(ignore_skip=True)
has_data = bool(clean_data)  # True if any non-skip values exist
```

---

## Part 9: The Data Flow Pattern

Understanding how References flow through the system:

```
┌─────────────────────────────────────────────────────────────────┐
│                      INFERENCE EXECUTION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. INPUT RETRIEVAL (IR)                                        │
│     └─ Concept Repo → References for input concepts             │
│                                                                 │
│  2. SYNTACTIC RESHAPING (GR, AR, etc.)                          │
│     └─ Grouper.and_in(), Assigner.continuation(), etc.          │
│     └─ cross_product(), join(), slice()                         │
│                                                                 │
│  3. SEMANTIC PROCESSING (MFP → MVP → TVA)                       │
│     └─ MFP: Prepare functions (paradigm → callable)             │
│     └─ MVP: Perceive values (Reference → interactable form)     │
│     └─ TVA: cross_action(functions, values)                     │
│                                                                 │
│  4. OUTPUT STORAGE (OR)                                         │
│     └─ Result Reference → Concept Repo                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary

### Reference as Computational Substrate

| Layer | What It Provides |
|-------|------------------|
| **Concept** | Semantic identity ("what does this data mean?") |
| **Reference** | Structural container ("how is this data organized?") |
| **Operations** | Transformations ("how does data combine and flow?") |

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Axes** | Named dimensions of referential indeterminacy |
| **Self-provided axis** | The concept's own plurality dimension |
| **Dependent axes** | Inherited from context/inputs |
| **`_none_axis`** | Degenerate axis for certain (singular) values |
| **Axis accumulation** | Axes compound through inference chains |
| **`%:[{axis}]`** | Collapse this axis (remove from output) |
| **`<$!={axis}>`** | Protect this axis (keep even when collapsing) |

The Reference system enables NormCode's core promise: **data isolation with explicit flow**. Each inference receives precisely the References it needs, transforms them through well-defined operations, and produces new References for downstream consumers.

This is why you can trace exactly what each step saw and produced—it's all encoded in the Reference structure.

---

## Next Steps

- **[Complete Syntax Reference](complete_syntax_reference.md)** - Full formal grammar
- **[Execution Section](../3_execution/README.md)** - How references work at runtime
- **[Semantic Concepts](semantic_concepts.md)** - Review concept types

---

## Quick Reference

### Axes
```
Self-provided:    {student} → "student" axis
Dependent:        Inherited from context
_none_axis:       Degenerate (singular) axis
```

### Axis Operations
```
%:[{axis}]        Collapse this axis
<$!={axis}>       Protect this axis
```

### Reference Operations
```
get()             Access by named axes
set()             Modify by named axes
slice()           Project onto subset of axes
append()          Add along an axis
cross_product()   Align and combine
cross_action()    Apply functions to values
```

---

**Ready for the complete grammar?** Continue to [Complete Syntax Reference](complete_syntax_reference.md).
