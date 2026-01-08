# Formalization Algorithm

**Goal**: Transform `.ncds` (NormCode Draft Straightforward) into `.ncd` (Formal NormCode Draft)

---

## Overview

The formalization algorithm adds structural rigor to a draft plan by annotating each inference with:
- **Flow indices**: Unique hierarchical addresses
- **Sequence types**: Operation classification
- **Semantic types**: Concept classification  
- **Value bindings**: Input ordering

**Key Design Principle**: Process inference-by-inference while maintaining overall context.

---

## Input/Output

**Input**: `.ncds` file with hierarchical structure
```ncds
<- result
    <= calculate sum
    <- input A
    <- input B
```

**Output**: `.ncd` file with formal annotations
```ncd
:<:{result} | ?{flow_index}: 1
    <= ::(calculate sum from {1} and {2}) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {input A}<:{1}> | ?{flow_index}: 1.2
    <- {input B}<:{2}> | ?{flow_index}: 1.3
```

---

## Phase 1: Parse NCDS Structure

### Step 1.1: Tokenize Lines

For each line in the .ncds file:
- Extract the **marker** (`<-`, `<=`, `<*`, `/:`, `:<:`)
- Extract the **content** (text after marker)
- Calculate **indentation level** (spaces / 4)
- Store as structured token

### Step 1.2: Build Tree Structure

Using indentation levels:
- Level 0 = root
- Level N+1 = child of previous Level N
- Build parent-child relationships
- Store tree for context during processing

### Step 1.3: Identify Ground Concepts

Ground concepts are "leaves" with no operation producing them:
- Value concepts at deepest level without a functional concept child
- Often marked with `/: Ground` comment in draft

---

## Phase 2: Assign Flow Indices

### Algorithm

```
function assign_flow_indices(tree):
    assign_index(root, "1")

function assign_index(node, index):
    node.flow_index = index
    child_counter = 1
    for each child of node:
        child_index = index + "." + child_counter
        assign_index(child, child_index)
        child_counter += 1
```

### Rules

| Situation | Index Pattern |
|-----------|---------------|
| Root concept | `1` |
| First child | `parent.1` |
| Second child | `parent.2` |
| Grandchild | `parent.child.1` |

### Example

```
Input tree:              Flow indices:
result                   1
├── calculate            1.1
├── input A              1.2
└── input B              1.3
    ├── process B        1.3.1
    └── raw B            1.3.2
```

---

## Phase 3: Determine Sequence Types

### For each functional concept (<=):

#### Step 3.1: Check for Syntactic Operators

| Operator Pattern | Sequence Type |
|-----------------|---------------|
| `$=`, `$.`, `$+`, `$-`, `$%` | `assigning` |
| `&[{}]`, `&[#]`, `&[]` | `grouping` |
| `@:'`, `@:!`, `@.` | `timing` |
| `*.`, `*$` | `looping` |

#### Step 3.2: If No Operator, Infer from NL

| Natural Language Pattern | Inferred Operator | Sequence |
|-------------------------|-------------------|----------|
| "collect", "combine", "bundle" | `&[#]` | grouping |
| "for each", "process all" | `*.` | looping |
| "if condition", "when" | `@:'` | timing |
| "select first", "choose" | `$.` | assigning |
| "return", "pass through" | `$.` | assigning |

#### Step 3.3: Default to Semantic

| Pattern | Sequence Type |
|---------|---------------|
| Action verbs (calculate, extract, analyze) | `imperative` |
| Evaluation phrases (is valid, check, verify) | `judgement` |

---

## Phase 4: Assign Semantic Types

### Value Concepts (<-)

| Concept Name Pattern | Semantic Type |
|---------------------|---------------|
| Singular noun ("document", "result") | `{name}` |
| Plural noun ("documents", "files") | `[name]` |
| "all X" pattern | `[name]` |
| Boolean phrase ("is valid", "passed") | `<name>` |

### Functional Concepts (<=)

| Operation Type | Semantic Type |
|----------------|---------------|
| Imperative (command) | `::(description)` |
| Judgement (evaluation) | `::(description)<ALL True>` |
| Syntactic operator | Keep operator as-is |

### Context Concepts (<*)

Follow value concept rules based on name.

---

## Phase 5: Add Value Bindings

### When to Add Bindings

- Operation has multiple input value concepts
- Order matters for the operation
- Need to disambiguate which input is which

### Algorithm

```
function add_value_bindings(functional_concept):
    value_siblings = get_value_concept_siblings(functional_concept)
    if len(value_siblings) > 1:
        for i, value in enumerate(value_siblings, start=1):
            value.binding = "<:{" + str(i) + "}>"
        
        # Update functional concept text with placeholders
        update_functional_with_placeholders(functional_concept, value_siblings)
```

### Pattern Matching

Try to match value concept names in the functional concept text:
- "calculate A and B" → {A}<:{1}>, {B}<:{2}>
- "combine X with Y" → {X}<:{1}>, {Y}<:{2}>
- If no match, use order of appearance

