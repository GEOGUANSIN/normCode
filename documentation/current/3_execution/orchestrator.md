# Orchestrator

**The central engine that manages execution flow, dependencies, and state.**

---

## Overview

The **Orchestrator** is the runtime heart of NormCode. While plans define *what* should happen and agents define *how* to do it, the Orchestrator defines *when* it happens.

**Key Responsibilities:**
- Manage execution flow and dependency resolution
- Track status of all concepts and inferences (Blackboard)
- Coordinate agent execution (AgentFrames)
- Handle loops, conditions, and branching
- Provide checkpointing and resumption
- Log execution history

---

## Core Architecture

### The Execution Model

The Orchestrator operates on a **dependency-driven, bottom-up** execution model:

```
An inference executes when:
1. All child inferences are complete
2. Functional concept is ready
3. Value concepts are ready
```

**Key Insight**: Unlike sequential or top-down execution, NormCode resolves dependencies dynamically. Ready inferences execute immediately; blocked inferences wait.

### Component Overview

```
┌─────────────────────────────────────────────────┐
│  ORCHESTRATOR                                    │
│                                                  │
│  ┌──────────┐   ┌───────────┐   ┌────────────┐ │
│  │ Waitlist │ → │ Blackboard│ ← │AgentFrames │ │
│  └──────────┘   └───────────┘   └────────────┘ │
│       ↓              ↓                ↓         │
│  ┌──────────────────────────────────────────┐  │
│  │         ProcessTracker                   │  │
│  └──────────────────────────────────────────┘  │
│       ↓              ↓                ↓         │
│  ┌──────────┐   ┌───────────┐   ┌────────────┐ │
│  │ConceptRepo│  │InferenceRepo│ │OrchestratorDB││
│  └──────────┘   └───────────┘   └────────────┘ │
└─────────────────────────────────────────────────┘
```

| Component | Purpose |
|-----------|---------|
| **Waitlist** | Static prioritized queue of all inferences (by flow_index) |
| **Blackboard** | Dynamic status tracker (pending/in_progress/completed/skipped) |
| **AgentFrames** | Factory for creating configured agents |
| **ConceptRepo** | Storage for all concept References |
| **InferenceRepo** | Storage for all inference definitions |
| **ProcessTracker** | Execution history and logs |
| **OrchestratorDB** | SQLite database for checkpoints |

---

## The Execution Loop

### Cycle Structure

The Orchestrator runs in **cycles**. Each cycle attempts to make progress on the plan.

```python
WHILE any inferences pending:
    # 1. CHECK PHASE
    ready_items = scan_waitlist_for_ready_inferences()
    
    # 2. EXECUTE PHASE
    for item in ready_items:
        agent_frame = create_agent_frame(item)
        result = agent_frame.execute_inference(item)
        
    # 3. UPDATE PHASE
    update_blackboard_and_repos(results)
    handle_skips_and_failures()
    check_loop_resets()
    
    # 4. CHECKPOINT
    save_checkpoint_if_configured()
    
    # 5. CHECK TERMINATION
    if all_complete:
        BREAK
```

### Cycle Example

**Plan**:
```ncd
:<:{result} | ?{flow_index}: 1
    <= ::(combine) | ?{flow_index}: 1.1
    <- {A} | ?{flow_index}: 1.2
        <= ::(process) | ?{flow_index}: 1.2.1
        <- {raw A} | ?{flow_index}: 1.2.1.1
    <- {B} | ?{flow_index}: 1.3
        <= ::(process) | ?{flow_index}: 1.3.1
        <- {raw B} | ?{flow_index}: 1.3.1.1
```

**Cycle 1**:
- **Ready**: 1.2.1, 1.3.1 (only need raw inputs)
- **Execute**: Both inferences run
- **Update**: Mark 1.2.1 and 1.3.1 as complete, store results

**Cycle 2**:
- **Ready**: 1.1 (now that {A} and {B} are ready)
- **Execute**: Inference 1.1 runs
- **Update**: Mark 1.1 complete

**Cycle 3**:
- **Ready**: None (all complete)
- **Terminate**: Return final result

---

## Readiness Criteria

### Standard Readiness

An inference is **ready to execute** when:

```python
def is_ready(inference):
    # 1. All supporting items (children) complete
    for child in inference.children:
        if child.status != 'completed':
            return False
    
    # 2. Functional concept ready
    if functional_concept.status != 'complete':
        return False
    
    # 3. Value concepts ready
    for value_concept in inference.value_concepts:
        if value_concept.status != 'complete':
            return False
    
    return True
```

