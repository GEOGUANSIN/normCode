# Understanding CLI orchestrator context
_Exported on 12/3/2025 at 16:58:20 GMT+8 from Cursor (2.1.32)_

---

**User**

understand how @cli_orchestrator.py @CLI_GUIDE.md  in context of @infra/_agent/_models/_paradigms/README.md @infra/_agent/_steps/imperative_in_composition/README.md @infra/_agent/_body.py @infra/_orchest/_orchestrator.py 

---

**Cursor**

I'll explain how these components work together to form a complete NormCode orchestration system.

## Architecture Overview

The system has several layers that work together:

```
CLI (cli_orchestrator.py)
    ↓ creates
Orchestrator (infra/_orchest/_orchestrator.py)
    ↓ uses
Body (infra/_agent/_body.py) + AgentFrame
    ↓ executes inferences via sequences
imperative_in_composition sequence
    ↓ loads and runs
Paradigms (declarative JSON workflows)
    ↓ uses tools from
Body (back to the tools)
```

## Key Components

### 1. **CLI Orchestrator** (`cli_orchestrator.py`)

This is the **entry point** for command-line users. It provides:

- **Commands**: `run`, `resume`, `fork`, `list-runs`, `list-checkpoints`, `export`
- **Workflow**: Loads JSON repositories → Creates Body → Creates Orchestrator → Executes

```python
# From cli_orchestrator.py lines 176-193
body = Body(llm_name=args.llm, base_dir=base_dir, new_user_input_tool=True)
orchestrator = Orchestrator(
    concept_repo=concept_repo,
    inference_repo=inference_repo,
    body=body,
    max_cycles=args.max_cycles,
    db_path=db_path,
    run_id=args.new_run_id
)
final_concepts = orchestrator.run()
```

### 2. **Body** (`infra/_agent/_body.py`)

The **toolbox** that provides capabilities to agents. It initializes:

- **`llm`**: Language model for generation
- **`file_system`**: File read/write operations
- **`python_interpreter`**: Execute Python code
- **`formatter_tool`**: Template string substitution
- **`composition_tool`**: Compose complex functions
- **`user_input`**: Interactive user prompts
- **`prompt_tool`**: Prompt management
- **`buffer`** and **`fn`**: Utility tools

```python
# From _body.py lines 13-14
class Body:
    def __init__(self, llm_name: str = "qwen-turbo-latest", 
                 base_dir: str | None = None, 
                 new_user_input_tool: bool = True) -> None:
        self.base_dir = base_dir
        self.prompt_tool = PromptTool(base_dir=base_dir)
        self.llm = _LM(llm_name)
        self.file_system = FileSystemTool(base_dir=base_dir)
        # ... etc
```

**Key insight**: The `base_dir` parameter flows through Body to all tools, ensuring file operations are relative to a consistent root.

### 3. **Orchestrator** (`infra/_orchest/_orchestrator.py`)

The **execution engine** that:

- Manages a waitlist of inferences
- Checks dependencies (function concepts, value concepts, supporting items)
- Executes inferences in proper order using **AgentFrame**
- Handles checkpointing and state management
- Supports resume/fork operations

```python
# From _orchestrator.py lines 335-347
def _execute_agent_frame(self, item: WaitlistItem, inference: Inference) -> BaseStates:
    working_interpretation = item.inference_entry.working_interpretation or {}
    working_interpretation["blackboard"] = self.blackboard
    working_interpretation["workspace"] = self.workspace
    
    agent_frame = AgentFrame(
        self.agent_frame_model,
        working_interpretation=working_interpretation,
        body=self.body  # <-- Body is passed here
    )
    agent_frame.configure(inference, item.inference_entry.inference_sequence)
    return inference.execute()
```

### 4. **Paradigms** (Declarative Workflows)

**Reusable JSON-defined multi-step operations** that specify:

- **`env_spec`**: Which tools are needed (e.g., `llm`, `file_system`, `formatter_tool`)
- **`sequence_spec`**: How to gather tool functions
- **`plan`**: The data flow - how output of one tool becomes input to the next

Example paradigm name: `h_PromptTemplate_SavePath-c_GenerateThinkJson-Extract-Save-o_FileLocation.json`

This paradigm:
- **Inputs** (h_): PromptTemplate, SavePath
- **Composition** (c_): Generate→Think→ExtractJSON→Save
- **Output** (o_): FileLocation

### 5. **imperative_in_composition Sequence**

A **paradigm executor** with steps:

1. **IWI** (Planner): Reads `working_interpretation` to get paradigm name, loads its spec
2. **IR**: Gathers input references
3. **MFP** (Composer): Executes `sequence_spec` to create a composed function from the paradigm's plan
4. **MVP** (Data Preprocessor): Prepares input data, processes wrappers like `%{file_location}(path)`
5. **TVA** (Executor): Calls the composed function with prepared data
6. **OR/OWI**: Returns results

## How They Work Together

### Example Flow: User runs CLI to generate and save a file

1. **CLI** (`run` command):
   ```bash
   python cli_orchestrator.py run \
     --concepts concepts.json \
     --inferences inferences.json \
     --llm qwen-plus
   ```

2. **CLI creates Body**:
   ```python
   body = Body(llm_name='qwen-plus', base_dir='./my_project')
   ```
   - Body initializes LLM, file_system with `base_dir`, etc.

3. **CLI creates Orchestrator**:
   ```python
   orchestrator = Orchestrator(
       concept_repo=concept_repo,
       inference_repo=inference_repo,
       body=body  # Tools available to all inferences
   )
   ```

4. **Orchestrator executes inferences**:
   - Checks if inference is ready (dependencies met)
   - Creates AgentFrame with Body
   - Executes inference

5. **Inference uses `imperative_in_composition` sequence**:
   - `working_interpretation` specifies:
     ```json
     {
       "paradigm": "h_PromptTemplate_SavePath-c_GenerateThinkJson-Extract-Save-o_FileLocation",
       "value_order": {
         "{my prompt}": 0,
         "{save path}": 1
       }
     }
     ```

6. **IWI step** loads paradigm JSON, finds it needs `llm`, `file_system`, `formatter_tool`

7. **MFP step** uses Body's `composition_tool` to create a composed function:
   ```python
   # Pseudo-code of what the composed function does:
   formatted_prompt = body.formatter_tool.format(template, inputs)
   llm_response = body.llm.generate(formatted_prompt)
   extracted = parse_json(llm_response)
   saved_path = body.file_system.save(extracted['answer'], save_path)
   return saved_path
   ```

8. **MVP step** prepares data:
   - Loads `%{prompt}id(prompt.txt)` → reads file content
   - Processes `%{save_path}id(output.txt)` → keeps path string

9. **TVA step** executes the composed function with prepared data

10. **Results** flow back to Orchestrator → updates concept references → continues to next inference

## CLI Resume/Fork Features

The CLI's **resume** and **fork** commands leverage Orchestrator's checkpointing:

### Resume (Continue same run):
```bash
python cli_orchestrator.py resume \
  --concepts concepts.json \
  --inferences inferences.json \
  --run-id abc123
```

- Loads checkpoint from `run-id: abc123`
- **PATCH mode** (default): Discards stale state, keeps valid state
- Continues execution with same run_id

### Fork (New run with checkpoint data):
```bash
python cli_orchestrator.py fork \
  --concepts NEW_concepts.json \
  --inferences NEW_inferences.json \
  --from-run abc123 \
  --new-run-id xyz789
```

- Loads state from `abc123`
- Applies to **different repository** (NEW_concepts.json)
- **OVERWRITE mode** (default): Trust checkpoint data
- Starts fresh execution history with `xyz789`

