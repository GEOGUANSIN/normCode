# Execution Overview

**How NormCode plans run at runtime—from compilation to completion.**

---

## Purpose

This section explains how NormCode plans execute. While the Grammar section covered *what you write*, this section covers *what happens* when your plan runs.

**Key Questions Answered:**
- How does the orchestrator decide which step runs next?
- How is data stored and passed between inferences?
- What happens during each agent sequence?
- How are loops, conditions, and branching handled?
- How does checkpointing and resuming work?

---

## The Big Picture

### From Plan to Execution

```
Your .ncd File
      ↓
Compilation → .concept.json + .inference.json (repositories)
      ↓
Orchestrator loads repositories
      ↓
Execution Loop (cycles)
      ↓
Final Result + Checkpoints
```

### Three Key Systems

The execution layer consists of three interconnected systems:

| System | Purpose | Details |
|--------|---------|---------|
| **Reference System** | Data storage | Multi-dimensional tensors holding all concept values |
| **Agent Sequences** | Step execution | Pre-defined pipelines that implement each operation |
| **Orchestrator** | Flow control | Manages dependencies, execution order, and state |

---

## Core Execution Model

### Bottom-Up Dependency Resolution

NormCode executes **bottom-up**: child inferences complete before their parents can run.

```ncd
:<:{result} | ?{flow_index}: 1
    <= ::(calculate) | ?{flow_index}: 1.1
    <- {input A} | ?{flow_index}: 1.2
        <= ::(process A) | ?{flow_index}: 1.2.1
        <- {raw A} | ?{flow_index}: 1.2.1.1
    <- {input B} | ?{flow_index}: 1.3
        <= ::(process B) | ?{flow_index}: 1.3.1
        <- {raw B} | ?{flow_index}: 1.3.1.1
```

**Execution order**:
1. Inferences 1.2.1 and 1.3.1 are ready immediately (only need raw inputs)
2. Once 1.2.1 completes → `{input A}` is ready
3. Once 1.3.1 completes → `{input B}` is ready
4. Once both inputs are ready → Inference 1.1 can execute
5. Once 1.1 completes → `{result}` is produced

### Readiness Criteria

An inference becomes **ready to execute** when:

1. **All child inferences are complete** (dependencies met)
2. **Functional concept is ready** (the operation definition exists)
3. **Value concepts are ready** (all inputs have data)

**Exception**: For `assigning` sequences (`$.`), only *one* valid source needs to be ready (for fallback selection).

---

## The Two Types of Execution

### Semantic Sequences (LLM Calls)

**Purpose**: Create information through reasoning, generation, or evaluation.

| Sequence | Marker | LLM? | Cost | Examples |
|----------|--------|------|------|----------|
| **Imperative** | `({})` or `::()` | ✅ Yes | Tokens | Extract, generate, transform |
| **Judgement** | `<{}>` | ✅ Yes | Tokens | Evaluate, validate, decide |

**Pipeline**: Perception → Actuation → Assertion (for judgement)
- **Perception**: Understand the norm (function) and the values
- **Actuation**: Apply the tool/LLM to the values
- **Assertion**: For judgement, check truth conditions

### Syntactic Sequences (Data Manipulation)

**Purpose**: Reshape information through deterministic tensor operations.

| Sequence | Operators | LLM? | Cost | Examples |
|----------|-----------|------|------|----------|
| **Assigning** | `$.`, `$+`, `$-` | ❌ No | Free | Select, accumulate, pick |
| **Grouping** | `&[{}]`, `&[#]` | ❌ No | Free | Collect, combine, bundle |
| **Timing** | `@:'`, `@:!`, `@.` | ❌ No | Free | Branch, wait, depend |
| **Looping** | `*.` | ❌ No* | Free* | Iterate, repeat |

*\* The loop structure is free; semantic operations inside the loop cost tokens.*

**Key Insight**: Syntactic operations handle data plumbing—no LLM involved, instant execution, fully deterministic.

---

## Data Flow Through References

### What Are References?

A **Reference** is the container that holds a concept's data. Think of it as a named, multi-dimensional array (tensor).

```python
# A 2D reference: 3 students × 4 assignments
grades = Reference(
    axes=['student', 'assignment'],
    shape=(3, 4)
)
```

### Key Properties

| Property | Description |
|----------|-------------|
| **Multi-dimensional** | Data organized across named axes |
| **Named axes** | Dimensions have meaningful names (not just indices) |
| **Perceptual signs** | Elements are often pointers (file paths, prompts) not raw data |
| **Skip values** | Missing data represented explicitly (`@#SKIP#@`) |

### Why This Matters

References enable **explicit data isolation**:
- Each inference receives specific References as inputs
- Operations transform References through well-defined algebra
- Output References are stored and tracked
- You can inspect exactly what each step saw

**Example flow**:
```
1. Inference retrieves input References from Concept Repository
2. Syntactic operations reshape References (grouping, slicing)
3. Semantic operations perceive signs → actual data
4. Tool executes on perceived data
5. Result stored as new Reference in repository
```

---

## The Orchestrator's Role

### Execution Loop (Cycles)