### Special Cases

**Assigning with Fallbacks** (`$.`):

Only *one* source needs to be ready:

```python
def is_ready_assigning(inference):
    # At least one value concept ready
    any_ready = any(
        vc.status == 'complete' 
        for vc in inference.value_concepts
    )
    return any_ready
```

**Timing Operators** (`@:'`, `@.`):

Readiness depends on referenced concept:

```python
def is_ready_timing(inference):
    # Wait for condition concept
    if condition_concept.status != 'complete':
        return False
    
    # If @:': check condition value, might skip
    if is_if_operator:
        condition_met = check_condition_value()
        if not condition_met:
            mark_as_skipped()
    
    return True
```

---

## The Blackboard

### What It Tracks

The **Blackboard** is the single source of truth for execution state.

**Concept Status**:
```python
{
    '{input A}': 'completed',
    '{input B}': 'pending',
    '<validation>': 'in_progress',
    ...
}
```

**Inference Status**:
```python
{
    '1.2.1': 'completed',
    '1.2.2': 'pending',
    '1.3': 'skipped',
    ...
}
```

**Status Values**:
| Status | Meaning |
|--------|---------|
| `pending` | Not yet ready to run |
| `in_progress` | Currently executing |
| `completed` | Successfully finished |
| `skipped` | Branch not taken (from `@:'` check) |
| `failed` | Execution error |

### Key Operations

```python
# Check if concept ready
is_ready = blackboard.is_concept_ready('{input A}')

# Get inference status
status = blackboard.get_status(flow_index='1.2.1')

# Mark inference complete
blackboard.mark_complete(
    flow_index='1.2.1',
    concept_to_infer='{input A}'
)

# Mark branch skipped
blackboard.mark_skipped(flow_index='1.3')
```

---

## AgentFrame Management

### Creating AgentFrames

For each ready inference, the Orchestrator creates a configured AgentFrame:

```python
# Create frame with specific mode
agent_frame = AgentFrame(model="demo")

# Configure with appropriate sequence
agent_frame.configure_imperative_demo(inference)

# Execute
result = agent_frame.execute()
```

### AgentFrame Modes

| Mode | Purpose |
|------|---------|
| `composition` | Default: uses paradigm composition |
| `demo` | Legacy: direct tool invocation |
| Custom | User-defined agent capabilities |

---

## Loop Management

### The Loop Challenge

Loops require **resetting** child inferences for each iteration:

```ncd
<- {all summaries}
    <= *. %>({documents}) %<({summary})
    <- {summary}
        <= ::(summarize)
        <- {document}*1
```

**Problem**: After first document, `{summary}` and all its children are marked `complete`. How do we run them again for the second document?

### The Solution: Workspace + Reset

**Workspace**: Tracks iteration state

```python
workspace = {
    0: {'{summary}': summary_ref_0},  # First iteration
    1: {'{summary}': summary_ref_1},  # Second iteration
    ...
}
```

**Reset Logic**:

1. **After each iteration**:
   ```python
   # Check if more items to process
   if more_items_remain:
       # Reset all child inferences to 'pending'
       for child in loop_children:
           if not child.is_invariant:
               blackboard.set_status(child.flow_index, 'pending')
   ```

2. **Invariant concepts preserved**:
   ```ncd
   <- {accumulated total}*-1
   ```
   Concepts with `*-1` marker are **not** reset—they maintain state across iterations.

3. **Next iteration**:
   - Loop executes with next item from collection
   - Children re-run with new input
   - Result stored in workspace

4. **Completion**:
   ```python
   # When all items processed
   final_ref = quantifier.combine_all_looped_elements_by_concept(
       concept_name='{summary}',
       axis_name='document_index'
   )
   ```

### Loop Execution Flow

```
Iteration 1:
  1. Quantifier: Get first document
  2. Execute children with document
  3. Store result in workspace[0]
  4. Reset children to 'pending'

Iteration 2:
  1. Quantifier: Get second document
  2. Execute children with document
  3. Store result in workspace[1]
  4. Reset children to 'pending'

...

Completion:
  1. No more documents
  2. Aggregate all workspace results
  3. Store as final reference
```

---

## Skip Propagation

### When Skips Occur

**Timing operators** can mark inferences as skipped:

