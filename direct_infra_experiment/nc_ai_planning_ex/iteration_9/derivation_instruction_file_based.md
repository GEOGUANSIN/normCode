# Derivation as a File-Based NormCode Plan

**The twist**: Derivation operates on files, saves intermediate artifacts, and can resume from checkpoints.

---

## The File-Based Derivation Algorithm

```
Given an instruction file, produce a .ncds file with checkpoints:

INPUT FILES:
  - instruction.txt         : Raw natural language instruction
  - refinement_questions.txt: The 7 refinement questions (constant)

OUTPUT FILES:
  - ncds_output.ncds        : Final .ncds file

CHECKPOINT FILES (intermediate artifacts):
  - 1_refined_instruction.txt  : Concrete instruction after refinement
  - 2_extraction.json          : Extracted concepts, operations, dependencies
  - 3_classifications.json     : Pattern classifications for each operation
  - 4_dependency_tree.json     : Tree structure before serialization
  - progress.txt               : Current phase (for resumption)

PHASE 1: REFINEMENT
  - Read instruction.txt
  - Read progress.txt (if exists, skip completed phases)
  - If instruction is vague:
    - Apply refinement questions
    - Write 1_refined_instruction.txt
  - Otherwise:
    - Copy instruction to 1_refined_instruction.txt
  - Update progress.txt → "phase_1_complete"

PHASE 2: EXTRACTION
  - Read 1_refined_instruction.txt
  - Extract concepts, operations, dependencies, patterns
  - Write 2_extraction.json
  - Update progress.txt → "phase_2_complete"

PHASE 3: CLASSIFICATION
  - Read 2_extraction.json
  - For each operation, classify pattern
  - Write 3_classifications.json
  - Update progress.txt → "phase_3_complete"

PHASE 4: TREE CONSTRUCTION
  - Read 2_extraction.json and 3_classifications.json
  - Build dependency tree
  - Write 4_dependency_tree.json
  - Update progress.txt → "phase_4_complete"

PHASE 5: SERIALIZATION
  - Read 4_dependency_tree.json
  - Serialize to .ncds format
  - Write ncds_output.ncds
  - Update progress.txt → "complete"

OUTPUT: ncds_output.ncds (with all checkpoints preserved)
```

---

## Derived `.ncds` for File-Based Derivation