## Key Design Patterns

1. **Body as Shared Context**: All tools share same `base_dir`, enabling consistent file resolution

2. **Paradigms as Declarative Code**: Complex operations defined in JSON, executed by generic sequence

3. **Separation of Concerns**:
   - CLI: User interface
   - Orchestrator: Execution management
   - Body: Tool capabilities
   - Paradigms: Reusable workflows

4. **Checkpointing**: Enables pause/resume, forking between repositories, debugging

5. **Dependency Management**: Orchestrator ensures inferences run in correct order based on concept dependencies

This architecture allows users to define complex multi-step AI workflows declaratively (JSON) and execute them via simple CLI commands, with the system handling all the orchestration, state management, and tool coordination automatically.

```plaintext
CLI (cli_orchestrator.py)
    ↓ creates
Orchestrator (infra/_orchest/_orchestrator.py)
    ↓ uses
Body (infra/_agent/_body.py) + AgentFrame
    ↓ executes inferences via sequences
imperative_in_composition sequence
    ↓ loads and runs
Paradigms (declarative JSON workflows)
    ↓ uses tools from
Body (back to the tools)
```

```python
# From cli_orchestrator.py lines 176-193
body = Body(llm_name=args.llm, base_dir=base_dir, new_user_input_tool=True)
orchestrator = Orchestrator(
    concept_repo=concept_repo,
    inference_repo=inference_repo,
    body=body,
    max_cycles=args.max_cycles,
    db_path=db_path,
    run_id=args.new_run_id
)
final_concepts = orchestrator.run()
```

```python
# From _body.py lines 13-14
class Body:
    def __init__(self, llm_name: str = "qwen-turbo-latest", 
                 base_dir: str | None = None, 
                 new_user_input_tool: bool = True) -> None:
        self.base_dir = base_dir
        self.prompt_tool = PromptTool(base_dir=base_dir)
        self.llm = _LM(llm_name)
        self.file_system = FileSystemTool(base_dir=base_dir)
        # ... etc
```

```python
# From _orchestrator.py lines 335-347
def _execute_agent_frame(self, item: WaitlistItem, inference: Inference) -> BaseStates:
    working_interpretation = item.inference_entry.working_interpretation or {}
    working_interpretation["blackboard"] = self.blackboard
    working_interpretation["workspace"] = self.workspace
    
    agent_frame = AgentFrame(
        self.agent_frame_model,
        working_interpretation=working_interpretation,
        body=self.body  # <-- Body is passed here
    )
    agent_frame.configure(inference, item.inference_entry.inference_sequence)
    return inference.execute()
```

```shellscript
   python cli_orchestrator.py run \
     --concepts concepts.json \
     --inferences inferences.json \
     --llm qwen-plus
```

```python
   body = Body(llm_name='qwen-plus', base_dir='./my_project')
```

```python
   orchestrator = Orchestrator(
       concept_repo=concept_repo,
       inference_repo=inference_repo,
       body=body  # Tools available to all inferences
   )
```

```json
     {
       "paradigm": "h_PromptTemplate_SavePath-c_GenerateThinkJson-Extract-Save-o_FileLocation",
       "value_order": {
         "{my prompt}": 0,
         "{save path}": 1
       }
     }
```

```python
   # Pseudo-code of what the composed function does:
   formatted_prompt = body.formatter_tool.format(template, inputs)
   llm_response = body.llm.generate(formatted_prompt)
   extracted = parse_json(llm_response)
   saved_path = body.file_system.save(extracted['answer'], save_path)
   return saved_path
```

```shellscript
python cli_orchestrator.py resume \
  --concepts concepts.json \
  --inferences inferences.json \
  --run-id abc123
```

```shellscript
python cli_orchestrator.py fork \
  --concepts NEW_concepts.json \
  --inferences NEW_inferences.json \
  --from-run abc123 \
  --new-run-id xyz789
```