```ncd
<- {result}
    <= $. %<[{primary}, {fallback}]
    <- {primary}
        <= ::(compute primary)
            <= @:' %>(<validation passed>)
            <* <validation passed>
    <- {fallback}
        <= ::(compute fallback)
            <= @:! %>(<validation passed>)
            <* <validation passed>
```

If `<validation passed>` is `False`:
- `{primary}` inference is **skipped**
- `{fallback}` inference **executes**

### Propagation Rules

When an inference is skipped:

```python
def propagate_skip(inference):
    # Mark inference as completed (but with 'skipped' detail)
    blackboard.mark_skipped(inference.flow_index)
    
    # Mark all children as skipped
    for child in inference.all_descendants:
        blackboard.mark_skipped(child.flow_index)
    
    # Mark concept as completed (with skip value)
    concept_ref.set('@#SKIP#@')
```

**Key Insight**: Skipped inferences are marked `completed` so the plan can proceed without them. Their dependents receive skip values.

### Skip Usage

**Assigning operator** handles skips gracefully:

```ncd
<- {final answer}
    <= $.
    <- {option A}  # Might be skipped
    <- {option B}  # Fallback
```

If `{option A}` is skip, assigning selects `{option B}`.

---

## Checkpointing and Persistence

### The Checkpoint System

The Orchestrator includes robust **checkpointing** via SQLite database.

**What's Saved**:
| Data | Purpose |
|------|---------|
| **Run metadata** | run_id, timestamp, configuration |
| **Blackboard state** | All concept/inference statuses |
| **References** | All concept data |
| **Workspace** | Loop iteration state |
| **ProcessTracker logs** | Execution history |

**Database Structure** (`OrchestratorDB`):
```sql
runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT,
    metadata JSON
)

snapshots (
    snapshot_id INTEGER PRIMARY KEY,
    run_id TEXT,
    cycle_number INTEGER,
    blackboard_state JSON,
    references JSON,
    workspace JSON
)
```

### Checkpoint Frequency

**Default**: Save after every cycle.

**Configurable**:
```python
orchestrator = Orchestrator(
    concept_repo, 
    inference_repo,
    checkpoint_every_n_cycles=5  # Save every 5 cycles
)
```

### Resume Modes

When loading a checkpoint, handle code changes via **reconciliation modes**:

#### PATCH Mode (Default - Smart Merge)

```python
orchestrator = Orchestrator.load_checkpoint(
    concept_repo,
    inference_repo,
    mode="PATCH"
)
```

**Behavior**:
1. Load saved Blackboard state
2. For each concept/inference:
   - Check if definition changed (compare logic signatures)
   - If **changed**: Discard saved state, mark as `pending` (will re-run)
   - If **unchanged**: Keep saved state (cached result)
3. Resume execution from current state

**Use Case**: Development iteration—re-run only changed logic.

#### OVERWRITE Mode (Trust Checkpoint)

```python
orchestrator = Orchestrator.load_checkpoint(
    concept_repo,
    inference_repo,
    mode="OVERWRITE"
)
```

**Behavior**: Trust checkpoint entirely, ignore current repository definitions.

**Use Case**: Exact reproduction of past run.

#### FILL_GAPS Mode (Prefer Current)

```python
orchestrator = Orchestrator.load_checkpoint(
    concept_repo,
    inference_repo,
    mode="FILL_GAPS"
)
```

**Behavior**: Load checkpoint to fill missing data, prefer current repository defaults.

**Use Case**: Code migration, updating to new repository structure.

### Forking Runs

Create a new run starting from an old checkpoint:

```python
orchestrator = Orchestrator.load_checkpoint(
    concept_repo,
    inference_repo,
    run_id=old_run_id,
    fork=True  # New run_id created
)
```

**Use Cases**:
- Branching experiments
- A/B testing configurations
- Retrying with modified logic

---

## Error Handling

### Failure Types

| Type | Handling |
|------|----------|
| **LLM timeout** | Retry with backoff |
| **Tool error** | Log and mark failed |
| **Parse error** | Store error message, mark failed |
| **Dependency cycle** | Detect and report at startup |

### Retry Logic

```python
max_retries = 3
retry_count = 0

while retry_count < max_retries:
    try:
        result = agent_frame.execute()
        break
    except RetryableError as e:
        retry_count += 1
        wait_time = 2 ** retry_count
        time.sleep(wait_time)

if retry_count >= max_retries:
    mark_as_failed()
```

### Critical vs. Non-Critical

**Critical inferences**: Failure stops execution
```ncd
<- {essential input}
    <= ::(must succeed)
```

