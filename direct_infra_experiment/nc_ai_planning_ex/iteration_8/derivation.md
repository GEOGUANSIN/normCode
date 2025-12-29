# Derivation

**Phase 1: Transforming natural language into hierarchical inference structure.**

---

## Overview

**Derivation** is the first phase of NormCode compilation. It transforms unstructured natural language instructions into a hierarchical tree of inferences using the `.ncds` (NormCode Draft Straightforward) format.

**Input**: Natural language instruction  
**Output**: `.ncds` file with hierarchical structure

**Core Task**: Extract concepts (data), operations (actions), and their dependencies from natural language.

---

## The Derivation Problem

### Why Derivation Is Needed

Natural language is ambiguous and unstructured:

```
"Analyze the sentiment of customer reviews after filtering out spam and duplicates."
```

**Questions that need answering**:
- What are the data entities? (reviews, sentiment scores, spam markers)
- What are the operations? (filter spam, remove duplicates, analyze sentiment)
- What's the dependency order? (filter first, then deduplicate, then analyze)
- Which concepts depend on which? (sentiment analysis needs clean reviews)

**Derivation resolves these ambiguities** by creating explicit structure.

---

## The `.ncds` Format

### Basic Structure

`.ncds` (NormCode Draft Straightforward) uses minimal markers to express hierarchical inferences:

| Marker | Name | Purpose |
|--------|------|---------|
| `<-` | Value Concept | Data (inputs and outputs) |
| `<=` | Functional Concept | Operations to execute |
| `<*` | Context Concept | Loop state or context data (optional) |

### Reading Direction

**Bottom-up execution**: Read from deepest concepts upward.

**Example**:
```ncds
<- final result
    <= calculate sum
    <- processed data
        <= clean the data
        <- raw data
```

**Execution order**:
1. Start with `raw data`
2. Run `clean the data` → produces `processed data`
3. Run `calculate sum` → produces `final result`

### Indentation

**4-space indentation** indicates hierarchy:
- 0 spaces: Root concept
- 4 spaces: Children of root
- 8 spaces: Grandchildren
- etc.

---

## Extraction Process

### Step 1: Identify Concepts

**Goal**: Extract all data entities mentioned in the natural language.

**Patterns to look for**:
- Nouns and noun phrases
- "the X", "a Y", "all Z"
- Input/output mentions
- Intermediate results

**Example**:

**Input**: "Summarize the document after extracting the main content."

**Identified Concepts**:
- `document` (input)
- `main content` (intermediate)
- `summary` (output)

### Step 2: Identify Operations

**Goal**: Extract all actions/operations mentioned.

**Patterns to look for**:
- Verbs and verb phrases
- "calculate", "extract", "analyze", "filter", "transform"
- Imperatives ("do X", "compute Y")

**Example**:

**Input**: "Summarize the document after extracting the main content."

**Identified Operations**:
- `extract the main content`
- `summarize`

### Step 3: Determine Dependencies

**Goal**: Figure out which concepts feed into which operations.

**Rules**:
- Temporal order ("after X, do Y" → X comes before Y)
- Data flow ("analyze the cleaned data" → clean first)
- Hierarchical nesting (child inferences produce parent inputs)

**Example**:

**Input**: "Summarize the document after extracting the main content."

**Dependencies**:
1. `extract the main content` depends on `document`
2. `summarize` depends on result of extraction
3. Final output is `summary`

### Step 4: Build Hierarchical Structure

**Goal**: Arrange concepts and operations in bottom-up tree.

**Algorithm**:
1. Start with final output (root)
2. For each concept, add its operation as child
3. For each operation, add its inputs as children
4. Recurse until all concepts placed

**Example**:

**Input**: "Summarize the document after extracting the main content."

**Output (`.ncds`)**:
```ncds
<- document summary
    <= summarize this text
    <- main content
        <= extract the main content
        <- raw document
```

---

## Complete Examples

### Example 1: Simple Linear Workflow

**Natural Language**:
```
"Calculate the average of the cleaned numbers after removing outliers from the raw data."
```

**Derivation Output (`.ncds`)**:
```ncds
<- average
    <= calculate the average
    <- cleaned numbers
        <= remove outliers
        <- raw data
```

**Breakdown**:
- **Root**: `average` (final output)
- **Operation 1**: `calculate the average`
- **Input to Op 1**: `cleaned numbers` (intermediate)
- **Operation 2**: `remove outliers`
- **Input to Op 2**: `raw data` (base input)

---

### Example 2: Multiple Inputs

**Natural Language**:
```
"Combine the sentiment scores and entity mentions to generate a comprehensive report."
```

**Derivation Output (`.ncds`)**:
```ncds
<- comprehensive report
    <= generate a comprehensive report
    <- sentiment scores
    <- entity mentions
```

**Breakdown**:
- **Root**: `comprehensive report`
- **Operation**: `generate a comprehensive report`
- **Input 1**: `sentiment scores`
- **Input 2**: `entity mentions`

