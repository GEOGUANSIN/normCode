# Execution Section

**Understanding how NormCode plans run at runtime.**

---

## 🎯 Purpose

This section explains the runtime execution of NormCode plans. You'll learn how the orchestrator manages dependencies, how data flows through References, and how each agent sequence executes.

**Key Questions Answered:**
- How does the orchestrator decide execution order?
- How is data stored and passed between steps?
- What happens inside each agent sequence?
- How do loops, conditions, and branching work?
- How can I resume from checkpoints?

---

## 📚 Documents in This Section

### 1. [Overview](overview.md)
**High-level execution model**

Learn about:
- The bottom-up dependency resolution model
- Semantic vs. syntactic sequences
- Reference system basics
- Orchestrator role and execution loop
- Control flow patterns
- Execution guarantees

**Start here if**: You want to understand the big picture of how plans run.

**Time**: 20 minutes

---

### 2. [Reference System](reference_system.md)
**How data is stored in multi-dimensional tensors**

Learn about:
- What References are (multi-dimensional tensors)
- Perceptual signs (data pointers)
- Creating and manipulating References
- Basic operations (get, set, copy)
- Reshaping operations (slice, append)
- Combining References (cross product, join, cross action)
- Skip values and error handling

**Start here if**: You want to understand how data is structured and flows.

**Time**: 30 minutes

---

### 3. [Agent Sequences](agent_sequences.md)
**The pre-defined pipelines that execute each inference**

Learn about:
- Agent (:S:) and AgentFrame
- Semantic sequences (Imperative, Judgement)
- The Perception-Actuation-Assertion cycle
- Paradigms and the norm system
- Syntactic sequences (Assigning, Grouping, Timing, Looping)
- Sequence interaction patterns
- Debugging sequences

**Start here if**: You want to understand what happens inside each step.

**Time**: 35 minutes

---

### 4. [Orchestrator](orchestrator.md)
**The central engine managing execution flow**

Learn about:
- Core architecture and components
- The execution loop (cycles)
- Readiness criteria
- Blackboard status tracking
- Loop management and workspace
- Skip propagation
- Checkpointing and persistence
- Resume modes (PATCH, OVERWRITE, FILL_GAPS)
- CLI and Streamlit tools

**Start here if**: You want to understand how the engine coordinates everything.

**Time**: 30 minutes

---

## 🗺️ Reading Paths

### For New Users
1. [Overview](overview.md) - Understand the execution model
2. [Orchestrator](orchestrator.md) - See how the engine works
3. [Agent Sequences](agent_sequences.md) - Learn what happens in each step

### For Debugging
1. [Reference System](reference_system.md) - Understand data structures
2. [Agent Sequences](agent_sequences.md) - Trace sequence execution
3. [Orchestrator](orchestrator.md) - Check dependencies and status

### For Optimization
1. [Overview](overview.md) - Identify semantic vs. syntactic operations
2. [Agent Sequences](agent_sequences.md) - Understand sequence costs
3. [Orchestrator](orchestrator.md) - Optimize checkpointing and loops

### For System Developers
1. [Overview](overview.md) - Architecture overview
2. [Reference System](reference_system.md) - Core data structures
3. [Agent Sequences](agent_sequences.md) - Sequence implementation
4. [Orchestrator](orchestrator.md) - Engine implementation

---

## 🔑 Key Concepts

### Execution Model

```
Bottom-Up Dependency Resolution
    ↓
Child inferences complete first
    ↓
Parent inferences wait for all inputs
    ↓
Ready inferences execute immediately
```

### The Three Systems

| System | Purpose | Key Component |
|--------|---------|---------------|
| **Reference System** | Data storage | Multi-dimensional tensors with named axes |
| **Agent Sequences** | Step execution | Pre-defined pipelines (semantic + syntactic) |
| **Orchestrator** | Flow control | Dependency manager + status tracker |

### Semantic vs. Syntactic

