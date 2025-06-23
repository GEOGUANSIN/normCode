# Norm-text Deconstruction by Question Sequencing - Example

This document provides concrete examples of how to deconstruct norm-text by sequencing questions, focusing on identifying the correct main question and its sub-questions.

## Example 1: User Account Creation

**Original Norm-text:**
Create a user account with email and password. The account has admin privileges and is active by default.

**Deconstruction Process:**

**Step 1: Identify the main question**
- How to do?  
  # This step captures the imperative/instructional nature of the norm-text. Since the text begins with an imperative ("Create..."), the main question focuses on the method or process of carrying out the instruction. We use the generic "do" as the question target to maintain minimal knowledge of the imperative.

**Step 2: For each aspect, generate sub-questions**
- How to do?  
  # This sub-question asks for the specific method or process by which the imperative is carried out, corresponding to the imperative sequence condition.
- Given it is done by the method, then it makes what happen?  
  # This sub-question identifies the restrictive conditional relationship, asking what consequence occurs given that the imperative has been performed by the specified method.

**Step 3: Rewrite norm-text sentences to directly answer each sub-question**
- Create a user account with email and password.  
  # This answer directly addresses the method by which the imperative is performed, matching the first sub-question.
- The account has admin privileges and is active by default.  
  # This answer specifies the consequence that occurs when the imperative is performed, providing a clear response to the second sub-question.

**Step 4: Rewrite each question with NormCode**
- How to do? → $how?(::(do), @by)  
  # Question condition: imperative sequence (@by) - specifies method/process, Question target: do (imperative) - the imperatives to be performed
- Given it is done by the method, then it makes what happen? → $when?(::(do)@by, @onlyIf)  
  # Question condition: judgement sequence (@onlyIf) - consequence judgement, Question target: do (imperative) - the imperatives with conditions

**Output:**

```json
{
  "norm_text": "Create a user account with email and password. The account has admin privileges and is active by default.",
  "deconstruction": {
    "level_1": {
      "main_process": {
        "formal_question": "$how?(::(do), @by)",
        "natural_question": "How to do?",
        "natural_answer": "Create a user account with email and password."
      },
      "consequence": {
        "formal_question": "$when?(::(do)@by, @onlyIf)",
        "natural_question": "Given it is done by the method, then it makes what happen?",
        "natural_answer": "The account has admin privileges and is active by default."
      }
    }
  },
  "question_hierarchy": {
    "main_question": "How to do?",
    "sub_questions": [
      "How to do?",
      "Given it is done by the method, then it makes what happen?"
    ]
  },
  "qa_hierarchy": {
    "main_qa": {
      "formal_question": "$how?(::(do), @by)",
      "natural_answer": "Create a user account with email and password."
    },
    "sub_qa": [
      {
        "formal_question": "$how?(::(do), @by)",
        "natural_answer": "Create a user account with email and password."
      },
      {
        "formal_question": "$when?(::(do)@by, @onlyIf)",
        "natural_answer": "The account has admin privileges and is active by default."
      }
    ]
  },
  "normcode_mapping": {
    "imperative_sequence": "@by",
    "judgement_sequence": "@onlyIf",
    "assignment": "$=",
    "nominalization": "$::"
  }
}
```

## Example 2: Butterfly Lifecycle

**Original Norm-text:**
Butterfly eggs hatch into caterpillars. The caterpillars form chrysalises and emerge as adult butterflies.

**Deconstruction Process:**

**Step 1: Identify the main question**
- What is butterfly?  
  # This step captures the descriptive nature of the norm-text. Since the text describes what a butterfly is and its lifecycle, the main question focuses on establishing the identity assignment of the entity.

**Step 2: For each aspect, generate sub-questions**
- What is butterfly?  
  # This sub-question establishes the basic identity assignment of butterfly, corresponding to the assignment condition.
- Given butterfly exists, then what makes butterfly?  
  # This sub-question identifies the antecedent condition, asking what characteristics define butterfly given that butterfly has an identity.
- Given butterfly is made to exist, then it makes what happen?  
  # This sub-question identifies the restrictive consequence condition, asking what process occurs given that butterfly exists and has been defined.

**Step 3: Rewrite norm-text sentences to directly answer each sub-question**
- Butterfly is butterfly.
  # This tautology establishes the basic identity assignment of butterfly, answering the first question and serving as the foundation for subsequent questions.
