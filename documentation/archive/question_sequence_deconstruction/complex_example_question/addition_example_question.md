# Norm-text Deconstruction by Question Sequencing - Algorithm Example

This document provides an example of how to deconstruct norm-text by sequencing questions, focusing on algorithmic instructions.

## Example: Human-style Addition Algorithm

**Original Norm-text:**
Algorithm: Human-style Addition (Digit-by-digit)
Input: Two natural numbers as strings (e.g., "456" and "789")
Output: Their sum as a string (e.g., "1245")

Reverse both number strings (so we add from right to left).

Initialize carry = 0 and result = "".

Loop through each digit (from least significant to most) of the longer number:

Get the current digit from each number (use 0 if one is shorter).

Add the two digits plus the carry.

The digit to store is sum % 10.

Update carry as sum // 10.

Append the digit to the result.

After the loop, if carry > 0, append it to the result.

Reverse the result to get the final answer.

**Deconstruction Process:**

**Step 1: Identify the main question**
- What are the steps of human-style addition?  
  # This step captures the definitional nature of the norm-text. Since the text defines the steps of the human-style addition algorithm, the main question focuses on identifying the sequence of steps.

**Step 2: Generate sub-questions to capture the flow of the norm-text**
- What are the steps of human-style addition?  
  # This sub-question asks for the definition of the steps that make up the human-style addition algorithm, corresponding to the assignment condition.

**Step 3: Rewrite norm-text sentences to directly answer each sub-question**
- Human-style addition consists of steps in step 1, step 2, step 3, step 4, and step 5.
  # This answer directly addresses the definition of the steps that make up human-style addition, matching the first sub-question.

**Step 2a: What is step 1?**
- What step 1 does?  
  # This question identifies what the nominalized imperative of the first step performs.

**Step 3a: Rewrite to answer what is step 1**
- Step 1 does reverse both number strings (so we add from right to left).
  # This answer specifies what the first step imperative performs.

**Step 2b: What is step 2?**
- What step 2 does?  
  # This question identifies what the nominalized imperative of the second step performs.

**Step 3b: Rewrite to answer what is step 2**
- Step 2 does initialize carry = 0 and result = "".
  # This answer specifies what the second step imperative performs.

**Step 2c: What is step 3?**
- What step 3 does?  
  # This question identifies what the nominalized imperative of the third step performs.

**Step 3c: Rewrite to answer what is step 3**
- Step 3 does loop through each digit (from least significant to most) of the longer number: Get the current digit from each number (use 0 if one is shorter). Add the two digits plus the carry. The digit to store is sum % 10. Update carry as sum // 10. Append the digit to the result.
  # This answer specifies what the third step imperative performs, treating the loop body as a single operation.

**Level 2 Deconstruction - Loop Analysis:**

**Step 2c1: What is the loop?**
- What is the loop?  
  # This question identifies the loop structure within step 3.

**Step 3c1: Rewrite to answer what is the loop**
- The loop is: Get the current digit from each number (use 0 if one is shorter). Add the two digits plus the carry. The digit to store is sum % 10. Update carry as sum // 10. Append the digit to the result.
  # This answer specifies what the loop does - the steps within the loop iteration.

**Step 2c2: When does loop continue?**
- When does loop continue?  
  # This question identifies the continuation condition of the loop.

**Step 3c2: Rewrite to answer when does loop continue**
- Loop continues when there are digits of the longer number.
  # This answer specifies the loop continuation condition.

**Level 3 Deconstruction - Loop Steps:**

**Step 2c3: What is the one loop?**
- What is the one loop?  
  # This question identifies what constitutes a single iteration of the loop.

**Step 3c3: Rewrite to answer what is the one loop**
- The one loop is: Get the current digit from each number (use 0 if one is shorter). Add the two digits plus the carry. The digit to store is sum % 10. Update carry as sum // 10. Append the digit to the result.
  # This answer specifies what happens in one complete loop iteration.

