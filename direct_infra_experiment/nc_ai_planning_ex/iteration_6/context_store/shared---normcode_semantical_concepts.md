# NormCode Guide - Semantical Concepts

Concepts are the building blocks of NormCode. Semantical concepts define the core entities and logical constructs of the domain. They can be subdivided into typically non-functional and functional types.

### Typically Non-Functional Concept Types
These concepts represent entities, their relationships, or their roles in the inference.

| Symbol                | Name                      | Description                                                                 |
| --------------------- | ------------------------- | --------------------------------------------------------------------------- |
| `{}`                  | Object                    | Represents a generic object or entity.                                      |
| `<>`                  | Statement                 | Represents a proposition or a state of affairs (non-functional).            |
| `[]`                  | Relation                  | Represents a relationship between two or more concepts.                     |
| `:S:`                 | Subject                   | Marks the subject of a relation or statement.                               |
| `:>:`                 | Input                     | A special type of Subject that marks a concept as an input parameter.       |
| `:<:`                 | Output                    | A special type of Subject that marks a concept as an output value.          |

**Examples:**
- **Object (`{}`):** `{new number pair}` declares a concept that will hold the state of the two numbers as they are processed.
- **Statement (`<>`):** `<all number is 0>` represents a condition that can be evaluated. The `judgement` agent's sequence will determine if this statement is true or false.
- **Relation (`[]`):** `[all {unit place value} of numbers]` defines a collection that will hold the digits from a specific place value of the numbers being added.

### Typically Functional Concept Types
These concepts define operations or evaluations that often initiate an inference.

| Symbol                | Name                      | Description                                                                 |
| --------------------- | ------------------------- | --------------------------------------------------------------------------- |
| `({})` or `::()`      | Imperative                | Represents a command or an action to be executed.                           |
| `<{}>` or `<...>`     | Judgement                 | Represents an evaluation that results in a boolean-like assessment.         |

**Examples:**
- **Imperative (`::()`):** `::(get the {1}?<$({remainder})%_> of {2}<$({digit sum})%_> divided by 10)` issues a command to a tool or model to perform a calculation. This is the heart of an `imperative` inference.
- **Judgement (`<...>`):** `<= :%(True):<{1}<$({carry-over number})%_> is 0>` evaluates whether the carry-over is zero. This is the core of a `judgement` inference. Note the use of `<...>` as a common syntax variant for a judgement.
