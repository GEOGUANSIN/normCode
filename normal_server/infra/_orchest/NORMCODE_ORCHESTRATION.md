# How NormCode Functions in Orchestration

This document explains how the NormCode language is executed by the orchestration system, connecting the theoretical concepts from the NormCode Guide with the actual implementation in `infra._orchest`.

## Overview: From NormCode Syntax to Execution

The orchestration system transforms a **static NormCode plan** (defined as JSON repositories) into a **dynamic execution** that runs inferences in the correct dependency order. The flow is:

```
NormCode Plan (JSON) 
  → Repositories (ConceptRepo, InferenceRepo)
  → Waitlist (ordered execution queue)
  → Orchestrator (dependency-driven execution loop)
  → AgentFrame (executes individual inferences)
  → Blackboard (tracks state)
```

## 1. NormCode Plan Structure → Repositories

### Concepts → ConceptRepo

A **Concept** in NormCode (like `{number pair}`, `[all {unit place value} of numbers]`, `::(sum ...)`) is stored as a `ConceptEntry` in the `ConceptRepo`:

```python
# From _repo.py
@dataclass
class ConceptEntry:
    concept_name: str          # e.g., "{number pair}"
    type: str                 # e.g., "object", "relation", "imperative"
    is_ground_concept: bool   # True if provided as input
    is_final_concept: bool    # True if this is the final output
    reference_data: Any       # Initial data (if ground concept)
    concept: Concept          # The actual Concept object with Reference
```

**Key Mapping:**
- **Semantical Concepts** (`{}`, `[]`, `<>`, `::()`) → `ConceptEntry.type`
- **Ground Concepts** (inputs) → `is_ground_concept=True`, initialized with `reference_data`
- **References** (multi-dimensional data) → Stored in `concept.reference`

### Inferences → InferenceRepo

An **Inference** in NormCode (a step that produces a concept) is stored as an `InferenceEntry`:

```python
# From _repo.py
@dataclass
class InferenceEntry:
    inference_sequence: str        # e.g., "quantifying", "imperative", "grouping"
    concept_to_infer: ConceptEntry # The output concept
    function_concept: ConceptEntry # The functional concept (<=)
    value_concepts: List[ConceptEntry] # Input concepts (<-)
    flow_info: Dict[str, any]     # Contains 'flow_index' (e.g., "1.1.2")
    working_interpretation: Dict  # Parsed NormCode syntax → execution config
```

**Key Mapping:**
- **Functional Concept (`<=`)** → `function_concept` (e.g., `*every({number pair})`)
- **Value Concepts (`<-`)** → `value_concepts` (inputs)
- **Flow Index** (e.g., `1.1.2`) → `flow_info['flow_index']` (hierarchical ordering)
- **Agent's Sequence** → `inference_sequence` (determines which sequence to invoke)

## 2. NormCode Syntax Parsing → Working Interpretation

The `_parser.py` module parses NormCode expressions and converts them into `working_interpretation` dictionaries that guide execution:

### Quantifying (`*every`)

```normcode
*every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]
```

**Parsed into:**
```python
{
    "syntax": {
        "marker": "every",
        "LoopBaseConcept": "{number pair}",
        "quantifier_index": 1,
        "InLoopConcept": {"{carry-over number}*1": 1},
        "ConceptToInfer": ["{new number pair}"]
    }
}
```

This tells the **Quantifying Agent's Sequence** how to iterate.

### Grouping (`&across`, `&in`)

```normcode
&across({unit place value}:{number pair}*1)
```

**Parsed into:**
```python
{
    "syntax": {
        "marker": "across",
        "by_axis_concepts": "{number pair}*1"
    }
}
```

This tells the **Grouping Agent's Sequence** how to collect items.

### Assigning (`$.`, `$+`, `$=`, `$%`)

```normcode
$.({remainder})
```

**Parsed into:**
```python
{
    "syntax": {
        "marker": ".",
        "assign_source": "{remainder}",
        "assign_destination": "*every({number pair})..."
    }
}
```

This tells the **Assigning Agent's Sequence** how to update state.

### Timing (`@if`, `@after`)

```normcode
@if!(<all number is 0>)
```

**Parsed into:**
```python
{
    "syntax": {
        "marker": "if!",
        "condition": "<all number is 0>"
    }
}
```

This tells the **Timing Agent's Sequence** when to execute.

## 3. Execution Order → Waitlist

The `Waitlist` organizes inferences by their **flow_index** (hierarchical dot notation):

```python
# From _waitlist.py
def sort_by_flow_index(self):
    # Converts "1.1.2" → (1, 1, 2) for proper sorting
    # Ensures bottom-up execution: children before parents
```

