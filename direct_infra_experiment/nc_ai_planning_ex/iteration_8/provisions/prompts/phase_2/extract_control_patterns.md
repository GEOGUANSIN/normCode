# Extract Control Patterns (Loops and Conditions)

## Task

Identify all **control flow patterns** in the instruction—loops, conditions, selections, and groupings.

## Input

- `input_1` — The refined instruction

---

## The Five Core Patterns

### 1. Linear Chain
**Intent**: "Transform A into B"

No special pattern—just operation with input producing output.

**Phrases**: "then", "produces", "results in"

---

### 2. Multiple Inputs
**Intent**: "Combine A and B to produce C"

One operation takes multiple inputs.

**Phrases**: "combine", "using X and Y", "from X and Y", "merge"

---

### 3. Iteration (Loop)
**Intent**: "For each X in collection, do Y"

Process each item in a collection.

**Phrases**:
| Phrase | Pattern |
|--------|---------|
| "for each X" | Loop over collection |
| "for every X" | Loop over collection |
| "process all X" | Loop over collection |
| "repeat until" | Loop with termination |
| "keep doing until" | Self-seeding loop |

**Key elements**:
- **Collection**: What is iterated over
- **Current item**: The variable for each iteration
- **Per-item result**: What is produced each time

---

### 4. Conditional (Single Gated Operation)
**Intent**: "If condition, then do A" (optionally with else)

Execute **one** operation based on a boolean condition.

**Phrases**:
| Phrase | Meaning |
|--------|---------|
| "if X then Y" | Do Y when X is true |
| "when X" | Do when X is true |
| "unless X" | Do when X is NOT true |

**Key elements**:
- **Condition**: What is checked (produces boolean)
- **Gated operation**: What happens if condition is met
- **Alternative** (optional): What happens if NOT met

**Example**: "If the file is valid, save it" → ONE operation gated by ONE condition

---

### 5. Selection (Multiple Exclusive Options)
**Intent**: "If type is A do X, if type is B do Y, if type is C do Z"

Pick one result from **multiple exclusive options**, each with its own condition.

**CRITICAL DISTINCTION FROM CONDITIONAL**:
| Conditional | Selection |
|-------------|-----------|
| ONE operation, ONE condition | MULTIPLE operations, each with OWN condition |
| "if valid, save" | "if A do X, if B do Y, if C do Z" |
| Simple gate | Multi-way branch based on type/category |

**Phrases**:
| Phrase | Meaning |
|--------|---------|
| "if type is A, do X; if type is B, do Y" | Selection between options |
| "based on the type, apply..." | Selection |
| "for each type, use appropriate..." | Selection |
| "choose first valid" | Selection |

**Key elements**:
- **Discriminator**: What value determines which option (e.g., "concept type")
- **Options**: The mutually exclusive choices
- **Conditions**: One boolean check per option
- **Gated operations**: Each option has its own operation

**Example**: 
```
If it is an {object}, apply object formalization
If it is a [relation], apply relation formalization
If it is a <proposition>, apply proposition formalization
```
→ This is **SELECTION** (3 options, each with condition), NOT conditional

---

### 6. Grouping
**Intent**: "Bundle A, B, C together"

Combine multiple items into one structure.

**Phrases**: "bundle", "collect", "group", "combine into", "package together"

**Key elements**:
- **Items**: What is bundled
- **Result**: The combined structure

---

## Self-Seeding Loops (Special)

For loops that build their own collection:

**Intent**: "Keep doing X until condition Y"

The loop appends to its own iteration base and terminates when append stops.

**Phrases**: "keep going until", "continue while", "repeat until done"

**Key insight**: Termination happens via conditional append, not explicit break.

---

## Output Format

```json
{
  "thinking": "Your pattern analysis",
  "result": {
    "patterns": [
      {
        "type": "iteration | conditional | selection | grouping | linear | multi_input",
        "trigger_phrase": "The phrase indicating this pattern",
        "elements": {
          "collection": "for iteration: what is iterated",
          "current_item": "for iteration: the per-item variable",
          "condition": "for conditional: what is checked",
          "gated_operation": "for conditional: what is executed when true",
          "discriminator": "for selection: what value determines the choice",
          "options": "for selection: list of {condition, operation} pairs",
          "items": "for grouping: what is bundled"
        }
      }
    ],
    "summary": {
      "has_iteration": true | false,
      "has_conditional": true | false,
      "has_selection": true | false,
      "has_grouping": true | false,
      "is_self_seeding": true | false,
      "pattern_count": 0
    }
  }
}
```

**Important**: Put all data in the `result` field. The `thinking` field is for your reasoning only.

---

## Example

**Instruction**: "For each file, read content. If valid JSON, parse and add to results. Otherwise log error. Bundle results and errors into report."

```json
{
  "thinking": "'For each file' = iteration. 'If valid JSON' = conditional with two branches. 'Bundle results and errors' = grouping.",
  "result": {
    "patterns": [
      {
        "type": "iteration",
        "trigger_phrase": "For each file",
        "elements": {
          "collection": "files",
          "current_item": "file",
          "condition": null,
          "true_branch": null,
          "false_branch": null,
          "options": null,
          "items": null
        }
      },
      {
        "type": "conditional",
        "trigger_phrase": "If valid JSON",
        "elements": {
          "collection": null,
          "current_item": null,
          "condition": "file is valid JSON",
          "true_branch": "parse and add to results",
          "false_branch": "log error",
          "options": null,
          "items": null
        }
      },
      {
        "type": "grouping",
        "trigger_phrase": "Bundle results and errors",
        "elements": {
          "collection": null,
          "current_item": null,
          "condition": null,
          "true_branch": null,
          "false_branch": null,
          "options": null,
          "items": ["results", "errors"]
        }
      }
    ],
    "summary": {
      "has_iteration": true,
      "has_conditional": true,
      "has_selection": false,
      "has_grouping": true,
      "is_self_seeding": false,
      "pattern_count": 3
    }
  }
}
```

---

## Common Mistakes

1. **Confusing selection with conditional**: 
   - "if valid, save" = conditional (one operation, one condition)
   - "if A do X, if B do Y, if C do Z" = selection (multiple options, each with condition)
2. **Missing loop variable**: "for each X" implies both "Xs" (collection) and "X" (current item)
3. **Missing selection discriminator**: "based on type, apply..." needs to identify WHAT determines the choice
4. **Treating multi-way branch as multiple conditionals**: "if type A..., if type B..., if type C..." is ONE selection pattern, not three conditionals

---

## Now Extract

$input_1
