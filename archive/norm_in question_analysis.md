          
## Example 1: Main Process    
          
```json     
          
{
    "level": 1,
    "question_type": "Main Process",
    "formal_question": "$how?(::(do), @by)",
    "natural_question": "How to do?",
    "natural_answer": "Create a user account with email and password."
},

```

### Explanation of the Analysis Process

This analysis transforms natural language into formal NormCode structures through several systematic steps:

### Step 1: Identify Structure Type
**"Create a user account with email and password."** is an imperative sentence (command/instruction).

### Step 2: Extract Core Elements
- **Action**: create
- **Object**: user account  
- **Instrument**: email and password

### Step 3: Create Template with Placeholders
Replace specific terms with numbered placeholders:
- `:S:(create {1} with {2})` where `:S:` represents the subject (agent performing the action)

### Step 4: Add Concept Typing
Add semantic type annotations using `<$({concept_type})%_>`:
- `:S:(create {1}<$({account})%_> with {2}<$({information})%_>)`
- This indicates that {1} is of type "account" and {2} is of type "information"

### Step 5: Decompose Complex Elements
Break down compound objects:
- `{email and password}` becomes `[{email} and {password}]`
- Use `&in()` to show component relationships

### Step 6: Map References
Add `<:{n}>` annotations to link concrete terms back to template positions:
- `{user account}?<:{1}>` maps "user account" to position {1}
- `[{email} and {password}]<:{2}>` maps the compound to position {2}

"Create a user account with email and password."： 
main structure: imperative 
::(create a user account with email and password)
obejct elements 
{user account} {email and password}
with the object elements removed and subject added (presuming the subject is S)
:S:(create {1} with {2}) 
with concept typing for arguments this will be `:S:(create {1}<$({account})%_> with {2}<$({information})%_>)`
further decomposable object: {email and password}
which is [{email} and {password}] with component {email} and {password}
under &in({email}: {email}; {password}: {password})
notice that user account is created so it is no guarantee that it has references with beings so it is more like an placeholder concept

Combining all these analysis and the question we get: 

### NormCode
```NormCode
::(do)
    <= @by(:S:)
    <- :S:(create {1}<$({account})%_> with {2}<$({information})%_>)
    <- {user account}?<:{1}>
    <- [{email} and {password}]<:{2}>
        <= &in({email}:{email}; {password}:{password})
        <- {email}
        <- {password}
```

## Example 2: Consequence Analysis

```json
{
    "level": 1,
    "question_type": "Consequence",
    "formal_question": "$when?(::(do)@by, @onlyIf)",
    "natural_question": "Given it is done by the method, then it makes what happen?",
    "natural_answer": "The account has admin privileges and is active by default."
}
```

### Explanation of Consequence Analysis

This example shows how to handle declarative statements that describe the result of an action:

### Step 1: Identify Structure Type
**"The account has admin privileges and is active by default."** is a declarative sentence describing a state.

### Step 2: Extract Core Elements
- **Subject**: the account
- **Predicates**: has admin privileges, is active by default

### Step 3: Create Template with Placeholders
- `S.<{1}<$({account})%_> has {2}<$({privileges})%_> and is {3}<$({status})%_>>`
- `S.` indicates the subject, `<...>` groups related predicates

### Step 4: Decompose Complex Predicate
Break the compound predicate into simpler ones:
- `S.<{1}<$({account})%_> has {2}<$({privileges})%_>>`
- `S.<{1}<$({account})%_> is {3}<$({status})%_>>`

### Step 5: Use @onlyIf for Conditional Relationship
The `@onlyIf` operator indicates this is a consequence that follows from the main action.

### Step 6: Reference Mapping
- `{account}<:{1}>` maps "account" to position {1}
- `{privileges}<:{2}>` maps "privileges" to position {2}  
- `{status}<:{3}>` maps "status" to position {3}