**Key Principle:** The flow_index establishes a **hierarchical dependency structure**:
- `1.1.2.4` (grouping) supports `1.1.2` (imperative)
- `1.1.2` supports `1.1` (quantifying loop)
- `1.1` supports `1` (top-level)

The orchestrator uses `get_supporting_items()` to find all child inferences that must complete before a parent can run.

## 4. Dependency Resolution → Blackboard

The `Blackboard` is the **single source of truth** for execution state:

```python
# From _blackboard.py
@dataclass
class Blackboard:
    concept_statuses: Dict[str, str]  # "empty" | "complete"
    item_statuses: Dict[str, str]     # "pending" | "in_progress" | "completed" | "failed"
    item_execution_counts: Dict[str, int]  # How many times executed
```

**State Transitions:**
1. **Initialization**: All concepts start as `"empty"`, all items as `"pending"`
2. **Ground Concepts**: Immediately set to `"complete"` (they have data)
3. **After Inference**: Concept status → `"complete"`, item status → `"completed"`

**Readiness Check** (`_is_ready()` in `_orchestrator.py`):
An inference is ready when:
- ✅ All **supporting items** (children) are `"completed"`
- ✅ The **function concept** (if any) is `"complete"`
- ✅ All **value concepts** (inputs) are `"complete"`

## 5. Execution Cycle → Orchestrator

The `Orchestrator.run()` method executes a **cycle-based loop**:

```python
# From _orchestrator.py
def run(self):
    while self.blackboard.get_all_pending_or_in_progress_items():
        self.tracker.cycle_count += 1
        progress_made, retries = self._run_cycle(retries)
        
        # Checkpoint at end of cycle
        if self.checkpoint_manager:
            self.checkpoint_manager.save_state(...)
```

**Each Cycle:**
1. **Scan Waitlist**: Find all `"pending"` items
2. **Check Readiness**: For each item, call `_is_ready(item)`
3. **Execute Ready Items**: Call `_execute_item(item)` → `_inference_execution(item)`
4. **Update State**: Update Blackboard with results
5. **Checkpoint**: Save state (if enabled)

**Execution Flow for One Inference:**
```python
def _execute_item(self, item: WaitlistItem):
    # 1. Mark as in_progress
    self.blackboard.set_item_status(flow_index, 'in_progress')
    
    # 2. Create AgentFrame and execute
    agent_frame = AgentFrame(...)
    agent_frame.configure(inference, inference_sequence)
    states = inference.execute()  # Runs the Agent's Sequence
    
    # 3. Process results
    self._update_references_and_check_completion(states, item)
    
    # 4. Update status
    self.blackboard.set_item_status(flow_index, 'completed')
```

## 6. Agent's Sequence Invocation → AgentFrame

When an inference executes, the `inference_sequence` (e.g., `"quantifying"`, `"imperative"`) determines which **Agent's Sequence** runs:

```python
# From _orchestrator.py
def _execute_agent_frame(self, item: WaitlistItem, inference: Inference):
    working_interpretation = item.inference_entry.working_interpretation
    working_interpretation["blackboard"] = self.blackboard
    working_interpretation["workspace"] = self.workspace
    
    agent_frame = AgentFrame(
        self.agent_frame_model,
        working_interpretation=working_interpretation,
        body=self.body
    )
    agent_frame.configure(inference, item.inference_entry.inference_sequence)
    return inference.execute()
```

**The `working_interpretation` contains:**
- Parsed NormCode syntax (from `_parser.py`)
- Blackboard reference (for reading concept states)
- Workspace (for loop state in quantifying sequences)

**Agent's Sequence Steps:**
- **IWI** (Input Working Interpretation): Processes the `working_interpretation`
- **IR** (Input References): Reads input concept references from Blackboard
- **GR/QR/AR/MFP/MVP/TVA/TIP/MIA** (Sequence-specific steps)
- **OR** (Output Reference): Produces output, updates concept reference
- **OWI** (Output Working Interpretation): Final state

## 7. Reference Updates → Concept Completion

After an inference executes, the `OR` (Output Reference) step produces a new `Reference` object:

```python
# From _orchestrator.py
def _update_concept_from_record(self, record, category, item, ...):
    concept_entry = self.concept_repo.get_concept(concept_name)
    concept_entry.concept.reference = record.reference.copy()  # Update reference
    self.blackboard.set_concept_status(concept_name, 'complete')  # Mark complete
```

**Key Behavior:**
- The `Reference` is a **multi-dimensional container** with named axes
- When a concept's reference is updated, it becomes `"complete"` on the Blackboard
- Other inferences waiting for this concept can now proceed

## 8. Special Behaviors

### Quantifying Loops

For `quantifying` sequences (loops with `*every`):

```python
# From _orchestrator.py
def _check_quantifying_completion(self, states, item):
    is_quantifying = item.inference_entry.inference_sequence == 'quantifying'
    is_complete = getattr(states.syntax, 'completion_status', False)
    return is_quantifying, is_complete
```