**Non-critical with fallback**: Failure allows continuation
```ncd
<- {result}
    <= $.
    <- {primary}
    <- {fallback}
```

---

## Execution Modes

### Synchronous Execution

```python
orchestrator = Orchestrator(concept_repo, inference_repo)
final_concepts = orchestrator.run()
```

**Use Case**: Scripts, batch processing.

### Asynchronous Execution

```python
orchestrator = Orchestrator(concept_repo, inference_repo)
final_concepts = await orchestrator.run_async()
```

**Use Case**: Web apps, UI contexts (Streamlit).

### Step-by-Step Execution

```python
orchestrator = Orchestrator(concept_repo, inference_repo)

while not orchestrator.is_complete():
    # Execute one cycle
    orchestrator.step()
    
    # Inspect state
    status = orchestrator.get_status()
    print(f"Cycle {status['cycle']}: {status['completed']}/{status['total']} complete")
```

**Use Case**: Debugging, interactive exploration.

---

## Tools for Running Plans

### 1. Command Line Interface

**Basic Execution**:
```bash
python cli_orchestrator.py run \
    --concepts concepts.json \
    --inferences inferences.json \
    --inputs inputs.json
```

**Resume from Checkpoint**:
```bash
# Resume latest run (PATCH mode)
python cli_orchestrator.py resume \
    --concepts concepts.json \
    --inferences inferences.json

# Resume specific run
python cli_orchestrator.py resume \
    --concepts concepts.json \
    --inferences inferences.json \
    --run-id abc123...
```

**List Past Runs**:
```bash
python cli_orchestrator.py list-runs
```

**Fork from Checkpoint**:
```bash
python cli_orchestrator.py fork \
    --from-run abc123... \
    --concepts new_concepts.json \
    --inferences new_inferences.json
```

### 2. Streamlit Application

**Launch**:
```bash
streamlit run streamlit_app/app.py
```

**Features**:
- **Visual plan tree**: See inference hierarchy
- **Real-time status**: Watch execution progress
- **Concept inspection**: Click any concept to view its Reference
- **Controls**: Start, pause, resume, reset
- **Configuration loading**: Load settings from past runs
- **File management**: Upload repositories, automatic saving

**Complete Setup Loading** (v1.3.1+):
1. Select previous run from dropdown
2. Check "📁 Also load repository files"
3. Click "Load Config"
4. Execute

**Benefits**:
- ⚡ 10x faster re-runs (no manual file uploads)
- 🎯 100% accurate (exact same files)
- 📁 Zero file management (automatic saving)

---

## Performance Considerations

### What's Expensive?

| Operation | Cost | Why |
|-----------|------|-----|
| **Semantic inferences** | High (tokens) | LLM API calls |
| **Checkpointing** | Medium (I/O) | Writing to SQLite |
| **Large References** | Medium (memory) | Storing tensors |
| **Perception** | Low-Medium (I/O) | Reading files |

### What's Cheap?

| Operation | Cost | Why |
|-----------|------|-----|
| **Dependency checks** | ~0 | Blackboard queries |
| **Syntactic inferences** | ~0 | Pure Python operations |
| **Reference operations** | ~0 | In-memory transformations |
| **Skip propagation** | ~0 | Status updates |

### Optimization Strategies

**1. Reduce Semantic Calls**:
- Use syntactic operators for data plumbing
- Batch similar operations in loops
- Cache results with assigning operators

**2. Checkpoint Less Frequently**:
```python
orchestrator = Orchestrator(
    ...,
    checkpoint_every_n_cycles=10  # Instead of every cycle
)
```

**3. Minimize Large References**:
- Use perceptual signs instead of storing full data
- Slice references early to reduce dimensions
- Clean up intermediate References

**4. Async Execution**:
```python
# Allow other work while waiting for LLM
await orchestrator.run_async()
```

---

## Advanced Features

### Environment Compatibility

When loading checkpoints, validate configuration:

```python
# Saved run used: qwen-plus, AgentFrame mode="demo"
# Current setup uses: gpt-4o, AgentFrame mode="composition"

# PATCH mode warns:
# "Warning: LLM model mismatch (saved: qwen-plus, current: gpt-4o)"
# "Warning: AgentFrame mode mismatch (saved: demo, current: composition)"
```

**Reconciliation**: Re-runs inferences affected by changes.

### Multi-Agent Planning

Different subjects can use different tools:

