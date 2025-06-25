# NormCode In-Question Analysis Algorithm

## Overview

This document outlines a systematic algorithm for transforming natural language questions and answers into formal NormCode structures. The algorithm provides a step-by-step approach to analyze different types of questions and their corresponding answers.

## Formal Question Structure Schema

### Question Format
```
"_question_marker_(_question_target_, _question_condition_)"
```

### Schema Components
- **question_marker**: `$what?` | `$how?` | `$when?`
- **question_target**: `(_question_target_)` - The entity, imperative, or judgement being questioned (enclosed in parentheses)
- **question_condition**: `$=` | `$::` | `@by` | `@onlyIf` | `@If` | etc.

### Examples
- `"$what?({step_2}, $::)"` - What does step_2 do?
- `"$how?(::(create accounnt), @by)"` - How to do create account?
- `"$when?(<money withdrawn>, @onlyIf)"` - When money withdrawn happen only if?

## General Algorithm Framework

### Phase 1: Question Analysis
1. **Parse Formal Question Structure**
   - Extract question marker: `$what?`, `$how?`, `$when?`
   - Extract question target: `(_question_target_)` (the entity, imperative, or judgement being questioned, enclosed in parentheses)
   - Extract question condition: `$=`, `$::`, `@by`, `@onlyIf`, `@If`, etc.

2. **Classify Question Components**
   - **Target Type**: Identify if target is an object, imperative, or judgement

3. **Validate Question Structure**
   - Ensure formal format: `"_question_marker_(_question_target_, _question_condition_)"`
   - Verify question marker matches condition type compatibility
   - Confirm target syntax follows NormCode object/imperative/judgement patterns

4. **Create Basic NormCode Inference Ground**
   - Construct minimal NormCode structure: `_question_target_ <= _condition_ <- _tbd_`
   - Establish entity foundation with target as root
   - Set relationship type based on condition

### Phase 1 End Result Examples

#### Example 1: `"$what?({step_2}, $::)"`
**Input**: Formal question about step definition
**Output**: Basic NormCode inference ground
```NormCodeDraft
{step_2}
    <= $::
```

**Horizontal Layout**:
```NormCodeDraft
|1|{step_2} |1.1|<= $:: |/1.1||/1|
```

#### Example 2: `"$how?(::(create account), @by)"`
**Input**: Formal question about imperative process
**Output**: Basic NormCode inference ground
```NormCodeDraft
::(create account)
    <= @by
```

**Horizontal Layout**:
```NormCodeDraft
|1|::(create account) |1.1|<= @by |/1.1||/1|
```

#### Example 3: `"$when?(<money withdrawn>, @onlyIf)"`
**Input**: Formal question about judgement condition
**Output**: Basic NormCode inference ground
```NormCodeDraft
<money withdrawn>
    <= @onlyIf
```

**Horizontal Layout**:
```NormCodeDraft
|1|<money withdrawn> |1.1|<= @onlyIf |/1.1||/1|
```

#### Example 4: `"$what?({bank_account}, $=)"`
**Input**: Formal question about object definition
**Output**: Basic NormCode inference ground
```NormCodeDraft
{bank_account}
    <= $=
```

**Horizontal Layout**:
```NormCodeDraft
|1|{bank_account} |1.1|<= $= |/1.1||/1|
```

### Phase 2: Clause Analysis
1. **Identify Sentence Structure Type**
   - **Imperative**: Commands, instructions, processes
   - **Declarative**: Statements, descriptions, definitions

2. **Identify and Separate Clauses**
   - **Single Clause**: Simple sentences with one main action or statement
   - **Multiple Clauses**: Complex sentences with coordinating conjunctions (and, or, but, then)
   - **Conditional Clauses**: Sentences with subordinating conjunctions (if, when, while, until)
   - **Sequential Clauses**: Ordered steps or processes (first, then, next, finally)

