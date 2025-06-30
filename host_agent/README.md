# Norm-based Plan in Concepts (NPC)

## Core Rationale

AI Foundation models have shown immense capability at generating coherent langauge but often **lack controlled, consistent alignment with norms** to unlock their full potential in applications. To address this, the NPC system explicitly separates and enforces two components:

1. **Norms**: Definitions, criteria, and rules that govern how tasks should be performed (e.g., "A medical diagnosis must prioritize patient safety over speed").
2. **Task Settings**: Specific scenarios processed under these norms (e.g., "Analyze this patient's symptoms").

Currently, there does not exist dedicated methods to enforce norms. Traditional methods—such as prompt engineering (Chain-of-Thought, RAG, etc.) and fine-tuning (SFT, Knowledge Editing, RL, etc.)—can incorporate norms to some extent but face key limitations:

Prompt Engineering:
- Lacks robust enforcement mechanisms.
- Norms can be misinterpreted or ignored.
- Norms can not compound coherently and organically as complexity increases.

Fine-tuning:
- Requires high-quality examples of good application of norms.
- Creates bootstrapping challenges for generating suitable training data.
- Nuances and interpretability can be lost in purely example-based learning.

The NPC system addresses these limitations by priorityzing norms as a strict plan above the step by step generation of the foundation models.

The system draws inspiration from how humans use concepts in inference. Concepts can have different references (e.g., many individuals may be referred to as "persons") across scenarios, but their structural relationships remain consistent. In other words, norms define the conceptual structure, while task execution involves assigning specific references to these concepts and inferring outcomes within the same structure. NPC formalizes and operationalizes this conceptual structure.

NPC operates in two phases:

1. **Conceptualization Phase**: This phase involves constructing the NPC. Experts/Users and AIs collaboratively define concepts and their relationships to represent the desired norms. This is achieved by parsing natural language inputs into a graphical interface and refining the structure of NPC through iterative adjustments.

2. **Reference Inference Phase**: This phase executes the NPC. The input and the output settings are configured via the interface, and when initial constant references (e.g., foundational concepts) and variable input references (e.g., task-specific data) are established, the desired references are inferred step-by-step through the NPC.

There are several benefits of doing this: 
1. Explicit Norm Encoding: Norms are structurally enforced, increasing robustness and verifiability.
2.Dynamic Adaptability: Norm graphs can be updated without retraining (e.g., adding new regulations).
3. Collaborative Governance: Combines expert domain knowledge with AI scalability.


## Architecture 





## Core Components

The NPC system consists of **four core components** that work together as the backbone ontology of NPC. These components include concepts, references, inferences, and working memory that form the foundation of the system's architecture. Each component plays a specific role in translating norms into executable plans and managing the flow of information through the system.


### 1. Concepts
- Fundamental building blocks of the NPC system
- Represent different types of conceptual entities in the system
- Can be configured in two key roles:
  - **Cognition Concepts**: Drive output generation and actions
  - **Perception Concepts**: Handle input processing with memory assistance
- Stored and managed by working memory
- Example:
```python
# Concept creation
plan.add_concept(
    name="task",
    type=CONCEPT_TYPE_OBJECT,
    context="specific task description"
)
```

### 2. References
- Tensor-like data structures that organize and store concept instances
- Key features:
  - Multi-dimensional structure with named axes
  - Organizes instances across different cases
  - Maintains state and relationships between concept executions
- Example:
```python
# Reference creation
task_ref = Reference(
    axes=["task", "case"],
    shape=(1, 1),
)

task_ref.tensor = ...
```

### 3. Inferences
- Define and manage relationships between concepts
- Two primary functions:
  - **Perception**: Processes input concepts with memory context
  - **Cognition**: Determines how output concepts are generated
- Enable the system to make logical connections between concepts
- Example:
```python
# Inference creation
plan.add_inference(
    concept_to_infer=output_concept,
    perception_concepts=[input_concept1, input_concept2],
    cognition_concept=action_concept
)
```

### 4. Plan
- The final executable object of NPC 
- Combined concepts and inferences organically
- Manages:
  - Concept definitions 
  - Inference definition
  - The topological order of the Inference and the step by step execution of the inference.
  - execution with agent frame. 


## 