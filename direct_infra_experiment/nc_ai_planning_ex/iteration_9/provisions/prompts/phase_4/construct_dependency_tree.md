# Construct Dependency Tree

## Task

Build a **dependency tree** structure from the goal concept, working backwards through operations and dependencies. This tree represents the complete computation structure.

## Inputs

- `input_1` — The goal/root concept (final output concept)
- `input_2` — Operations with their pattern classifications (classified operations)
- `input_3` — Dependency relationships between concepts/operations (all dependencies)

---

## The Core Derivation Algorithm

From `derivation_v2.md`, tree construction follows this recursive process:

> **"What do I need to produce this?"**

Applied recursively:
1. What's the final output? → This is the goal (root)
2. What operation produces it? → First child of goal
3. What inputs does that operation need? → Children of operation
4. For each input: go back to step 2

**This recursion builds the tree.**

---

## The Tree Structure

Every node in the tree represents either:
- A **concept** (data that exists)
- An **operation** (transformation that produces data)

Each node has:
| Field | Description |
|-------|-------------|
| `concept` | The concept at this node |
| `producer` | The operation that produces this concept (null if ground) |
| `pattern` | The pattern type (linear, multi_input, iteration, etc.) |
| `children` | Concepts this node's producer needs as inputs |
| `context` | Loop/conditional context if inside control flow |
| `is_ground` | True if this is an input (no producer) |

---

## The Five Core Patterns

When constructing the tree, each operation maps to one of these patterns:

### Pattern 1: Linear Chain
**Structure**: Single input → operation → single output

```
output
└── operation
    └── input
```

### Pattern 2: Multiple Inputs
**Structure**: Multiple inputs → operation → single output

```
output
└── operation
    ├── input 1
    └── input 2
```

### Pattern 3: Iteration
**Structure**: Collection → for-each → aggregated results

```
all results
└── for each item
    ├── result (per-item)
    │   └── process item
    │       └── current item (loop var)
    └── items (collection) [context]
```

**Key**: The collection being iterated is marked as **context**.

### Pattern 4: Conditional
**Structure**: Condition gates execution

```
result
└── operation (gated)
    ├── inputs
    └── condition [context]
```

**Key**: The condition is marked as **context**.

### Pattern 5: Grouping
**Structure**: Multiple items bundled together

```
bundle
└── group operation
    ├── item 1
    ├── item 2
    └── item 3
```

---

## Building the Tree: Step by Step

### Step 1: Start from Goal
The goal becomes the root node.

```json
{
  "root": "summary report",
  "nodes": {
    "summary report": { "is_ground": false, ... }
  }
}
```

### Step 2: Find Producer
Look at dependencies to find what operation produces the goal.

**Look for**: `dependency where target = goal`  
**The source operation** is the producer.

```json
"summary report": {
  "producer": "generate summary",
  ...
}
```

### Step 3: Find Inputs
Look at dependencies to find what the producer operation needs.

**Look for**: `dependency where source = producer operation and type = "needs"`

```json
"summary report": {
  "producer": "generate summary",
  "children": ["all sentiments", "review count"],
  ...
}
```

### Step 4: Recurse
For each child that isn't a ground concept (input), repeat steps 2-3.

### Step 5: Handle Control Flow

**For Iterations**:
- The loop operation's children include:
  - The per-item result
  - The collection being iterated (marked as context)

**For Conditionals**:
- The gated operation's children include:
  - Normal inputs
  - The condition (marked as context)

---

## Ground Concepts

**Ground concepts** are the leaves of the tree:
- They have no producer (no operation produces them)
- They're the initial inputs to the plan
- In dependencies, they only appear as sources, never as targets

Mark these with `"is_ground": true`.

---

## Output Format

```json
{
  "thinking": "Your tree construction process",
  "result": {
    "tree": {
      "root": "goal concept name",
      "nodes": {
        "concept name": {
          "producer": "operation name or null if ground",
          "pattern": "linear | multi_input | judgement | iteration | conditional | selection | grouping | null",
          "children": ["child concept names"],
          "context": "context concept for loops/conditions, or null",
          "is_ground": true | false
        }
      }
    },
    "ground_concepts": ["list of input concepts with no producer"],
    "depth": 0
  }
}
```

**Important**: Put the tree in the `result` field. The `thinking` field is for your reasoning only.

---

## Complete Example

**Goal**: `summary report`

**Classified Operations**:
- `generate summary` (multi_input, llm)
- `for each review` (iteration, orchestrator)
- `extract sentiment` (linear, llm)

**Dependencies**:
- generate summary needs all sentiments
- generate summary needs review count
- for each review needs reviews (collection)
- for each review produces sentiment (per-item)
- extract sentiment needs current review
- extract sentiment produces sentiment

**Tree Construction**:

```json
{
  "thinking": "Starting from goal 'summary report'. Producer is 'generate summary' (multi_input). It needs 'all sentiments' and 'review count'. 'review count' is ground (input). 'all sentiments' is produced by 'for each review' (iteration). The iteration needs 'reviews' (context, ground) and produces 'sentiment' per-item. Each 'sentiment' is produced by 'extract sentiment' (linear) which needs 'current review' (loop variable).",
  "result": {
    "tree": {
      "root": "summary report",
      "nodes": {
        "summary report": {
          "producer": "generate summary",
          "pattern": "multi_input",
          "children": ["all sentiments", "review count"],
          "context": null,
          "is_ground": false
        },
        "all sentiments": {
          "producer": "for each review",
          "pattern": "iteration",
          "children": ["sentiment"],
          "context": "reviews",
          "is_ground": false
        },
        "sentiment": {
          "producer": "extract sentiment",
          "pattern": "linear",
          "children": ["current review"],
          "context": null,
          "is_ground": false
        },
        "current review": {
          "producer": null,
          "pattern": null,
          "children": [],
          "context": null,
          "is_ground": false,
          "note": "loop variable - bound by iteration context"
        },
        "reviews": {
          "producer": null,
          "pattern": null,
          "children": [],
          "context": null,
          "is_ground": true
        },
        "review count": {
          "producer": null,
          "pattern": null,
          "children": [],
          "context": null,
          "is_ground": true
        }
      }
    },
    "ground_concepts": ["reviews", "review count"],
    "depth": 4
  }
}
```

**Visual Tree**:
```
summary report
└── generate summary (multi_input)
    ├── all sentiments
    │   └── for each review (iteration)
    │       ├── sentiment
    │       │   └── extract sentiment (linear)
    │       │       └── current review (loop var)
    │       └── reviews [context, ground]
    └── review count [ground]
```

---

## Common Mistakes

| Mistake | Why It's Wrong | Correct Approach |
|---------|----------------|------------------|
| Circular dependencies | Trees are acyclic | Check for cycles during construction |
| Missing ground concepts | Every path must end at input | Trace all paths to leaves |
| Wrong context placement | Context marks control, not data | Only loop base and conditions are context |
| Orphan operations | Every operation must produce something | Verify all operations connect to tree |
| Depth miscalculation | Depth is longest path | Count from root to deepest ground |

---

## Data to Analyze

### Goal
$input_1

### Classified Operations
$input_2

### Dependencies
$input_3
