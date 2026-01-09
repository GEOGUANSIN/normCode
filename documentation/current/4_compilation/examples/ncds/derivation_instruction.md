# Derivation as a NormCode Plan

**The meta-question**: How do we derive `.ncds` from natural language? 

**The answer**: Derivation itself is a structured process that can be expressed as NormCode.

---

## The Derivation Algorithm (Natural Language)

```
Given a natural language instruction, produce a .ncds file:

PHASE 1: REFINEMENT
If the instruction is vague:
  - Apply each refinement question to the instruction
  - Collect the answers
  - Synthesize a concrete instruction from the answers
Otherwise:
  - Use the instruction as-is

PHASE 2: EXTRACTION  
From the concrete instruction:
  - Extract all concepts (nouns, data entities)
  - Extract all operations (verbs, actions)
  - Extract all dependencies (what needs what)
  - Extract all control patterns (loops, conditions)

PHASE 3: PATTERN CLASSIFICATION
For each operation identified:
  - Classify as: linear, multi-input, iteration, conditional, or grouping
  - Determine context requirements (<* markers)

PHASE 4: TREE CONSTRUCTION
Starting from the final output (root):
  - For each concept that needs computation:
    - Add its producing operation as child
    - Add operation's inputs as grandchildren
    - Add context markers where needed
  - Recurse until all concepts placed

PHASE 5: SERIALIZATION
Convert the tree to .ncds text:
  - Root at indentation 0
  - Each level adds 4 spaces
  - Apply markers: <- for values, <= for operations, <* for context

OUTPUT: The .ncds file
```

---

## Derived `.ncds` for the Derivation Algorithm

```ncds
/: ========================================
/: The Derivation Algorithm as NormCode
/: ========================================
/: Meta-plan: Transforms natural language into .ncds
/: This is the "compiler's compiler" - self-hosting derivation
/:
/: INPUT: raw instruction (natural language text)
/: OUTPUT: ncds file (structured .ncds text)

<- ncds file
    <= serialize tree to ncds format
    /: PHASE 5: Convert tree structure to text
    
    <- dependency tree
        <= construct tree from classified operations
        /: PHASE 4: Build hierarchical structure
        
        <- tree with contexts
            <= for each classified operation
            /: Add context markers where patterns require them
            
                <= return node with context markers
                
                <- node with context
                    <= add context markers based on pattern type
                    <- operation classification
                    <- operation node
                        <= create node from operation and its inputs
                        <- current operation
                        <- inputs for operation
                            <= find inputs for this operation
                            <- current operation
                            <- all dependencies
                
                <- node with context
                    <= append to tree if has dependencies
                    <- node with context
                    <- tree with contexts
            
            <- classified operations
            <* current operation in classified operations
        
        <- final output concept
            <= identify the goal from extraction results
            <- extraction results
        <- classified operations
        <- all dependencies
            <= extracted from extraction results
            <- extraction results
    
    <- classified operations
        <= classify each operation by pattern
        /: PHASE 3: Pattern recognition
        
        <- all classifications
            <= for each extracted operation
            
                <= return classification for this operation
                
                <- classification
                    <= determine pattern type
                    /: Linear, multi-input, iteration, conditional, or grouping
                    <- current operation
                    <- operation context
                        <= gather context clues for this operation
                        <- current operation
                        <- all dependencies
                        <- all control patterns
                
                <- all classifications
                    <= append classification
                    <- classification
                    <- all classifications
            
            <- extracted operations
            <* current operation in extracted operations
        
        <- extracted operations
            <= from extraction results
            <- extraction results
        <- all dependencies
        <- all control patterns
            <= from extraction results
            <- extraction results
    
    <- extraction results
        <= extract concepts, operations, dependencies, and patterns
        /: PHASE 2: Parse the concrete instruction
        
        <- combined extraction
            <= bundle all extractions together
            
            <- extracted concepts
                <= identify all nouns and data entities
                <- concrete instruction
            
            <- extracted operations  
                <= identify all verbs and actions
                <- concrete instruction
            
            <- extracted dependencies
                <= identify what needs what
                /: Parse temporal and data flow indicators
                <- concrete instruction
                <- extracted concepts
                <- extracted operations
            
            <- extracted control patterns
                <= identify loops and conditions
                /: Look for "for each", "if", "until", etc.
                <- concrete instruction
        
        <- concrete instruction
    
    <- concrete instruction
        <= refine if needed, otherwise pass through
        /: PHASE 1: Ensure instruction is derivable
        
        <- refined or original
            <= select based on concreteness check
            
            <- refined instruction
                <= synthesize from refinement answers
                    <= if instruction is vague
                    <* instruction is vague?
                <- refinement answers
                    <= apply refinement questions
                    <- raw instruction
                    <- refinement questions
                        /: The 7 questions from derivation_v2.md
            
            <- raw instruction
                /: Pass through if already concrete
            
            <- instruction is vague?
                <= judge if instruction lacks concrete details
                <- raw instruction
    
    <- raw instruction
        /: Ground concept: The natural language input
```

