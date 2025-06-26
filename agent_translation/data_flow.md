# NormCode Agentic Translation: Data Flow

## Overview

This document outlines the data flow for the NormCode agentic translation process, showing how NormText is decomposed, analyzed in loops, and finally integrated into a unified structure.

## Data Flow Architecture

```
NormText Input
    ↓
Question Sequencing Agent
    ↓
[Question Decomposition]
    ↓
┌─────────────────────────────────────┐
│           LOOP START                │
│                                     │
│  Individual Question + Answer       │
│           ↓                         │
│  In-Question Analysis Agent         │
│           ↓                         │
│  Individual NormCode Structure      │
│                                     │
└─────────────────────────────────────┘
    ↓
[All Individual Structures Collected]
    ↓
NormCode Integration Agent
    ↓
Unified NormCode Structure
```

## Detailed Data Flow

### Phase 1: Input Processing
```
Input: NormText (Natural Language Instructions)
    ↓
Question Sequencing Agent
    ↓
Output: {
    "main_question": {
        "type": "what|how|when",
        "target": "main_process",
        "condition": "$=|@by|@if"
    },
    "ensuing_questions": [
        {
            "question": "$what?({chunk_1}, $=)",
            "answer": "concrete answer text",
            "chunk_index": 0
        },
        {
            "question": "$how?({chunk_2}, @by)", 
            "answer": "concrete answer text",
            "chunk_index": 1
        },
        ...
    ]
}
```

### Phase 2: Looped Analysis
```
For each question-answer pair in ensuing_questions:
    ↓
    Input: {
        "question": "$what?({chunk_1}, $=)",
        "answer": "concrete answer text"
    }
    ↓
    In-Question Analysis Agent
    ↓
    Output: {
        "normcode_structure": {
            "content": "NormCode syntax",
            "validation_status": "valid|invalid",
            "errors": []
        },
        "question_sequence": {...},
        "validation_report": {...}
    }
    ↓
    [Add to collection]
```

### Phase 3: Integration
```
Input: [
    NormCodeStructure_1,
    NormCodeStructure_2,
    NormCodeStructure_3,
    ...
]
    ↓
NormCode Integration Agent
    ↓
Output: {
    "integrated_structure": {
        "content": "Unified NormCode with hierarchical nesting",
        "relationships": [
            "agent-consequence mappings",
            "shared reference systems", 
            "semantic flow connections"
        ],
        "modular_components": [
            "individual structures preserved",
            "hierarchical relationships established"
        ]
    }
}
```

## Data Structures

### NormText Input
```python
class NormText:
    text: str                    # Raw natural language instructions
    context: Optional[Dict]      # Additional context information
    metadata: Optional[Dict]     # Processing metadata
```

### Question Decomposition
```python
class QuestionDecomposition:
    main_question: MainQuestion
    ensuing_questions: List[QuestionAnswerPair]
    decomposition_metadata: Dict
```

### Individual Analysis Result
```python
class IndividualAnalysisResult:
    question: str
    answer: str
    normcode_structure: NormCodeStructure
    validation_status: str
    processing_time: float
```

### Integration Result
```python
class IntegrationResult:
    unified_structure: NormCodeStructure
    component_mappings: Dict[str, str]
    hierarchical_relationships: List[Dict]
    shared_references: Dict[str, List[str]]
    integration_metadata: Dict
```

## Processing Loop Details

### Loop Configuration
```python
loop_config = {
    "max_iterations": len(ensuing_questions),
    "parallel_processing": False,  # Sequential for now
    "error_handling": "continue",  # Skip failed items
    "validation_required": True
}
```

### Loop Execution
```python
individual_results = []

for i, qa_pair in enumerate(question_decomposition.ensuing_questions):
    try:
        # Process individual question-answer pair
        result = in_question_agent.analyze(qa_pair)
        individual_results.append(result)
        
    except Exception as e:
        # Handle errors based on configuration
        if loop_config["error_handling"] == "stop":
            raise e
        else:
            # Log error and continue
            log_error(f"Failed to process question {i}: {e}")
            continue
```

## Integration Process

### Step 1: Structure Collection
```python
# Collect all successfully processed structures
valid_structures = [
    result.normcode_structure 
    for result in individual_results 
    if result.normcode_structure.validation_status == "valid"
]
```

### Step 2: Relationship Analysis
```python
# Analyze relationships between structures
relationships = integration_agent.analyze_relationships(valid_structures)

# Identify shared references
shared_refs = integration_agent.identify_shared_references(valid_structures)

# Map agent-consequence relationships
agent_consequences = integration_agent.map_agent_consequences(valid_structures)
```

### Step 3: Hierarchical Composition
```python
# Create hierarchical structure
hierarchical_structure = integration_agent.create_hierarchy(
    valid_structures,
    relationships,
    shared_refs,
    agent_consequences
)
```

### Step 4: Reference Unification
```python
# Unify reference systems
unified_structure = integration_agent.unify_references(hierarchical_structure)

# Validate integration
integration_validation = integration_agent.validate_integration(unified_structure)
```

## Error Handling and Recovery

### Loop-Level Errors
- **Individual question failure**: Skip and continue with remaining questions
- **Validation failure**: Mark structure as invalid but include in collection
- **Processing timeout**: Implement timeout handling for long-running analyses

### Integration-Level Errors
- **Reference conflicts**: Resolve by creating unique reference mappings
- **Structural incompatibilities**: Create adapter structures for compatibility
- **Validation failures**: Provide detailed error reports for manual review

## Performance Considerations

### Loop Optimization
- **Caching**: Cache common question patterns and analysis results
- **Parallel processing**: Enable parallel processing for independent questions
- **Batch processing**: Process questions in batches for efficiency

### Integration Optimization
- **Incremental integration**: Integrate structures incrementally rather than all at once
- **Reference optimization**: Optimize reference lookup and mapping
- **Memory management**: Efficient handling of large structure collections

## Output Validation

### Individual Structure Validation
- Syntax validation
- Logical consistency checking
- Reference integrity verification

### Integration Validation
- Hierarchical structure validation
- Cross-reference consistency
- Semantic flow verification
- Agent-consequence relationship validation

## Example Flow

### Input NormText
```
"Create a user account with email and password. The account gets admin privileges and active status."
```

### Decomposition
```
Main Question: "$what?({account_creation}, $::)"
Ensuing Questions:
1. "$what?({account}, $=)" → "user account with email and password"
2. "$what?({privileges}, $=)" → "admin privileges"  
3. "$what?({status}, $=)" → "active status"
```

### Looped Analysis
```
Loop 1: Process account definition → NormCodeStructure_1
Loop 2: Process privileges definition → NormCodeStructure_2  
Loop 3: Process status definition → NormCodeStructure_3
```

### Integration
```
Unified Structure: {
    "main_process": "account_creation",
    "components": [
        "account_definition",
        "privileges_assignment", 
        "status_assignment"
    ],
    "relationships": [
        "account → privileges",
        "account → status"
    ],
    "shared_references": {
        "account": ["account_definition", "privileges_assignment", "status_assignment"]
    }
}
``` 