**Note**: Both inputs are siblings (same indentation level).

---

### Example 3: Branching Workflow

**Natural Language**:
```
"Generate a summary by analyzing both the quantitative data and the qualitative feedback."
```

**Derivation Output (`.ncds`)**:
```ncds
<- summary
    <= generate summary
    <- quantitative analysis
        <= analyze quantitative data
        <- quantitative data
    <- qualitative analysis
        <= analyze qualitative feedback
        <- qualitative feedback
```

**Breakdown**:
- Both branches compute independently
- Root combines their results

---

### Example 4: Conditional Logic

**Natural Language**:
```
"If the validation passes, use the processed result, otherwise use the fallback value."
```

**Derivation Output (`.ncds`)**:
```ncds
<- final result
    <= select the first valid option
    <- processed result
        <= process the input if validation passes
        <- input data
    <- fallback value
```

**Note**: Conditional logic typically uses selection operators (introduced in Formalization). At derivation stage, we just structure the options.

---

### Example 5: Iteration

**Natural Language**:
```
"For each document, extract the key entities and collect all results."
```

**Derivation Output (`.ncds`)**:
```ncds
<- all extracted entities
    <= for each document
    <- extracted entities
        <= extract key entities
        <- document
    <* documents
```

**Key features**:
- Loop concept: `for each document`
- Per-iteration result: `extracted entities`
- Loop base: `documents` (marked with `<*`)

---

## Natural Language Patterns

### Common Patterns and Their Structure

| NL Pattern | `.ncds` Structure |
|------------|------------------|
| "A then B" | B depends on A (A is child of B) |
| "Combine A and B" | Both A and B are sibling inputs |
| "For each X, do Y" | Loop structure with `<*` |
| "If condition, use A else B" | Selection with A and B as options |
| "Extract X from Y" | Y is input to extraction operation |
| "Calculate X using Y and Z" | Y and Z are sibling inputs |

### Temporal Indicators

Words that indicate order:
- "after", "before", "then", "following", "preceding"
- "first X, then Y" → X before Y
- "once X is complete, do Y" → X → Y

### Data Flow Indicators

Words that indicate dependencies:
- "using", "from", "based on", "with", "given"
- "analyze X using Y" → Y is input
- "extract X from Y" → Y is input

---

## Derivation Strategies

### Strategy 1: Top-Down (Goal-Oriented)

1. Identify final goal (what needs to be produced?)
2. Ask: "What operations produce this?"
3. Ask: "What inputs does that operation need?"
4. Recurse until reaching base inputs

**Example**:

**Goal**: "Generate investment recommendation"

**Questions**:
- What produces recommendation? → `generate recommendation` operation
- What does it need? → `analysis results`
- What produces analysis results? → `analyze signals` operation
- What does it need? → `raw signals`

**Result**:
```ncds
<- investment recommendation
    <= generate recommendation
    <- analysis results
        <= analyze signals
        <- raw signals
```

### Strategy 2: Bottom-Up (Data-Driven)

1. Identify all inputs/data sources
2. Ask: "What can we do with this data?"
3. Chain operations based on capabilities
4. Stop when final goal reached

**Example**:

**Starting data**: "customer reviews"

**Questions**:
- What can we do with reviews? → Filter spam
- What next? → Extract sentiment
- What next? → Aggregate statistics
- Final goal? → Report

**Result**:
```ncds
<- aggregate report
    <= generate report
    <- sentiment statistics
        <= aggregate sentiment
        <- sentiment scores
            <= extract sentiment
            <- clean reviews
                <= filter spam
                <- customer reviews
```

### Strategy 3: Hybrid (Most Common)

1. Identify goal and inputs
2. Work from both ends toward middle
3. Connect when paths meet

**Most practical approach** for complex workflows.

---

## Derivation with LLMs

### Using LLMs for Derivation

LLMs can assist with or fully automate derivation:

**Prompt Pattern**:
```
Convert this natural language instruction into NormCode .ncds format.

Instruction: [YOUR INSTRUCTION]

Rules:
1. Use <- for data concepts
2. Use <= for operations
3. Use 4-space indentation
4. Read bottom-up (deepest concepts first)
5. Final output at top (root)

Output the .ncds file:
```

**Example Output**:
```ncds
<- final result
    <= compute result
    <- processed input
        <= process input
        <- raw input
```

### Validation After LLM Generation

**Check**:
1. All concepts have proper markers (`<-`, `<=`)
2. Indentation is consistent (4 spaces)
3. Bottom-up reading makes sense
4. No orphaned concepts (all connected to tree)
5. Final output at root (level 0)

---

## Common Derivation Mistakes

### Mistake 1: Wrong Execution Order

**Problem**: Putting operations in wrong order.

**Example (Wrong)**:
```ncds
<- analysis
    <= analyze
    <- raw data
        <= clean data
        <- preprocessed data
```

