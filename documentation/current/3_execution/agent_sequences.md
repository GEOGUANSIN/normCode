# Agent Sequences

**The pre-defined pipelines that execute each inference's logic.**

---

## Overview

**Agent sequences** are the operational realization of inferences. When a functional concept is encountered in a NormCode plan, it triggers a corresponding sequence—a standardized pipeline that transforms inputs into outputs.

**Key Points:**
- Sequences are categorized into **Semantic** (LLM-based) and **Syntactic** (data manipulation)
- Each sequence follows a specific pattern of steps
- Semantic sequences use paradigms to define execution logic
- Syntactic sequences use pure tensor algebra (free, deterministic)

---

## The Agent (:S:)

### What Is an Agent?

In NormCode, an **Agent** is represented by the **Subject Concept** (`:S:`). It's not just an abstract actor—it's a concrete container of capability.

**Agent Components**:
- **Body**: Registry of available tools (LLM clients, file system, Python executor, etc.)
- **Sequences**: Logic pipelines (imperative, grouping, assigning, etc.)
- **AgentFrame**: Factory that configures sequences based on mode

### AgentFrame Implementation

The `AgentFrame` class manages the agent's capabilities:

```python
# Initialize with specific mode
agent_frame = AgentFrame(model="demo")

# Configure inference with appropriate sequence
agent_frame.configure_imperative_demo(inference)
```

### Specifying Agent in NormCode

You can explicitly direct an inference to use a specific subject's capabilities (body of tools) by using the `:_S_:` subject concept notation.

**Meta-variable Convention**: Terms enclosed in underscores (e.g., `_Subject_`, `_S_`) are **meta-variables**—placeholders to be replaced with actual names during planning.

**Full Format Structure**:
```ncd
:_Subject_:{_norm_}(_functional_input_with_value_placements_)
```

Where:
- `_Subject_`: The entity performing the action (whose reference contains tools/sequences)
- `_norm_`: The paradigm or execution mode (e.g., `paradigm`, `sequence: imperative`)
- `_functional_input_with_value_placements_`: The operation definition with inputs

**Example with specific body reference**:
```ncd
<- {result}
    <= :%>(composition):{paradigm}(_functional_input_: {_value_placements_}) 
    ...
```

This tells the system: "Use the `>` Body (from reference/declaration/attribute of the AgentFrame) and interpret the sequences of the inference using the `composition` mode."

**Example with named subject**:
```ncd
<- {reviewed code}
    <= :%reviewer_agent(composition):{review code quality}
    <- {code}
```

---

## Sequence Classification

### The Two Categories

```
┌─────────────────────────────────────────────────────┐
│  SEMANTIC SEQUENCES                                  │
│  → CREATE information via LLM/tools                  │
│  → Expensive (tokens), non-deterministic             │
│  → Imperative, Judgement                            │
├─────────────────────────────────────────────────────┤
│  SYNTACTIC SEQUENCES                                 │
│  → RESHAPE information via tensor algebra            │
│  → Free, deterministic, auditable                    │
│  → Assigning, Grouping, Timing, Looping             │
└─────────────────────────────────────────────────────┘
```

### Complete List

| Sequence | Category | LLM? | Operators | Purpose |
|----------|----------|------|-----------|---------|
| **Imperative** | Semantic | ✅ Yes | `({})`, `::()` | Execute operations, generate content |
| **Judgement** | Semantic | ✅ Yes | `<{}>`, `::<>` | Evaluate conditions, return boolean |
| **Assigning** | Syntactic | ❌ No | `$.`, `$+`, `$-` | Select, accumulate, pick |
| **Grouping** | Syntactic | ❌ No | `&[{}]`, `&[#]` | Collect, bundle, combine |
| **Timing** | Syntactic | ❌ No | `@:'`, `@:!`, `@.` | Branch, wait, sequence |
| **Looping** | Syntactic | ❌ No | `*.` | Iterate with state |
| **Simple** | Syntactic | ❌ No | N/A | Pass-through (testing) |