**Loop Behavior:**
- If loop **not complete**: Reset supporting items to `"pending"`, keep concept as `"pending"`
- If loop **complete**: Mark concept as `"complete"`, allow parent to proceed

### Timing Inferences

For `timing` sequences (conditionals with `@if`, `@after`):

```python
# From _orchestrator.py
def _handle_timing_inference(self, states, item):
    timing_ready = getattr(states, 'timing_ready', False)
    if not timing_ready:
        return "pending"  # Retry later
    
    # If condition triggers skip, propagate to children
    if getattr(states, 'to_be_skipped', False):
        dependent_items = self.waitlist.get_dependent_items(item)
        for dependent in dependent_items:
            self._propagate_skip_state(dependent, flow_index)
```

**Timing Behavior:**
- Checks if condition is met (e.g., `@if(<all number is 0>)`)
- If not met: Retry in next cycle
- If met: Complete and optionally skip dependent items

### Invariant Concepts

Some concepts should **not** be reset during loop iterations:

```python
# From _orchestrator.py
if inferred_concept_entry.is_invariant:
    # Skip resetting its reference during loop
    self.blackboard.set_concept_status(concept_name, 'pending')
    # But keep reference intact
```

## 9. Checkpointing & Persistence

The system supports **state persistence** for resumability:

```python
# From _orchestrator.py
def __init__(self, ..., db_path: Optional[str] = None, 
             checkpoint_frequency: Optional[int] = None,
             run_id: Optional[str] = None):
    if db_path:
        self.db = OrchestratorDB(db_path, run_id=self.run_id)
        self.checkpoint_manager = CheckpointManager(self.db)
```

**Checkpoint Granularity:**
- **End-of-Cycle**: Default (saves after each cycle)
- **Intra-Cycle**: Optional `checkpoint_frequency=N` (saves every N inferences)

**Checkpoint Contents:**
- Blackboard state (all concept/item statuses)
- Workspace (loop state)
- Concept References (serialized as JSON)
- Execution history (tracked in DB)

## 10. Complete Execution Example

**NormCode Plan:**
```normcode
{new number pair} | 1. quantifying
    <= *every({number pair})%:[{number pair}]@(1)
    <- {number pair}
    
    <- {digit sum} | 1.1.2. imperative
        <= ::(sum {1} and {2} to get {3})
        <- [all {unit place value} of numbers]<:{1}>
        <- {carry-over number}*1<:{2}>
        <- {sum}?<:{3}>
```

**Execution Flow:**

1. **Initialization:**
   - `{number pair}` (ground concept) → `"complete"` on Blackboard
   - All other concepts → `"empty"`
   - All inferences → `"pending"`

2. **Cycle 1:**
   - Check `1.1.2` (imperative): ❌ Not ready (needs `[all {unit place value} of numbers]`)
   - Check `1.1.2.4` (grouping): ✅ Ready (inputs available)
   - Execute `1.1.2.4` → Updates `[all {unit place value} of numbers]` → `"complete"`

3. **Cycle 2:**
   - Check `1.1.2` (imperative): ✅ Ready (all inputs complete)
   - Execute `1.1.2` → Updates `{digit sum}` → `"complete"`

4. **Cycle 3:**
   - Check `1` (quantifying): ✅ Ready (supporting items complete)
   - Execute `1` → Loop iteration completes → Updates `{new number pair}`
   - If loop not done: Reset supporting items, continue
   - If loop done: Mark `{new number pair}` → `"complete"`, finish

## Summary: NormCode → Execution Mapping

| NormCode Element | Orchestration Component | Purpose |
|-----------------|------------------------|---------|
| Concept (`{}`, `[]`, `<>`) | `ConceptEntry` in `ConceptRepo` | Data structure definition |
| Functional Concept (`<=`) | `InferenceEntry.function_concept` | Determines agent's sequence |
| Value Concepts (`<-`) | `InferenceEntry.value_concepts` | Input dependencies |
| Flow Index (`1.1.2`) | `InferenceEntry.flow_info['flow_index']` | Execution order |
| Reference (data) | `Concept.reference` | Multi-dimensional data storage |
| Agent's Sequence | `inference_sequence` → `AgentFrame` | Execution pipeline |
| Working Interpretation | `working_interpretation` dict | Parsed syntax → execution config |
| Blackboard | `Blackboard` | State tracking (concept/item status) |
| Waitlist | `Waitlist` | Ordered execution queue |
| Orchestrator | `Orchestrator` | Dependency-driven execution loop |

The orchestration system transforms the **declarative NormCode plan** into a **procedural execution** that respects dependencies, manages state, and handles complex control flow patterns like loops and conditionals.