### NormCode
```NormCode
::(do)@by
    <= @onlyIf
    <- S.<{1}<$({account})%_> has {2}<$({privileges})%_> and is {3}<$({status})%_>>
        <= &in(S.^({1}<:{1}>, {2}<:{2}>, {3}<:{3}>))
        <- S.<{1}<$({account})%_> has {2}<$({privileges})%_>>
        <- S.<{1}<$({account})%_> is {3}<$({status})%_>>
    <- {account}<:{1}>
    <- {privileges}<:{2}>
    <- {status}<:{3}>
```

## Example 3: Antecedent Analysis

```json
{
    "level": 1,
    "question_type": "Antecedent",
    "formal_question": "$when?(({butterfly})$=, @If)",
    "natural_question": "Given butterfly exists, then what makes butterfly?",
    "natural_answer": "Butterfly eggs hatch into caterpillars."
}
```

### Explanation of Antecedent Analysis

This example shows how to handle causal relationships where one entity produces another:

### Step 1: Identify Structure Type
**"Butterfly eggs hatch into caterpillars."** is a declarative sentence describing a causal process.

### Step 2: Extract Core Elements
- **Subject**: butterfly eggs
- **Action**: hatch
- **Result**: caterpillars

### Step 3: Create Template with Placeholders
- `S.<{1}<$({organism})%_> hatch into {2}<$({organism})%_>>` where both entities are organisms
- This captures the transformation from one organism type to another

### Step 4: Identify Causal Relationship
This is an antecedent relationship where:
- Input: butterfly eggs (precursor)
- Process: hatching
- Output: caterpillars (result)

### Step 5: Use @If for Antecedent Relationship
The `@If` operator indicates this is a prerequisite condition that leads to the target entity.

### Step 6: Reference Mapping and Entity Relationships
- `{butterfly eggs}<:{1}>` maps the precursor to position {1}
- `{caterpillars}?<:{2}>` maps the result to position {2}
- `$.({1}:{butterfly eggs}?)` establishes the relationship between position {1} and the concrete term
- `::({eggs}? of {butterfly})` shows that butterfly eggs are eggs belonging to a butterfly

### Step 7: Entity Composition Analysis
The structure shows that:
- Butterfly eggs are composed of eggs that belong to a butterfly
- This creates a hierarchical relationship: butterfly → eggs → hatching → caterpillars

"Butterfly eggs hatch into caterpillars."：
main structure: declarative (causal process)
::(butterfly eggs hatch into caterpillars)
subject element: {butterfly eggs}
action element: hatch
result element: {caterpillars}
with subject element as precursor and result as output
`S.<{1}<$({organism})%_> hatch into {2}<$({organism})%_>>`
notice that this describes a transformation process where one entity becomes another, and the precursor has a compositional relationship with the target entity

Combining all these analysis and the question we get:

### NormCode
```NormCode
({butterfly})$=
    <= @If
    <- S.<{1}<$({organism})%_> hatch into {2}<$({organism})%_>>
    <- {butterfly eggs}<:{1}>
        <= $.({1}:{butterfly eggs}?)
        <- ::({eggs}? of {butterfly})
        <- {butterfly}
    <- {caterpillars}?<:{2}>
```

## Example 4: Main Entity Analysis

```json
{
    "level": 1,
    "question_type": "Main Entity",
    "formal_question": "$what?({butterfly}, $=)",
    "natural_question": "What is butterfly?",
    "natural_answer": "Butterfly is butterfly."
}
```

### Explanation of Main Entity Analysis

This example shows how to handle definition/identity questions where an entity is defined in terms of itself:

### Step 1: Identify Structure Type
**"Butterfly is butterfly."** is a declarative sentence describing an identity relationship.

### Step 2: Extract Core Elements
- **Subject**: butterfly
- **Predicate**: is butterfly
- **Relationship**: identity/equivalence