3. **Classify Clause Types**
   - **Main Clause**: Primary action or statement
   - **Subordinate Clause**: Supporting or conditional information
   - **Coordinate Clause**: Equal-level actions or statements
   - **Sequential Clause**: Ordered steps in a process

4. **Build on NormCodeDraft**
   - Take the basic NormCode inference ground from Phase 1
   - Add clause structure information to the draft
   - Translate clauses into appropriate NormCode syntax:
     - **Imperative clauses**: `::(action)`
     - **Declarative clauses**: `<statement>`
     - **Coordinate clauses**: Use `across()` operator for "and" logic
       - Create placeholder `<{1}<${ALL TRUE}%_>>` where the judgement is one instance of "all true"
       - Use `across()` to ensure both sub-clauses must be true simultaneously
     - **Conditional clauses**: Use `@if` operator for prerequisite relationships
     - **Sequential clauses**: Use `&in()` operator with ordered lists `[...]`
   - Prepare for template creation in Phase 3

### Phase 2 End Result Examples

#### Example 1: Single Clause (Imperative)
**Input**: "Mix the ingredients together"
**Phase 1 NormCodeDraft**:
```NormCodeDraft
{step_2}
    <= $::
```
**Phase 2 Addition**:
```NormCodeDraft
{step_2}
    <= $::
    <- ::(mix the ingredients together)
```

**Horizontal Layout**:
```NormCodeDraft
|1|{step_2} |1.1|<= $:: |/1.1||1.2|<- ::(mix the ingredients together) |/1.2||/1|
```

#### Example 2: Multiple Coordinate Clauses (Declarative)
**Input**: "The bread is heated and the pan is greased"
**Phase 1 NormCodeDraft**:
```NormCodeDraft
{step_2}
    <= $::
```
**Phase 2 Addition**:
```NormCodeDraft
{step_2}
    <= $::
    <- <{1}<${ALL TRUE}%_>>
    <- [<_heated> and <_greased>]<:1>
        <= across(<_heated>:_;<_greased>:_)
        <- <the bread is heated><:<_heated>>
        <- <the pan is greased><:<_greased>>
```

**Horizontal Layout**:
```NormCodeDraft
|1|{step_2} |1.1|<= $:: |/1.1||1.2|<- <{1}<${ALL TRUE}%_>> |/1.2||1.3|<- [<_heated> and <_greased>]<:1> |1.3.1|<= across(<_heated>:_;<_greased>:_) |/1.3.1||1.3.2|<- <the bread is heated><:<_heated>> |/1.3.2||1.3.3|<- <the pan is greased><:<_greased>> |/1.3.3||/1.3||/1|
```

**Comment**: Coordinate clauses linked by "and" require both sub-clauses to be 
true. The `across()` operator ensures the overall coordinate clause is true only 
when both `<_heated>` and `<_greased>` are true simultaneously.

#### Example 3: Conditional Clauses (Imperative)
**Input**: "If the dough is sticky, add more flour"
**Analysis**:
- **Structure Type**: Imperative
- **Clause Count**: Multiple clauses
- **Clause Types**:
  - Subordinate clause: "If the dough is sticky"
  - Main clause: "add more flour"
**Phase 1 NormCodeDraft**:
```NormCodeDraft
{step_2}
    <= $::
```
**Phase 2 Addition**:
```NormCodeDraft
{step_2}
    <= $::
    <- ::(add more flour)
        <= @if
        <- <the dough is sticky>
```

**Horizontal Layout**:
```NormCodeDraft
|1|{step_2} |1.1|<= $:: |/1.1||1.2|<- ::(add more flour) |1.2.1|<= @if |/1.2.1||1.2.2|<- <the dough is sticky> |/1.2.2||/1.2||/1|
```

**Comment**: Conditional clauses linked by "if" create a prerequisite 
relationship. The `@if` operator establishes that the imperative action `::(add more flour)` is performed only when the condition `<the dough is sticky>` is  true.