The Orchestrator runs in **cycles**. Each cycle:

```
1. CHECK: Scan waitlist for ready inferences
2. EXECUTE: Run ready inferences (via AgentFrames)
3. UPDATE: Mark completed, store results, propagate skips
4. REPEAT: Until all inferences complete
```

### State Management

| Component | Purpose |
|-----------|---------|
| **Waitlist** | Static list of all inferences (by flow_index) |
| **Blackboard** | Dynamic status tracker (pending/in_progress/completed/skipped) |
| **ConceptRepo** | Stores References for all concepts |
| **InferenceRepo** | Stores inference definitions and sequences |
| **ProcessTracker** | Logs execution history |

### Advanced Features

**Loop Management**:
- Maintains workspace for iteration state
- Resets child inferences for next iteration
- Aggregates results across iterations

**Checkpointing**:
- Saves full state to SQLite database
- Resume from any cycle
- Fork from checkpoints for experiments

**Smart Patching**:
- Loads checkpoints but validates against current code
- Re-runs inferences with changed logic
- Keeps valid cached results

---

## Agent Sequences in Detail

### The Subject Concept (Agent)

In NormCode, an **Agent** (`:S:`) is the "body" that performs work. It holds:
- **Tools**: Python executor, LLM clients, file system, etc.
- **Sequences**: The logic pipelines (imperative, grouping, etc.)
- **AgentFrame**: Configuration for interpreting norms

**Key principle**: Different agents can have different capabilities, even if they use the same NormCode structure.

### Semantic Sequence Pipeline

**Imperative** and **Judgement** sequences follow a cognitive cycle:

| Phase | Steps | Purpose |
|-------|-------|---------|
| **Initialization** | IWI, IR | Parse syntax, retrieve references |
| **Perception** | MFP, MVP | Understand function and values |
| **Actuation** | TVA | Apply tool to values |
| **Assertion** | TIA (judgement only) | Check truth conditions |
| **Conclusion** | OR, OWI | Store result, update state |

**MFP (Model Function Perception)**: The agent "compiles" the functional concept into an executable function using paradigms.

**MVP (Memory Value Perception)**: The agent retrieves and transmutes perceptual signs into actual data.

**TVA (Tool Value Actuation)**: The agent applies the function to the values using `cross_action`.

### Syntactic Sequence Operations

| Sequence | Key Method | What It Does |
|----------|------------|--------------|
| **Assigning** | `Assigner.specification` | Select first valid from candidates |
| | `Assigner.continuation` | Append along axis (accumulation) |
| | `Assigner.derelation` | Structural selection by index |
| **Grouping** | `Grouper.and_in` | Combine into labeled dictionary |
| | `Grouper.or_across` | Flatten into list |
| **Timing** | `Timer.check_progress_condition` | Wait for dependency |
| | `Timer.check_if_condition` | Branch on condition |
| **Looping** | `Quantifier.retireve_next_base_element` | Get next item |
| | `Quantifier.store_new_in_loop_element` | Save iteration result |
| | `Quantifier.combine_all_looped_elements_by_concept` | Aggregate results |

---

## Paradigms: The Norm System

**Paradigms** are declarative JSON specifications that define *how* semantic sequences execute.

### Vertical vs. Horizontal

```
VERTICAL STEPS (MFP Phase)
    ↓
Setup: Resolve tools, bind functions, prepare executable
    ↓
HORIZONTAL STEPS (TVA Phase)
    ↓
Runtime: Pass values through execution plan, apply functions
    ↓
Result Reference
```

**Naming Convention**: `[inputs]-[composition]-[outputs].json`

Example: `h_PromptTemplate_SavePath-c_GenerateThinkJson-Extract-Save-o_FileLocation.json`
- `h_PromptTemplate_SavePath`: Horizontal inputs (runtime values)
- `c_GenerateThinkJson-Extract-Save`: Composition steps
- `o_FileLocation`: Output format

### Key Engines

1. **ModelSequenceRunner** (Vertical): Compiles paradigm specs into callable functions
2. **CompositionTool** (Horizontal): Executes the runtime data flow

**Mathematical View**:
$$
\text{Output} = [\text{CompositionTool}(\text{ModelSequenceRunner}(\text{State}, \text{Paradigm}), \text{Plan})](\text{Values})
$$

---

## Control Flow Patterns

### Sequential Execution

```ncd
<- {step 3}
    <= ::(execute step 3)
        <= @. %>({step 2})
    <- {step 2}
        <= ::(execute step 2)
            <= @. %>({step 1})
        <- {step 1}
```

Each step waits for the previous step to complete. The `@.` timing operator controls when the functional concept (imperative) executes.

### Conditional Branching

```ncd
<- {result}
    <= $. %<[{valid result}, {fallback result}]  | ?{sequence}: assigning
    <- {valid result}
        <= ::(compute result)
            <= @:' %>(<validation passed>)
            <* <validation passed>
        <- {input}
    <- {fallback result}
        <= ::(use default)
            <= @:! %>(<validation passed>)
            <* <validation passed>
```

