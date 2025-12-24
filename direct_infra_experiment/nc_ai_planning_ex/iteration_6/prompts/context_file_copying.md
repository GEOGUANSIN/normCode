# [context]

## [pipeline_goal_and_structure]
# The NormCode AI Planning Pipeline

## Project Goal

The project goal is to bootstrap from a high-level natural language prompt into a structured and executable plan using a meta-algorithmic pipeline. This pipeline, itself powered by a NormCode plan, methodically transforms an instruction by:

1.  **Distilling** the user's intent into a clean instruction and registering all raw context.
2.  **Deconstructing** the instruction into a formal, hierarchical NormCode plan (`.ncd`).
3.  **Formalizing** the plan by applying serialization and redirection patterns and generating a final `.nc` file.
4.  **Contextualizing** the plan by enriching each formal step with precise, granular context and assembling prompts.
5.  **Materializing** the final plan into an executable script, ready for an orchestrator.

This creates a system that can understand, decompose, contextualize, and act upon complex instructions in a transparent and repeatable manner.

## [file_info-context_store-dir]
# Directory Guide: context_store

The `context_store` is a directory that holds the "knowledge base" for the pipeline. It contains a variety of files, primarily Markdown (`.md`) but also plain text (`.txt`), which provide the necessary information and guidance for the AI to execute the steps of the NormCode plan.

**Purpose:**
The context store holds the "knowledge base" for the pipeline. Each file contains a specific piece of context—a procedure, a guide, a data format explanation, or a principle—that is required by one or more prompts during the plan's execution. This modular approach allows for precise context distribution, ensuring that each prompt receives only the information it needs.

**File Categories:**
The files within the directory are categorized by a naming prefix, which indicates their role. The full inventory of these files is referenced in `1.2_initial_context_registerd.json` (for raw context) and `4.1_context_manifest.json` (for refined, task-specific context). The categories are:

-   `shared--*.md`: These files contain context that is potentially relevant to many different steps across the pipeline (e.g., `shared---pipeline_goal_and_structure.md`).
-   `[flow_index]---*.md`: These files contain context that is highly specific to a single step in the plan, identified by its unique `flow_index` (e.g., `1.6.2.1---automated_script_generation.md`).
-   `raw--*.(md|txt)`: These files represent initial, unprocessed context registered at the beginning of the pipeline. They are intended to be analyzed or transformed into more refined context files, but are kept intact as a record of the original state.

**Role in the Pipeline:**
During Phase 4 (Contextualization), the system analyzes the plan and generates a `context_manifest.json` file. This manifest explicitly maps which files from the `context_store` are required for each prompt, enabling the final assembly of targeted, context-aware prompts.

---
# [TASK]

## [MAIN INSTRUCTION]
### Step 1.2a: Generate Python Script for Context File Copying

This step generates a Python script that handles the mechanical task of copying identified context files into the `context_store` directory. This is a purely operational script that follows the intelligent file identification performed in Step 1.2 (Context Registration).

**Purpose:**
Generate a Python function that takes a file mapping and a `Body` object (infrastructure wrapper), then copies all referenced files into the `context_store` directory using the `Body`'s file system tool. The script will be saved and executed by the paradigm executor.

**Function Requirements:**
The generated Python code must define a function named `main` with the following signature:
```python
def main(file_mapping, body):
    """
    Copy files from source paths to target paths in context_store.
    
    Args:
        file_mapping: A JSON string or dictionary mapping source file paths to target paths.
                      Example: {"raw---prompt.md": "./context_store/raw---prompt.md"}
        body: Body instance providing access to infrastructure tools.
              Uses body.file_system for all file operations:
              - body.file_system.read(source_path)
              - body.file_system.save(content, target_path)
              - body.file_system.exists(path)
    
    Returns:
        Dictionary with:
        - "copied_files": List of dicts with source_path, target_path, status, error_message
        - "context_store_directory": Path to context_store directory
    """
```

**Script Behavior:**
1. Parse `file_mapping` into a dictionary if it is provided as a JSON string.
2. For each entry in the mapping:
   - Read the source file content using `body.file_system.read(source_path)`
   - Save the content to the target path using `body.file_system.save(content, target_path)`
   - Verify the copy using `body.file_system.exists(target_path)`
   - Track success/failure for each file
3. Return a status report dictionary

**Important Notes:**
- Use `body.file_system` for all I/O operations; do not use `open()`, `shutil`, or `os` file methods directly.
- Handle file not found errors gracefully—continue processing other files.
- `body.file_system` handles base directory resolution automatically.

---
*From Project Context:*

#### **Example: Expected Python Code Structure**

-   **Input (to the generated function):**
    ```python
    file_mapping = {
        "raw---prompt.md": "./context_store/raw---prompt.md",
        "raw--normcode_terminology_guide.md": "./context_store/raw--normcode_terminology_guide.md"
    }
    # body is passed automatically by the infrastructure
    ```

