# NormCode Guide - References and Operations

While concepts define the *meaning* of data in a NormCode plan, the actual information is stored in a **Reference**. Understanding References is key to grasping how data is stored, manipulated, and flows through the plan.


## 1. What is a Reference?

A **Reference** is the container where the information for a concept is kept. Specifically, it is the **semantical concepts** (like `{object}`, `[]`, or `<>`) that have an associated Reference, as they represent the data-holding entities within the plan.

**Key Characteristics:**

| Property | Description |
|----------|-------------|
| **Multi-dimensional** | A Reference is a tensor—it can hold data across multiple dimensions (axes). |
| **Named Axes** | Each dimension has a name (e.g., `student`, `assignment`), not just an index. |
| **Shape** | The size of each dimension defines the `shape` (e.g., `(3, 4)` for 3 students × 4 assignments). |
| **Skip Values** | Missing or invalid data is represented by a special skip value (`@#SKIP#@`). |

In short, a `Concept` gives information its meaning within the plan, while a `Reference` provides the structure to hold and organize that information.

---

## 2. The Elements: Perceptual Signs

While a Reference provides the container structure (tensor), the *elements* inside that tensor are often not raw data (like the full text of a book) but **Perceptual Signs**. These are specially formatted strings that tell the Agent *how* to find or interpret the data.

### 2.1. The Format

A Perceptual Sign follows a strict syntax encoded by the system (see `infra/_agent/_models/_formatter_tool.py`):

`%{Norm}ID(Signifier)`

*   **`Norm`**: (Optional) The "Norm of Perception". It dictates *which faculty* or tool the agent should use to perceive the object.
    *   *Examples*: `file_location`, `prompt_location`, `save_path`.
*   **`ID`**: A unique, short hexadecimal identifier (e.g., `a1b`) used to track the object's lineage.
*   **`Signifier`**: The payload or pointer (e.g., a file path `data/input.txt`).

**Example:**
`%{file_location}7f2(data/input.txt)`
*   *Meaning*: "This element points to a file. Use the FileSystem faculty to read 'data/input.txt' to get the actual object."

### 2.2. The Act of Perception

When an Agent "perceives" a Reference (typically during the **MVP** step of a semantic sequence), it doesn't just read the string. It **transmutes** the sign into the actual object using the `PerceptionRouter` (see `infra/_agent/_models/_perception_router.py`):

1.  **Decode**: The router parses the string `%{file_location}...(data/input.txt)`.
2.  **Select Faculty**: The norm `file_location` maps to the Agent's `FileSystem` faculty.
3.  **Transmute**: The agent executes `file_system.read('data/input.txt')` and replaces the sign in the Reference with the actual file content.

This mechanism allows NormCode to be **lightweight**—passing around small pointers (Signs) instead of heavy data volumes—until the exact moment the data is needed for an operation.

### 2.3. Specialized Element Types

Elements are not always simple pointers. The content of a Reference depends heavily on the *type* of concept it supports:

#### A. Relational Elements (Complex Data)
For **Relation concepts (`[]`)** or grouped data, elements are often complex structures rather than single strings:
*   **Lists**: `[{'name': 'A'}, {'name': 'B'}]` — Often produced by `&across` grouping.
*   **Dictionaries**: `{'user query': '...', 'context': '...'}` — Produced by `&in` grouping to bundle inputs together.

These structures are passed "as-is" until a downstream step (like a template substitution) unpacks them.

#### B. Truth Value Elements (Propositions)
For **Proposition concepts (`<>`)**, elements represent boolean states used for logic and branching (`@if`). They use a reserved norm:
*   `%{truth_value}(True)`
*   `%{truth_value}(False)`

When the `Timer` checks a condition, it looks specifically for these values.