```ncd
<- {reviewed code}
    <= :reviewer_agent:{review code}
    <- {generated code}
        <= :coder_agent:{generate code}
        <- {requirements}
```

Each `:subject:` has its own body (tools) and AgentFrame configuration.

### Dependency Visualization

```python
# Generate dependency graph
from orchestrator_utils import visualize_dependencies

viz = visualize_dependencies(inference_repo)
viz.save("plan_graph.png")
```

---

## Debugging the Orchestrator

### Common Issues

**Inference never becomes ready**:
```python
# Check dependencies
inference = inference_repo.get(flow_index='1.2.1')
for child in inference.children:
    status = blackboard.get_status(child.flow_index)
    print(f"Child {child.flow_index}: {status}")

# Check inputs
for value_concept in inference.value_concepts:
    is_ready = blackboard.is_concept_ready(value_concept.name)
    print(f"Input {value_concept.name}: {is_ready}")
```

**Loop doesn't terminate**:
```python
# Check Quantifier workspace
workspace = orchestrator.get_workspace()
print(f"Processed items: {list(workspace.keys())}")

# Check loop base reference
loop_ref = concept_repo.get_reference('{documents}')
print(f"Total items: {loop_ref.shape}")
```

**Unexpected skip**:
```python
# Check Timing operators
condition_ref = concept_repo.get_reference('<condition>')
print(f"Condition value: {condition_ref.tensor}")

# Check Blackboard for skipped inferences
skipped = [
    fi for fi, status in blackboard.all_statuses.items()
    if status == 'skipped'
]
print(f"Skipped inferences: {skipped}")
```

**Checkpoint won't load**:
```python
# Check compatibility
try:
    orchestrator = Orchestrator.load_checkpoint(
        concept_repo,
        inference_repo,
        mode="PATCH",
        strict_validation=True
    )
except ValidationError as e:
    print(f"Incompatibility: {e}")
```

### Logging and Tracing

**Enable detailed logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

orchestrator = Orchestrator(
    concept_repo,
    inference_repo,
    verbose=True
)
```

**ProcessTracker inspection**:
```python
# Get execution history
history = orchestrator.process_tracker.get_history()

for cycle in history:
    print(f"Cycle {cycle['number']}: {len(cycle['executed'])} inferences")
    for inference in cycle['executed']:
        print(f"  - {inference['flow_index']}: {inference['status']}")
```

---

## Summary

### Key Takeaways

| Concept | Insight |
|---------|---------|
| **Bottom-up execution** | Dependencies resolve dynamically |
| **Blackboard is truth** | Single source for all status |
| **Cycles make progress** | Each cycle executes ready inferences |
| **Loops require reset** | Child inferences re-run per iteration |
| **Skips propagate** | Failed branches don't block plan |
| **Checkpoints enable resumption** | Full state saved to database |
| **PATCH mode is smart** | Re-runs only changed logic |

### The Orchestrator Promise

**NormCode's orchestrator enforces data isolation**:

1. No inference runs until dependencies met
2. Blackboard tracks all status explicitly
3. References passed through ConceptRepo
4. Loops maintain separate workspace state
5. Checkpoints enable reproducibility

**Result**: Transparent, auditable, resumable execution.

---

## Next Steps

- **[Overview](overview.md)** - High-level execution model
- **[Reference System](reference_system.md)** - How data is stored
- **[Agent Sequences](agent_sequences.md)** - What happens in each inference
- **[Tools Section](../5_tools/README.md)** - Using CLI and Streamlit app

---

## Quick Reference

### Key Classes

```python
from infra._orchestrator import Orchestrator, Blackboard
from infra._core import ConceptRepo, InferenceRepo
from infra._agent import AgentFrame

# Create orchestrator
orchestrator = Orchestrator(concept_repo, inference_repo)

# Execute
final_concepts = orchestrator.run()

# Resume with PATCH
orchestrator = Orchestrator.load_checkpoint(
    concept_repo,
    inference_repo,
    mode="PATCH"
)
```

### CLI Commands

```bash
# Run
python cli_orchestrator.py run --concepts C.json --inferences I.json

# Resume
python cli_orchestrator.py resume --concepts C.json --inferences I.json

# Fork
python cli_orchestrator.py fork --from-run <ID> --concepts C.json --inferences I.json

# List
python cli_orchestrator.py list-runs
```

---

**Ready for the full picture?** Return to [Execution Overview](overview.md) or explore [Tools](../5_tools/README.md) to start running your plans.
