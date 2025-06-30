# Prompt Files Organization

## Naming Convention

### Question Sequencing Agent (Phase 1)
- `ntd_1_establishing_main_question.txt` - Establish main question from input text
- `ntd_2_sentence_chunking.txt` - Split text into sentence chunks  
- `ntd_3_chunk_question_generation.txt` - Generate ensuing questions for each chunk

### In-Question Analysis Agent (Phase 2)
- `iqa_1_question_structure_analysis.txt` - Phase 1: Parse formal question structure
- `iqa_2_clause_analysis.txt` - Phase 2a: Analyze sentence structure and clauses
- `iqa_2b_phase2_draft_creation.txt` - Phase 2b: Create draft with clause structure
- `iqa_3_template_creation.txt` - Phase 3: Create templates with placeholders

### General Prompts
- `normcode_context.txt` - General NormCode terminology and context
- `direct_prompt.txt` - Direct prompt template

## Sequence Flow

### Question Sequencing Agent
```
ntd_1 → ntd_2 → ntd_3
```

### In-Question Analysis Agent  
```
iqa_1 → iqa_2 → iqa_2b → iqa_3
```

## Agent Types

- **question_sequencing**: Uses ntd_* prompts
- **in_question_analysis**: Uses iqa_* prompts  
- **general**: Uses normcode_context and direct_prompt 