#### C. Functional Reference Elements (Vertical Inputs)
For **Functional concepts (`({})`, `<{}>`)**, the Reference holds the "Vertical Inputs"—the instructions that define the operation itself. These are typically:
*   **Direct Prompts**: `%{prompt}...` — The raw text of a prompt.
*   **Prompt Locations**: `%{prompt_location}...` — A pointer to a template file.
*   **Script Locations**: `%{script_location}...` — A pointer to a Python script or tool definition.

During the **MFP** (Model Function Perception) step, the agent reads these to "compile" the executable function.

#### D. Subject Reference Elements (Agents)
For **Subject concepts (`:S:`)**, the Reference holds the configuration of the actor:
*   **Body + Config**: A dictionary or object specifying the `AgentFrame` mode (e.g., "composition") and the `Body` (toolset) to use.

This tells the Orchestrator *who* is performing the work and *which capabilities* they have access to.

---

## 3. Creating References

### 3.1. Direct Construction

```python
from infra._core import Reference

# A 2D reference: 3 students × 4 assignments
grades = Reference(
    axes=['student', 'assignment'],
    shape=(3, 4),
    initial_value=0
)
```

### 3.2. From Existing Data

```python
# Automatically infer shape from nested list structure
data = [[85, 90], [78, 88], [92, 95]]
grades = Reference.from_data(data, axis_names=['student', 'assignment'])

# Result: axes=['student', 'assignment'], shape=(3, 2)
```

**Advanced: Tensor with List Elements**
If you provide fewer axis names than the data's dimensions (rank), the "extra" inner dimensions are preserved as list elements inside the tensor. This is crucial for handling complex objects.

```python
# 3D data: 3 students, 2 semesters, each with a list of scores
raw_data = [
    [[80, 85], [90, 95]], 
    [[70, 75], [80, 85]], 
    [[60, 65], [70, 75]]
]

# We only specify 2 axes. The inner lists become the elements.
complex_ref = Reference.from_data(raw_data, axis_names=['student', 'semester'])

#### 3.3.1. Why So Many Operations?

A NormCode plan does two fundamentally different things:

1. **Semantic work**: Calling LLMs, running tools, generating content—this is *expensive* and *non-deterministic*.
2. **Syntactic work**: Collecting, selecting, iterating, branching—this is *free* and *deterministic*.

The operations are designed to cleanly separate these concerns. **Syntactic operations** handle data plumbing so that **semantic operations** receive exactly what they need—nothing more, nothing less.

#### 3.3.2. The Four Layers

| Layer | Operations | What It Does | LLM? |
|-------|------------|--------------|------|
| **1. Basic** | `get`, `set`, `copy` | Direct element access | No |
| **2. Reshaping** | `slice`, `append` | Change structure, preserve content | No |
| **3. Combining** | `cross_product`, `join`, `cross_action`, `element_action` | Merge References together | Depends* |
| **4. Sequences** | `Assigner`, `Grouper`, `Quantifier`, `Timer` | Orchestrate workflows | Depends* |

*\* `cross_action` is the bridge—it's used by semantic sequences to apply LLM-prepared functions to values.*


#### 3.3.3.1. Basic Operations (Direct Access)

| Operation | Signature | Description |
|-----------|-----------|-------------|
| `get` | `ref.get(axis=index, ...)` | Retrieve element(s) by named axis coordinates |
| `set` | `ref.set(value, axis=index, ...)` | Assign element(s) by named axis coordinates |
| `copy` | `ref.copy()` | Create an independent deep copy |
| `tensor` | `ref.tensor` / `ref.get_tensor(ignore_skip=True)` | Access raw nested list structure |

#### 3.3.3.2. Reshaping Operations (Structure Transformation)

| Operation | Signature | Description |
|-----------|-----------|-------------|
| `slice` | `ref.slice(*axes)` | Project onto subset of axes; aggregate others |
| `append` | `ref.append(other, by_axis)` | Add elements along an axis (extend or broadcast) |

#### 3.3.3.3. Combining Operations (Reference Algebra)

| Operation | Signature | Description |
|-----------|-----------|-------------|
| `cross_product` | `cross_product([ref1, ref2, ...])` | Align by shared axes; combine elements into lists |
| `join` | `join([ref1, ref2, ...], new_axis)` | Stack same-shape refs along a new axis |
| `cross_action` | `cross_action(funcs_ref, vals_ref, result_axis)` | Apply functions from one ref to values from another |
| `element_action` | `element_action(fn, [refs], index_awareness)` | Apply function element-wise across aligned refs |

#### 3.3.3.4. Syntactic Sequence Classes (Workflow Patterns)

| Class | NormCode Operators | Description |
|-------|-------------------|-------------|
| `Assigner` | `$.`, `$+`, `$-` | Selection, accumulation, structural picking |
| `Grouper` | `&in`, `&across` | Collection into relations (dicts) or lists |
| `Quantifier` | `*every` | Loop iteration with workspace state management |
| `Timer` | `@if`, `@if!`, `@after` | Conditional branching and dependency ordering |

#### 3.3.3.5. The Key Insight

```
┌─────────────────────────────────────────────────────────────┐
│  SEMANTIC sequences (imperative, judgement)                 │
│    └─ Use cross_action to apply LLM functions to values     │
│                                                             │
│  SYNTACTIC sequences (grouping, assigning, looping, timing) │
│    └─ Use cross_product, join, slice to restructure data    │
│    └─ NO LLM involvement—pure data plumbing                 │
└─────────────────────────────────────────────────────────────┘
```

This separation is what makes NormCode plans **auditable**: you can trace exactly which steps called an LLM and which steps just moved data around.

---

---

## 4. Basic Operations

### 4.1. Get and Set

Access and modify data using **named axes**:

```python
# Set a specific value
grades.set(95, student=0, assignment=1)

