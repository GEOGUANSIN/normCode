# NormCode Integration: Main Process + Consequence Analysis

## Integrated NormCode Structure

This integration combines the Main Process (Example 1) and Consequence Analysis (Example 2) into a unified NormCode representation that shows the complete workflow from action to consequence.

### Combined NormCode

```NormCode
:S:(do)
    <= @by(:S:)
        <= @onlyIf
        <- S.<{1}<$={account}> has {2}<$={privileges}> and is {3}<$={status}>>
            <= &in(S.^({1}<:{1}>, {2}<:{2}>, {3}<:{3}>))
            <- S.<{1}<$={account}> has {2}<$={privileges}>>
            <- S.<{1}<$={account}> is {3}<$={status}>>
        <- {account}<:{1}>
        <- {privileges}<:{2}>
        <- {status}<:{3}>
    <- :S:(create {1}<$={account}> with {2}<$={information}>)
    <- {user account}?<:{1}>
    <- [{email} and {password}]<:{2}>
        <= &in({email}:{email}; {password}:{password})
        <- {email}
        <- {password}
```

## Integration Explanation

### Structure Overview

The integrated NormCode demonstrates a hierarchical relationship where:

1. **Main Action**: `:S:(do)` - The subject performs the action
2. **Agent Specification**: `<= @by(:S:)` - Defines who performs the action
3. **Consequence Analysis**: `<= @onlyIf` - Nested under the agent, showing automatic consequences
4. **Process Details**: The creation process with account and information components

### Key Integration Points

#### 1. Hierarchical Nesting
- The consequence analysis (`@onlyIf`) is nested under the agent specification (`@by`)
- This shows that the consequences are directly related to the agent's action
- Each level maintains the single `<=` rule

#### 2. Agent-Consequence Relationship
- `@by(:S:)` specifies the agent performing the action
- `@onlyIf` under `@by` shows what automatically happens when this agent performs the action
- The nesting indicates that consequences are agent-specific

#### 3. Shared Reference System
- Account references are unified: `{user account}?<:{1}>` (process) and `{account}<:{1}>` (consequence)
- Both reference the same position `{1}` in their respective contexts
- The consequence references the account created by the agent

### Semantic Flow

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
