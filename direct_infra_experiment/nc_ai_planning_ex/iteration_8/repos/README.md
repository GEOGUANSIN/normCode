# NormCode Derivation Algorithm - Iteration 8

This directory contains the compiled repositories and input configuration for the file-based derivation algorithm.

## Files

### Repository Files (Compiled from Post-Formalization)

- **`concept_repo.json`** — All concepts (value, functional, context) with their metadata
- **`inference_repo.json`** — Execution plan with flow indices, paradigms, and value orders

### Input Configuration

- **`inputs.json`** — Ground concept values (file paths) needed for execution
- **`instruction.txt`** — Sample natural language instruction to derive

## Ground Concepts (Required Inputs)

The derivation algorithm requires these file path inputs:

| Concept | Type | Purpose | Default Value |
|---------|------|---------|---------------|
| `{instruction file path}` | Perceptual sign | Input instruction to derive | `instruction.txt` |
| `{refinement questions file path}` | Perceptual sign | Refinement questions (in provisions) | `provisions/data/refinement_questions.txt` |
| `{progress file path}` | Literal path | Progress tracking for checkpoints | `progress.txt` |
| `{refined instruction file path}` | Perceptual sign | Phase 1 checkpoint | `1_refined_instruction.txt` |
| `{extraction file path}` | Perceptual sign | Phase 2 checkpoint | `2_extraction.json` |
| `{classifications file path}` | Literal path | Phase 3 checkpoint | `3_classifications.json` |
| `{tree file path}` | Literal path | Phase 4 checkpoint | `4_dependency_tree.json` |
| `{output file path}` | Literal path | Final NCDS output | `ncds_output.ncds` |

## Execution Flow

The algorithm proceeds through 5 phases:

1. **Phase 1 (Refinement)**: Judge if instruction is vague → refine if needed → save to checkpoint
2. **Phase 2 (Extraction)**: Extract concepts, operations, dependencies, control patterns → save to checkpoint
3. **Phase 3 (Classification)**: For each operation, gather context and classify pattern → save to checkpoint
4. **Phase 4 (Tree Construction)**: Identify goal, construct dependency tree → save to checkpoint
5. **Phase 5 (Serialization)**: Serialize tree to NCDS format → write to output file

### Checkpointing

The algorithm tracks progress in `progress.txt`. If execution is interrupted, it can resume from the last completed phase by reading checkpoint files.

## Usage

### 1. Prepare Your Instruction

Edit `instruction.txt` or create a new file with your natural language instruction:

```txt
Build a sentiment analysis tool that processes customer reviews.

For each review in the input file:
- Extract the sentiment (positive/negative/neutral)
- Extract key themes mentioned
- Assign a confidence score

Output: JSON report with sentiment breakdown and themes
```

### 2. Configure Input Paths (Optional)

If you want different file paths, edit `inputs.json`. For example, to use a different instruction file:

```json
"{instruction file path}": {
  "data": [["%(my_custom_instruction.txt)"]],
  "axes": ["_none_axis"]
}
```

### 3. Run the Orchestrator

```bash
# Execute the derivation plan
python -m infra._agent._orchestrator \
  --concept_repo repos/concept_repo.json \
  --inference_repo repos/inference_repo.json \
  --inputs repos/inputs.json
```

### 4. Check Outputs

After execution, you'll have:

- `progress.txt` — Phase completion status
- `1_refined_instruction.txt` — Refined instruction (if vague)
- `2_extraction.json` — Extracted concepts/operations
- `3_classifications.json` — Classified operations
- `4_dependency_tree.json` — Dependency tree structure
- `ncds_output.ncds` — **Final NormCode plan**

## Perceptual Signs vs Literals

The algorithm uses two different input annotation types:

### Perceptual Signs (MVP perceives them)

Used when the paradigm expects **loaded content** as input:

```json
"{instruction file path}": {
  "data": [["%(instruction.txt)"]],
  "axes": ["_none_axis"]
}
```

→ MVP perceives `%{file_location}(instruction.txt)` → loads file → passes content to paradigm

### Literal Paths (MVP passes through)

Used when the paradigm handles **file I/O internally**:

```json
"{progress file path}": {
  "data": [["%(progress.txt)"]],
  "axes": ["_none_axis"]
}
```

→ MVP passes `"progress.txt"` as-is → paradigm does the file read/write

## Example: Resuming from Checkpoint

If execution fails during phase 3, the next run will:

1. Read `progress.txt` → see phase 1, 2 complete
2. Skip phase 1, 2 (read from checkpoint files)
3. Continue from phase 3

To force a full re-run, delete `progress.txt`.

## Provisions

The algorithm uses provisions from `../provisions/`:

- **Prompts**: LLM instructions for each operation (`provisions/prompts/phase_*/`)
- **Data**: Refinement questions (`provisions/data/refinement_questions.txt`)
- **Scripts**: Python helper scripts (e.g., `check_phase_complete.py`)
- **Paradigms**: Composition specifications (`provisions/paradigms/`)

See `../provisions/path_mapping.json` for resource resolution mappings.

---

For more details on the provision system, see:
- `documentation/current/4_compilation/provision_new_vision.md`
- `documentation/current/4_compilation/post_formalization.md`

