# NormCode AI Planning Pipeline - Iteration 7

## Overview

This iteration updates the NormCode AI Planning pipeline to use the **new syntax** from the updated NormCode documentation (located in `documentation/current/`).

## What Changed from Iteration 6

### Syntax Updates

1. **Flow indices**: Moved from prefix (`1.1.grouping|`) to suffix annotation (`| ?{flow_index}: 1.1`)
2. **Sequence types**: Now use explicit `| ?{sequence}: type` annotation
3. **Comments**: Formalized into three categories:
   - `?{...}:` - Syntactical (flow_index, sequence)
   - `%{...}:` - Referential (paradigm, file_location)
   - `/:` - Description
4. **Operators**: Updated notation (e.g., `&across` → `&[#]`)
5. **File extensions**: `.ncds` for drafts, `.ncd` for formalized

See `SYNTAX_MIGRATION.md` for complete migration guide.

### Pipeline Updates

The 5-phase pipeline is now:
1. **Confirmation of Instruction** → produces instruction block + context
2. **Deconstruction** → produces `.ncds` draft + `.ncn` companion
3. **Formalization** → produces `.ncd` with annotations
4. **Post-Formalization & Contextualization** → enriches `.ncd` with paradigms
5. **Activation & Materialization** → produces JSON repos + executable script

## File Structure

```
iteration_7/
├── README.md                    # This file
├── SYNTAX_MIGRATION.md          # Old→New syntax mapping guide
├── 1.1_instruction_block.md     # Pipeline instruction
├── 2.1_draft.ncds               # NormCode Draft Straightforward
├── 3.1_formalized.ncd           # Formalized NormCode Draft
├── context_store/
│   ├── shared---normcode_overview.md
│   ├── shared---ncd_syntax.md
│   ├── shared---compilation_pipeline.md
│   ├── shared---operators_reference.md
│   └── raw---prompt.md
└── prompts/                     # (to be generated)
```

## Key Documentation References

- `documentation/current/1_intro/overview.md` - NormCode overview
- `documentation/current/2_grammar/ncd_format.md` - .ncd format specification
- `documentation/current/3_execution/overview.md` - Execution model
- `documentation/current/4_compilation/overview.md` - Compilation pipeline

## Next Steps

1. Create initial context manifest (`1.2_initial_context_registered.json`)
2. Generate prompt files in `prompts/` directory
3. Run formalization to create `.nci.json` inference structure
4. Activate to produce `.concept.json` and `.inference.json`
5. Create executable script

## Usage

```python
# Once complete, the pipeline can be executed with:
from infra._orchest._repo import ConceptRepo, InferenceRepo
from infra._orchest._orchestrator import Orchestrator
from infra._agent._body import Body

concept_repo = ConceptRepo.from_json("repos/concept_repo.json")
inference_repo = InferenceRepo.from_json("repos/inference_repo.json")
body = Body(llm_name="qwen-plus", base_dir=SCRIPT_DIR)

orchestrator = Orchestrator(
    concept_repo=concept_repo,
    inference_repo=inference_repo,
    body=body,
)
final_concepts = orchestrator.run()
```

