# NormCode Guide - Agent's Sequences

Agent's sequences are the **operational realization** of inferences - they are the pre-defined pipelines that execute the actual logic when a functional concept invokes them. Each agent's sequence represents a specific pattern of processing steps that transform inputs into outputs.

When a functional concept is encountered in a NormCode script, it triggers the corresponding agent's sequence, which then executes a series of standardized processing steps to realize the inference's logic.

These sequences are categorized into **Semantic** and **Syntactic** types, mirroring the classification of the concepts that invoke them.

## 1. The NormCode Agent (:S:)

In NormCode, an **Agent** is represented by the **Subject Concept** (`:S:`). It is not just an abstract actor; it is a concrete container of capability.

*   **The Context of State**: When a functional concept executes, it does so *within* a specific Agent. The Agent's reference serves as the local environment, resolving which specific tools or seuqences are available to fulfill the inference.
*   **The Body of Execution**: The Agent acts as the "body" that performs the work. It holds the registry of available **Tools** (e.g., Python Execution Tool, API clients for LLMs call, ModelSequenceRunner, CompositionTool, FileSystemTool, UserInputTool, etc.) and **Sequences** (the logic pipelines described below).
*   **Role in Inference**: Every functional inference (like `({})` or `<{}>`) effectively says: "Subject X, according to your AgentFrame's understanding of the norm, use your tools to perform Operation Y on Values Z."

This separation allows for multi-agent planning where different Subjects (e.g., `:coder_agent:`, `:reviewer_agent:`) might possess different sets of tools and paradigms, even if they use similar NormCode structures.

### 1.1. The AgentFrame Implementation

In the codebase, the abstract Agent is realized by the `AgentFrame` class. This class serves as the factory and manager for the agent's capabilities.

*   **Initialization**: An `AgentFrame` is initialized with a specific `AgentFrameModel` (e.g., `"demo"`), which dictates which sequence variants are available to it, and how norms in functional concepts are interpreted.
*   **Configuration**: When an inference is ready to be executed, the `AgentFrame` configures the specific `Inference` instance with the appropriate sequence of methods (e.g., `configure_imperative_demo`).

### 1.2. Specifying AgentFrame and Body in NormCode
Customization is typically achieved by selecting a specific `AgentFrame` (or "mode of interpretation") along with a specific `Body` (a body of tools). 

In NormCode syntax, when invoking a semantic sequence, you can explicitly direct it to use a specific subject's capabilities (a body of tools) by using the `:_S_:` subject concept. In this case, the inference will be executed with the tools of Subject S.

If a specific **Body** is named (e.g., a reference to an input body concept like `>`, the input subject), you can indicate that the inference should use this body with a specific mode (like `composition`) using the syntax `%>(__)`.

*   **Syntax Example**: `:%>(composition):{paradigm}(__)`
    *   This tells the system: "Use the > Body (from reference/declaration/attribute of the AgentFrame) and interpret the sequences of the inference using the `composition` mode of AgentFrame."

## 2. Semantic Agent Sequences

Semantic sequences empowers an agent to perform the "thinking" and "acting" demanded by one inference. They typically stage the invocation of a Large Language Model (LLM) or an external tool to perform complex operations or evaluations. They follow a comprehensive **Perception-Actuation(-Assertion)** pattern of steps. These are the meat of the agent's reasoning and action.


### 2.1. Semantic Agent's Sequence Types

There are two types of semantic agent's sequences: **Imperative** and **Judgement**, corresponding to the two types of typically functional semantic concepts: **Imperative** and **Judgement**.

| Sequence Name | Steps (Default) | Functional Concepts | Purpose |
| :--- | :--- | :--- | :--- |
| **Imperative** | `(IWI-IR-MFP-MVP-TVA-OR-OWI)` | `({})` | Executes complex commands, operations, or calculations using a composition paradigm. |
| **Judgement** | `(IWI-IR-MFP-MVP-TVA-TIA-OR-OWI)` | `<{}>` | Evaluates conditions or propositions to return a boolean-like assessment using a composition paradigm. |


