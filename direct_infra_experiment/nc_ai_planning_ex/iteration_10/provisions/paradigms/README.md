# Paradigm Definitions

Paradigms are declarative JSON specifications that define how operations execute.

## Naming Convention

```
[inputs]-[composition]-[outputs].json

Prefixes:
  h_ = horizontal input (runtime value)
  v_ = vertical input (setup metadata)
  c_ = composition steps
  o_ = output format
```

## Paradigms Used in This Plan

### LLM Paradigms
- `h_PromptTemplate-h_Data-c_GenerateThinkJson-o_Literal.json`
- `h_PromptTemplate-h_Data-c_GenerateThinkJson-o_Boolean.json`

### File System Paradigms
- `h_FilePath-c_ReadFile-o_Literal.json`
- `h_FilePath-c_ReadFileIfExists-o_Literal.json`
- `h_FilePath-c_ReadJsonFile-o_Struct.json`
- `h_FilePath-h_Content-c_WriteFile-o_Literal.json`
- `h_FilePath-h_Data-c_WriteJsonFile-o_Literal.json`
- `h_FilePath-h_Content-c_AppendFile-o_Literal.json`

### Python Interpreter Paradigms
- `h_Data-c_CheckPhaseComplete-o_Boolean.json`
- `h_Data-c_ExtractField-o_Literal.json`
- `h_Data-c_PassThrough-o_Literal.json`

## Directory Structure

```
paradigms/
├── llm/
│   ├── h_PromptTemplate-h_Data-c_GenerateThinkJson-o_Literal.json
│   └── h_PromptTemplate-h_Data-c_GenerateThinkJson-o_Boolean.json
├── file_system/
│   ├── h_FilePath-c_ReadFile-o_Literal.json
│   ├── h_FilePath-c_ReadFileIfExists-o_Literal.json
│   ├── h_FilePath-c_ReadJsonFile-o_Struct.json
│   ├── h_FilePath-h_Content-c_WriteFile-o_Literal.json
│   ├── h_FilePath-h_Data-c_WriteJsonFile-o_Literal.json
│   └── h_FilePath-h_Content-c_AppendFile-o_Literal.json
└── python_interpreter/
    ├── h_Data-c_CheckPhaseComplete-o_Boolean.json
    ├── h_Data-c_ExtractField-o_Literal.json
    └── h_Data-c_PassThrough-o_Literal.json
```