- Butterfly eggs hatch into caterpillars.  
  # This answer directly addresses what makes butterfly when identity is assigned, matching the second sub-question.
- The caterpillars form chrysalises and emerge as adult butterflies.  
  # This answer specifies the consequence that occurs when both antecedent conditions are met, providing a clear response to the third sub-question.

**Step 4: Rewrite each question with NormCode**
- What is butterfly? → $what?({butterfly}, $=)
  # Question condition: assignment ($=) - establishes identity/definition, Question target: butterfly (object) - the entity being defined
- Given butterfly exists, then what makes butterfly? → $when?($=({butterfly}), @If)  
  # Question condition: judgement sequence (@If) - antecedent judgement, Question target: $=({butterfly}) - the defined butterfly entity
- Given butterfly is made to exist, then it makes what happen? → $when?(@If($=({butterfly})), @onlyIf)  
  # Question condition: judgement sequence (@onlyIf) - consequence judgement, Question target: @If($=({butterfly})) - the conditional butterfly definition

**Output:**

```json
{
  "norm_text": "Butterfly eggs hatch into caterpillars. The caterpillars form chrysalises and emerge as adult butterflies.",
  "deconstruction": {
    "level_1": {
      "main_entity": {
        "formal_question": "$what?({butterfly}, $=)",
        "natural_question": "What is butterfly?",
        "natural_answer": "Butterfly is butterfly."
      },
      "antecedent": {
        "formal_question": "$when?($=({butterfly}), @If)",
        "natural_question": "Given butterfly exists, then what makes butterfly?",
        "natural_answer": "Butterfly eggs hatch into caterpillars."
      },
      "consequence": {
        "formal_question": "$when?(@If($=({butterfly})), @onlyIf)",
        "natural_question": "Given butterfly is made to exist, then it makes what happen?",
        "natural_answer": "The caterpillars form chrysalises and emerge as adult butterflies."
      }
    }
  },
  "question_hierarchy": {
    "main_question": "What is butterfly?",
    "sub_questions": [
      "What is butterfly?",
      "Given butterfly exists, then what makes butterfly?",
      "Given butterfly is made to exist, then it makes what happen?"
    ]
  },
  "qa_hierarchy": {
    "main_qa": {
      "formal_question": "$what?({butterfly}, $=)",
      "natural_answer": "Butterfly is butterfly."
    },
    "sub_qa": [
      {
        "formal_question": "$what?({butterfly}, $=)",
        "natural_answer": "Butterfly is butterfly."
      },
      {
        "formal_question": "$when?($=({butterfly}), @If)",
        "natural_answer": "Butterfly eggs hatch into caterpillars."
      },
      {
        "formal_question": "$when?(@If($=({butterfly})), @onlyIf)",
        "natural_answer": "The caterpillars form chrysalises and emerge as adult butterflies."
      }
    ]
  },
  "normcode_mapping": {
    "assignment": "$=",
    "judgement_sequence_antecedent": "@If",
    "judgement_sequence_consequence": "@onlyIf",
    "nominalization": "$::"
  }
}
```

## Example 3: Chocolate Chip Cookie Recipe

**Original Norm-text:**
Preheat the oven to 350°F. Mix flour, sugar, and butter until creamy. Add chocolate chips and bake for 12 minutes. The cookies are ready when golden brown.

**Deconstruction Process:**

**Step 1: Identify the main question**
- How to do?  
  # This step captures the imperative/instructional nature of the norm-text. Since the text begins with imperatives ("Preheat...", "Mix...", "Add...", "bake..."), the main question focuses on the method or process of carrying out the instructions. We use the generic "do" as the question target to maintain minimal knowledge of the imperative.

**Step 2: For each aspect, generate sub-questions**
- How to do?  
  # This sub-question asks for the specific method or process by which the imperatives are carried out, corresponding to the imperative sequence condition.
- Given it is done by the method, then it makes what happen?  
  # This sub-question identifies the restrictive conditional relationship, asking what consequence occurs given that the imperatives have been performed by the specified method.

**Step 3: Rewrite norm-text sentences to directly answer each sub-question**
- Preheat the oven to 350°F. Mix flour, sugar, and butter until creamy. Add chocolate chips and bake for 12 minutes.  
  # This answer directly addresses the method by which the imperatives are performed, matching the first sub-question.
- The cookies are ready when golden brown.  
  # This answer specifies the consequence that occurs when the imperatives are performed, providing a clear response to the second sub-question.