### 2.2. Modes of Agent's Sequence Interpretation

There are two distinct modes for executing semantic sequences. **Mode 1 (Composition) is currently the default and preferred mode** due to its flexibility and power.

#### Mode 1: Paradigm Composition (Composition Mode) [DEFAULT]
*   **Imperative Syntax**: `:%(composition):{paradigm}(functional_input: {value_placements})`
*   **Judgement Syntax**: `:%(composition):{paradigm}(functional_input: {value_placements}) <truth_assertion>`
*   **Description**: Invokes a composition tool or paradigm to handle the execution logic. This mode is highly flexible because the paradigm definition itself (stored as a declarative JSON structure) can internalize the complex "Perception" and "Actuation" logic.
*   **Step Pattern**: 7-step pipeline for imperative and 8-step pipeline for judgement. The steps are:
    ` (IWI-IR-MFP-MVP-TVA-OR-OWI) ` for imperative
    ` (IWI-IR-MFP-MVP-TVA-TIA-OR-OWI) ` for judgement
    *(TIA step for judgement, handling the truth assertion, which is the result of the assertion of the TVA reference against the truth assertion)*

#### Mode 2: Sequence Variant (Demo Mode) [DEPRECATED]
*   **Syntax**: `:%(demo):{sequence_variant}(functional_input: {value_placements})` for imperative and `:%(demo)(Truth Assertion):{sequence_variant}<functional_input: {value_placements}>` for judgement
    *   *Note: Explicitly used for legacy or simple direct tool calls.*
*   **Description**: Directly invokes a specific sequence variant (e.g., `imperative_direct`). The agent manages the full lifecycle of tool execution and result perception through explicit steps. Where two legacy finalization steps are used for the perception and actuation of the result. TIP (Tool Inference Perception): The agent perceives the raw output from the tool execution. MIA (Memory Inference Actuation): The agent structures the raw result back into the standard memory format (Reference/Tensor). This mode is deprecated and will be removed in the future.
*   **Pattern**: Full 9-step pipeline for both imperative and judgement.
    ` (IWI-IR-MFP-MVP-TVA-TIP-MIA-OR-OWI) `
        *(Mode 1 skips TIP and MIA steps for imperative, as these are assimilated into the customized paradigm; and the judgement's TIP's truth assertion is handled by the TIA step)*

For the following discussion, we will only focus on the Mode 1 (Composition) paradigm composition mode, which is the default and preferred mode.

### 2.3. The Semantic Steps: Perception & Actuation
The semantic pipeline is grounded in a cognitive cycle of **Perception** (understanding the norm and the values) and **Actuation** (implementing the tool logic).

#### I. Initialization
1.  **IWI (Input Working Interpretation)**: Parses the syntax and intent.
2.  **IR (Input Reference)**: Retrieves necessary data references.

#### II. Perception Phase
3.  **MFP (Model Function Perception)**: *Perception of the Function.*
    The agent executes the generation plan (determined in IWI) upon the functional reference (retrieved in IR). It uses a `ModelSequenceRunner` to process the instructions (typically using LLMs or foundation models configured by the paradigm), transforming the abstract functional instructions into a reference of executable functions (e.g., `instruction_fn`). This reference constitutes the "model" that will be applied to the values in the Actuation phase.
4.  **MVP (Memory Value Perception)**: *Perception of the Values.*
    The agent perceives the input value concepts and translates their abstract names into concrete, **interactable information** retrieved from memory, i.e. files, databases, and actual objects in the interaction.

#### III. Actuation Phase
5.  **TVA (Tool Value Actuation)**: *The Actual Implementation.*
    The agent applies the **tools** (as defined by the model from MFP) to the **memory** (as perceived in MVP). This is the core "action" step. This is set up by 'cross_action' the MFP reference and the MVP reference. The end result is a unified reference that is the result of acting the MFP on the MVP element by element.
    *   *In Mode 1 (Composition), this step invokes the paradigm which handles the rest of the execution internally.*

