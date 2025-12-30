# Serialize Dependency Tree to NCDS

## Task

Convert the dependency tree structure into **NormCode Draft Straightforward (.ncds)** text format.

## Input

You will receive:
- `{dependency tree}`: The tree structure with nodes, operations, and patterns

## NCDS Format Rules

### Basic Syntax

```ncds
<- {concept name}                    /: Value concept (data)
    <= operation description         /: Functional concept (action)
    <- {input concept}               /: Input to the operation
    <* {context concept}             /: Context (loop variable)
```

### Indentation

- Each level of nesting = 4 spaces
- Children are indented under their parent
- Comments start with `/:` and are indented to match

### Pattern-Specific Syntax

**Linear/Multi-input**:
```ncds
<- {output concept}
    <= do the operation
    <- {input 1}
    <- {input 2}
```

**Iteration**:
```ncds
<- [all results]
    <= for each item in collection
        <= return the processed item
        <- {processed item}
            <= process this item
            <- {current item}
    <- [collection]
    <* {current item}
```

**Conditional**:
```ncds
<- {result}
    <= do something
        <= if condition
        <* <condition>
    <- {input}
    <- <condition>
        <= check if something
        <- {data to check}
```

**Selection**:
```ncds
<- {result}
    <= select first available
    <- {option 1}
    <- {option 2}
```

**Grouping**:
```ncds
<- {grouped result}
    <= collect these items together
    <- {item 1}
    <- {item 2}
    <- {item 3}
```

### Ground Concepts

Ground concepts (inputs) appear as:
```ncds
<- {ground concept}
    /: Ground: description of this input
```

### Output Marker

The root concept uses `:<:` marker:
```ncds
:<: {final result}
    <= produce the final result
    <- {intermediate}
```

Or in simplified form for the plan:
```ncds
<- {final result}
    <= produce the final result
    <- {intermediate}
```

## Serialization Algorithm

1. Start from root node
2. Write the concept marker (`<-` or `:<:`)
3. Write the operation (`<=`) if present
4. For each pattern type, apply specific formatting
5. Recurse into children with increased indent
6. Handle context (`<*`) and conditions appropriately
7. Add ground concept comments for leaf nodes

## Output Format

Return a JSON object:

```json
{
  "thinking": "Your serialization process",
  "ncds_content": "The complete .ncds file content as a string",
  "line_count": <number of lines>,
  "concept_count": <number of concepts>,
  "operation_count": <number of operations>
}
```

## Example Output

For a simple summarization tree:

```ncds
/: Document Summarization Plan
/: Generated from dependency tree

<- {document summary}
    <= summarize this text
    <- {clean text}
        <= extract main content, removing headers
        <- {raw document}

<- {raw document}
    /: Ground: input document to process
```

## Dependency Tree to Serialize

{{dependency tree}}

