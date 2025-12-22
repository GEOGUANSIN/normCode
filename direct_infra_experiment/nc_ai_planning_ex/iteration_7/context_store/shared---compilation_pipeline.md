# NormCode Compilation Pipeline

## The Five Phases

```
Phase 1: Derivation
    Natural language → .ncds (draft)
         ↓
Phase 2: Formalization  
    .ncds → .ncd (with flow indices and sequences)
         ↓
Phase 3: Post-Formalization
    .ncd → .ncd (enriched with paradigms and resources)
         ↓
Phase 4: Activation
    .ncd → .concept.json + .inference.json
         ↓
Phase 5: Execution
    Orchestrator runs the plan
```

## Phase Details

### Phase 1: Derivation
**Input**: Natural language instruction  
**Output**: `.ncds` (NormCode Draft Straightforward)

- Identifies concepts (data entities)
- Identifies operations (actions)
- Extracts dependencies
- Creates hierarchical tree structure

### Phase 2: Formalization
**Input**: `.ncds`  
**Output**: `.ncd` (formalized)

- Assigns unique flow indices
- Determines sequence types
- Resolves concept identity and value bindings
- Adds metadata comments

### Phase 3: Post-Formalization  
**Input**: `.ncd` (formalized)  
**Output**: `.ncd` (enriched)

Three sub-phases:
1. **Re-composition**: Maps intent to normative context
   - `%{norm_input}:` paradigm ID
   - `%{body_faculty}:` body faculty to invoke
2. **Provision**: Fills in concrete resources
   - `%{file_location}:` paths to data
   - `%{prompt_location}:` paths to prompts
3. **Syntax Re-confirmation**: Confirms reference structure
   - `%{ref_axes}:` named axes
   - `%{ref_element}:` element type

### Phase 4: Activation
**Input**: `.ncd` (enriched)  
**Output**: `.concept.json` + `.inference.json`

- Extracts concept definitions
- Extracts inference definitions  
- Generates `working_interpretation` for each inference
- Maps syntax to what each sequence's IWI step expects

### Phase 5: Execution
**Input**: JSON repositories  
**Output**: Results + Checkpoints

- Orchestrator loads repositories
- Runs execution loop (cycles)
- Bottom-up dependency resolution
- Produces final output

