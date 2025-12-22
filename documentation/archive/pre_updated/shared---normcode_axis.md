# Axes of Reference

## 1. What Are Axes?

Axes of reference are **frozen modes of presentation** that model the **indeterminacies** inherent in expressions like "a student", "a number pair", or "a file".

When we say "a student" in a specific context, we encounter many dimensions of indeterminacy: class, school, nationality, gender, age, etc. These dimensions form the **axes** of a tensor-like structure.

---

## 2. From Determinate to Indeterminate Reference

### 2.1. Determinate Reference (Flat List)

When we fully reveal all students in a context, we get a flat list:

```
{student} = [
    {class: "A", school: "School A", nationality: "American", name: "John Doe"},
    {class: "A", school: "School B", nationality: "British", name: "Jane Smith"},
    {class: "C", school: "School C", nationality: "American", name: "Jim Beam"},
    {class: "C", school: "School C", nationality: ["British", "American"], name: "Fallon Doe"},
]
```

### 2.2. Indeterminate Reference (Tensor Structure)

When we use an **indeterminate reference** — we don't know which exact student, but we know the context — the data organizes into a nested tensor:

```
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
        [ //: class = "A"
            [ //: nationality = "American"
            ],
            [ //: nationality = "British"
            ]
        ],
        [ //: class = "C"
            [ //: nationality = "American"
            ],
            [ //: nationality = "British"
            ]
        ]
    ],
    [ //: school = "School C"
        [ //: class = "A"
            [ //: nationality = "American"
            ],
            [ //: nationality = "British"
            ]
        ],
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

## 3. Why This Design is Useful

This structure enables **context-agnostic operations**:

- We can apply an operation to "a student" (singular) using `element_action` or `cross_action`
- The operation doesn't need to know the surrounding context (school, class, nationality)
- The context can change over time without modifying the operation
- The formality of the context structure can evolve independently

---

## 4. Types of Axes

### 4.1. Self-Provided Axis

The concept's own dimension of plurality. For example:
- `{student}` provides the "student" axis
- `{school}` provides the "school" axis

### 4.2. Dependent Axes

Axes inherited from context or other concepts. For example:
- When discussing students, "school", "class", and "nationality" are dependent axes

### 4.3. The `_none_axis` Case

If a concept has no inherent plurality (a singular, certain value), it uses `_none_axis` as a degenerate axis with shape `(1,)`.

**Rule**: Each self-provided axis should be **unique** within a NormCode plan. If a concept cannot guarantee uniqueness, it should use `_none_axis`.

---

## 5. Axis Accumulation Through Inference

Consider this inference:

```ncds
<- parent
    <= find parent
    <- student
```

The `parent` concept can accumulate axes because:
1. There are usually **multiple parents** per student → introduces a "parent" axis
2. The **student's axes** (school, class, nationality) become dependent axes of `parent`
3. If `find parent` has multiple interpretations (biological vs. legal) → it may contribute its own axis

**Result**: `parent` axes might become `[school, class, nationality, student, parent_type, parent]`

When the operation is **certain** (no ambiguity), its contribution is `_none_axis` (effectively invisible).

---

## 6. Grouping Examples

The following examples demonstrate how grouping operators interact with axes.

### 6.1. `&[{}]` — Group In (Annotated Collapse)

```ncds
<- students in a school 
    <= map students in the same school | %{ncd}: &[{}] %>[{student}, {school}] %:[{school}]
    <- student 
    <- school
    <* school
```

**Effect**: The `school` axis is collapsed, but each element is **annotated** with its school:

```
axes: [class, nationality, student]  ← school axis dropped