```ncds
/: ========================================
/: File-Based Derivation Algorithm
/: ========================================
/: Meta-plan with explicit file I/O and checkpoints
/:
/: INPUT:  instruction.txt (file path)
/: OUTPUT: ncds_output.ncds (file path)
/: CHECKPOINTS: progress.txt, 1_*.txt, 2_*.json, 3_*.json, 4_*.json

<- derivation complete
    <= write completion status to progress file
    <- progress file path
    <- ncds output written
    
<- ncds output written
    <= write ncds file to output path
        <= if phase 5 NOT already complete
        <* phase 5 already complete?
    /: PHASE 5: Serialize and write final output
    <- output file path
    <- ncds content
        <= serialize dependency tree to ncds text format
        <- dependency tree
    <- phase 5 already complete?
        <= check if phase 5 already complete in progress
        <- current progress
    <- phase 4 complete
        /: Dependency: must complete tree construction first

<- phase 4 complete
    <= write phase 4 status to progress file
    <- progress file path
    <- tree file written

<- tree file written
    <= write dependency tree to checkpoint file
        <= if phase 4 NOT already complete
        <* phase 4 already complete?
    /: PHASE 4: Build and save tree
    <- tree file path
    <- dependency tree
        <= construct tree from classifications and extractions
        <- final output concept
            <= identify goal from extraction data
            <- extraction data
        <- classified operations
            <= read classifications from checkpoint
            <- classifications file path
        <- all dependencies
            <= extract dependencies from extraction data
            <- extraction data
    <- phase 4 already complete?
        <= check if phase 4 already complete in progress
        <- current progress
    <- phase 3 complete
        /: Dependency: must complete classification first

<- phase 3 complete
    <= write phase 3 status to progress file
    <- progress file path
    <- classifications file written

<- classifications file written
    <= write classifications to checkpoint file
        <= if phase 3 NOT already complete
        <* phase 3 already complete?
    /: PHASE 3: Classify and save
    <- classifications file path
    <- all classifications
        <= for each extracted operation
        
            <= return classification for this operation
            
            <- classification
                <= determine pattern type for operation
                <- current operation
                <- operation context
                    <= gather context from extraction data
                    <- current operation
                    <- extraction data
        
        <- extracted operations
            <= get operations from extraction data
            <- extraction data
        <* current operation
    <- phase 3 already complete?
        <= check if phase 3 already complete in progress
        <- current progress
    <- phase 2 complete
        /: Dependency: must complete extraction first

<- phase 2 complete
    <= write phase 2 status to progress file
    <- progress file path
    <- extraction file written

<- extraction file written
    <= write extraction results to checkpoint file
        <= if phase 2 NOT already complete
        <* phase 2 already complete?
    /: PHASE 2: Extract and save
    <- extraction file path
    <- extraction data
        <= bundle all extractions together
        
        <- extracted concepts
            <= identify all nouns and data entities
            <- refined instruction content
        
        <- extracted operations
            <= identify all verbs and actions
            <- refined instruction content
        
        <- extracted dependencies
            <= identify what needs what
            <- refined instruction content
            <- extracted concepts
            <- extracted operations
        
        <- extracted control patterns
            <= identify loops and conditions
            <- refined instruction content
    <- phase 2 already complete?
        <= check if phase 2 already complete in progress
        <- current progress
    <- phase 1 complete
        /: Dependency: must complete refinement first

<- phase 1 complete
    <= write phase 1 status to progress file
    <- progress file path
    <- refined instruction file written

<- refined instruction file written
    <= write refined instruction to checkpoint file
        <= if phase 1 NOT already complete
        <* phase 1 already complete?
    /: PHASE 1: Refine and save
    <- refined instruction file path
    <- refined instruction content
        <= select first available result
        
        <- cached refined instruction
            <= read refined instruction from checkpoint
                <= if phase 1 already complete
                <* phase 1 already complete?
            <- refined instruction file path
        
        <- freshly refined instruction
            <= select refined or original based on check
                <= if phase 1 NOT already complete
                <* phase 1 already complete?
            
            <- refined version
                <= synthesize from refinement answers
                    <= if instruction is vague
                    <* instruction is vague?
                <- refinement answers
                    <= apply each refinement question
                    <- raw instruction content
                    <- refinement questions content
                        <= read refinement questions from file
                        <- refinement questions file path
            
            <- original version
                <= pass through raw instruction
                    <= if instruction is NOT vague
                    <* instruction is vague?
                <- raw instruction content
            
            <- instruction is vague?
                <= judge if instruction lacks concrete details
                <- raw instruction content
    
    <- phase 1 already complete?
        <= check if phase 1 already complete in progress
        <- current progress
    
<- raw instruction content
    <= read instruction from input file
    <- instruction file path

<- current progress
    <= read progress from file if exists
    <- progress file path

/: ========================================
/: FILE PATH CONFIGURATION (Ground Concepts)
/: ========================================

<- instruction file path
    /: Ground: path to instruction.txt

<- refinement questions file path
    /: Ground: path to refinement_questions.txt

<- progress file path
    /: Ground: path to progress.txt

<- refined instruction file path
    /: Ground: path to 1_refined_instruction.txt

<- extraction file path
    /: Ground: path to 2_extraction.json

<- classifications file path
    /: Ground: path to 3_classifications.json

<- tree file path
    /: Ground: path to 4_dependency_tree.json

<- output file path
    /: Ground: path to ncds_output.ncds
```

---

## File Flow Diagram

```
INPUT                    CHECKPOINTS                         OUTPUT
─────                    ───────────                         ──────

instruction.txt ─────┐
                     │
                     ▼
              ┌─────────────┐
              │  PHASE 1    │──────► 1_refined_instruction.txt
              │ Refinement  │                    │
              └─────────────┘                    │
                     │                           │
                     ▼                           ▼
              ┌─────────────┐
              │  PHASE 2    │──────► 2_extraction.json
              │ Extraction  │                    │
              └─────────────┘                    │
                     │                           │
                     ▼                           ▼
              ┌─────────────┐
              │  PHASE 3    │──────► 3_classifications.json
              │Classification│                   │
              └─────────────┘                    │
                     │                           │
                     ▼                           ▼
              ┌─────────────┐
              │  PHASE 4    │──────► 4_dependency_tree.json
              │Construction │                    │
              └─────────────┘                    │
                     │                           │
                     ▼                           ▼
              ┌─────────────┐
              │  PHASE 5    │─────────────► ncds_output.ncds
              │Serialization│
              └─────────────┘
                     │
                     ▼
              progress.txt (updated after each phase)
```