**Step 2c4: What does loop step 1 do?**
- What does loop step 1 do?  
  # This question identifies the first substep within the loop iteration.

**Step 3c4: Rewrite to answer what does loop step 1 do**
- Loop step 1 does get the current digit from each number (use 0 if one is shorter).
  # This answer specifies the first substep of the loop iteration.

**Step 2c5: What does loop step 2 do?**
- What does loop step 2 do?  
  # This question identifies the second substep within the loop iteration.

**Step 3c5: Rewrite to answer what does loop step 2 do**
- Loop step 2 does add the two digits plus the carry.
  # This answer specifies the second substep of the loop iteration.

**Step 2c6: What does loop step 3 do?**
- What does loop step 3 do?  
  # This question identifies the third substep within the loop iteration.

**Step 3c6: Rewrite to answer what does loop step 3 do**
- Loop step 3 does the digit to store is sum % 10.
  # This answer specifies the third substep of the loop iteration.

**Step 2c7: What does loop step 4 do?**
- What does loop step 4 do?  
  # This question identifies the fourth substep within the loop iteration.

**Step 3c7: Rewrite to answer what does loop step 4 do**
- Loop step 4 does update carry as sum // 10.
  # This answer specifies the fourth substep of the loop iteration.

**Step 2c8: What does loop step 5 do?**
- What does loop step 5 do?  
  # This question identifies the fifth substep within the loop iteration.

**Step 3c8: Rewrite to answer what does loop step 5 do**
- Loop step 5 does append the digit to the result.
  # This answer specifies the fifth substep of the loop iteration.

**Step 2d: What is step 4?**
- What step 4 does?  
  # This question identifies what the nominalized imperative of the fourth step performs.

**Step 3d: Rewrite to answer what is step 4**
- Step 4 does after the loop, if carry > 0, append it to the result.
  # This answer specifies what the fourth step imperative performs.

**Step 2e: What is step 5?**
- What step 5 does?  
  # This question identifies what the nominalized imperative of the fifth step performs.

**Step 3e: Rewrite to answer what is step 5**
- Step 5 does reverse the result to get the final answer.
  # This answer specifies what the fifth step imperative performs.

**Step 4: Rewrite each question with NormCode**
- What are the steps of human-style addition? → $what?({human-style addition steps}, $=)  
  # Question condition: assignment ($=) - establishes identity/definition, Question target: human-style addition steps (object) - the sequence of steps being defined
- What step 1 does? → $what?({human-style addition step_1}, $::)  
  # Question condition: nominalization assignment ($::) - converts imperative to object, Question target: human-style addition step_1 (object) - the first step imperative being nominalized
- What step 2 does? → $what?({human-style addition step_2}, $::)  
  # Question condition: nominalization assignment ($::) - converts imperative to object, Question target: human-style addition step_2 (object) - the second step imperative being nominalized
- What step 3 does? → $what?({human-style addition step_3}, $::)  
  # Question condition: nominalization assignment ($::) - converts imperative to object, Question target: human-style addition step_3 (object) - the third step imperative being nominalized
- What step 4 does? → $what?({human-style addition step_4}, $::)  
  # Question condition: nominalization assignment ($::) - converts imperative to object, Question target: human-style addition step_4 (object) - the fourth step imperative being nominalized
- What step 5 does? → $what?({human-style addition step_5}, $::)  
  # Question condition: nominalization assignment ($::) - converts imperative to object, Question target: human-style addition step_5 (object) - the fifth step imperative being nominalized

**Level 2 NormCode Translations:**
- What is the loop? → $what?({loop}, $::)  
  # Question condition: nominalization assignment ($::) - converts loop imperative to object, Question target: loop (object) - the loop structure being defined
- When does loop continue? → $when?($::({loop}?), @while)  
  # Question condition: while (@while) - indicates looping condition, Question target: loop continuation (object) - the condition for loop continuation