students: [ 
    [ //: class = "A"
        [ //: nationality = "American"
            {student: John Doe, school: School A}
        ],
        [ //: nationality = "British"
        ]
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

### 6.2. `&[#]` — Group Across (Flattened Collapse)

```ncds
<- students across schools 
    <= collect students across different schools | %{ncd}: &[#] %>[{student}] %:[{school}]
    <- student
    <* school
```

**Effect**: The `school` axis is collapsed, and values are **flattened** into raw elements:

```
axes: [class, nationality, student]  ← school axis dropped

students: [
    [ //: class = "A"
        [ //: nationality = "American"
            John Doe,
        ],
        [ //: nationality = "British"
        ]
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

### 6.3. `&[{}]` with Protected Axes

```ncds
<- students and parents for each student with a nationality | %{ncd}: [{student} and {parent}]<%:({nationality})>
    <= map students and parents for each student | %{ncd}: &[{}] %>[{student}; {parent}] %:[{student}<$!={nationality}>]
    <- student 
    <- parent
    <* nationality
```

**Effect**: The `student` axis is collapsed, but `nationality` is **protected** (kept):

```
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
## 7. Assigning Examples

The following examples demonstrate how assigning operators interact with axes.

### 7.1. `$-`

```ncds
<- parents for a student with a nationality | %{ncd}: [{parent}]<%:({nationality})>
    <= select all the parents from the following | %{ncd}: $- %>[{student} and {parent}]<%:({nationality})> %^<$*#><$({parent})%>
    <- students and parents for each student with a nationality | %{ncd}: [{student} and {parent}]<%:{nationality}>
```

```
axes: [nationality]
parents: 
[ 
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

```ncds
<- a parent for a student with a nationality | %{ncd}: {parent}<%:({nationality})>
    <= select a parent from the following | %{ncd}: $- %>[{student} and {parent}]<%:({nationality})> %^<$*#><$({parent})%> %:{parent}<%:({nationality})>
    <- students and parents for each student with a nationality | %{ncd}: [{student} and {parent}]<%:{nationality}>
```

```
axes: [nationality, parent]
parents: 
[ 
    [ //: nationality = "American"
        [ //: parent list 
            Kim Doe, Lowe Doe, Kim Beam, Lowe Beam
        ],
    ],
    [ //: nationality = "British"
        [ //: parent list 
            Kim Smith, Lowe Smith, Kim Doe, Lowe Doe
        ]
    ]
]
```


---

### 7.2. `$+` — Continuation (Simple Append)

**Use Case**: Adding a new student to an existing collection

```ncds
<- updated student with nationality | %{ncd}: {student}<%:({nationality})>
    <= add new student to the current student | %{ncd}: $+ %>({current student}) %<({new student}) %:({student})
    <- current student | %{ncd}: {student}<%:({nationality})>
    <- new student | %{ncd}: {student}<%:({nationality})>
```

**Before** (current students):
```
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

**Append** (new student):
```
axes: [nationality, student]
shape: (2, 1)

new_student: [
    [ //: nationality = "American"
        Alice Wang
    ],
    [ //: nationality = "British"
        Bob Chen
    ]
]
```

**After** (append along `student` axis):
```
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

### 7.3. `$+` — Continuation (Element-wise Append)

**Use Case**: Adding test scores to each student (extending a different axis)

```ncds
<- updated student with all test scores | %{ncd}: {student}<%:({nationality}, {test})>
    <= append new test scores to the current student | %{ncd}: $+ %>({current student}) %<({new test scores}) %:({test})
    <- current student test scores | %{ncd}: {student}<%:({nationality}, {test})>
    <- new test scores | %{ncd}: {test score}<%:({nationality}, {student})>
```

**Before** (students with existing test scores):
```
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
    ],
    [ //: nationality = "British"
        [ //: student = Jane Smith
            [Test1: 92, Test2: 88]
        ]
    ]
]
```

**Append** (new test scores):
```
axes: [nationality, student, test]
shape: (2, 2, 1)  ← 1 new test per student

new_test_scores: [
    [ //: nationality = "American"
        [ //: student = John Doe
            [Test3: 87]
        ],
        [ //: student = Jim Beam
            [Test3: 80]
        ]
    ],
    [ //: nationality = "British"
        [ //: student = Jane Smith
            [Test3: 95]
        ]
    ]
]
```

**After** (append along `test` axis, element-wise per student):
```
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
    ],
    [ //: nationality = "British"
        [ //: student = Jane Smith
            [Test1: 92, Test2: 88, Test3: 95]
        ]
    ]
]
```

---

### 7.4. `$+` — Continuation (Broadcast Append)

**Use Case**: Adding a common property to all students

```ncds
<- students with school info | %{ncd}: {student}<%:({nationality}, {school})>
    <= add school info to all students | %{ncd}: $+ %>({students}) %<({school info}) %:({school})
    <- students | %{ncd}: {student}<%:({nationality})>
    <- school info | %{ncd}: {school info}
```

**Before** (students without school info):
```
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

**Append** (school info - broadcast to all):
```
axes: [school]
shape: (1,)

school_info: [
    { //: school info
        school_name: "Central High",
        district: "District 5"
    }
]
```

**After** (broadcast append - same info added to each student):
```
axes: [nationality, student, school]
shape: (2, 3, 1)  ← new school axis added

students_with_school: [
    [ //: nationality = "American"
        [ //: student = John Doe
            { school_name: "Central High", district: "District 5" }
        ],
        [ //: student = Jim Beam
            { school_name: "Central High", district: "District 5" }
        ],
        [ //: student = Fallon Doe
            { school_name: "Central High", district: "District 5" }
        ]
    ],
    [ //: nationality = "British"
        [ //: student = Jane Smith
            { school_name: "Central High", district: "District 5" }
        ],
        [ //: student = Fallon Doe
            { school_name: "Central High", district: "District 5" }
        ]
    ]
]
```

**Note**: Broadcast append occurs when the appended data has **no matching prefix axes** with the target, so it's replicated to every element.

---

## 8. Summary

| Concept | Description |
|---------|-------------|
| **Axes** | Named dimensions of referential indeterminacy |
| **Self-provided axis** | The concept's own plurality dimension |
| **Dependent axes** | Inherited from context/inputs |
| **`_none_axis`** | Degenerate axis for certain (singular) values |
| **Axis accumulation** | Axes compound through inference chains |
| **`%:[{axis}]`** | Collapse this axis (remove from output) |
| **`<$!={axis}>`** | Protect this axis (keep even when collapsing) |
| **`$-`** | Selection/unpacking - extract elements from nested structure |
| **`$+`** | Continuation/append - extend data along a specified axis |
| **Simple append** | Grows the target axis (e.g., adding more students) |
| **Element-wise append** | Appends to each element along shared axes |
| **Broadcast append** | Replicates data to all elements (no shared axes) |
