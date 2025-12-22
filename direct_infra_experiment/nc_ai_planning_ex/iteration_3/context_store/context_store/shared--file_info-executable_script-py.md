# File Format: Executable Script (`.py`)

The executable Python script is the final, tangible output of the entire NormCode AI Planning Pipeline, generated in Phase 5. It is a runnable script that takes the generated repositories (`concept_repo.json`, `inference_repo.json`) and executes the plan they describe.

**Purpose:**
This script is the materialization of the abstract plan. It serves as the entry point for an `Orchestrator` to run the entire logical flow, from initial inputs to final outputs. It bridges the gap between the formal plan and a concrete, executable process.

**Key Responsibilities:**
The script is a standard Python file containing a main execution block (`if __name__ == "__main__":`) that is responsible for:
1.  **File System Preparation**: Creating any necessary directories (e.g., `generated_scripts/`, `prompts/`) that ground concepts in the repositories might reference.
2.  **Loading Repositories**: Reading `concept_repo.json` and `inference_repo.json` from disk.
3.  **Instantiating Repositories**: Creating `ConceptRepo` and `InferenceRepo` objects from the loaded data.
4.  **Initializing a Body**: Setting up a `Body` object, which provides the connection to reasoning capabilities (like an LLM) needed to execute imperatives and judgements.
5.  **Initializing the Orchestrator**: Creating an `Orchestrator` instance, passing it the repositories and the body.
6.  **Running the Plan**: Calling the `orchestrator.run()` method to start the execution cycle.
7.  **Reporting Results**: Printing or logging the final concepts produced by the run.

**Example Snippet:**
```python
from infra._orchest._repo import ConceptRepo, InferenceRepo
from infra._orchest._orchestrator import Orchestrator
from infra._agent._body import Body
import json
import os
from pathlib import Path

def create_repositories_from_files():
    # ... code to load .json files ...
    concept_repo = ConceptRepo.from_json_list(...)
    inference_repo = InferenceRepo.from_json_list(...)
    return concept_repo, inference_repo

if __name__ == "__main__":
    # 1. Prepare file system
    Path("./generated_prompts").mkdir(exist_ok=True)
    
    # 2. Build repositories
    concept_repo, inference_repo = create_repositories_from_files()

    # 3. Construct a Body for imperatives/judgements
    body = Body(llm_name="qwen-plus", base_dir=Path("./generated_prompts"))

    # 4. Construct and run the orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        body=body,
        max_cycles=300,
    )
    final_concepts = orchestrator.run()

    # ... code to print final concepts ...
```