**Level 3 NormCode Translations:**
- What is the one loop? → $what?({one loop}, $=)  
  # Question condition: assignment ($=) - establishes identity/definition, Question target: one loop (object) - the single iteration being defined
- What does loop step 1 do? → $what?({loop step_1}, $::)  
  # Question condition: nominalization assignment ($::) - converts imperative to object, Question target: loop step_1 (object) - the first loop substep being nominalized
- What does loop step 2 do? → $what?({loop step_2}, $::)  
  # Question condition: nominalization assignment ($::) - converts imperative to object, Question target: loop step_2 (object) - the second loop substep being nominalized
- What does loop step 3 do? → $what?({loop step_3}, $::)  
  # Question condition: nominalization assignment ($::) - converts imperative to object, Question target: loop step_3 (object) - the third loop substep being nominalized
- What does loop step 4 do? → $what?({loop step_4}, $::)  
  # Question condition: nominalization assignment ($::) - converts imperative to object, Question target: loop step_4 (object) - the fourth loop substep being nominalized
- What does loop step 5 do? → $what?({loop step_5}, $::)  
  # Question condition: nominalization assignment ($::) - converts imperative to object, Question target: loop step_5 (object) - the fifth loop substep being nominalized

**Output:**

```json
{
  "norm_text": "Algorithm: Human-style Addition (Digit-by-digit)\nInput: Two natural numbers as strings (e.g., \"456\" and \"789\")\nOutput: Their sum as a string (e.g., \"1245\")\n\nReverse both number strings (so we add from right to left).\n\nInitialize carry = 0 and result = \"\".\n\nLoop through each digit (from least significant to most) of the longer number:\n\nGet the current digit from each number (use 0 if one is shorter).\n\nAdd the two digits plus the carry.\n\nThe digit to store is sum % 10.\n\nUpdate carry as sum // 10.\n\nAppend the digit to the result.\n\nAfter the loop, if carry > 0, append it to the result.\n\nReverse the result to get the final answer.",
  "deconstruction": {
    "level_1": {
      "step_identification": {
        "formal_question": "$what?({human-style addition steps}, $=)",
        "natural_question": "What are the steps of human-style addition?",
        "natural_answer": "Human-style addition consists of steps in step 1, step 2, step 3, step 4, and step 5."
      },
      "step_1_identification": {
        "formal_question": "$what?({human-style addition step_1}, $::)",
        "natural_question": "What step 1 does?",
        "natural_answer": "Step 1 does reverse both number strings (so we add from right to left)."
      },
      "step_2_identification": {
        "formal_question": "$what?({human-style addition step_2}, $::)",
        "natural_question": "What step 2 does?",
        "natural_answer": "Step 2 does initialize carry = 0 and result = \"\"."
      },
      "step_3_identification": {
        "formal_question": "$what?({human-style addition step_3}, $::)",
        "natural_question": "What step 3 does?",
        "natural_answer": "Step 3 does loop through each digit (from least significant to most) of the longer number: Get the current digit from each number (use 0 if one is shorter). Add the two digits plus the carry. The digit to store is sum % 10. Update carry as sum // 10. Append the digit to the result."
      },
      "step_4_identification": {
        "formal_question": "$what?({human-style addition step_4}, $::)",
        "natural_question": "What step 4 does?",
        "natural_answer": "Step 4 does after the loop, if carry > 0, append it to the result."
      },
      "step_5_identification": {
        "formal_question": "$what?({human-style addition step_5}, $::)",
        "natural_question": "What step 5 does?",
        "natural_answer": "Step 5 does reverse the result to get the final answer."
      }
    },
    "level_2": {
      "step_3_loop_analysis": {
        "loop_identification": {
          "formal_question": "$what?({loop}, $::)",
          "natural_question": "What is the loop?",
          "natural_answer": "The loop is: Get the current digit from each number (use 0 if one is shorter). Add the two digits plus the carry. The digit to store is sum % 10. Update carry as sum // 10. Append the digit to the result."
        },
        "loop_continuation": {
          "formal_question": "$when?($::({loop}?), @while)",
          "natural_question": "When does loop continue?",
          "natural_answer": "Loop while there are digits of the longer number."
        }
      }
    },
    "level_3": {
      "step_3_loop_steps": {
        "one_loop_identification": {
          "formal_question": "$what?({one loop}, $=)",
          "natural_question": "What is the one loop?",
          "natural_answer": "The one loop is: Get the current digit from each number (use 0 if one is shorter). Add the two digits plus the carry. The digit to store is sum % 10. Update carry as sum // 10. Append the digit to the result."
        },
        "loop_step_1": {
          "formal_question": "$what?({loop step_1}, $::)",
          "natural_question": "What does loop step 1 do?",
          "natural_answer": "Loop step 1 does get the current digit from each number (use 0 if one is shorter)."
        },
        "loop_step_2": {
          "formal_question": "$what?({loop step_2}, $::)",
          "natural_question": "What does loop step 2 do?",
          "natural_answer": "Loop step 2 does add the two digits plus the carry."
        },
        "loop_step_3": {
          "formal_question": "$what?({loop step_3}, $::)",
          "natural_question": "What does loop step 3 do?",
          "natural_answer": "Loop step 3 does the digit to store is sum % 10."
        },
        "loop_step_4": {
          "formal_question": "$what?({loop step_4}, $::)",
          "natural_question": "What does loop step 4 do?",
          "natural_answer": "Loop step 4 does update carry as sum // 10."
        },
        "loop_step_5": {
          "formal_question": "$what?({loop step_5}, $::)",
          "natural_question": "What does loop step 5 do?",
          "natural_answer": "Loop step 5 does append the digit to the result."
        }
      }
    }
  },
  "question_hierarchy": {
    "main_question": "What are the steps of human-style addition?",
    "sub_questions": [
      "What step 1 does?",
      "What step 2 does?",
      "What step 3 does?",
      "What step 4 does?",
      "What step 5 does?"
    ],
    "level_2_questions": {
      "What step 3 does?": [
        "What is the loop?",
        "When does loop continue?"
      ]
    },
    "level_3_questions": {
      "What is the loop?": [
        "What is the one loop?",
        "What does loop step 1 do?",
        "What does loop step 2 do?",
        "What does loop step 3 do?",
        "What does loop step 4 do?",
        "What does loop step 5 do?"
      ]
    }
  },
  "qa_hierarchy": {
    "main_qa": {
      "formal_question": "$what?({human-style addition steps}, $=)",
      "natural_answer": "Human-style addition consists of steps in step 1, step 2, step 3, step 4, and step 5."
    },
    "sub_qa": [
      {
        "formal_question": "$what?({human-style addition step_1}, $::)",
        "natural_answer": "Step 1 does reverse both number strings (so we add from right to left)."
      },
      {
        "formal_question": "$what?({human-style addition step_2}, $::)",
        "natural_answer": "Step 2 does initialize carry = 0 and result = \"\"."
      },
      {
        "formal_question": "$what?({human-style addition step_3}, $::)",
        "natural_answer": "Step 3 does loop through each digit (from least significant to most) of the longer number: Get the current digit from each number (use 0 if one is shorter). Add the two digits plus the carry. The digit to store is sum % 10. Update carry as sum // 10. Append the digit to the result."
      },
      {
        "formal_question": "$what?({human-style addition step_4}, $::)",
        "natural_answer": "Step 4 does after the loop, if carry > 0, append it to the result."
      },
      {
        "formal_question": "$what?({human-style addition step_5}, $::)",
        "natural_answer": "Step 5 does reverse the result to get the final answer."
      }
    ],
    "level_2_qa": {
      "$what?({human-style addition step_3}, $::)": [
        {
          "formal_question": "$what?({loop}, $::)",
          "natural_answer": "The loop is: Get the current digit from each number (use 0 if one is shorter). Add the two digits plus the carry. The digit to store is sum % 10. Update carry as sum // 10. Append the digit to the result."
        },
        {
          "formal_question": "$when?($::({loop}?), @while)",
          "natural_answer": "Loop continues when there are digits of the longer number."
        }
      ]
    },
    "level_3_qa": {
      "$what?({loop}, $::)": [
        {
          "formal_question": "$what?({one loop}, $=)",
          "natural_answer": "The one loop is: Get the current digit from each number (use 0 if one is shorter). Add the two digits plus the carry. The digit to store is sum % 10. Update carry as sum // 10. Append the digit to the result."
        },
        {
          "formal_question": "$what?({loop step_1}, $::)",
          "natural_answer": "Loop step 1 does get the current digit from each number (use 0 if one is shorter)."
        },
        {
          "formal_question": "$what?({loop step_2}, $::)",
          "natural_answer": "Loop step 2 does add the two digits plus the carry."
        },
        {
          "formal_question": "$what?({loop step_3}, $::)",
          "natural_answer": "Loop step 3 does the digit to store is sum % 10."
        },
        {
          "formal_question": "$what?({loop step_4}, $::)",
          "natural_answer": "Loop step 4 does update carry as sum // 10."
        },
        {
          "formal_question": "$what?({loop step_5}, $::)",
          "natural_answer": "Loop step 5 does append the digit to the result."
        }
      ]
    }
  },
  "normcode_mapping": {
    "assignment": "$=",
    "nominalization": "$::",
    "object_while_loop": "@while"
  }
}
```