# Get a specific value
score = grades.get(student=0, assignment=1)  # Returns 95

# Get an entire row (all assignments for student 0)
student_grades = grades.get(student=0)  # Returns [85, 95, ...]
```

### 4.2. Copying

Create an independent copy of a Reference:

```python
grades_backup = grades.copy()  # Deep copy—changes don't affect original
```

### 4.3. Tensor Access

Direct access to the underlying nested list structure:

```python
raw_data = grades.tensor  # The full nested list with skip values
clean_data = grades.get_tensor(ignore_skip=True)  # Skip values removed
```

---

## 5. Reshaping Operations

### 5.1. Slice

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

### 5.2. Append

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

## 6. Combining References

These functions combine multiple References into new structures. They are the building blocks for **Grouping** and **Looping** sequences.

### 6.1. Cross Product

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

**Key behavior:**
- Shared axes are aligned (must have matching shapes)
- Non-shared axes are added to the result
- If any input has a skip value at a position, the result is skip

### 6.2. Join

Stacks References with the *same shape* along a new axis:

```python
from infra._core import join

ref1 = Reference.from_data([[1, 2], [3, 4]], axis_names=['B', 'A'])
ref2 = Reference.from_data([[5, 6], [7, 8]], axis_names=['B', 'A'])

joined = join([ref1, ref2], new_axis_name='C')
# Result: axes=['C', 'B', 'A'], shape=(2, 2, 2)
# joined.tensor = [[[1,2],[3,4]], [[5,6],[7,8]]]
```

### 6.3. Cross Action

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

### 6.4. Element Action

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

**Index-aware variant:**
```python
def labeled_add(a, b, index_dict):
    return f"({index_dict['x']},{index_dict['y']}): {a + b}"

result = element_action(labeled_add, [A, B], index_awareness=True)
```

---

## 7. Syntactic Operations on References

The **syntactic sequences** (`assigning`, `grouping`, `timing`, `looping`) use the Reference primitives above. Here's how each class operates:

### 7.1. Assigner (for `$.`, `$+`, `$-`)

The `Assigner` class handles variable assignment and selection.

| Method | Operator | Purpose |
|--------|----------|---------|
| `specification` | `$.` | Select the first valid reference from a list of candidates |
| `continuation` | `$+` | Append source to destination along an axis |
| `derelation` | `$-` | Pure structural selection (by index or key) |

**Specification example:**
```python
assigner = Assigner()