### Step 3: Identify Identity Relationship
This is a self-referential definition where:
- Entity: butterfly
- Definition: butterfly (same entity)
- The entity is defined as itself - a tautological identity

### Step 4: Use $= for Entity Definition
The `$=` operator indicates this is an entity definition/identity statement.

### Step 5: Simplified Structure
Since this is a tautological definition where an entity equals itself, the structure is much simpler:
- No need for complex templates or placeholders
- No need for reference mapping since it's the same entity
- The entity is simply defined as itself

"Butterfly is butterfly."：
main structure: declarative (identity statement)
::(butterfly is butterfly)
subject element: {butterfly}
predicate element: {butterfly}
with subject and predicate being the same entity
notice that this is a tautological definition where an entity is defined as itself, requiring no complex decomposition

Combining all these analysis and the question we get:

###NormCode
```NormCode
{butterfly}
    <= $=({butterfly}:{butterfly}?)
    <- {butterfly}
```

## Example 5: Step Identification Analysis

```json
{
    "level": 2,
    "question_type": "Step Identification",
    "formal_question": "$what?({steps}, $=)",
    "natural_question": "What are the steps to do?",
    "natural_answer": "Do steps in step 1, step 2 and step 3."
}
```

### Explanation of Step Identification Analysis

This example shows how to handle questions about identifying the components of a process:

### Step 1: Identify Structure Type
**"Do steps in step 1, step 2 and step 3."** is an imperative sentence describing a sequence of steps.

### Step 2: Extract Core Elements
- **Action**: do
- **Object**: steps
- **Components**: step 1, step 2, step 3

### Step 3: Identify Sequence Relationship
This is a step identification where:
- Process: steps
- Sequence: step 1, step 2, step 3
- Order: sequential execution

### Step 4: Use $= for Step Definition
The `$=` operator indicates this defines what the steps are.

### Step 5: Simplified Structure
Since this is asking "what are the steps?", the answer directly lists the steps:
- `$=([{step 1}, {step 2}, {step 3}]:{steps}?)` defines steps as the sequence
- `&in({step 1}:_; {step 2}:_; {step 3}:_)` shows each step is defined as itself
- The `_` notation means each step equals itself (e.g., `{step 1}:{step 1}`)

### Step 6: Component Analysis
Each step in the sequence is a component of the overall process:
- `{step 1}`, `{step 2}`, `{step 3}` are the individual components
- They form a sequence `[{step 1}, {step 2}, {step 3}]`
- Each step is defined as itself in the sequence

"Do steps in step 1, step 2 and step 3."：
main structure: imperative (sequence instruction)
::(do steps in step 1, step 2 and step 3)
action element: do
object element: {steps}
sequence element: [{step 1}, {step 2}, {step 3}]
with object being a process and sequence being ordered steps
notice that this describes a process with ordered sequential steps, where each step is defined as itself

Combining all these analysis and the question we get:

### NormCode
```NormCode
{steps}
    <= $=([{step 1}, {step 2}, {step 3}]:{steps}?)
    <- [{step 1}, {step 2}, {step 3}]
        <= &in({step 1}:_; {step 2}:_; {step 3}:_)
        <- {step 1}
        <- {step 2}
        <- {step 3}
```

## Example 6: Step Analysis

```json
{
    "level": 2,
    "question_type": "Step 2",
    "formal_question": "$what?({step_2}, $::)",
    "natural_question": "What step 2 does?",
    "natural_answer": "Step 2 does mix flour, sugar, and butter until creamy."
}
```

### Explanation of Step Analysis

This example shows how to handle questions about specific steps in a process:

### Step 1: Identify Structure Type
**"Step 2 does mix flour, sugar, and butter until creamy."** is a declarative sentence describing a specific action within a process.

### Step 2: Extract Core Elements
- **Subject**: step 2
- **Action**: mix
- **Objects**: flour, sugar, butter
- **Condition**: until creamy