#### Example 4: Sequential Clauses (Imperative)
**Input**: "First mix the ingredients, then pour into pan, finally bake"
**Analysis**:
- **Structure Type**: Imperative
- **Clause Count**: Multiple clauses
- **Clause Types**:
  - Sequential clause: "First mix the ingredients"
  - Sequential clause: "then pour into pan"
  - Sequential clause: "finally bake"
**Phase 1 NormCodeDraft**:
```NormCodeDraft
{step_2}
    <= $::
```
**Phase 2 Addition**:
```NormCodeDraft
{step_2}
    <= $::
    <- [::(mix the ingredients), ::(pour into pan), ::(bake)]
        <= &in(::(mix the ingredients):_; ::(pour into pan):_; ::(bake):_)
        <- ::(mix the ingredients)
        <- ::(pour into pan)
        <- ::(bake)
```

**Horizontal Layout**:
```NormCodeDraft
|1|{step_2} |1.1|<= $:: |/1.1||1.2|<- [::(mix the ingredients), ::(pour into pan), ::(bake)] |1.2.1|<= &in(::(mix the ingredients):_; ::(pour into pan):_; ::(bake):_) |/1.2.1||1.2.2|<- ::(mix the ingredients) |/1.2.2||1.2.3|<- ::(pour into pan) |/1.2.3||1.2.4|<- ::(bake) |/1.2.4||/1.2||/1|
```

**Comment**: Sequential clauses create an ordered sequence of actions. The `&in()
` operator groups the sequential steps, and the list `[...]` maintains the 
order: first mix, then pour, finally bake.

### Phase 3: Template Creation
1. **Build on Phase 2 NormCodeDraft**
   - Take the clause-analyzed NormCodeDraft from Phase 2
   - Preserve the logical structure and operators from Phase 2
   - Add template abstractions while maintaining existing relationships

2. **Add Template Abstractions**
   - Replace specific concrete terms with typed placeholders: `{n}<$({type})%_>`
   - Create abstract patterns for similar content (objects, states, materials, etc.)
   - Maintain the original clause structure and operators

3. **Create Reference Mappings**
   - Link concrete terms to abstract placeholders: `{concrete_term}<:{n}>`
   - Map template patterns to concrete placeholders: `<<template>><:<placeholder>>`
   - Establish bidirectional references between concrete and abstract levels

4. **Preserve Logical Structure**
   - Keep all operators from Phase 2 (`@if`, `across()`, `&in()`)
   - Maintain clause relationships and groupings
   - Ensure template abstractions don't break logical connections

### Phase 3 End Result Examples

#### Example 1: Single Clause Template
**Phase 2 NormCodeDraft**:
```NormCodeDraft
{step_2}
    <= $::
    <- ::(mix the ingredients together)
```
**Phase 3 Template**:
```NormCodeDraft
{step_2}
    <= $::
    <- ::(mix {1}<$({ingredients})%_> together)
    <- {ingredients}<:{1}>
```

**Horizontal Layout**:
```NormCodeDraft
|1|{step_2} |1.1|<= $:: |/1.1||1.2|<- ::(mix {1}<$({ingredients})%_> together) |/1.2||1.3|<- {ingredients}<:{1}> |/1.3||/1|
```

#### Example 2: Coordinate Clauses Template
**Phase 2 NormCodeDraft**:
```NormCodeDraft
{step_2}
    <= $::
    <- <{1}<${ALL TRUE}%_>>
    <- [<_heated> and <_greased>]<:1>
        <= across(<_heated>:_;<_greased>:_)
        <- <the bread is heated><:<_heated>>
        <- <the pan is greased><:<_greased>>
```
**Phase 3 Template**:
```NormCodeDraft
{step_2}
    <= $::
    <- <{1}<${ALL TRUE}%_>>
    <- [<_heated> and <_greased>]<:1>
        <= across(<_heated>:_;<_greased>:_)
        <- <<{2}<$({object})%_> is {3}<$({state})%_>><:<_heated>>
        <- <<{4}<$({object})%_> is {5}<$({state})%_>><:<_greased>>
        <- {bread}<:{2}>
        <- {heated}<:{3}>
        <- {pan}<:{4}>
        <- {greased}<:{5}>
```