---

## Semantic Sequences

### The Two Types

| Sequence | Steps | Purpose |
|----------|-------|---------|
| **Imperative** | 7 steps (IWI-IR-MFP-MVP-TVA-OR-OWI) | Execute commands/operations |
| **Judgement** | 8 steps (IWI-IR-MFP-MVP-TVA-TIA-OR-OWI) | Evaluate to boolean |

The only difference: Judgement adds **TIA** (Tool Inference Assertion) to check truth conditions.

### Execution Modes

**Mode 1: Paradigm Composition** [DEFAULT]

Uses declarative JSON paradigms to define execution logic.

**Syntax**:
```ncd
<- {result}
    <= :%(composition):{paradigm}(_functional_input_: {_value_placements_})
    <- {input 1}
    <- {input 2}
```

**Advantages**:
- Flexible: paradigm defines complex workflows
- Reusable: paradigms are configuration files
- Maintainable: change behavior without code changes

**Mode 2: Sequence Variant** [DEPRECATED]

Directly invokes specific sequence variants (e.g., `imperative_direct`).

**Syntax**:
```ncd
<- {result}
    <= :%(demo):{sequence_variant}(_functional_input_: {_value_placements_})
```

**Note**: This mode is deprecated. All new plans should use composition mode.

---

## Semantic Sequence Pipeline

### The Cognitive Cycle

Semantic sequences follow a **Perception → Actuation → Assertion** pattern:

```
PERCEPTION: Understand the norm and the values
    ↓
ACTUATION: Apply the tool/paradigm to the data
    ↓
ASSERTION: (Judgement only) Check truth conditions
```

### Detailed Steps

#### Phase I: Initialization

**1. IWI (Input Working Interpretation)**
- Parse the syntax and intent
- Determine which paradigm or tool to use
- Extract norm configurations

**2. IR (Input Reference)**
- Retrieve References for all input concepts
- Load functional concept's Reference (prompts, scripts)

#### Phase II: Perception

**3. MFP (Model Function Perception)**

*Perception of the Function.*

- **Purpose**: Transform abstract functional definition → executable function
- **Process**: 
  1. Read functional concept's Reference (vertical inputs)
  2. Use `ModelSequenceRunner` to process paradigm specs
  3. Bind tools from agent's body
  4. Produce `instruction_fn` (callable function)
- **Result**: Reference containing prepared function(s)

**4. MVP (Memory Value Perception)**

*Perception of the Values.*

- **Purpose**: Transform abstract value concepts → interactable data
- **Process**:
  1. Read value concepts' References
  2. Encounter perceptual signs (e.g., `%{file_location}7f2(data/input.txt)`)
  3. Use `PerceptionRouter` to transmute signs → actual data
  4. Load files, evaluate expressions, etc.
- **Result**: References with concrete, usable data

#### Phase III: Actuation

**5. TVA (Tool Value Actuation)**

*The Actual Implementation.*

- **Purpose**: Apply prepared functions to perceived values
- **Process**:
  1. Use `cross_action(MFP_reference, MVP_reference)`
  2. For each function × value pair, execute function on value
  3. Paradigm's composition tool handles complex workflows
- **Result**: Reference containing operation results

**In composition mode**: The paradigm's horizontal execution plan runs here, managing data flow through multiple steps.

#### Phase IV: Assertion (Judgement Only)

**6. TIA (Tool Inference Assertion)**

*Assertion of the Result.*

- **Purpose**: Check if TVA result satisfies truth condition
- **Process**:
  1. Read truth assertion from judgement syntax
  2. Apply quantifier (all, any, exists, etc.)
  3. Evaluate condition on TVA results
- **Result**: Boolean reference (`%{truth_value}(True/False)`)

#### Phase V: Conclusion

**7. OR (Output Reference)**
- Create or update the concept's Reference with result
- Store in ConceptRepo

**8. OWI (Output Working Interpretation)**
- Update execution state
- Log to ProcessTracker
- Mark inference as complete

---