**Step 2a: Hinging question - What are the steps?**
- What are the steps to do?  
  # This hinging question identifies the individual steps that make up the overall process, establishing the sequence of actions required.

**Step 3a: Rewrite to answer the hinging question**
- Do steps in step 1, step 2 and step 3.  
  # This answer references the individual steps that are defined in the subsequent questions.

**Step 2a1: What is step 1?**
- What step 1 does?  
  # This question identifies what the nominalized imperative of the first step performs.

**Step 3a1: Rewrite to answer what is step 1**
- Step 1 does preheat the oven to 350°F.  
  # This answer specifies what the first step imperative performs.

**Step 2a2: What is step 2?**
- What step 2 does?  
  # This question identifies what the nominalized imperative of the second step performs.

**Step 3a2: Rewrite to answer what is step 2**
- Step 2 does mix flour, sugar, and butter until creamy.  
  # This answer specifies what the second step imperative performs.

**Step 2a3: What is step 3?**
- What step 3 does?  
  # This question identifies what the nominalized imperative of the third step performs.

**Step 3a3: Rewrite to answer what is step 3**
- Step 3 does add chocolate chips and bake for 12 minutes.  
  # This answer specifies what the third step imperative performs.

**Step 4: Rewrite each question with NormCode**
- How to do? → $how?(::(do), @by)  
  # Question condition: imperative sequence (@by) - specifies method/process, Question target: do (imperative) - the imperatives to be performed
- Given it is done by the method, then it makes what happen? → $when?(::(do)@by, @onlyIf)  
  # Question condition: judgement sequence (@onlyIf) - consequence judgement, Question target: do (imperative) - the imperatives with conditions
- What are the steps to do? → $what?({steps}, $=)  
  # Question condition: assignment ($=) - establishes identity/definition, Question target: steps (object) - the sequence of steps being defined
- What step 1 does? → $what?({step_1}, $::)  
  # Question condition: nominalization assignment ($::) - converts imperative to object, Question target: step_1 (object) - the first step imperative being nominalized
- What step 2 does? → $what?({step_2}, $::)  
  # Question condition: nominalization assignment ($::) - converts imperative to object, Question target: step_2 (object) - the second step imperative being nominalized
- What step 3 does? → $what?({step_3}, $::)  
  # Question condition: nominalization assignment ($::) - converts imperative to object, Question target: step_3 (object) - the third step imperative being nominalized

**Output:**

```json
{
  "norm_text": "Preheat the oven to 350°F. Mix flour, sugar, and butter until creamy. Add chocolate chips and bake for 12 minutes. The cookies are ready when golden brown.",
  "deconstruction": {
    "level_1": {
      "main_process": {
        "formal_question": "$how?(::(do), @by)",
        "natural_question": "How to do?",
        "natural_answer": "Preheat the oven to 350°F. Mix flour, sugar, and butter until creamy. Add chocolate chips and bake for 12 minutes."
      },
      "consequence": {
        "formal_question": "$when?(::(do)@by, @onlyIf)",
        "natural_question": "Given it is done by the method, then it makes what happen?",
        "natural_answer": "The cookies are ready when golden brown."
      }
    },
    "level_2": {
      "step_identification": {
        "formal_question": "$what?({steps}, $=)",
        "natural_question": "What are the steps to do?",
        "natural_answer": "Do steps in step 1, step 2 and step 3."
      },
      "step_1_identification": {
        "formal_question": "$what?({step_1}, $::)",
        "natural_question": "What step 1 does?",
        "natural_answer": "Step 1 does preheat the oven to 350°F."
      },
      "step_2_identification": {
        "formal_question": "$what?({step_2}, $::)",
        "natural_question": "What step 2 does?",
        "natural_answer": "Step 2 does mix flour, sugar, and butter until creamy."
      },
      "step_3_identification": {
        "formal_question": "$what?({step_3}, $::)",
        "natural_question": "What step 3 does?",
        "natural_answer": "Step 3 does add chocolate chips and bake for 12 minutes."
      }
    }
  },
  "question_hierarchy": {
    "main_question": "How to do?",
    "sub_questions": [
      "How to do?",
      "Given it is done by the method, then it makes what happen?",
    ],
    "second_sub_questions": {
        "How to do?": [
            "What are the steps to do?",
            "What step 1 does?",
            "What step 2 does?",
            "What step 3 does?",
        ]
    }
  },
  "qa_hierarchy": {
    "main_qa": {
      "formal_question": "$how?(::(do), @by)",
      "natural_answer": "Preheat the oven to 350°F. Mix flour, sugar, and butter until creamy. Add chocolate chips and bake for 12 minutes."
    },
    "sub_qa": [
      {
        "formal_question": "$how?(::(do), @by)",
        "natural_answer": "Preheat the oven to 350°F. Mix flour, sugar, and butter until creamy. Add chocolate chips and bake for 12 minutes."
      },
      {
        "formal_question": "$when?(::(do)@by, @onlyIf)",
        "natural_answer": "The cookies are ready when golden brown."
      }
    ],
    "second_sub_qa": {
      "$how?(::(do), @by)": [
        {
          "formal_question": "$what?({steps}, $=)",
          "natural_answer": "Do steps in step 1, step 2 and step 3."
        },
        {
          "formal_question": "$what?({step_1}, $::)",
          "natural_answer": "Step 1 does preheat the oven to 350°F."
        },
        {
          "formal_question": "$what?({step_2}, $::)",
          "natural_answer": "Step 2 does mix flour, sugar, and butter until creamy."
        },
        {
          "formal_question": "$what?({step_3}, $::)",
          "natural_answer": "Step 3 does add chocolate chips and bake for 12 minutes."
        }
      ]
    }
  },
  "normcode_mapping": {
    "imperative_sequence": "@by",
    "judgement_sequence": "@onlyIf",
    "assignment": "$=",
    "nominalization": "$::"
  }
}
```