## Key Insights from Algorithm Example

1. **Complex Algorithm Handling**: The deconstruction process works for complex algorithmic instructions with multiple detailed steps.

2. **Step-by-Step Breakdown**: Complex algorithms benefit from the hinging question approach to break down into individual steps.

3. **Algorithmic Flow**: The method captures the logical flow of algorithmic operations from initialization to completion.

4. **Technical Instruction Analysis**: Shows how technical, mathematical algorithms can be systematically deconstructed.

5. **Multi-Step Process Management**: Demonstrates handling of algorithms with many sequential steps.

6. **Computational Logic**: Reveals the underlying logical structure of computational processes.

7. **Loop Consolidation**: The looping steps are treated as a single cohesive operation rather than being broken down individually, maintaining the logical grouping of related operations.

8. **Multi-Level Deconstruction**: Complex steps can be further deconstructed into multiple levels, allowing for granular analysis of algorithmic components.

9. **Loop Analysis**: Loops can be analyzed at multiple levels:
    - Level 2: Loop structure identification and continuation conditions
    - Level 3: Individual loop iteration steps and substeps

10. **@when Condition Usage**: The `@while` condition in `$when?($::({loop}?), @while)` demonstrates how to handle looping constructs in NormCode, where `@when` indicates the temporal/conditional nature of the question.

11. **Hierarchical Question Structure**: The methodology supports nested question hierarchies that mirror the complexity of algorithmic structures.

12. **Granular Control**: Different levels of abstraction can be chosen based on the desired level of detail in the analysis.

## Comparison with Other Examples

| Example Type | Main Question | Pattern | Complexity | Steps |
|--------------|---------------|---------|------------|-------|
| User Account | "How to do?" | Imperative | Simple | 1 |
| Butterfly | "What is butterfly?" | Descriptive | Simple | 2 |
| Cookie Recipe | "How to do?" | Imperative | Complex | 3 |
| Stereotype | "What is stereotype?" | Descriptive | Complex | 3 |
| Addition Algorithm | "What is human-style addition?" | Descriptive | Complex | 5 |

This algorithm example demonstrates that the norm-text deconstruction methodology can handle highly complex, multi-step algorithmic instructions while maintaining the same systematic approach and providing complete traceability of each step. The consolidation of looping steps shows how the methodology can adapt to different levels of granularity based on the logical grouping of operations. The example also shows how algorithmic definitions can be treated as descriptive patterns rather than imperative instructions, capturing the essence of what the algorithm is rather than just how to execute it.
