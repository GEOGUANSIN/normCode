# Provisions for File-Based Derivation Plan

This directory contains all resources required to execute the derivation NormCode plan.

## Directory Structure

```
provisions/
├── data/                    # Input data files
│   └── refinement_questions.txt
├── paradigms/               # Paradigm definitions (JSON)
│   ├── file_system/         # File I/O paradigms
│   └── python_interpreter/  # Python execution paradigms
├── prompts/                 # LLM prompt templates
│   ├── phase_1/             # Refinement phase prompts
│   ├── phase_2/             # Extraction phase prompts
│   ├── phase_3/             # Classification phase prompts
│   ├── phase_4/             # Tree construction phase prompts
│   └── phase_5/             # Serialization phase prompts
└── scripts/                 # Python scripts for python_interpreter
```

## Paradigm Reference

### LLM Paradigms
| Paradigm | Purpose |
|----------|---------|
| `h_PromptTemplate-h_Data-c_GenerateThinkJson-o_Literal` | Generate structured JSON output from prompt + data |
| `h_PromptTemplate-h_Data-c_GenerateThinkJson-o_Boolean` | Generate boolean judgement from prompt + data |

### File System Paradigms
| Paradigm | Purpose |
|----------|---------|
| `h_FilePath-c_ReadFile-o_Literal` | Read file content as string |
| `h_FilePath-c_ReadFileIfExists-o_Literal` | Read file if exists, else return empty |
| `h_FilePath-c_ReadJsonFile-o_Struct` | Read and parse JSON file |
| `h_FilePath-h_Content-c_WriteFile-o_Literal` | Write string content to file |
| `h_FilePath-h_Data-c_WriteJsonFile-o_Literal` | Write data as JSON to file |
| `h_FilePath-h_Content-c_AppendFile-o_Literal` | Append content to file |

### Python Interpreter Paradigms
| Paradigm | Purpose |
|----------|---------|
| `h_Data-c_CheckPhaseComplete-o_Boolean` | Check if phase N is complete in progress string |
| `h_Data-c_ExtractField-o_Literal` | Extract specific field from dict |
| `h_Data-c_PassThrough-o_Literal` | Pass data through unchanged |

## Prompt Reference

### Phase 1: Refinement
- `judge_instruction_vagueness.md` - Determine if instruction needs refinement
- `apply_refinement_questions.md` - Apply 7 refinement questions to instruction
- `synthesize_refined_instruction.md` - Synthesize refined instruction from answers

### Phase 2: Extraction
- `extract_concepts.md` - Extract nouns/data entities from instruction
- `extract_operations.md` - Extract verbs/actions from instruction
- `extract_dependencies.md` - Identify what-needs-what relationships
- `extract_control_patterns.md` - Identify loops and conditions

### Phase 3: Classification
- `gather_operation_context.md` - Get context for operation classification
- `classify_operation.md` - Determine pattern type for each operation

### Phase 4: Tree Construction
- `identify_goal.md` - Identify the final output concept
- `construct_dependency_tree.md` - Build tree from classifications

### Phase 5: Serialization
- `serialize_tree_to_ncds.md` - Convert tree to .ncds text format