**Why wrong**: Can't clean data that doesn't exist yet. Should be:

**Correct**:
```ncds
<- analysis
    <= analyze
    <- preprocessed data
        <= clean data
        <- raw data
```

### Mistake 2: Missing Intermediate Concepts

**Problem**: Skipping necessary intermediate results.

**Example (Wrong)**:
```ncds
<- summary
    <= summarize
        <= extract content
        <- document
```

**Why wrong**: `extract content` needs to produce an intermediate concept that `summarize` uses.

**Correct**:
```ncds
<- summary
    <= summarize
    <- extracted content
        <= extract content
        <- document
```

### Mistake 3: Unclear Dependencies

**Problem**: Multiple possible interpretations.

**Example (Ambiguous)**:
```ncds
<- result
    <= combine
    <- data A
        <= process
        <- input A
    <- data B
        <= process
        <- input B
```

**Issue**: Unclear if both processes run independently or one depends on the other.

**Better**: Add explicit structure or comments.

### Mistake 4: Incorrect Indentation

**Problem**: Wrong hierarchy due to indentation errors.

**Example (Wrong)**:
```ncds
<- result
    <= compute
<- input     # Wrong! Should be indented 8 spaces
```

**Correct**:
```ncds
<- result
    <= compute
        <- input
```

---

## Derivation Comments

### Using Derivation Comments

During derivation, you can add comments to guide the process:

| Comment | Purpose | Example |
|---------|---------|---------|
| `...:` | Source text (un-decomposed) | `...: Calculate the sum of all digits` |
| `?:` | Question guiding decomposition | `?: What operation should be performed?` |
| `/:` | Description (complete) | `/: This computes the final total` |

**Example**:
```ncds
<- digit sum
    ...: Calculate the sum of all digits
    ?: What's the operation?
    <= calculate sum
    /: This computes the final total
    <- all digits
```

**These comments**:
- Document the derivation process
- Help LLMs understand intent
- Preserved through compilation
- Can be removed in final `.ncd`

---

## Derivation Checklist

Before moving to formalization, verify:

### Structure
- [ ] All concepts have proper markers (`<-`, `<=`, `<*`)
- [ ] Indentation is consistent (4 spaces)
- [ ] Root concept at level 0
- [ ] No orphaned concepts

### Logic
- [ ] Bottom-up reading makes sense
- [ ] Operations have inputs
- [ ] Inputs precede operations that use them
- [ ] Final output is clear

### Completeness
- [ ] All mentioned data has concepts
- [ ] All mentioned operations are present
- [ ] Dependencies are explicit
- [ ] No ambiguous references

### Clarity
- [ ] Natural language is understandable
- [ ] Concept names are descriptive
- [ ] Operation descriptions are clear
- [ ] No unnecessary complexity

---

## Tools for Derivation

### Manual Derivation

1. Read the natural language carefully
2. List all nouns (concepts) and verbs (operations)
3. Draw dependency graph on paper
4. Convert to `.ncds` format
5. Validate with checklist

### LLM-Assisted Derivation

1. Provide prompt with rules
2. Generate `.ncds`
3. Review output
4. Iterate if needed
5. Validate with checklist

### Editor Tools

The NormCode editor can help visualize structure:
- Load `.ncds`
- See hierarchical tree
- Edit inline
- Validate syntax

See [Editor](editor.md) for details.

---

## Derivation vs. Formalization

### What Derivation Does

- ✅ Extracts structure and hierarchy
- ✅ Identifies concepts and operations
- ✅ Orders dependencies

### What Derivation Does NOT Do

- ❌ Assign flow indices (that's Formalization)
- ❌ Determine sequence types (that's Formalization)
- ❌ Add semantic types (`{}`, `[]`, etc.) (that's Formalization)
- ❌ Configure execution (that's Post-Formalization)

**Derivation focuses on WHAT, not HOW.**

---

## Next Steps

After derivation, your `.ncds` file moves to:

- **[Formalization](formalization.md)** - Add flow indices, sequence types, and semantic types

---

## Summary

### Key Takeaways

| Concept | Insight |
|---------|---------|
| **Natural language → Structure** | Derivation extracts explicit hierarchy from ambiguous text |
| **Bottom-up reading** | Deepest concepts execute first, results flow upward |
| **Three markers** | `<-` (data), `<=` (operations), `<*` (context) |
| **Four-space indentation** | Hierarchy through indentation |
| **LLM-friendly** | Both humans and LLMs can write `.ncds` |

### The Derivation Promise

**Derivation makes intent explicit**:

1. Ambiguous natural language becomes structured hierarchy
2. Dependencies are clear and traceable
3. Ready for formalization into rigorous `.ncd`

**Result**: A plan that captures WHAT needs to happen, ready to specify HOW it happens.

---

**Ready to add rigor?** Continue to [Formalization](formalization.md) to transform `.ncds` into formal `.ncd` with flow indices and sequence types.