```
┌────────────────────────────────────────────────┐
│  SEMANTIC SEQUENCES                             │
│  → CREATE information via LLM/tools             │
│  → Expensive (tokens), non-deterministic        │
│  → Imperative, Judgement                       │
├────────────────────────────────────────────────┤
│  SYNTACTIC SEQUENCES                            │
│  → RESHAPE information via tensor algebra       │
│  → Free, deterministic, auditable              │
│  → Assigning, Grouping, Timing, Looping        │
└────────────────────────────────────────────────┘
```

---

## 💡 The Big Picture

### Data Flow

```
1. Concept declared in plan
      ↓
2. Reference initialized in ConceptRepo
      ↓
3. Child inferences execute
      ↓
4. Child results stored as References
      ↓
5. Parent inference retrieves input References (IR)
      ↓
6. Syntactic operations reshape References
      ↓
7. Semantic operations perceive signs → actual data (MVP)
      ↓
8. Tool/paradigm applies function to data (TVA)
      ↓
9. Result stored as new Reference (OR)
      ↓
10. Blackboard updated, cycle continues
```

### Execution Loop

```
CYCLE 1:
  Check readiness → Execute ready items → Update Blackboard
  
CYCLE 2:
  Check readiness → Execute ready items → Update Blackboard
  
...

CYCLE N:
  All complete → Return final results
```

### References Are Tensors

```
Reference for {student grades}
    axes=['student', 'assignment']
    shape=(3, 4)
    tensor=[
        [85, 90, 88, 92],
        [78, 88, 85, 90],
        [92, 95, 93, 98]
    ]
```

**Named axes** enable meaningful operations:
- `grades.get(student=0)` → all assignments for student 0
- `grades.slice('student')` → aggregate across assignments

---

## 📖 Common Questions

**Q: How does the orchestrator know which step to run next?**  
A: It scans the Waitlist for inferences whose dependencies (children + inputs) are all complete.

**Q: What's the difference between semantic and syntactic sequences?**  
A: Semantic sequences call LLMs (expensive, non-deterministic). Syntactic sequences manipulate tensors (free, deterministic).

**Q: How are References different from regular variables?**  
A: References are multi-dimensional tensors with named axes. They support rich operations like cross products and slicing.

**Q: What happens when a loop runs?**  
A: The Quantifier manages a workspace, resets child inferences after each iteration, and aggregates results at completion.

**Q: How do I resume from a checkpoint?**  
A: Use `Orchestrator.load_checkpoint(..., mode="PATCH")` which re-runs only changed logic.

**Q: What are perceptual signs?**  
A: Formatted strings like `%{file_location}7f2(data/input.txt)` that tell agents how to retrieve actual data. They enable lazy loading.

**Q: How do `@:'` conditions work?**  
A: The Timing sequence checks the condition's boolean value. If not met, the inference and all its children are marked "skipped".

**Q: Can I inspect what each step saw?**  
A: Yes! Check the Reference for any concept in the ConceptRepo. Everything is explicit and traceable.

---

## 🎓 Understanding Levels

### Level 1: Basic Execution
**Goal**: Run plans and understand what's happening

**Learn**:
- [Overview](overview.md) - Execution model
- [Orchestrator](orchestrator.md) - How to run plans

**You can**: Execute plans, use CLI/Streamlit, inspect results.

---

### Level 2: Debugging Mastery
**Goal**: Diagnose issues and trace execution

**Learn**:
- [Reference System](reference_system.md) - Data structures
- [Agent Sequences](agent_sequences.md) - Sequence details
- [Orchestrator](orchestrator.md) - Blackboard and logs

**You can**: Debug failures, trace data flow, optimize performance.

---

### Level 3: Deep Understanding
**Goal**: Extend the system and build custom components

**Learn**:
- All documents in detail
- [Compilation Section](../4_compilation/README.md) - How plans are compiled
- Source code exploration

**You can**: Build custom sequences, create paradigms, extend orchestrator.

---

## 🚀 Quick Start Examples

### Example 1: Basic Execution

**Python API**:
```python
from infra._orchestrator import Orchestrator
from infra._core import ConceptRepo, InferenceRepo

# Load repositories
concept_repo = ConceptRepo.from_file('concepts.json')
inference_repo = InferenceRepo.from_file('inferences.json')

# Create orchestrator
orchestrator = Orchestrator(concept_repo, inference_repo)

# Execute
final_concepts = orchestrator.run()

# Get result
result_ref = concept_repo.get_reference('{final result}')
print(result_ref.tensor)
```