## Key Patterns Observed

1. **Imperative-to-Question Mapping**: Imperative norm-texts naturally map to "How to do?" as the main question, capturing the instructional intent while maintaining the action-oriented nature.

2. **Descriptive-to-Question Mapping**: Descriptive norm-texts naturally map to "What is [entity]?" questions, capturing the informational intent while maintaining the definitional nature.

3. **Minimal Knowledge Principle**: Question targets start with minimal knowledge - using generic "do" for imperatives and generic entity names for objects, allowing for progressive specification in subsequent questions.

4. **Adaptive Decomposition Principle**: Hinging questions and step/process breakdown are only applied when there are multiple complex steps or processes that benefit from individual identification. Simple content (single steps or natural sequences) does not require further decomposition.

5. **Hierarchical Question Structure**: Questions can follow a hierarchical structure where subsequent questions build upon previous ones, creating nested conditional relationships (e.g., "What is butterfly?" → "Given butterfly exists, then what makes butterfly?" → "Given butterfly is made to exist, then it makes what happen?").

6. **Sequential Question Structure**: Sub-questions follow a logical sequence that mirrors the temporal flow of the original instruction or description, with precise correspondence to NormCode operators.

7. **Tautological Foundation**: Basic identity questions often require tautological answers (e.g., "Butterfly is butterfly") to establish the foundational definition that subsequent questions build upon.

8. **Atomic Answer Preservation**: Each rewritten answer maintains the original meaning while being structured to directly address its corresponding sub-question, ensuring no information is lost in translation.

9. **Process-Oriented Deconstruction**: The deconstruction focuses on the process flow rather than static definitions, making it suitable for procedural and instructional content.

10. **Minimal Restructuring**: The approach preserves the original sentence structure where possible, only reorganizing to match the question-answer format without changing the core meaning.

11. **Clear Question-Answer Correspondence**: Each sub-question has a direct, unambiguous answer from the original text, creating a one-to-one mapping that facilitates further processing or translation.

12. **NormCode Question Translation**: Each question is translated into NormCode format by identifying the question condition (imperative sequence, judgement sequence, assignment) and question target (imperative, object, etc.), with hierarchical relationships reflected in nested operators and precise natural language correspondence.

13. **Nominalization Pattern**: When breaking down complex processes, questions use "What [step/process] does?" format to properly reflect the nominalization of imperatives/processes into objects, using the `$::` operator.

14. **Referential Answer Structure**: Hinging questions can use referential answers (e.g., "Do steps in step 1, step 2 and step 3") that reference subsequent detailed definitions, avoiding redundancy and creating clear structural relationships.

15. **Universal Methodology**: The deconstruction process works across different types of content (imperative instructions, descriptive definitions, simple processes, complex procedures) while maintaining consistent structural patterns and adapting terminology appropriately.

16. **JSON Output Standardization**: The structured output format provides machine-readable representations that maintain the hierarchical relationships, formal-natural language correspondence, and complete traceability of the deconstruction process.