## Paradigms in Detail

### What Are Paradigms?

**Paradigms** are declarative JSON specifications that bridge abstract intent and concrete execution.

**Key Insight**: Instead of hardcoding "call LLM, extract code, execute it" into sequences, paradigms externalize this logic as reusable configurations.

### Vertical vs. Horizontal

**The Core Distinction**:

```
VERTICAL STEPS (Setup Phase)
    Handled by ModelSequenceRunner during MFP
    Process: Vertical inputs → Executable function
    
HORIZONTAL STEPS (Runtime Phase)
    Handled by CompositionTool during TVA
    Process: Horizontal inputs → Final output
```

| Aspect | Vertical | Horizontal |
|--------|----------|------------|
| **When** | MFP phase (setup) | TVA phase (runtime) |
| **Input** | Functional concept metadata | Value concepts data |
| **Output** | Callable function(s) | Final result |
| **Engine** | ModelSequenceRunner | CompositionTool |

### Naming Convention

Paradigms self-document via naming: `[inputs]-[composition]-[outputs].json`

**Format**:
- `h_`: Horizontal input (runtime value)
- `v_`: Vertical input (setup metadata)
- `c_`: Composition step
- `o_`: Output format

**Example**: `h_PromptTemplate_SavePath-c_GenerateThinkJson-Extract-Save-o_FileLocation.json`

**Decoding**:
- Horizontal inputs: PromptTemplate, SavePath
- Composition: Generate (LLM) → Extract (parse JSON) → Save (write file)
- Output: FileLocation (pointer to saved file)

### Mathematical Formalization

Let:
- $\mathcal{S}$ = Agent's State (context)
- $\mathcal{P}$ = Paradigm Definition
  - $V_{spec}$ = Vertical Specs
  - $H_{plan}$ = Horizontal Plan
- $\mathcal{V}$ = Runtime Values (from MVP)

**The Paradigm Operation**:

$$
\text{Output} = [F_C(F_V(\mathcal{S}, V_{spec}), H_{plan})](\mathcal{V})
$$

Where:
- $F_V$ = Vertical Function (ModelSequenceRunner)
  - $\mathcal{T} = F_V(\mathcal{S}, V_{spec})$ produces tool handles
- $F_C$ = Composition Function (CompositionTool)
  - $\Phi = F_C(\mathcal{T}, H_{plan})$ produces composed function
- $\Phi(\mathcal{V})$ = Horizontal execution on runtime values

**This cleanly separates Construction Time (vertical) from Runtime (horizontal).**

### Example Paradigm Flow

**Paradigm**: `h_Prompt-c_LLMGenerate-o_Text.json`

**Vertical Steps** (MFP):
1. Load LLM client from agent body
2. Configure model settings (temperature, max_tokens)
3. Prepare generation function: `fn = llm.generate`

**Horizontal Steps** (TVA):
1. Receive prompt from value concepts
2. Call `fn(prompt)` → raw LLM response
3. Return text result

**Paradigm**: `h_PromptTemplate_SavePath-c_GenerateThinkJson-Extract-Save-o_FileLocation.json`

**Vertical Steps** (MFP):
1. Load LLM client
2. Load file system tool
3. Configure JSON parser
4. Compose functions: `generate → parse → save`

**Horizontal Steps** (TVA):
1. Receive prompt template and save path
2. Generate with LLM → raw response
3. Extract JSON from response
4. Save to file system
5. Return file location sign

---

## Syntactic Sequences

### Key Characteristics

**Subject-Agnostic**: Don't rely on specific agent body—operate on structure, not content.

**Universality**: Function identically across all AgentFrames.

**Plan-Level Utility**: Enable the plan to function as a cohesive whole.

**Implementation**: Core logic in `_syntax` module, shared across all agents.

---

### 1. Assigning Sequence

**Steps**: `(IWI-IR-AR-OR-OWI)`

**Purpose**: Variable assignment, state updates, and selection.

**Operators**:

| Operator | Method | Purpose |
|----------|--------|---------|
| `$.` | `specification` | Select first valid from candidates |
| `$+` | `continuation` | Append to destination along axis |
| `$-` | `derelation` | Pure structural selection by index |

#### Specification (`$.`)

**Use Case**: Fallback selection, choose first non-empty option.

**Syntax**:
```ncd
<- {final answer}
    <= $. %<({final answer})
    <- {option A}
    <- {option B}
    <- {option C}
    <- {default value}
```

**Behavior**:
1. Check `{option A}` → if has data, use it
2. Else check `{option B}` → if has data, use it
3. Continue until valid option found
4. If all empty, use destination reference itself

**Implementation**:
```python
assigner.specification(
    source_refs=[optionA_ref, optionB_ref, optionC_ref],
    dest_ref=default_ref
)
```

#### Continuation (`$+`)

**Use Case**: Accumulation in loops, building collections.

**Syntax**:
```ncd
<- {accumulated results}
    <= $+ %<({accumulated results}) %^({new result}*-1)
    <- {new result}
        <= ::(process item)
        <- {item}*1
    <- {accumulated results}*-1
```

**Behavior**:
1. Take new result
2. Append to accumulated results along specified axis
3. Update destination reference

**Implementation**:
```python
assigner.continuation(
    source_ref=new_result_ref,
    dest_ref=accumulated_ref,
    by_axes=['iteration']
)
```

#### Derelation (`$-`)

**Use Case**: Structural selection from grouped data (by index or key).

**Syntax**:
```ncd
<- {selected item}
    <= $- %<({selected item}) %@(0)
    <- {collection}
```

**Behavior**:
- Select element by index from list or dictionary
- Pure structural operation (no semantic interpretation)

**Note**: Currently integrated into MVP step; being extracted as standalone operation.

---

### 2. Grouping Sequence

**Steps**: `(IWI-IR-GR-OR-OWI)`

**Purpose**: Collect, filter, and group data into collections or relations.

**Operators**:

| Operator | Method | Purpose |
|----------|--------|---------|
| `&[{}]` | `and_in` | Combine into annotated dictionary (Relation) |
| `&[#]` | `or_across` | Combine into flat list (Collection) |

#### And-In (`&[{}]`)

**Use Case**: Bundle inputs with labels for semantic processing.

**Syntax**:
```ncd
<- {bundled input}
    <= &[{}]
    <- {user query}
    <- {context}
    <- {retrieved documents}
```

**Behavior**:
1. Use `cross_product` to align inputs by shared axes
2. Create dictionary with concept names as keys
3. Aggregate along axes specified by context concepts

**Result**:
```python
{
    'user query': '...',
    'context': '...',
    'retrieved documents': [...]
}
```

**Implementation**:
```python
grouper.and_in(
    references=[query_ref, context_ref, docs_ref],
    annotation_list=['{user query}', '{context}', '{retrieved documents}']
)
```

#### Or-Across (`&[#]`)

**Use Case**: Flatten multiple sources into single collection.

**Syntax**:
```ncd
<- {all features}
    <= &[#]
    <- {quantitative features}
    <- {qualitative features}
    <- {metadata}
```

**Behavior** (Legacy Mode):
1. Align and cross-product inputs
2. Flatten result into single list
3. Aggregate along context-specified axes

**Behavior** (Per-Reference Mode):
1. Collapse each input along specified axes independently
2. Concatenate all results
3. Wrap in new axis dimension

**Result**: Flat list combining all inputs.

**Implementation**:
```python
# Legacy
grouper.or_across(
    references=[quant_ref, qual_ref, meta_ref]
)

# Per-reference with new axis
grouper.or_across(
    references=[quant_ref, qual_ref, meta_ref],
    by_axes_list=[[axis1], [axis2], [axis3]],
    create_axis='feature_type'
)
```

---

### 3. Timing Sequence

**Steps**: `(IWI-T-OWI)`

**Purpose**: Control conditional execution and dependency management.

**Operators**:

| Operator | Method | Purpose |
|----------|--------|---------|
| `@.` | `check_progress_condition` | Wait for dependency |
| `@:'` | `check_if_condition` | Branch if condition met |
| `@:!` | `check_if_not_condition` | Branch if condition not met |

**Key Feature**: Queries **Blackboard** for status of other concepts.

#### Sequencing (`@.`)

**Use Case**: Enforce execution order, create dependencies.

**Syntax**:
```ncd
<- {step 3}
    <= ::(execute step 3)
        <= @. %>({step 2})
    <- {step 2}
        <= ::(execute step 2)
            <= @. %>({step 1})
        <- {step 1}
```

**Behavior**:
1. Check if referenced concept is `complete`
2. If yes → mark inference as ready to proceed
3. If no → inference remains "not ready"

**Implementation**:
```python
is_ready = timer.check_progress_condition('{step 2}')
```

#### Branching (`@:'` / `@:!`)

**Use Case**: Conditional execution, skip branches.

**Syntax**:
```ncd
<- {result}
    <= $. %<[{option A}, {option B}]
    <- {option A}
        <= ::(compute A)
            <= @:' %>(<condition>)
            <* <condition>
        <- {input}
    <- {option B}
        <= ::(compute B)
            <= @:! %>(<condition>)
            <* <condition>
        <- {input}
```

**Behavior**:
1. Wait for condition concept to be `complete`
2. Check condition's result (boolean value)
3. **If condition met (`@:'`)**: Proceed with inference
4. **If condition not met (`@:'`)**: Mark inference as **SKIPPED**
5. **Opposite logic for `@:!`**

**Skip Propagation**: When inference skipped, all its children are marked `completed` (with detail `skipped`).

**Implementation**:
```python
is_ready, should_skip = timer.check_if_condition('<condition>')
if should_skip:
    states.to_be_skipped = True
```

---

### 4. Looping Sequence

**Steps**: `(IWI-IR-GR-LR-OR-OWI)`

**Purpose**: Manage iterative loops with state accumulation.

**Operator**: `*.`

**Note**: Implementation historically named "Quantifying" (`Quantifier` class); being renamed to "Looping" (`Looper` class).

#### Loop Structure

**Syntax**:
```ncd
<- {all summaries}
    <= *. %>({documents}) %<({summary}) %:({document}) %@(1)
    <- {summary}
        <= ::(summarize document)
        <- {document}*1
    <* {document}<$({documents})*>
```

**Components**:
- `*. %>({documents})`: Loop source (collection to iterate over)
- `%<({summary})`: Loop output (concept to produce per iteration)
- `%:({document})`: Loop axis name
- `%@(1)`: Loop index in value concept list (position of loop base)
- `{document}*1`: Current loop item (instance marker)
- `<* {document}<$({documents})*>`: Context carrying loop state

#### Loop Execution

**Phase 1: Initialization**
1. Grouping step (`GR`) prepares collection
2. Quantifier reads workspace (past iterations)

**Phase 2: Iteration Check (`LR`)**
```python
# Check if there's a new element to process
next_element, index = quantifier.retireve_next_base_element(
    to_loop_element_reference=documents_ref,
    current_loop_base_element=current_doc_ref
)

if next_element found:
    # Initialize context for this iteration
    # Flag: is_quantifier_progress = True
    # Execute child inferences for this item
else:
    # All items processed
    # Combine results from all iterations
```

**Phase 3: Per-Iteration**
1. Child inferences execute with current item
2. Result stored in workspace keyed by iteration index

**Phase 4: Completion**
```python
# Aggregate all iteration results
all_results = quantifier.combine_all_looped_elements_by_concept(
    to_loop_element_reference=documents_ref,
    concept_name='{summary}',
    axis_name='document_index'
)
```

**Phase 5: Reset for Next Iteration**
1. Orchestrator resets child inferences to `pending`
2. Invariant concepts (marked with `*-1`) preserved
3. Loop repeats with next item

#### Workspace Management

**Purpose**: Track which items processed, store intermediate results.