---

## Key File Operations

| Operation | NormCode Expression | Blocking? |
|-----------|---------------------|-----------|
| **Read file** | `<= read content from file path` | No (immediate) |
| **Write file** | `<= write content to file path` | No (immediate) |
| **Check exists** | `<= check if file exists` | No (immediate) |
| **Read progress** | `<= read progress from file if exists` | No |
| **Update progress** | `<= write phase status to progress file` | No |

---

## Resumption Logic

The plan supports resumption via `progress.txt`. Each phase checks if it's already complete:

```ncds
<- phase N already complete?
    <= check if phase N already complete in progress
    <- current progress

<- current progress
    <= read progress from file if exists
    <- progress file path
```

Each phase write operation is gated by the completion check:

```ncds
<- phase N output written
    <= write output to checkpoint file
        <= if phase N NOT already complete
        <* phase N already complete?
    ...
```

For Phase 1, we also select between cached (from checkpoint) or fresh computation:

```ncds
<- refined instruction content
    <= select first available result
    <- cached refined instruction
        <= read from checkpoint
            <= if phase 1 already complete
            <* phase 1 already complete?
        <- refined instruction file path
    <- freshly refined instruction
        <= compute fresh
            <= if phase 1 NOT already complete
            <* phase 1 already complete?
        ...
```

If the process is interrupted after Phase 2, on restart:
1. Read `progress.txt` → "phase_2_complete"
2. Phase 1: reads from checkpoint (already complete)
3. Phase 2: skip write (already complete)
4. Phase 3: executes normally

---

## Checkpoint File Formats

### progress.txt
```
phase_1_complete
phase_2_complete
phase_3_complete
...
```

### 1_refined_instruction.txt
```
For each customer review:
  1. Extract sentiment score
  2. Identify key themes
  3. Generate summary
Collect all summaries into final report.
```

### 2_extraction.json
```json
{
  "concepts": ["customer review", "sentiment score", "key themes", "summary", "final report"],
  "operations": ["extract sentiment", "identify themes", "generate summary", "collect summaries"],
  "dependencies": {
    "sentiment score": ["customer review"],
    "summary": ["sentiment score", "key themes"],
    "final report": ["all summaries"]
  },
  "control_patterns": {
    "for_each": ["customer review"],
    "collect": ["summary"]
  }
}
```

### 3_classifications.json
```json
{
  "extract sentiment": {"pattern": "linear", "context": null},
  "identify themes": {"pattern": "linear", "context": null},
  "generate summary": {"pattern": "multi-input", "context": null},
  "collect summaries": {"pattern": "iteration", "context": "customer review"}
}
```

### 4_dependency_tree.json
```json
{
  "root": "final report",
  "nodes": {
    "final report": {
      "operation": "collect summaries",
      "children": ["summary"],
      "context": "customer review"
    },
    "summary": {
      "operation": "generate summary",
      "children": ["sentiment score", "key themes"]
    }
  }
}
```

---

## Why File-Based?

| Benefit | Explanation |
|---------|-------------|
| **Resumption** | If LLM call fails, restart from last checkpoint |
| **Debugging** | Inspect intermediate artifacts |
| **Iteration** | Re-run Phase 3 with different classification rules |
| **Audit trail** | All decisions are recorded |
| **Composition** | Other tools can read/modify checkpoints |

---

## Integration with Execution

When this plan is executed:

1. **Ground concepts** are file paths (provided by user or config)
2. **File read operations** use Python's file I/O
3. **LLM operations** (extraction, classification) call the model
4. **File write operations** persist results
5. **Progress tracking** enables resume-on-failure

This is the foundation for a **robust, interruptible compiler**.

---

## Summary

File-based derivation adds:

1. **Explicit I/O** — Read/write operations as first-class concepts
2. **Checkpoints** — Each phase saves its output
3. **Progress tracking** — `progress.txt` enables resumption
4. **Structured artifacts** — JSON for structured data, text for content
5. **Path configuration** — All paths are ground concepts

The derivation algorithm is now **stateful, resumable, and debuggable**.