If validation passes, use computed result; otherwise use fallback. The timing operators control whether the functional concepts (imperatives) execute.

### Iteration (Loops)

```ncd
<- {all summaries}
    <= *. %>({documents}) %<({summary}) | ?{sequence}: looping
    <- {summary}
        <= ::(summarize this document)
        <- {document}*1
    <* {document}<$({documents})*>
```

For each document, produce a summary. Aggregate all summaries.

---

## Execution Traces and Debugging

### What You Can Inspect

| Level | What to Check | How |
|-------|---------------|-----|
| **Concept** | Current Reference value | Blackboard + ConceptRepo |
| **Inference** | Status, inputs seen, output produced | ProcessTracker logs |
| **Sequence** | Which steps executed, intermediate states | Detailed logs |
| **Cycle** | Which inferences ran, what changed | Cycle summaries |

### Common Debugging Patterns

**Inference not running?**
→ Check dependencies: Are all child inferences completed?
→ Check inputs: Are all value concepts ready?

**Wrong result?**
→ Inspect input References: What did the inference actually see?
→ Check paradigm configuration: Is the right tool being used?

**Loop not terminating?**
→ Check Quantifier workspace: Are items being marked as processed?
→ Check loop base reference: Is it empty or has skip values?

**Skip propagation?**
→ Check Timing operators: Did an `@:'` condition fail?
→ Check Blackboard: Which inferences are marked "skipped"?

---

## Checkpointing and Resuming

### Checkpoint Database

The Orchestrator saves state to SQLite (`OrchestratorDB`):
- **Run metadata**: run_id, timestamp, configuration
- **Snapshots**: Full state at each cycle
- **Blackboard state**: Status of all concepts/inferences
- **References**: All concept data
- **Workspace**: Loop iteration state

### Resume Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| **PATCH** (default) | Smart merge: re-run changed logic | Development iteration |
| **OVERWRITE** | Trust checkpoint entirely | Exact reproduction |
| **FILL_GAPS** | Prefer current repo defaults | Code migration |

### Forking

Create a new run starting from an old checkpoint:
```bash
python cli_orchestrator.py fork --from-run <OLD_UUID> --concepts new_concepts.json
```

Useful for:
- Branching experiments
- Retrying with modified logic
- A/B testing configurations

---

## Performance Considerations

### What's Expensive?

| Operation | Cost | Why |
|-----------|------|-----|
| **Semantic sequences** | Tokens | LLM API calls |
| **Large References** | Memory | Storing many axes/elements |
| **Perception** | I/O | Reading files from perceptual signs |
| **Checkpointing** | Disk I/O | Writing full state to database |

### What's Cheap?

| Operation | Cost | Why |
|-----------|------|-----|
| **Syntactic sequences** | ~0 | Pure Python tensor operations |
| **Reference operations** | ~0 | In-memory transformations |
| **Dependency checking** | ~0 | Blackboard queries |
| **Skip propagation** | ~0 | Status updates |

### Optimization Strategies

1. **Minimize semantic calls**: Use syntactic operations for data plumbing
2. **Use assigning wisely**: Cache results with `$+` accumulation
3. **Checkpoint less frequently**: Trade resumability for speed
4. **Lazy perception**: Perceptual signs delay data loading until needed

---

## The Execution Guarantee

**NormCode's core promise**: Every inference sees exactly—and only—what you explicitly declare.

How this is enforced:

| Mechanism | Enforcement |
|-----------|-------------|
| **Bottom-up execution** | Can't run until inputs ready |
| **Reference isolation** | Each concept has its own Reference |
| **Explicit retrieval** | IR step fetches only declared inputs |
| **No global state** | No hidden context bleeding |
| **Blackboard transparency** | All status is queryable |

**Result**: Full auditability. You can trace exactly what each step saw and produced.

---

## Next Steps

Now that you understand the high-level execution model, dive deeper:

- **[Reference System](reference_system.md)** - How data is stored in multi-dimensional tensors
- **[Agent Sequences](agent_sequences.md)** - Detailed pipeline for each sequence type
- **[Orchestrator](orchestrator.md)** - How the orchestrator manages execution flow

---

## Quick Reference

### Execution Flow

```
1. Orchestrator loads .concept.json + .inference.json
2. Build Waitlist (all inferences by flow_index)
3. Initialize Blackboard (all statuses to "pending")
4. FOR EACH CYCLE:
   a. Check readiness (dependencies met?)
   b. Execute ready inferences (via AgentFrame)
   c. Update Blackboard and ConceptRepo
   d. Save checkpoint
   e. Stop if all complete
5. Return final concept References
```

### Key Classes

| Class | Purpose |
|-------|---------|
| `Orchestrator` | Main execution engine |
| `AgentFrame` | Factory for agent capabilities |
| `Reference` | Multi-dimensional data container |
| `Blackboard` | Status tracker |
| `Assigner`, `Grouper`, `Quantifier`, `Timer` | Syntactic operations |
| `ModelSequenceRunner`, `CompositionTool` | Paradigm execution |

---

**Ready to dive deeper?** Start with [Reference System](reference_system.md) to understand how data flows through the execution.
