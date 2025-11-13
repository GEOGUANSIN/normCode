# In-Question Analysis Agent

## Overview

The In-Question Analysis Agent is a Phase 2 agent that transforms question-answer pairs into formal NormCode structures using a three-phase algorithm.

## Three Phases

### Phase 1: Question Analysis
- **Input**: Formal question like `"$what?({step_2}, $::)"`
- **Process**: Parse question marker, target, and condition
- **Output**: Basic NormCode inference ground

### Phase 2: Clause Analysis  
- **Input**: Natural language answer + Phase 1 draft
- **Process**: Analyze sentence structure and translate clauses into NormCode syntax
- **Output**: Clause-analyzed NormCode draft with logical operators

### Phase 3: Template Creation
- **Input**: Phase 2 draft
- **Process**: Create abstract templates with typed placeholders
- **Output**: Complete NormCode structure with templates and references

## Usage

```python
from translate_agent.phase_agent.in_question_analysis_agent import InQuestionAnalysisAgent

# Create agent
agent = InQuestionAnalysisAgent(verbose=True)

# Analyze question-answer pair
question = "$what?({step_2}, $::)"
answer = "Mix the ingredients together"

result = agent.analyze(question, answer, prompt_context)

# Access results
print(f"Phase 1: {result.phase1_draft.content}")
print(f"Phase 2: {result.phase2_draft.content}") 
print(f"Phase 3: {result.phase3_draft.content}")
```

## Example Workflow

**Input**: `"$what?({step_2}, $::)"` + `"Mix the ingredients together"`

**Phase 1**: `{step_2} <= $::`

**Phase 2**: `{step_2} <= $:: <- ::(mix the ingredients together)`

**Phase 3**: `{step_2} <= $:: <- ::(mix {1}<$({ingredients})%_> together) <- {ingredients}<:{1}>`

## Key Features

- Incremental three-phase processing
- Preservation of logical structure
- Template abstraction with references
- Robust error handling
- Verbose logging support
- File/database result storage

## Testing

Run: `python translate_agent/tests/test_in_question_analysis.py` 