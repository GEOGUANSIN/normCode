# Provisions for Formalization Phase

This directory contains all resources required to execute the NormCode Formalization plan.

## Directory Structure

```
provisions/
├── data/                    # Input data files
│   └── refinement_questions.txt
├── paradigms/               # Paradigm definitions (JSON)
│   ├── h_LiteralPath-c_ReadFile-o_Literal.json
│   ├── h_LiteralPath-c_ReadFileIfExists-o_Literal.json
│   ├── h_LiteralPath-h_Literal-c_WriteFile-o_Literal.json
│   ├── v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Boolean.json
│   ├── v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal.json
│   ├── v_ScriptLocation-h_Literal-c_Execute-o_Boolean.json
│   └── v_ScriptLocation-h_Literal-c_Execute-o_Literal.json
├── prompts/                 # LLM prompt templates
│   └── formalization/       # Formalization phase prompts
│       ├── judge_concept_type.md
│       ├── formalize_object.md
│       ├── formalize_relation.md
│       ├── formalize_proposition.md
│       ├── formalize_imperative.md
│       ├── formalize_judgement.md
│       ├── formalize_assigning.md
│       ├── formalize_grouping.md
│       ├── formalize_timing.md
│       └── formalize_looping.md
├── scripts/                 # Python scripts
│   ├── pass_through.py
│   ├── ncds_parser.py
│   ├── filter_concepts.py
│   ├── check_type.py
│   └── append_line.py
└── path_mapping.json        # Resource path mappings
```

## Paradigm Reference

### LLM Paradigms
| Paradigm | Purpose |
|----------|---------|
| `v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal` | Generate structured JSON output from prompt + data |
| `v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Boolean` | Generate boolean judgement from prompt + data |

### File System Paradigms
| Paradigm | Purpose |
|----------|---------|
| `h_LiteralPath-c_ReadFile-o_Literal` | Read file content as string |
| `h_LiteralPath-c_ReadFileIfExists-o_Literal` | Read file if exists, else return empty |
| `h_LiteralPath-h_Literal-c_WriteFile-o_Literal` | Write string content to file |

### Python Interpreter Paradigms
| Paradigm | Purpose |
|----------|---------|
| `v_ScriptLocation-h_Literal-c_Execute-o_Literal` | Execute Python script, return any value |
| `v_ScriptLocation-h_Literal-c_Execute-o_Boolean` | Execute Python script, return boolean |

## Script Reference

### Formalization Scripts

| Script | Function | Purpose |
|--------|----------|---------|
| `pass_through.py` | `main(input_1)` | Identity function, returns input unchanged |
| `ncds_parser.py` | `main(input_1)` | Parse .ncds content into structured JSON list |
| `filter_concepts.py` | `main(input_1)` | Filter out comments, keep only concept lines |
| `check_type.py` | `main(input_1, input_2)` | Check if concept type equals expected type |
| `append_line.py` | `main(input_1, input_2)` | Append formalized line to accumulating content |

## Prompt Reference

### Formalization Phase

| Prompt | Purpose |
|--------|---------|
| `judge_concept_type.md` | Determine concept type (object, relation, proposition, imperative, etc.) |
| `formalize_object.md` | Apply `{name}` object syntax with ref_axes/shape/element annotations |
| `formalize_relation.md` | Apply `[name]` relation syntax for collections |
| `formalize_proposition.md` | Apply `<name>` proposition syntax for truth values |
| `formalize_imperative.md` | Apply `::()` imperative syntax with paradigm annotations |
| `formalize_judgement.md` | Apply `::<{}>` judgement syntax with boolean paradigms |
| `formalize_assigning.md` | Apply `$` assigning operator syntax |
| `formalize_grouping.md` | Apply `&` grouping operator syntax |
| `formalize_timing.md` | Apply `@` timing operator syntax for conditional gates |
| `formalize_looping.md` | Apply `*` looping operator syntax for iteration |

## Formalization Flow

The formalization plan processes `.ncds` files line by line:

1. **Read .ncds file** → Get raw content
2. **Parse into JSON** → `ncds_parser.py` creates structured line list
3. **Filter comments** → `filter_concepts.py` keeps only concept lines
4. **For each line:**
   - Judge concept type using `judge_concept_type.md`
   - Branch to type-specific formalization prompt
   - Apply formalization rules
   - Append to output using `append_line.py`
5. **Write .ncd file** → Save formalized content

## The Demand/Supply Model

Per `provision_new_vision.md`:

| Phase | Role | What It Does |
|-------|------|--------------|
| **Post-Formalization** | **Demand** | Declares *what* resources are needed via annotations |
| **Activation** | **Supply** | Validates, resolves, and includes actual resources |

This provisions directory supplies all resources demanded by `formalization.pf.ncd`.
