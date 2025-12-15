# Complete NormCode Generation Process: Account Creation

## Overview

This document demonstrates the complete three-step process for generating NormCode from natural language:
1. **Normtext Deconstruction** - Breaking down the original text
2. **Question Analysis** - Formalizing the structure and relationships
3. **Integration** - Combining multiple aspects into unified NormCode

## Original Norm-text

**"Create a user account with email and password. The account has admin privileges and is active by default."**

---

## Step 1: Normtext Deconstruction

### Deconstruction Process

**Step 1.1: Identify the main question**
- How to do? (Main Process)
- Given it is done by the method, then it makes what happen? (Consequence)

**Step 1.2: Break down into components**
- **Main Action**: "Create a user account with email and password"
- **Consequence**: "The account has admin privileges and is active by default"

**Step 1.3: Identify structural elements**
- **Imperative sentence**: Command/instruction format
- **Declarative sentence**: State description format
- **Compound objects**: "email and password", "admin privileges and is active"

---

## Step 2: Specific Analysis

### Example 1: Main Process Analysis

#### Formal Question Structure
```json
{
    "level": 1,
    "question_type": "Main Process",
    "formal_question": "$how?(::(do), @by)",
    "natural_question": "How to do?",
    "natural_answer": "Create a user account with email and password."
}
```

#### Analysis Process

**Step 2.1: Identify Structure Type**
- "Create a user account with email and password." is an imperative sentence (command/instruction)

**Step 2.2: Extract Core Elements**
- **Action**: create
- **Object**: user account  
- **Instrument**: email and password

**Step 2.3: Create Template with Placeholders**
- Replace specific terms with numbered placeholders: `:S:(create {1} with {2})`
- `:S:` represents the subject (agent performing the action)

**Step 2.4: Add Concept Typing**
- Add semantic type annotations using `<$={concept_type}>`:
- `:S:(create {1}<$={account}> with {2}<$={information}>)`
- This indicates that {1} is of type "account" and {2} is of type "information"

**Step 2.5: Decompose Complex Elements**
- Break down compound objects: `{email and password}` becomes `[{email} and {password}]`
- Use `&in()` to show component relationships

**Step 2.6: Map References**
- Add `<:{n}>` annotations to link concrete terms back to template positions:
- `{user account}?<:{1}>` maps "user account" to position {1}
- `[{email} and {password}]<:{2}>` maps the compound to position {2}

#### Main Process NormCode
```NormCode
::(do)
    <= @by(:S:)
    <- :S:(create {1}?<$={account}> with {2}<$={information}>)
    <- {user account}?<:{1}>
    <- [{email} and {password}]<:{2}>
        <= &in({email}:{email}; {password}:{password})
        <- {email}
        <- {password}
```

### Example 2: Consequence Analysis

#### Formal Question Structure
```json
{
    "level": 1,
    "question_type": "Consequence",
    "formal_question": "$when?(::(do)@by, @onlyIf)",
    "natural_question": "Given it is done by the method, then it makes what happen?",
    "natural_answer": "The account has admin privileges and is active by default."
}
```

#### Analysis Process

**Step 2.1: Identify Structure Type**
- "The account has admin privileges and is active by default." is a declarative sentence describing a state

**Step 2.2: Extract Core Elements**
- **Subject**: the account
- **Predicates**: has admin privileges, is active by default

**Step 2.3: Create Template with Placeholders**
- `S.<{1}<$={account}> has {2}<$={privileges}> and is {3}<$={status}>>`
- `S.` indicates the subject, `<...>` groups related predicates

**Step 2.4: Decompose Complex Predicate**
- Break the compound predicate into simpler ones:
- `S.<{1}<$={account}> has {2}<$={privileges}>>`
- `S.<{1}<$={account}> is {3}<$={status}>>`

**Step 2.5: Use @onlyIf for Conditional Relationship**
- The `@onlyIf` operator indicates this is a consequence that follows from the main action

**Step 2.6: Reference Mapping**
- `{account}<:{1}>` maps "account" to position {1}
- `{privileges}<:{2}>` maps "privileges" to position {2}  
- `{status}<:{3}>` maps "status" to position {3}