---

## Phase 6: Mark Root Concept

### Rules

- The top-level value concept (level 0) is the root
- Change marker from `<-` to `:<:`
- Root represents the final output of the plan

---

## Phase 7: Output Formatting

### Format Each Line

```
[marker] [semantic_type][content][value_binding] | ?{flow_index}: X.Y.Z [| ?{sequence}: type]
```

### Examples

**Value concept**:
```ncd
<- {input data}<:{1}> | ?{flow_index}: 1.2
```

**Functional concept**:
```ncd
<= ::(calculate sum) | ?{flow_index}: 1.1 | ?{sequence}: imperative
```

**Root concept**:
```ncd
:<:{final result} | ?{flow_index}: 1
```

**Comment** (preserved):
```ncd
/: This is a description
```

---

## Processing Strategy: Inference-by-Inference

### Why Inference-by-Inference?

1. **Manageable context**: Each inference is processed with its immediate context
2. **Incremental progress**: Can checkpoint after each inference
3. **Error isolation**: Issues are localized to specific inferences
4. **LLM-friendly**: Smaller, focused prompts work better

### Context Window

When processing inference N, provide context:
- The parsed tree structure (global)
- Parent inference
- Sibling inferences
- Already-processed inferences (with their annotations)

### Order of Processing

1. Parse entire .ncds to build tree (Phase 1)
2. Assign flow indices to all nodes (Phase 2)
3. For each inference in tree-order:
   - Determine sequence type (if functional)
   - Assign semantic types
   - Add value bindings (if applicable)
4. Format and output

---

## Checkpointing

Similar to derivation, formalization can checkpoint:

| Checkpoint | Content |
|------------|---------|
| `1_parsed_structure.json` | Parsed tree with indentation levels |
| `2_flow_indices.json` | Tree with flow indices assigned |
| `3_sequence_types.json` | Sequence type annotations |
| `4_semantic_types.json` | Semantic type annotations |
| `5_value_bindings.json` | Value binding annotations |
| `formalized_output.ncd` | Final .ncd file |

---

## Example: Full Formalization

### Input (.ncds)

```ncds
/: Investment Analysis
<- investment decision
    <= synthesize recommendation
    <- risk analysis
        <= analyze risk
        <- price data
        <- market signals
    <- sentiment score
        <= analyze sentiment
        <- news articles
```

### Phase 1: Parsed Tree

```json
{
  "root": {
    "marker": "<-",
    "content": "investment decision",
    "level": 0,
    "children": [...]
  }
}
```

### Phase 2: Flow Indices

```
investment decision     → 1
├── synthesize...       → 1.1
├── risk analysis       → 1.2
│   ├── analyze risk    → 1.2.1
│   ├── price data      → 1.2.2
│   └── market signals  → 1.2.3
└── sentiment score     → 1.3
    ├── analyze...      → 1.3.1
    └── news articles   → 1.3.2
```

### Phase 3-5: Annotations

- `synthesize recommendation` → `imperative`, 2 inputs → bindings
- `analyze risk` → `imperative`, 2 inputs → bindings
- `analyze sentiment` → `imperative`

### Output (.ncd)

```ncd
/: Investment Analysis
:<:{investment decision} | ?{flow_index}: 1
    <= ::(synthesize recommendation from {1} and {2}) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {risk analysis}<:{1}> | ?{flow_index}: 1.2
        <= ::(analyze risk based on {1} and {2}) | ?{flow_index}: 1.2.1 | ?{sequence}: imperative
        <- {price data}<:{1}> | ?{flow_index}: 1.2.2
        <- {market signals}<:{2}> | ?{flow_index}: 1.2.3
    <- {sentiment score}<:{2}> | ?{flow_index}: 1.3
        <= ::(analyze sentiment) | ?{flow_index}: 1.3.1 | ?{sequence}: imperative
        <- {news articles} | ?{flow_index}: 1.3.2
```

---

## Integration with Canvas App

### Parser Support

The Canvas App editor includes parsers that can:
- Parse .ncds files into tree structures
- Validate indentation
- Display hierarchical view

These can be reused or referenced for Phase 1 parsing.

### Future: Provision Integration

After formalization, the .ncd file needs:
- Paradigm assignments (Post-Formalization)
- Resource linking

This formalization algorithm produces the structural foundation for that phase.

---

## Summary

| Phase | Input | Output | Key Operation |
|-------|-------|--------|---------------|
| Parse | .ncds text | Tree structure | Tokenize, build hierarchy |
| Flow Index | Tree | Tree + indices | Hierarchical numbering |
| Sequence | Functional concepts | + sequence types | Pattern matching |
| Semantic | All concepts | + semantic types | Type inference |
| Bindings | Multi-input ops | + value bindings | Order assignment |
| Root | Tree | Final tree | Mark :<: |
| Output | Annotated tree | .ncd text | Format and serialize |

**Result**: Rigorous structural plan ready for Post-Formalization.

