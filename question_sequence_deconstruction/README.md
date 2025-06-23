# Norm-text Deconstruction by Question Sequencing

This directory contains the first step of the NormCode translation process: **Norm-text Deconstruction by Question Sequencing**. This step systematically breaks down instructive natural language text into a structured sequence of questions that reveal the underlying instruction patterns and intent.

## Overview

Question sequence deconstruction is the foundational step that transforms natural language instructions into a hierarchical question-answer structure. This process makes explicit the implicit structure of instructional text by identifying the main question and generating a sequence of sub-questions that build upon each other.

## Core Principles

### 1. Main Question Identification
Every norm-text has a primary focus that determines the main question type:
- **"What"** - For assignment conditions (identity, specification, nominalization)
- **"How"** - For imperative sequences (method, process, procedure)
- **"When"** - For judgement sequences (conditions, timing, loops)

### 2. Question Hierarchy Building
Questions should build logically upon previous ones:
- Each question references elements introduced by preceding questions
- Maintains logical flow and dependency relationships
- Creates a clear progression from general to specific

### 3. Question Condition Mapping
The translation process maps natural language patterns to specific NormCode conditions:

#### Assignment Conditions (`$`)
- **$= (Identity)**: Establishes what something is
- **$. (Specification)**: Provides detailed characteristics
- **$:: (Nominalization)**: Converts actions to named concepts

#### Imperative Sequences (`@`)
- **@by**: Specifies method or means
- **@after**: Indicates what follows
- **@before**: Specifies prerequisites
- **@with**: Describes concurrent actions

#### Judgement Sequences (`@`)
- **@if**: Establishes conditional relationships
- **@onlyIf**: Specifies restrictive conditions
- **@ifOnlyIf**: Creates bidirectional conditions

#### Object Looping (`@`)
- **@while**: Loops while condition is true
- **@until**: Loops until condition is met
- **@afterstep**: Actions after each iteration

## Process Steps

### Step 1: Read and Establish Main Question
1. Analyze the norm-text to identify the primary concern
2. Determine if the focus is on:
   - Defining/establishing something (use "what")
   - Explaining a process/method (use "how")
   - Describing conditions/timing (use "when")
3. Formulate the main question using the appropriate question type

### Step 2: Find Related Sentence Chunks
1. Identify all sentences that address the main question
2. Group related content segments
3. Extract relevant information for each chunk

### Step 3: Generate Ensuing Questions
1. Create follow-up questions for each sentence chunk
2. Ensure questions build upon previous ones
3. Reference elements introduced by preceding questions
4. Maintain logical progression

### Step 4: Translate to NormCode Format
1. Apply specific translation rules based on question type
2. Map natural language patterns to NormCode syntax
3. Create formal question representations

## Question Translation Rules

### Determining Question Target
- **Object**: Entity, thing, or defined element
- **Process**: Method, procedure, or action sequence
- **Judgement**: Conditional relationship or evaluation

### Determining Question Condition
- **"What"** → Assignment conditions (`$=`, `$.`, `$::`)
- **"How"** → Imperative sequences (`@by`, `@after`, `@before`, `@with`)
- **"When"** → Judgement sequences (`@if`, `@onlyIf`, `@ifOnlyIf`) or Object looping (`@while`, `@until`, `@afterstep`)

## Output Structure

The deconstruction process produces a structured output with:

```json
{
  "norm_text": "Original instructive text",
  "deconstruction": {
    "level_1": {
      "main_process": {
        "formal_question": "NormCode question format",
        "natural_question": "Natural language question",
        "natural_answer": "Direct answer from text"
      }
    }
  },
  "question_hierarchy": {
    "main_question": "Primary question",
    "sub_questions": ["List of sub-questions"]
  },
  "qa_hierarchy": {
    "main_qa": {
      "formal_question": "NormCode format",
      "natural_answer": "Answer text"
    },
    "sub_qa": ["List of question-answer pairs"]
  },
  "normcode_mapping": {
    "assignment": "$=",
    "imperative_sequence": "@by",
    "judgement_sequence": "@if"
  }
}
```

## Examples

This directory contains several example files demonstrating the deconstruction process:

### Basic Examples (`Example_question.md`)
- **User Account Creation**: Demonstrates imperative-focused deconstruction
- **Butterfly Lifecycle**: Shows object/identity-focused deconstruction
- **Chocolate Chip Cookie Recipe**: Illustrates process-focused deconstruction

### Complex Examples (`complex_example_question/`)
- **Addition Algorithm** (`addition_example_question.md`): Multi-level deconstruction of algorithmic instructions
- **Stereotype Example** (`stereotype_example.md`): Complex conceptual deconstruction

## Usage Guidelines

### For Simple Instructions
1. Identify the main action or definition
2. Generate 2-3 sub-questions that build logically
3. Map to appropriate NormCode conditions

### For Complex Algorithms
1. Break down into hierarchical levels
2. Handle loops and conditional structures separately
3. Create detailed step-by-step deconstruction

### For Conceptual Definitions
1. Focus on identity establishment
2. Build from basic definition to detailed characteristics
3. Include conditional relationships

## Best Practices

1. **Maintain Logical Flow**: Each question should naturally follow from previous ones
2. **Reference Previous Elements**: Use elements introduced in earlier questions
3. **Be Specific**: Avoid vague questions; target specific aspects of the text
4. **Consistent Terminology**: Use consistent naming for concepts across questions
5. **Complete Coverage**: Ensure all important aspects of the text are addressed

## Common Patterns

### Imperative Instructions
- Main question: "How to do?"
- Sub-questions: Method specification, consequence identification
- NormCode mapping: `@by`, `@onlyIf`

### Object Definitions
- Main question: "What is [object]?"
- Sub-questions: Identity establishment, characteristic specification
- NormCode mapping: `$=`, `$.`

### Process Descriptions
- Main question: "What are the steps?"
- Sub-questions: Step identification, step details, sequencing
- NormCode mapping: `$=`, `$::`, `@after`

## Next Steps

After completing question sequence deconstruction, the structured output serves as input for the next phase of NormCode translation, where the question-answer pairs are transformed into formal NormCode representations.

## Related Documentation

- Main README: Overview of the complete NormCode system
- NormCode Syntax: Detailed syntax and semantic rules
- Translation Process: Complete translation pipeline documentation 