### Step 3: Create Template with Placeholders
- `:S:(mix {1}<$({ingredients})%_> until {2}<$({condition})%_>)` where `:S:` represents the agent performing the action
- This captures the mixing action with ingredients and a completion condition

### Step 4: Decompose Complex Object
Break down the compound ingredients:
- `{flour, sugar, and butter}` becomes `[{flour}, {sugar}, {butter}]`
- Use `&in()` to show component relationships

### Step 5: Use $:: for Step Definition
The `$::` operator indicates this defines what a specific step does.

### Step 6: Reference Mapping
- `[{flour}, {sugar}, {butter}]<:{1}>` maps the ingredients to position {1}
- `{creamy}<:{2}>` maps the condition to position {2}

### Step 7: Component Analysis
The ingredients form a compound object:
- `{flour}`, `{sugar}`, `{butter}` are the individual components
- They form a set `[{flour}, {sugar}, {butter}]`
- The condition `{creamy}` represents the desired state

### Step 8: Process Logic Analysis
The step involves a conditional process:
- **Agent relationship**: `@by(:S:^({1}<:{1}>, {2}<:{2}>))` shows the agent works with both ingredients and condition
- **Core action**: `:S:(mix {1}<$({ingredients})%_>)` - the basic mixing action
- **Conditional logic**: `@onlyIf(S.^({1}<:{1}>, {2}<:{2}>))` - the condition that must be met
- **State transition**: `S.<{1}<$({ingredients})%_> not {2}<$({condition})%_>>` - shows the initial state (ingredients not yet creamy)

"Step 2 does mix flour, sugar, and butter until creamy."：
main structure: declarative (step description)
::(step 2 does mix flour, sugar, and butter until creamy)
subject element: {step 2}
action element: mix
object elements: {flour, sugar, and butter}
condition element: {creamy}
with subject being a process step and objects being ingredients
`:S:(mix {1}<$({ingredients})%_> until {2}<$({condition})%_>)`
further decomposable object: {flour, sugar, and butter}
which is [{flour}, {sugar}, {butter}] with components {flour}, {sugar}, and {butter}
under &in({flour}:{flour}; {sugar}:{sugar}; {butter}:{butter})
notice that this describes a specific step in a larger process with multiple ingredients and a completion condition
the process logic shows: agent relationship (@by), core mixing action, conditional completion (@onlyIf), and state transition from "not creamy" to "creamy"

Combining all these analysis and the question we get:

### NormCode
```NormCode
{step_2}
    <= $::(:S:)
    <- :S:(mix {1}<$({ingredients})%_> until {2}<$({condition})%_>)
        <= @by(:S:^({1}<:{1}>, {2}<:{2}>))
        <- :S:(mix {1}<$({ingredients})%_>)
            <= @onlyIf(S.^({1}<:{1}>, {2}<:{2}>))
            <- S.<{1}<$({ingredients})%_> not {2}<$({condition})%_>>
    <- [{flour}, {sugar}, {butter}]<:{1}>
        <= &in({flour}:{flour}; {sugar}:{sugar}; {butter}:{butter})
        <- {flour}
        <- {sugar}
        <- {butter}
    <- {creamy}<:{2}>
```

## Key NormCode Notation Explained

- `::(do)` - Main action/process
- `@by` - Agent performing the action
- `@onlyIf` - Conditional relationship (consequence)
- `@If` - Antecedent relationship (prerequisite)
- `$what?({entity}, $=)` - Entity definition question
- `$=` - Identity/definition operator
- `:S:` - Subject placeholder
- `{n}<$({type})%_>` - Typed placeholder where n is position, type is semantic category
- `<:{n}>` - Reference mapping from concrete term to placeholder position
- `{..}` - **Object/Concept** (represents an actual object or concept)
- `{..}?` - **Object Placeholder** (placeholder for an object/concept)
- `&in()` - Component relationship operator
- `S.<...>` - Subject-predicate grouping
- `S.^()` - Component relationship under a subject