**Structure**:
```python
workspace = {
    0: {'{summary}': summary_ref_0, ...},
    1: {'{summary}': summary_ref_1, ...},
    2: {'{summary}': summary_ref_2, ...},
    ...
}
```

**Key Methods**:
- `retireve_next_base_element`: Get next unprocessed item
- `store_new_in_loop_element`: Save result for current iteration
- `combine_all_looped_elements_by_concept`: Aggregate all results

#### Accumulation Pattern

**Use Case**: Running totals, incremental builds.

**Syntax**:
```ncd
<- {running total}
    <= *. %>({numbers}) %<({total}) %@(1)
    <- {total}
        <= $+ %<({total}) %^({new value}*-1)
        <- {new value}
            <= ::(add to total)
            <- {number}*1
            <- {total}*1
    <- {total}<$({total})*-1>
    <* {number}<$({numbers})*>
    <- {numbers}
```

**Behavior**:
1. Each iteration computes `{new value}` based on current item and previous total
2. `$+` continuation appends to `{total}`
3. `{total}*-1` is invariant—preserved across iterations

---

### 5. Simple Sequence

**Steps**: `(IWI-IR-OR-OWI)`

**Purpose**: Minimal pass-through for testing or basic data flow.

**Use Case**: Testing infrastructure, placeholder operations.

**Behavior**:
1. Retrieve input References
2. Directly assign to output Reference
3. No transformation

---

## Sequence Selection

### How Sequences Are Chosen

**During Compilation** (Formalization Phase):
1. Compiler analyzes functional concept syntax
2. Assigns appropriate `sequence` marker
3. Adds to `?{sequence}:` comment

**Example**:
```ncd
<= ::(calculate) | ?{sequence}: imperative
<= $. | ?{sequence}: assigning
<= &[{}] | ?{sequence}: grouping
<= @:' | ?{sequence}: timing
<= *. | ?{sequence}: looping
```

**During Execution** (AgentFrame Configuration):
1. Orchestrator reads `?{sequence}:` marker
2. AgentFrame selects appropriate configuration method
3. Inference configured with correct pipeline

### Sequence Markers

| Marker | Sequence | Category |
|--------|----------|----------|
| `imperative` | Imperative | Semantic |
| `judgement` | Judgement | Semantic |
| `assigning` | Assigning | Syntactic |
| `grouping` | Grouping | Syntactic |
| `timing` | Timing | Syntactic |
| `looping` (or `quantifying`) | Looping | Syntactic |
| `simple` | Simple | Syntactic |

---

## Sequence Interaction Patterns

### Sequential Composition

**Pattern**: Chain semantic operations with syntactic plumbing.

```ncd
<- {final result}
    <= ::(aggregate analysis)  | ?{sequence}: imperative
    <- {all analyses}
        <= &[#]  | ?{sequence}: grouping
        <- {analysis A}
            <= ::(analyze with method A)  | ?{sequence}: imperative
            <- {input}
        <- {analysis B}
            <= ::(analyze with method B)  | ?{sequence}: imperative
            <- {input}
```

**Flow**:
1. Semantic: Analyze with method A
2. Semantic: Analyze with method B
3. Syntactic: Group analyses
4. Semantic: Aggregate analysis

### Loop with Accumulation

**Pattern**: Iterate with state carried across iterations.

```ncd
<- {accumulated insights}
    <= *. %>({documents}) %<({insight})  | ?{sequence}: looping
    <- {insight}
        <= $+ %<({insight}) %^({new insight}*-1)  | ?{sequence}: assigning
        <- {new insight}
            <= ::(extract insight considering previous)  | ?{sequence}: imperative
            <- {document}*1
            <- {insight}*-1
        <- {insight}*-1
    <* {document}<$({documents})*>
```

**Flow**:
1. Syntactic: Loop over documents
2. Semantic: Extract insight for current document (sees previous insights)
3. Syntactic: Accumulate insight
4. Repeat for next document

### Conditional with Fallback