#### Consequence Analysis NormCode
```NormCode
::(do)@by
    <= @onlyIf(S.)
    <- S.<{1}<$={account}> has {2}<$={privileges}> and is {3}<$={status}>>
        <= &in(S.^({1}<:{1}>, {2}<:{2}>, {3}<:{3}>))
        <- S.<{1}<$={account}> has {2}<$={privileges}>>
        <- S.<{1}<$={account}> is {3}<$={status}>>
    <- {account}<:{1}>
    <- {privileges}<:{2}>
    <- {active by default}<:{3}>
```

---

## Step 3: Integration

### Combined NormCode Structure

The integration combines the Main Process and Consequence Analysis into a unified NormCode representation that shows the complete workflow from action to consequence.

#### Integrated NormCode
```NormCode
:S:(do)
    <= @by(:S:^({1}<:{1}>))
        <= @onlyIf(S.)
        <- S.<{1}<$={account}> has {2}<$={privileges}> and {3}<$={status}>>
            <= &in(S.^({1}<:{1}>, {2}<:{2}>, {3}<:{3}>))
            <- S.<{1}<$={account}> has {2}<$={privileges}>>
            <- S.<{1}<$={account}> {3}<$={status}>>
        <- {privileges}<:{2}>
            <= :S_conceptual:({privileges}?)
        <- {active by default}<:{3}>
            <= :S_conceptual:({active by default}?)
    <- :S:(create {1}?<$={account}> with {2}<$={information}>)
    <- {user account}?<:{1}>
    <- [{email} and {password}]<:{2}>
        <= &in({email}:{email}; {password}:{password})
        <- {email}
            <= :S_provision:({email}?)
        <- {password}
            <= :S_provision:({password}?)
```

### Integration Explanation

#### Structure Overview

The integrated NormCode demonstrates a hierarchical relationship where:

1. **Main Action**: `:S:(do)` - The subject performs the action
2. **Agent Specification**: `<= @by(:S:)` - Defines who performs the action
3. **Consequence Analysis**: `<= @onlyIf` - Nested under the agent, showing automatic consequences
4. **Process Details**: The creation process with account and information components

#### Key Integration Points

**1. Hierarchical Nesting**
- The consequence analysis (`@onlyIf`) is nested under the agent specification (`@by`)
- This shows that the consequences are directly related to the agent's action
- Each level maintains the single `<=` rule

**2. Agent-Consequence Relationship**
- `@by(:S:)` specifies the agent performing the action
- `@onlyIf` under `@by` shows what automatically happens when this agent performs the action
- The nesting indicates that consequences are agent-specific

**3. Shared Reference System**
- Account references are unified: `{user account}?<:{1}>` (process) and `{account}<:{1}>` (consequence)
- Both reference the same position `{1}` in their respective contexts
- The consequence references the account created by the agent

#### Semantic Flow

1. **Agent Action**: `:S:` is specified as the agent performing the action
2. **Automatic Consequence**: When `:S:` performs the action, the account automatically gets admin privileges and active status
3. **Process Execution**: The agent creates a user account with email and password
4. **Component Decomposition**: Email and password are broken down into individual components

### Benefits of Integration

- **Agent-Specific Consequences**: Shows that consequences are tied to specific agents
- **Hierarchical Clarity**: Clear nesting shows the relationship between agent, action, and consequences
- **Complete Workflow**: Demonstrates the full cycle from agent action to automatic state changes
- **Modular Structure**: Each component can be analyzed independently while maintaining integration

### Usage Context

This integrated structure is particularly useful for:
- **Role-based systems**: Where different agents have different consequences
- **Access control specifications**: Showing automatic privilege assignments
- **Business process modeling**: Capturing agent-specific workflows
- **Regulatory compliance**: Documenting who does what and what automatically follows

---

## Summary

The complete NormCode generation process transforms natural language into formal, structured representations through:

1. **Deconstruction**: Breaking down complex text into manageable components
2. **Analysis**: Formalizing each component with proper typing and relationships
3. **Integration**: Combining multiple aspects into a unified, hierarchical structure

This process ensures that the resulting NormCode captures both the explicit actions and implicit consequences, providing a complete specification of the system behavior.
