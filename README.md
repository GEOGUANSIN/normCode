# NormCode

A tool that translates instructive natural language into structured text, revealing the underlying instruction patterns and structure.

## Overview

NormCode takes natural language instructions as input and transforms them into a specific style of text that makes the instruction structure explicit and clear. This helps in understanding, analyzing, and processing instructional content.

## Terminology

NormCode operates on **concepts** - the fundamental units that represent what the system translates. Each concept has three essential components:

- **Representation**: The name or label of the concept (e.g., "concept")
- **Sense**: The explanation or meaning of the concept
- **Reference**: What the concept refers to in the real world or context

### Concepts and Beings

What concepts refer to are called **"beings"** - they have a direct and tight link with the world, enabling perceptual and actuated interaction with what is linked under the representation of the being. Beings are meant to be unique and only exist here for the sake of explicating the concepts' reference. However, in usual use of language, everything we say is conceptual and we cannot directly refer to beings without concepts.

These concepts fall into three semantic categories:

- **Objects**: Concepts with references that represent entities, things, or defined elements
- **Judgements**: Concepts that represent conditional relationships, decisions, or evaluative statements  
- **Imperatives**: Concepts that represent actions, processes, or procedural instructions

These three concept types form the foundation of how NormCode structures and processes instructive text, allowing for systematic analysis and translation of natural language instructions.


### Syntactical Concepts and Linguistic Actions

There are also **syntactical concepts** whose references are linguistic actions. These linguistic actions fall into four types:

- **Assignment**: Deals with assignment of references among concepts
  - Identity ($=), specification ($.), nominalization ($::)
  - Questions ($_..._?) for querying assignments
- **Sequence**: Deals with sequencing of actions such as imperatives and judgements
- **Group**: Creates relations among references
- **Quantification**: Makes relations workable

These four linguistic action types provide the structural framework for how concepts are organized and related within the NormCode system.

## Core Concepts and Syntax

### Semantic Concepts

**1. Objects** `*{_…_}*`
- `{*_object_*}` - Object with references (concrete instances)
- `{*_placeholder_*}?` - Placeholder without references (empty tensor with axes)
- `*[{_concept1_}, …, {_conceptn_}]*` - Relation object (combines multiple concepts)
- `*_subject_(::)` - Subject specification for judgements and imperatives

**2. Judgements** `*<_…_>*`
- `*<_completeStatement_>*` - Predicate without arguments
- `*_S_.<_statement[{_arg1_},…, {_argn_}]_>*` - Judgement with arguments

**3. Imperatives** `*::(_…_)*`
- `*:_S_:(_completeImperative_)*` - Independent imperative without arguments
- `*:_S_:(_completeImperative[{_arg1_},…, {_argn_}]_)*` - Dependent imperative with arguments

### Syntactic Concepts

**4. Assignment** `*$*`
- `$=` - Identity (equates concepts by sharing references)
- `$.` - Specification (runs imperative to specify a reference)
- `$::` - Nominalization (encloses imperative as object)
- `$*_questMarker_*?(*_questTarget_*, *_questCondition_*)` - Questions (What/How/When)

**5. Sequencing** `*@_sequenceMarker_*`
- **Judgement Sequencing**: `@If`, `@OnlyIf`, `@IfOnlyIf`
- **Imperative Sequencing**: `@after`, `@by`, `@before`, `@with`
- **Object Looping**: `@while`, `@afterstep`, `@until`

**6. Grouping** `&**_*groupMarker_*`
- `&in` - View preserving grouping
- `&across` - View dissolving grouping
- `&set` - Intra-combination
- `&pair` - Inter-combination

**7. Quantification** `****_quantifyMarker_*`
- `*every` - Universal quantification
- `*some` - Existential quantification
- `*count` - Cardinal quantification


## Purpose

NormCode processes instructive text (referred to as "norm-text") through a systematic translation process. The first step in this process is **"Norm-text deconstruction by question sequencing"**.

### Norm-text Deconstruction by Question Sequencing

This initial step involves breaking down the instructive text into a sequence of questions that reveal the underlying structure and intent of the instructions.

#### Algorithmic Process

The deconstruction follows this systematic approach:

1. **Read the norm-text and establish a main question**
   - The main question must be one of: "what", "how", or "when"
   - This establishes the primary focus of the instruction

2. **Find all sentence chunks related to this main question**
   - Identify and group sentences that address the main question
   - Extract relevant content segments

3. **Generate ensuing questions for each sentence**
   - Create follow-up questions that build upon the main question
   - Questions should reference elements introduced by previous questions

4. **Translate each question into NormCode format**
   - Apply specific translation rules based on question type

#### Question Translation Rules

The translation process follows these steps:

**Step 1: Determine the main question target**
- Identify the most important concern of the text as a whole
- Can be: an object to be defined, a process to explain, or a main judgement

**Step 2: Determine the question condition**
- Use "what" if the question condition is **assignment** (including identity $=, specification $., norminalization $::), which means that the question target is to define or establish something
  - **$= (Identity)**: Establishes what something is or identifies an entity
  - **$. (Specification)**: Provides detailed characteristics or properties of an entity
  - **$:: (Nominalization)**: Converts actions or processes into named concepts or entities
- Use "how" if the question condition is **imperative sequence** (including imperative replacement @by, imperative future @after, imperative past @before, imperative current @with)
  - **@by (Imperative replacement)**: Specifies the method or means to accomplish something
  - **@after (Imperative future)**: Indicates what should happen following a certain action or condition
  - **@before (Imperative past)**: Specifies prerequisites or what must be done prior to an action
  - **@with (Imperative current)**: Describes concurrent actions or accompanying conditions
- Use "when" if the question condition is **judgement sequence** (including judgement antecedent @if, judgement consequence @onlyIf, judgement replacement @ifOnlyIf) or **"object looping"**.
  - **@if (Judgement antecedent)**: Establishes a conditional relationship where an action depends on a specific condition
  - **@onlyIf (Judgement consequence)**: Specifies that an action is permitted or valid only under certain conditions
  - **@ifOnlyIf (Judgement replacement)**: Creates a bidirectional conditional relationship where both conditions are equivalent
  - **@while (Object loop while)**: Loops while a condition is true (loop while there are elements to process)
  - **@until (Object loop until)**: Loops until a judgement is reached (loop until a specific condition is met)
  - **@afterstep (Object loop after step)**: Performs an action after each step of the loop (does something after each iteration)

**Step 3: Build question hierarchy**
- Questions should build on top of previous ones
- Each question should reference elements introduced by preceding questions
- Maintain logical flow and dependency relationships

This deconstruction step serves as the foundation for the subsequent translation phases, ensuring that all instructional elements are properly identified and structured before being transformed into the final output format.

## Getting Started

*[Development in progress]*

## Features



## Usage

*[Coming soon]*

## Contributing

*[Guidelines to be added]*

## License

*[To be determined]* 