-   **Expected Function Behavior:**
    1. For each mapping entry:
       - Read the source file via `body.file_system.read(source_path)`
       - Save it via `body.file_system.save(content, target_path)`
       - Verify via `body.file_system.exists(target_path)`
       - Track result
    2. Return status dictionary

-   **Expected Return Value:**
    ```python
    {
        "copied_files": [
            {
                "source_path": "raw---prompt.md",
                "target_path": "./context_store/raw---prompt.md",
                "status": "success",
                "error_message": None
            },
            # ... other files
        ],
        "context_store_directory": "./context_store"
    }
    ```

## [INPUT]

### Input:
**File mapping from Step 1.2 (Context Registration):**
```json
$input_file_mapping
```

## [OUTPUT FORMAT]

**Your task:** Generate Python code that implements the file copying functionality described above. The code should be a complete, executable Python function.

**Output structure:** Return a JSON object with:
- **`analysis`**: Brief summary of the code you generated (e.g., "Generated Python script that copies files from mapping to context_store directory using body.file_system")
- **`answer`**: A string containing the complete Python code. The code must:
  - Import necessary modules (e.g., `pathlib`, `json`)
  - Define a `main` function with signature: `def main(file_mapping, body)`
  - Implement all the file copying logic using `body.file_system`
  - Return the expected dictionary structure
  - Handle errors gracefully

**Example Output:**
```json
{
  "analysis": "Generated Python script that copies files from the file_mapping dictionary to the context_store directory using body.file_system, creating directories as needed and handling errors gracefully.",
  "answer": "from pathlib import Path\nimport json\n\ndef main(file_mapping, body):\n    \"\"\"\n    Copy files from source paths to target paths in context_store.\n    \n    Args:\n        file_mapping: A JSON string or dictionary mapping source file paths to target paths.\n        body: Body instance providing access to infrastructure tools.\n    \n    Returns:\n        Dictionary with copied_files list and context_store_directory path.\n    \"\"\"\n    if isinstance(file_mapping, str):\n        try:\n            file_mapping = json.loads(file_mapping)\n        except json.JSONDecodeError:\n            return {\n                \"copied_files\": [],\n                \"context_store_directory\": \"./context_store\",\n                \"error\": \"Invalid JSON in file_mapping\"\n            }\n    \n    copied_files = []\n    context_store_dir = None\n    \n    for source_path, target_path in file_mapping.items():\n        try:\n            target = Path(target_path)\n            if context_store_dir is None:\n                context_store_dir = str(target.parent)\n            \n            read_result = body.file_system.read(source_path)\n            if read_result.get(\"status\") != \"success\":\n                copied_files.append({\n                    \"source_path\": source_path,\n                    \"target_path\": target_path,\n                    \"status\": \"error\",\n                    \"error_message\": read_result.get(\"message\", \"Failed to read source file\")\n                })\n                continue\n            content = read_result.get(\"content\", \"\")\n            \n            save_result = body.file_system.save(content, target_path)\n            if save_result.get(\"status\") != \"success\":\n                copied_files.append({\n                    \"source_path\": source_path,\n                    \"target_path\": target_path,\n                    \"status\": \"error\",\n                    \"error_message\": save_result.get(\"message\", \"Unknown error saving file\")\n                })\n                continue\n            \n            if not body.file_system.exists(target_path):\n                copied_files.append({\n                    \"source_path\": source_path,\n                    \"target_path\": target_path,\n                    \"status\": \"error\",\n                    \"error_message\": \"File copy completed but target file not found\"\n                })\n                continue\n            \n            copied_files.append({\n                \"source_path\": source_path,\n                \"target_path\": target_path,\n                \"status\": \"success\",\n                \"error_message\": None\n            })\n        except Exception as e:\n            copied_files.append({\n                \"source_path\": source_path,\n                \"target_path\": target_path,\n                \"status\": \"error\",\n                \"error_message\": str(e)\n            })\n    \n    return {\n        \"copied_files\": copied_files,\n        \"context_store_directory\": context_store_dir or \"./context_store\"\n    }\n"
}
```

**Code Requirements:**
- The code must be valid, executable Python
- Use standard library modules only (`pathlib`, `json`)
- MUST use `body.file_system` for file operations (read/save/exists)
- Handle all edge cases (missing files, permission errors, etc.)
- Return the exact dictionary structure specified
- Handle JSON string input for `file_mapping`

**Error Handling:**
- Wrap each file operation in try/except
- Continue processing remaining files if one fails
- Provide descriptive error messages
- Handle invalid JSON input

Return only the JSON object with `analysis` and `answer` fields. The `answer` field must contain the complete Python code as a string.