# Select first non-empty source
result = assigner.specification(
    source_refs=[maybe_empty_ref, valid_ref, fallback_ref],
    dest_ref=default_ref
)
# Returns the first source_ref that has data, or dest_ref if all empty
```

**Continuation example:**
```python
# Accumulate results in a loop
accumulated = assigner.continuation(
    source_ref=new_item,
    dest_ref=running_total,
    by_axes=['loop_index']
)
```

### 7.2. Grouper (for `&in`, `&across`)

The `Grouper` class collects and restructures data.

| Method | Operator | Purpose |
|--------|----------|---------|
| `and_in` | `&in` | Combine inputs into an annotated dictionary (Relation) |
| `or_across` | `&across` | Combine inputs into a flat list (Collection) |

**And-In example:**
```python
grouper = Grouper()

# Combine user query and system context into a labeled structure
result = grouper.and_in(
    references=[query_ref, context_ref],
    annotation_list=['{user query}', '{system context}']
)
# Each element becomes: {'user query': ..., 'system context': ...}
```

**Or-Across example:**
```python
# Collect extracted features from multiple documents
result = grouper.or_across(
    references=[features_A, features_B, features_C]
)
# Elements are flattened into a single list
```

### 7.3. Quantifier (for `*every`)

The `Quantifier` class manages loop iteration state using a **Workspace**.

**Key responsibilities:**
1. Track which elements have been processed
2. Store intermediate results per iteration
3. Combine results when the loop completes

```python
quantifier = Quantifier(
    workspace={},  # Persistent state across iterations
    loop_base_concept_name='{document}',
    loop_concept_index=1
)

# Check if there's a new element to process
next_element, index = quantifier.retireve_next_base_element(
    to_loop_element_reference=documents_ref,
    current_loop_base_element=current_doc
)

# Store the result for this iteration
quantifier.store_new_in_loop_element(
    looped_base_reference=current_doc,
    looped_concept_name='{summary}',
    looped_concept_reference=summary_ref
)

# When done, combine all summaries
all_summaries = quantifier.combine_all_looped_elements_by_concept(
    to_loop_element_reference=documents_ref,
    concept_name='{summary}',
    axis_name='document_index'
)
```

### 7.4. Timer (for `@if`, `@if!`, `@after`)

The `Timer` class checks conditions against the **Blackboard**.

```python
timer = Timer(blackboard=blackboard)

# Check if a dependency is complete
is_ready = timer.check_progress_condition('{previous step}')

# Check a conditional branch
is_ready, should_skip = timer.check_if_condition('<validation passed>')
# Returns (True, False) if condition met → proceed
# Returns (True, True) if condition not met → skip this branch
```

---

## 8. The Data Flow Pattern

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

## 9. Skip Values and Error Handling

The skip value (`@#SKIP#@`) propagates through operations:

| Scenario | Behavior |
|----------|----------|
| `cross_product` with any skip input | Result element is skip |
| `cross_action` on skip function or value | Result is skip |
| `element_action` with any skip input | Result element is skip |
| `get()` on missing index | Returns skip |

**Checking for valid data:**
```python
clean_data = reference.get_tensor(ignore_skip=True)
has_data = bool(clean_data)  # True if any non-skip values exist
```

---

## 10. Summary: Reference as the Computational Substrate

| Layer | What It Provides |
|-------|------------------|
| **Concept** | Semantic identity ("what does this data mean?") |
| **Reference** | Structural container ("how is this data organized?") |
| **Operations** | Transformations ("how does data combine and flow?") |

The Reference system enables NormCode's core promise: **data isolation with explicit flow**. Each inference receives precisely the References it needs, transforms them through well-defined operations, and produces new References for downstream consumers.

This is why you can trace exactly what each step saw and produced—it's all encoded in the Reference structure.