#### IV. Assertion Phase (Judgement Only)
6.  **TIA (Tool Inference Assertion)**: *Assertion of the Result.*
    The agent asserts the result of the TVA reference against the truth assertion, i.e. the quantifier and condition. The end result is a boolean-like value that is the result of the assertion, which will be used to control the flow of the plan.

#### V. Conclusion
7.  **OR (Output Reference)**: The final reference is created/updated. This is the result of the TVA or the TIA assertion.
8.  **OWI (Output Working Interpretation)**: Updates the execution state/logs.

### 2.4. Paradigms and their Role in the Semantic Sequences
Paradigms are declarative JSON specifications that define the "how" of an agent's execution. They bridge the gap between abstract intent and concrete code execution, allowing complex, multi-step workflows (like "prompt an LLM, extract code, execute it") to be defined as reusable components. Paradigms are the norms of the semantic sequences, which are the instructions for the agent to execute the inference.

The paradigm system is built on a distinction between **Vertical Steps** (Setup) and **Horizontal Steps** (Execution), which maps directly to the NormCode structure:

*   **Vertical Steps (MFP - "Handling the Functional Reference"):** Handled by the `ModelSequenceRunner` during the **MFP** phase. This phase resolves "Vertical Inputs" (typically from the `function` concept's name or metadata) and prepares the tools. It constructs the *executable function* that will be used later.
    *   *Example:* Resolving a prompt template from the functional concept definition.

*   **Horizontal Steps (TVA - "Handling the Memory Value Reference"):** Handled by the `CompositionTool`'s execution plan during the **TVA** phase. This phase manages the runtime flow of data, passing "Horizontal Inputs" (typically from the `value` concepts in **MVP**) through a sequence of operations.
    *   *Example:* Taking a specific file path (value) and passing it to the pre-configured function. The end result is a unified reference that is the result of acting the MFP on the MVP element by element.

**Naming Convention:**
Paradigms follow a strict naming convention `[inputs]-[composition]-[outputs].json` to self-document their behavior:
1.  **Inputs (`h_` or `v_`)**: Describes inputs, prefixed with `h_` (Horizontal/Runtime) or `v_` (Vertical/Composition-time).
2.  **Composition (`c_`)**: Describes the internal workflow sequence.
3.  **Outputs (`o_`)**: Describes the final output format.

*Example:* `h_PromptTemplate_SavePath-c_GenerateThinkJson-Extract-Save-o_FileLocation.json`

#### The Technical Grounds: ModelSequenceRunner & CompositionTool

The paradigm system is powered by two specialized engines that enforce the vertical/horizontal separation:

1.  **ModelSequenceRunner (The Vertical Engine)**: 
    Operates during the MFP phase. It is responsible for **resolving tool affordances** (like "llm.generate" or "file_system.read") into actual callable functions. It uses a `ModelEnv` to bind these tools to the current state, handling dependencies and initialization. It effectively "compiles" the abstract vertical steps of the paradigm into a set of ready-to-use function handles.

2.  **CompositionTool (The Horizontal Engine)**:
    Operates during the TVA phase (as the result of the final vertical step). It takes the **Execution Plan**—a list of steps referencing the functions prepared by the Runner—and compiles them into a single, cohesive Python function. This composed function manages the runtime data flow (`output_key` passing), conditional logic (branching execution), and parameter mapping, allowing the agent to execute complex logic purely through configuration.

### 2.5. Mathematical Formalization of the Paradigm
To formalize the distinction between vertical and horizontal phases, we can view the agent's operation as a composition of functions:

Let $\mathcal{S}$ be the Agent's State (context).
Let $\mathcal{P}$ be the Paradigm Definition, consisting of Vertical Specs ($V_{spec}$) and a Horizontal Plan ($H_{plan}$).

1.  **The Vertical Function ($F_V$) - MFP Phase**:
    This function maps the state and specs to a set of initialized tool handles ($\mathcal{T}$).
    $$ \mathcal{T} = F_V(\mathcal{S}, V_{spec}) $$
    *Implementation:* `ModelSequenceRunner.run()`

2.  **The Composition Function ($F_C$) - MFP Phase Conclusion**:
    This higher-order function compiles the tool handles and the plan into a single executable function ($\Phi$).
    $$ \Phi = F_C(\mathcal{T}, H_{plan}) $$
    *Implementation:* `CompositionTool.compose()`

3.  **The Horizontal Function ($F_H$) - TVA Phase**:
    The composed function is then applied to the runtime values ($\mathcal{V}$) derived from MVP to produce the final output ($\mathcal{O}$).
    $$ \mathcal{O} = \Phi(\mathcal{V}) $$
    *Implementation:* Execution of the `instruction_fn`.

**Total Operation**:
$$ \mathcal{O} = [F_C(F_V(\mathcal{S}, V_{spec}), H_{plan})](\mathcal{V}) $$

This cleanly separates the **Construction Time** (Vertical) from the **Runtime** (Horizontal).

---

## 3. Syntactic Agent Sequences

Syntactic sequences control the **structure, flow, and data management** of the plan. They manipulate the state, organize data, or control execution order, typically without requiring deep semantic reasoning from an LLM.

**Key Characteristics:**
*   **Subject-Agnostic**: Unlike semantic sequences, syntactic operations do not rely on a specific "Body" or Subject (`:S:`) to execute. They operate on the *container* of the data (the references and control flow), not the semantic content itself.
*   **Universality**: These sequences are typically invariant across different `AgentFrames`. An assignment or a loop functions identically regardless of which agent is performing the surrounding semantic tasks. Their key functionalities come from a `_syntax` module that is shared across all `AgentFrames`.
*   **Plan-Level Utility**: Their primary purpose is to enable the *plan* to function as a cohesive whole—transforming data's tensor structure, routing data flow, managing loops, and handling condition dependencies—rather than performing the individual "cognitive work" of an inference.

Here we introduce the seqeunces that are implemented in the `_syntax` module, or readily implemnented. These are a subset of the syntactic concepts that are used in the NormCode plan. During the compilation time, other concepts can always be reduced (despite verbosity) to these implemented ones, hence they are the core of the syntactic sequences.

### 3.1. Data Flow
These sequences manage the flow of data references, variable assignments, and state updates.

| Sequence Name | Steps (Default) | Associated Concepts | Purpose |
| :--- | :--- | :--- | :--- |
| **Simple** | `(IWI-IR-OR-OWI)` | N/A (Testing) | A minimal sequence for basic data pass-through or testing purposes. |
| **Assigning** | `(IWI-IR-AR-OR-OWI)` | `$.`, `$+`, `$-` (about to implement - as derelation) | Manages variable assignments, state updates, and specifications. |

#### Implementation Details (Assigning)
The `Assigning` sequence delegates its logic to the `Assigner` class in the `_syntax` module during the **AR** step.
*   **Specification (`$.`)**: Uses `Assigner.specification`. It takes a prioritized list of source references (candidates) and assigns the first valid (non-empty) one to the destination. If no source is valid, it falls back to the destination reference itself. This allows for selection of a concept of output from a list of candidates.
*   **Continuation (`$+`)**: Uses `Assigner.continuation`. It appends the source reference to the destination reference along a specified axis (`by_axes`). This is used for accumulating results, often in loops.
*   **Derelation (`$-`)**: *(Planned)* Will use `Assigner.derelation` to perform pure structural selection (by index or key) without invoking semantic perception. This is particularly useful when a concept has elements that are structured as a list or dictionary (after grouping), and we want to select a specific element from it. *(Note: at the moment it is integrated into the MVP step, which will be deprecated in the future.)*

### 3.2. Data Re-Structuring
These sequences handle the organization of data into collections or iterations.

| Sequence Name | Steps (Default) | Associated Concepts | Purpose |
| :--- | :--- | :--- | :--- |
| **Grouping** | `(IWI-IR-GR-OR-OWI)` | `&in`, `&across` | Collects, filters, and groups disparate data items into collections or relations. |

#### Implementation Details (Grouping)
The `Grouping` sequence logic is centrally handled by the `Grouper` class in the `_syntax` module during the **GR** step. It heavily relies on **Context Concepts** (`<*`) to determine the axes of aggregation.
*   **And-In (`&in`)**: Uses `Grouper.and_in`. It aligns multiple input references by their shared axes and performs a cross-product to combine elements. Crucially, it creates a **Relation** (a dictionary-like structure) where elements are annotated with their source concept names. It aggregates (slices) the result along axes specified by the *context concepts* present in the inference state.
*   **Or-Across (`&across`)**: Uses `Grouper.or_across`. Similar to `&in`, it aligns and cross-products inputs, but it produces a **Collection** (a flat list) by flattening the result. It also uses context concepts to determine the `by_axes` for aggregation.

### 3.3. Control Flow
These sequences control the execution order or branching logic of the plan, rather than manipulating the data itself.

| Sequence Name | Steps (Default) | Associated Concepts | Purpose |
| :--- | :--- | :--- | :--- |
| **Timing** | `(IWI-T-OWI)` | `@if`, `@if!`, `@after` | Controls conditional execution (branching) and dependency management (sequencing). |

#### Implementation Details (Timing)
The `Timing` sequence logic is handled by the `Timer` class in the `_syntax` module during the **T** step. Unlike other sequences, it strictly relies on the **Blackboard** to query the status of other concepts in the plan.
*   **Sequencing (`@after`)**: Uses `Timer.check_progress_condition`. It checks if the referenced condition (usually a concept's completion) is met. If satisfied, the inference is marked as ready to proceed. This is purely for ordering execution.
*   **Branching (`@if` / `@if!`)**: Uses `Timer.check_if_condition` or `check_if_not_condition`. These operators also enforce sequencing (they wait for the condition concept to be `complete`) but add a branching decision.
    *   **Readiness**: The step remains "not ready" until the condition concept is complete.
    *   **Skip Logic**: Once ready, the Timer evaluates the condition's result (success/failure or boolean value). If the condition is not met (for `@if`) or met (for `@if!`), the inference is marked to be **SKIPPED** (`states.to_be_skipped = True`), effectively bypassing its execution.

| **Looping** | `(IWI-IR-GR-LR-OR-OWI)` | `*every` | Manages iterative loops (`LR` step), handling state reset and accumulation across iterations. |

#### Implementation Details (Looping)
*(Note: In the implementation, this sequence and its supporting classes are historically named **Quantifying** (`quantifying` folder, `Quantifier` class) instead of **Looping** (`looping` folder, `Looper` class). This will be deprecated in the future.)*

The `Looping` sequence delegates its logic to the `Quantifier` class in the `_syntax` module during the **LR** (implemented as **QR**) step. It manages a persistent **Workspace** to track the state of iterations.
*   **Workspace Management**: The `Quantifier` maintains a sub-workspace keyed by loop indices. This allows it to "remember" which items from the input collection have been processed.
*   **Iteration Logic**: The `QR` step checks if the current item from the input collection (provided by `GR`) is "new" (not in the workspace).
    *   **If New**: It initializes the context for this new iteration, potentially carrying over values from previous iterations (e.g., a running sum). It flags the state (`is_quantifier_progress = True`) to indicate that the loop is active and processing a new item.
    *   **If Processed**: It continues to the next item or signals completion.
*   **Aggregation**: Upon completion of all iterations, the `Quantifier` combines the results (concept values) from all workspace entries into a single output reference, effectively "stacking" the results along a new axis.