**Horizontal Layout**:
```NormCodeDraft
|1|{step_2} |1.1|<= $:: |/1.1||1.2|<- <{1}<${ALL TRUE}%_>> |/1.2||1.3|<- [<_heated> and <_greased>]<:1> |1.3.1|<= across(<_heated>:_;<_greased>:_) |/1.3.1||1.3.2|<- <<{2}<$({object})%_> is {3}<$({state})%_>><:<_heated>> |/1.3.2||1.3.3|<- <<{4}<$({object})%_> is {5}<$({state})%_>><:<_greased>> |/1.3.3||1.3.4|<- {bread}<:{2}> |/1.3.4||1.3.5|<- {heated}<:{3}> |/1.3.5||1.3.6|<- {pan}<:{4}> |/1.3.6||1.3.7|<- {greased}<:{5}> |/1.3.7||/1.3||/1|
```

#### Example 3: Conditional Clauses Template
**Phase 2 NormCodeDraft**:
```NormCodeDraft
{step_2}
    <= $::
    <- ::(add more flour)
        <= @if
        <- <the dough is sticky>
```
**Phase 3 Template**:
```NormCodeDraft
{step_2}
    <= $::
    <- ::(add more {2}<$({ingredient})%_>)
        <= @if
        <- <{3}<$({material})%_> is {4}<$({condition})%_>>
        <- {dough}<:{3}>
        <- {sticky}<:{4}>
    <- {flour}<:{2}>
```

**Horizontal Layout**:
```NormCodeDraft
|1|{step_2} |1.1|<= $:: |/1.1||1.2|<- ::(add more {2}<$({ingredient})%_>) |1.2.1|<= @if |/1.2.1||1.2.2|<- <{3}<$({material})%_> is {4}<$({condition})%_>> |/1.2.2||1.2.3|<- {dough}<:{3}> |/1.2.3||1.2.4|<- {sticky}<:{4}> |/1.2.4||/1.2||1.3|<- {flour}<:{2}> |/1.3||/1|
```

## Algorithm Summary

The NormCode In-Question Analysis Algorithm transforms natural language questions and answers into formal NormCode structures through three sequential phases:

### Phase 1: Question Analysis
- **Input**: Formal question in format `"question_marker(question_target, question_condition)"`
- **Process**: Parse question marker, target, and condition; validate structure
- **Output**: Basic NormCode inference ground with target and relationship operator

### Phase 2: Clause Analysis
- **Input**: Natural language answer + Phase 1 NormCodeDraft
- **Process**: Analyze sentence structure (imperative/declarative); identify and classify clauses (single, coordinate, conditional, sequential); translate into NormCode syntax
- **Output**: Clause-analyzed NormCodeDraft with concrete content and logical operators

### Phase 3: Template Creation
- **Input**: Phase 2 NormCodeDraft
- **Process**: Add template abstractions with typed placeholders; create reference mappings between concrete and abstract levels; preserve logical structure
- **Output**: Complete NormCode structure with templates, references, and validation

### Key Features
- **Incremental Building**: Each phase builds on the previous phase's output
- **Preservation of Logic**: All logical operators and relationships are maintained throughout
- **Reference Mapping**: Bidirectional links between concrete terms and abstract templates
- **Type Safety**: Semantic typing ensures consistency across elements
- **Modular Design**: Each phase has a distinct, focused responsibility

This three-phase approach ensures systematic, consistent transformation from natural language to formal NormCode structures while maintaining semantic accuracy and logical completeness.