**CLI**:
```bash
python cli_orchestrator.py run \
    --concepts concepts.json \
    --inferences inferences.json \
    --inputs inputs.json
```

---

### Example 2: Resume from Checkpoint

**Python API**:
```python
# Resume in PATCH mode (re-run changed logic)
orchestrator = Orchestrator.load_checkpoint(
    concept_repo,
    inference_repo,
    mode="PATCH"
)

# Continue execution
orchestrator.run()
```

**CLI**:
```bash
# Resume latest run
python cli_orchestrator.py resume \
    --concepts concepts.json \
    --inferences inferences.json

# Resume specific run
python cli_orchestrator.py resume \
    --concepts concepts.json \
    --inferences inferences.json \
    --run-id abc123...
```

---

### Example 3: Inspect References

```python
# Get concept's Reference
ref = concept_repo.get_reference('{intermediate result}')

# Inspect structure
print(f"Axes: {ref.axes}")
print(f"Shape: {ref.shape}")
print(f"Tensor: {ref.tensor}")

# Get clean data (skip values removed)
clean_data = ref.get_tensor(ignore_skip=True)
```

---

### Example 4: Check Status

```python
# Check inference status
status = orchestrator.blackboard.get_status(flow_index='1.2.1')
print(f"Inference 1.2.1: {status}")

# Check concept readiness
is_ready = orchestrator.blackboard.is_concept_ready('{input A}')
print(f"Input A ready: {is_ready}")

# Get execution history
history = orchestrator.process_tracker.get_history()
for cycle in history:
    print(f"Cycle {cycle['number']}: {len(cycle['executed'])} executed")
```

---

## 🔗 External Resources

### Previous Sections
- **[Introduction](../1_intro/README.md)** - What is NormCode?
- **[Grammar](../2_grammar/README.md)** - The `.ncd` syntax

### Next Sections
- **[Compilation](../4_compilation/README.md)** *(Coming Soon)* - The 5-phase compilation pipeline
- **[Tools](../5_tools/README.md)** *(Coming Soon)* - CLI, editor, Streamlit app

### Source Code
- `infra/_orchestrator/` - Orchestrator implementation
- `infra/_core/` - Reference and repository classes
- `infra/_agent/` - AgentFrame and sequence implementations

---

## 📊 Document Status

| Document | Status | Content Coverage |
|----------|--------|------------------|
| **Overview** | ✅ Complete | Execution model, systems, control flow |
| **Reference System** | ✅ Complete | Tensors, operations, perceptual signs |
| **Agent Sequences** | ✅ Complete | All sequences, paradigms, patterns |
| **Orchestrator** | ✅ Complete | Architecture, loops, checkpointing, tools |

---

## 🎯 Next Sections

After mastering execution:

- **[4. Compilation](../4_compilation/README.md)** *(Coming Soon)* - How `.ncd` becomes executable
- **[5. Tools](../5_tools/README.md)** *(Coming Soon)* - User-facing tools and APIs

---

## 💡 Key Takeaways

### The Execution Promise

**NormCode's execution enforces data isolation by design**:

1. **Bottom-up resolution**: Can't run until inputs ready
2. **Reference isolation**: Each concept has its own tensor
3. **Explicit retrieval**: IR step fetches only declared inputs
4. **No hidden state**: Everything tracked in Blackboard
5. **Full auditability**: Inspect exactly what each step saw

### Performance Characteristics

| Type | Cost | Deterministic | Cacheable |
|------|------|---------------|-----------|
| **Semantic** | Tokens | ❌ No | ✅ Yes (via checkpoints) |
| **Syntactic** | ~0 | ✅ Yes | N/A (instant) |

### Debugging Strategy

```
1. Check Blackboard → What's the status?
2. Check References → What data was present?
3. Check ProcessTracker → What happened during execution?
4. Check dependencies → Why isn't an inference ready?
5. Check workspace → What's the loop state?
```

---

**Ready to dive in?** Start with [Overview](overview.md) to understand the execution model, then explore each system in detail.
