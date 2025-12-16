# NormCode Examples

Simple, self-contained example plans showing common patterns.

> **Note on Format**: These examples show NormCode's core syntax (usable in `.ncds`, `.ncd`, or `.ncdn` formats). You can also:
> - Start with `.ncds` format (draft/authoring) when creating new plans
> - Use `.ncdn` format in the editor to see both formal and natural language
> - Convert between formats using `update_format.py` tool
> 
> See [Editor Guide](../../Editor_README.md) for format details.

---

## Table of Contents

1. [Basic Linear Flow](#basic-linear-flow)
2. [Multi-Input Processing](#multi-input-processing)
3. [Conditional Execution](#conditional-execution)
4. [Iteration Over Collections](#iteration-over-collections)
5. [Data Collection](#data-collection)
6. [Nested Workflows](#nested-workflows)
7. [Error Handling](#error-handling)

---

## Basic Linear Flow

### Document Summarization

```ncds
<- document summary
    <= summarize this text
    <- clean text
        <= extract main content, removing headers
        <- raw document
```

**Execution**:
1. Get `raw document`
2. Extract main content → `clean text`
3. Summarize → `document summary`

**LLM calls**: 2 (extract, summarize)

---

## Multi-Input Processing

### Sentiment Analysis with Context

```ncds
<- user sentiment
    <= determine sentiment level (high, medium, low) based on the user's experience
    <- support ticket
    <- conversation history
```

**Execution**:
1. Get `support ticket` and `conversation history`
2. Analyze both → `user sentiment`

**LLM calls**: 1 (determine sentiment)

---

### Report Generation

```ncds
<- quarterly report
    <= compile findings into executive summary
    <- analyzed data
        <= identify trends and anomalies
        <- raw metrics
    <- previous quarter report
```

**Execution**:
1. Get `raw metrics`
2. Identify trends → `analyzed data`
3. Get `previous quarter report`
4. Compile both → `quarterly report`

**LLM calls**: 2 (identify trends, compile)

---

## Conditional Execution

### Review Workflow

```ncds
<- final output
    <= select reviewed output if available otherwise use draft output
    <- draft needs review?
        <= check if draft requires review
        <- draft output
    <- reviewed output
        <= perform human review and corrections
            <= if draft needs review
            <* draft needs review?
        <- draft output
    <- draft output
```

**Execution**:
1. Generate `draft output`
2. Check if `draft needs review?` is true
3. If true: run review → `reviewed output`
4. Select appropriate output (syntactic) → `final output`

**LLM calls**: 1-2 (check + optional review)

**Structure notes**:
- Timer `<= if draft needs review` is on the review operation, not the selection
- Selection is syntactic (no LLM call), just picks available output

---

### Error Recovery

```ncds
<- validated result
    <= select valid result
        <= if primary analysis failed
        <* primary analysis failed?
    <- primary analysis failed?
        <= check if primary result is valid
        <- primary result
    <- primary result
        <= attempt primary analysis
        <- input data
    <- fallback result
        <= use simple approach as fallback
        <- input data
```

**Execution**:
1. Try primary analysis → `primary result`
2. Check if failed → `primary analysis failed?`
3. Select: if failed use `fallback result`, else use `primary result`
4. Return `validated result`

---

## Iteration Over Collections

### Summarize Multiple Documents

```ncds
<- all summaries
    <= for every document in the list return the document summary
        <= select document summary to return
        <- document summary
            <= summarize this document
            <- document to process now
    <- documents
    <* document to process now
```

**Execution**:
1. For each `document to process now` in `documents`
2. Summarize → `document summary`
3. Collect all results → `all summaries`

**LLM calls**: N (one per document)

**Structure notes**:
- `<- documents`: Base collection (value concept)
- `<* document to process now`: Current element in iteration (context concept)
- `<= select document summary to return`: Specification selecting output per iteration

---

### Extract Features

```ncds
<- extracted features
    <= for each document in collection return the feature from doc
        <= select feature from doc
        <- feature from doc
            <= extract key features and themes
            <- current document
    <- document collection
    <* current document
```

**Execution**:
1. For each `current document` in `document collection`
2. Extract features → `feature from doc`
3. Gather all results → `extracted features`

**LLM calls**: N (one per document)

---

## Data Collection

### Collect Multiple Inputs

```ncds
<- all inputs
    <= collect these items together as one group
    <- user query
    <- system context
    <- retrieved documents
```

**Execution**:
- Group all three inputs into `all inputs`

**LLM calls**: 0 (syntactic grouping)

---

### Parallel Collection

```ncds
<- analysis results
    <= gather results from all analyses as one info unit
    <- sentiment analysis
        <= analyze sentiment
        <- text
    <- entity extraction
        <= extract entities
        <- text
    <- topic classification
        <= classify topics
        <- text
```

**Execution**:
1. Run all three analyses in parallel (same input)
2. Collect results

**LLM calls**: 3 (can run in parallel)

---

## Nested Workflows

### Legal Document Analysis

```ncds
<- risk assessment
    <= evaluate legal exposure based on the extracted clauses
    <- relevant clauses
        <= extract clauses related to liability and indemnification
        <- classified sections
            <= identify and classify document sections
            <- full contract
```

**Execution**:
1. Get `full contract`
2. Classify sections → `classified sections`
3. Extract relevant clauses → `relevant clauses`
4. Assess risk → `risk assessment`

**LLM calls**: 3

**Key**: Each step only sees its direct inputs. Risk assessment never sees the full contract.

---

### Research Synthesis

```ncds
<- final synthesis
    <= synthesize insights across all themes
    <- major themes
        <= identify common themes
        <- all findings
            <= for every paper return the key findings
                <= select key findings
                <- key findings
                    <= extract main findings
                    <- current paper
            <- research papers
            <* current paper
```

**Execution**:
1. For each `current paper` in `research papers`: extract findings
2. Collect `all findings`
3. Identify `major themes`
4. Synthesize → `final synthesis`

**LLM calls**: N + 2 (N papers + theme identification + synthesis)

---

## Error Handling

### Try with Fallback

```ncds
<- final answer
    <= select the first valid result
    <- complex reasoning failed?
        <= check if primary answer is valid
        <- primary answer
    <- fallback answer
        <= use simple approach
            <= if complex reasoning failed
            <* complex reasoning failed?
        <- question
    <- primary answer
        <= attempt complex reasoning
        <- question
```

**Execution**:
1. Try complex reasoning → `primary answer`
2. Check validity → `complex reasoning failed?`
3. If failed: use `fallback answer`
4. Select first valid → `final answer`

---

### Validation Chain

```ncds
<- validated output
    <= select the first available as output
    <= corrected output
        <= correct 
            <= if validation result is not ok
            <* validation result?
        <- generated output
    <- generated output
        <= generate initial output
        <- input
    <- validation result?
        <= check if output meets requirements
        <- generated output
        <- requirements
```

**Execution**:
1. Generate initial output
2. Validate against requirements
3. Correct if needed

---

## Practical Patterns

### Pattern 1: Clean → Process → Validate


```ncds
<- validated output
    <= select the first available as output
    <= corrected output
        <= correct 
            <= if validation result is not ok
            <* validation result?
        <- generated output
    <- generated output
        <= generate initial output
        <- input
    <- validation result?
        <= check if output meets requirements
        <- generated output
        <- requirements
```

Common for production workflows.

---

### Pattern 2: Collect → Analyze → Decide

```ncds
<- decision
    <= make final decision based on all evidence
    <- all evidence
        <= collect evidence from all sources
        <- source A
        <- source B
        <- source C
```

Common for decision support systems.

---

### Pattern 3: Iterate → Aggregate → Summarize

```ncds
<- final summary
    <= create high-level summary
    <- aggregated results
        <= combine all individual results
        <- individual result
            <= for every item return the processed item
                <= select processed item
                <- processed item
                    <= process this item
                    <- current item
            <- items to process
            <* current item
```

Common for batch processing.

**Structure**: Loop over `items to process`, for each `current item` process it, collect `individual result`, aggregate, then summarize.

---

## Tips for Writing Plans

### 1. Start Simple

Begin with a linear flow. Add complexity only when needed.

```ncds
# Good: Start here
<- output
    <= process
    <- input

# Then evolve to:
<- output
    <= process
    <- intermediate
        <= prepare
        <- input
```

### 2. One Action Per Inference

Each inference has exactly one `<=` line.

```ncds
# Wrong
<- output
    <= step 1
    <= step 2  # ❌ Two actions

# Right
<- output
    <= step 2
    <- result
        <= step 1
        <- input
```

### 3. Explicit Dependencies

Make data flow obvious.

```ncds
# Unclear
<- output
    <= process all the data
    <- data A
    <- data B

# Clear
<- output
    <= combine A and B results
    <- processed A
        <= process data A
        <- data A
    <- processed B
        <= process data B
        <- data B
```

### 4. Use Descriptive Names

```ncds
# Weak
<- result
    <= do it
    <- x

# Strong
<- risk assessment
    <= evaluate legal exposure
    <- relevant clauses
```

### 5. Isolate Expensive Operations

Group free syntactic operations, isolate costly semantic ones.

```ncds
<- final result
    <= expensive LLM analysis        # Semantic (costs tokens)
    <- all inputs
        <= collect items together as a group    # Syntactic (free)
        <- input A
        <- input B
        <- input C
```

---

## Real-World Examples

### Email Triage System

```ncds
<- triage decision
    <= assign priority and route to appropriate team
    <- email metadata
        <= extract sender, subject, keywords
        <- raw email
    <- urgency assessment
        <= determine urgency level
        <- email content
            <= extract body text
            <- raw email
    <- historical context
        <= look up previous conversations
        <- sender info
```

### Code Review Assistant

```ncds
<- review summary
    <= generate comprehensive review report
    <- code issues
        <= identify bugs and anti-patterns
        <- code diff
    <- security concerns
        <= check for security vulnerabilities
        <- code diff
    <- style suggestions
        <= evaluate code style and readability
        <- code diff
```

---

## Next Steps

- **[Quickstart](quickstart.md)** - Learn the basics
- **[Grammar](../2_grammar/README.md)** - Complete syntax reference  
- **[Editor Guide](../../Editor_README.md)** - Using the visual editor
- **[Editor Examples](../../Editor_EXAMPLES.md)** - Advanced patterns with format conversion

---

## Format Notes

All examples above show NormCode's core syntax, which works across formats:

- **`.ncds`** - Start here when authoring new plans (draft format)
- **`.ncd`** - Formal syntax after compilation (executable format)
- **`.ncn`** - Natural language view (review format)
- **`.ncdn`** - Hybrid format showing both formal and natural language together

The **visual editor** supports all formats, and **format tools** (`update_format.py`) convert between them automatically.

See the [Editor README](../../Editor_README.md) for:
- Detailed format specifications
- Conversion examples
- Batch processing workflows
- Validation procedures

---

**Start with these patterns and adapt them to your needs.**

The key is clear data flow and explicit isolation.
