# Quantification in NormCode Framework

## Overview

Quantification in the NormCode framework is a formal process for iterating over elements of a concept, applying inference, and aggregating results. It is implemented as a sequence of well-defined steps, each with a specific role in the quantification pipeline. The process is orchestrated by an agent (e.g., `QuantAgent`) and supported by utility classes such as `Quantifier`.

---

## Quantification Operator Syntax

The quantification operator in NormCode is described by the following template:

```
*every(_loopBaseConcept_)%:[_viewAxis_].[_conceptToInfer_?]@(_loopIndex_)^(_inLoopConcept_<*_carryoverCondition_>)
```

- `*every(...)` — Quantifies (loops) over a base concept.
- `%:[...]` — Specifies axes or dimensions to view/group by.
- `.[...]` — Specifies the concept(s) to infer.
- `@(...)` — (Optional) Loop index.
- `^(...)` — (Optional) In-loop concept, possibly with a carryover condition (`<*...>`).

---

## Quantification Sequence Steps

The quantification process is broken down into the following steps:

1. **Input Working Configuration (IWC):**
   - Sets up the initial working configuration for the quantification process.
2. **Memorized Values Perception (MVP):**
   - Retrieves references for value concepts, ordered as required by the function concept.
3. **Cross Perception (CP):**
   - Produces the cross product of the perception references.
4. **Formal Actuator Perception (FAP):**
   - Parses the quantification operator and returns a function for grouping/crossing references, along with the parsed structure.
5. **Group Perception (GP):**
   - Applies the formal actuator function to the perception references to produce the list of elements to loop over.
6. **Context Value Perception (CVP):**
   - Determines if the current loop element is new (i.e., not yet processed).
7. **Actuator Value Perception (AVP):**
   - Retrieves the current value for the concept to infer.
8. **Perception Tool Actuation (PTA):**
   - Updates the workspace with the new looped element and its result.
9. **Grouping Actuation (GA):**
   - Combines all processed elements for the concept to infer into a single reference.
10. **Memory Actuation (MA):**
    - (Placeholder) Updates memory with the combined reference.
11. **Return Reference (RR):**
    - Assigns the combined reference to the concept to infer and returns it.
12. **Output Working Configuration (OWC):**
    - Checks if all loop elements have been processed and sets the completion status in the working configuration.

---

## The `Quantifier` Class

The `Quantifier` class is a stateful utility that manages the workspace for quantification. It is responsible for:

- Initializing and managing sub-workspaces for each quantification loop.
- Storing and retrieving looped elements and their results.
- Checking if all required elements have been processed.
- Combining results for output.

### Key Methods
- `store_new_base_element`: Records a new looped element in the workspace.
- `store_new_in_loop_element`: Records the result for a concept to infer for a given looped element.
- `check_all_base_elements_looped`: Checks if all required elements have been processed.
- `combine_all_looped_elements_by_concept`: Aggregates results for output.
- `retireve_next_base_element`: Retrieves the next unprocessed element.

---

## Mapping: Sequence Steps to Methods

| Sequence Step | Method Name                        | Uses Quantifier? | Role of Quantifier in Step                                  |
|---------------|------------------------------------|------------------|-------------------------------------------------------------|
| IWC           | input_working_configurations       | No               | N/A                                                         |
| MVP           | memorized_values_perception        | No               | N/A                                                         |
| CP            | cross_product (inline)             | No               | N/A                                                         |
| FAP           | formal_actuator_perception         | No               | N/A                                                         |
| GP            | group_perception                   | No               | N/A                                                         |
| CVP           | context_value_perception           | Yes              | Checks if element is new                                    |
| AVP           | actuator_value_perception          | No               | N/A                                                         |
| PTA           | perception_tool_actuation          | Yes              | Stores new elements/results in workspace                    |
| GA            | grouping_actuation                 | Yes              | Combines all processed elements for output                  |
| MA            | memory_actuation                   | No               | (Placeholder)                                               |
| RR            | return_reference                   | No               | Assigns combined reference to concept                       |
| OWC           | output_working_configurations      | Yes              | Checks if all elements are processed (completion status)    |

---

## Example: Quantification Flow

1. **Setup:** Agent initializes with concepts and working configuration.
2. **IWC:** Initial configuration is prepared.
3. **MVP/CP:** Value concepts are retrieved and crossed.
4. **FAP/GP:** Operator is parsed and elements to loop over are determined.
5. **CVP:** For each element, check if it is new.
6. **AVP/PTA:** If new, retrieve value and store in workspace.
7. **GA:** Aggregate results for output.
8. **MA/RR/OWC:** Finalize, return results, and update completion status.

---

## References
- See `core/_new_np/_methods/_quantification_demo.py` for implementation details.
- See `core/_new_np/example_math.py` for agent orchestration and usage examples.

---

This document provides a high-level and practical overview for developers and users working with quantification in the NormCode framework. 