---

## Key Insights: Derivation as a Plan

### The Structure

| Phase | Pattern | Input | Output |
|-------|---------|-------|--------|
| **Refinement** | Conditional | raw instruction | concrete instruction |
| **Extraction** | Grouping | concrete instruction | concepts, operations, dependencies, patterns |
| **Classification** | Iteration | extracted operations | classified operations |
| **Construction** | Iteration + Recursion | classifications | dependency tree |
| **Serialization** | Linear | tree | .ncds text |

### The Patterns Used

1. **Conditional** (Phase 1): Refine only if vague
2. **Grouping** (Phase 2): Bundle all extractions together
3. **Iteration** (Phase 3): Classify each operation
4. **Iteration + Accumulation** (Phase 4): Build tree node by node
5. **Linear** (Phase 5): Convert tree to text

### The Recursion

Phase 4 (tree construction) is implicitly recursive:
- For each concept needing computation
- Find its operation and inputs
- Those inputs may themselves need computation
- Recurse until reaching ground concepts

In NormCode, this recursion is expressed as **nested iteration with conditional append** — the same pattern as the addition algorithm!

---

## The Meta-Observation

**Derivation uses the same patterns it recognizes.**

| Derivation Step | NormCode Pattern |
|-----------------|------------------|
| "Apply each question" | Iteration |
| "If vague, refine" | Conditional |
| "Bundle extractions" | Grouping |
| "For each operation" | Iteration |
| "Add to tree" | Accumulation |
| "Recurse on inputs" | Nested iteration |

This is why derivation can be self-hosting: **the patterns are finite and compositional**.

---

## Simplification: The Core Loop

At its heart, derivation is one recursive question:

```ncds
<- ncds structure
    <= for each concept that needs computation
    
        <= return concept with its producing structure
        
        <- concept structure
            <= build structure for this concept
            <- current concept
            <- operation that produces it
                <= find operation for concept
                <- current concept
                <- all operations
            <- inputs to operation
                <= find dependencies of operation
                <- operation that produces it
                <- all dependencies
            /: RECURSE: inputs may themselves need computation
    
    <- concepts needing computation
    <* current concept in concepts needing computation
```

**The recursion bottoms out** when a concept is:
- A ground concept (external input)
- Already computed (appears elsewhere in tree)

---

## Using This Plan

This derivation plan could theoretically be:

1. **Executed by LLM** — Each operation is an LLM call:
   - "Extract concepts from this instruction"
   - "Classify this operation's pattern"
   - "Build tree node for this concept"

2. **Executed by hybrid** — Some operations are deterministic:
   - Serialization to `.ncds` text (Python)
   - Tree manipulation (Python)
   - Pattern matching (rules + LLM)

3. **Used as specification** — Guides implementation of compiler

---

## The Promise

If we can derive the derivation algorithm into NormCode, and execute that NormCode, we have:

> **A self-hosting NormCode compiler that uses NormCode to compile NormCode.**

This is the goal of `canvas_app/SELF_HOSTING_COMPILER_PLAN.md`.

---

## Summary

Derivation is:

1. **Refinement** — Make vague instructions concrete (conditional)
2. **Extraction** — Pull out concepts, operations, dependencies (grouping)
3. **Classification** — Label each operation's pattern (iteration)
4. **Construction** — Build the dependency tree (recursive iteration)
5. **Serialization** — Output as `.ncds` text (linear)

Each phase uses patterns that NormCode can express. Therefore, **derivation is expressible in NormCode**.

The derivation algorithm is Example 09 — the plan that creates plans.