**Pattern**: Try primary method, fall back to secondary.

```ncd
<- {result}
    <= $.  | ?{sequence}: assigning
    <- {primary result}
        <= ::(compute with primary method)  | ?{sequence}: imperative
            <= @:' %>(<primary succeeded>)  | ?{sequence}: timing
            <* <primary succeeded>
        <- {input}
    <- {fallback result}
        <= ::(compute with fallback method)  | ?{sequence}: imperative
            <= @:! %>(<primary succeeded>)  | ?{sequence}: timing
            <* <primary succeeded>
        <- {input}
```

**Flow**:
1. Semantic: Try primary method
2. Syntactic: Check if succeeded
3. If yes → syntactic: Select primary result
4. If no → semantic: Compute fallback → syntactic: Select fallback

---

## Debugging Sequences

### Common Issues

**Semantic sequence not calling LLM**:
- Check paradigm configuration
- Verify MFP step produced function
- Inspect agent body: are tools available?

**Loop not terminating**:
- Check workspace: are items marked as processed?
- Verify loop base reference has valid elements
- Inspect Quantifier state

**Timing operator not skipping**:
- Check condition concept status (must be `complete`)
- Verify condition result is boolean
- Check Blackboard for skip propagation

**Grouping produces wrong structure**:
- Check operator: `&[{}]` (dict) vs `&[#]` (list)
- Verify axes alignment
- Inspect intermediate References

### Debugging Tools

**ProcessTracker Logs**:
```python
# View step-by-step execution
tracker.get_inference_log(flow_index='1.2.1')
```

**Blackboard Inspection**:
```python
# Check inference status
status = blackboard.get_status(flow_index='1.2.1')

# Check concept readiness
is_ready = blackboard.is_concept_ready('{input A}')
```

**Reference Inspection**:
```python
# View concept's current value
ref = concept_repo.get_reference('{intermediate result}')
print(ref.tensor)
```

---

## Performance Optimization

### Semantic Sequence Costs

| Aspect | Cost | Optimization |
|--------|------|--------------|
| **LLM calls** | Tokens | Batch similar operations |
| **Perception** | I/O | Use caching, lazy loading |
| **Paradigm complexity** | CPU | Simplify horizontal plans |

### Syntactic Sequence Costs

| Aspect | Cost | Optimization |
|--------|------|--------------|
| **Reference operations** | ~0 | No optimization needed |
| **Large tensors** | Memory | Slice early, reduce dimensions |
| **Deep loops** | Iterations | Consider batching |

### General Strategies

1. **Minimize semantic calls**: Use syntactic operations for all data manipulation
2. **Batch processing**: Group similar LLM calls in loops
3. **Cache intermediate results**: Use `$+` accumulation to avoid recomputation
4. **Lazy perception**: Let perceptual signs delay data loading until actually needed

---

## Summary

### Key Takeaways

| Concept | Insight |
|---------|---------|
| **Two categories** | Semantic (create info) vs Syntactic (reshape info) |
| **Perception-Actuation** | Semantic sequences understand then act |
| **Paradigms are norms** | Declarative execution logic |
| **Syntactic is free** | Pure tensor algebra, no LLM costs |
| **Sequences compose** | Build complex workflows from simple steps |

### The Sequence Promise

**NormCode's execution model relies on sequences**:

1. Every functional concept triggers a sequence
2. Sequences follow standardized pipelines
3. Semantic sequences have auditable perception/actuation
4. Syntactic sequences are deterministic and free
5. Paradigms make semantic logic reusable

**Result**: Predictable, auditable, composable execution.

---

## Next Steps

- **[Orchestrator](orchestrator.md)** - How the orchestrator manages sequence execution
- **[Reference System](reference_system.md)** - How sequences manipulate References
- **[Syntactic Operators (Grammar)](../2_grammar/syntactic_operators.md)** - Detailed operator syntax

---

**Ready to understand orchestration?** Continue to [Orchestrator](orchestrator.md) to see how the execution engine coordinates all sequences.
