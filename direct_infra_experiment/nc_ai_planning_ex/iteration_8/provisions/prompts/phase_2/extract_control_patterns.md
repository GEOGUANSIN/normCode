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

### 4. Conditional
**Intent**: "If condition, then do A, else do B"

Execute based on a boolean condition.

**Phrases**:
| Phrase | Meaning |
|--------|---------|
| "if X then Y" | Do Y when X is true |
| "when X" | Do when X is true |
| "unless X" | Do when X is NOT true |
| "otherwise" / "else" | Alternative branch |

**Key elements**:
- **Condition**: What is checked
- **True branch**: What happens if true
- **False branch**: What happens if not true (optional)

---

### 5. Selection
**Intent**: "Choose first valid from options"

Pick one result from multiple possibilities.

**Phrases**: "choose first", "select", "use X if available else Y", "prefer X otherwise Y"

**Key elements**:
- **Options**: The choices available
- **Priority**: Which to try first

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
  "patterns": [
    {
      "type": "iteration" | "conditional" | "selection" | "grouping" | "linear" | "multi_input",
      "trigger_phrase": "The phrase indicating this pattern",
      "elements": {
        "collection": "for iteration: what is iterated",
        "current_item": "for iteration: the per-item variable",
        "condition": "for conditional: what is checked",
        "true_branch": "for conditional: what happens if true",
        "false_branch": "for conditional: what happens if not true",
        "options": "for selection: the choices",
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
```

---

## Example

**Instruction**: "For each file, read content. If valid JSON, parse and add to results. Otherwise log error. Bundle results and errors into report."

```json
{
  "thinking": "'For each file' = iteration. 'If valid JSON' = conditional with two branches. 'Bundle results and errors' = grouping.",
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
```

---

## Common Mistakes

1. **Missing both branches**: "if X then Y, otherwise Z" has TWO conditional patterns
2. **Confusing selection with conditional**: Selection chooses between options; conditional gates execution
3. **Missing loop variable**: "for each X" implies both "Xs" (collection) and "X" (current item)

---

## Now Extract

$input_1
