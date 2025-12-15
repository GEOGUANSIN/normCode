# Norm-text Deconstruction by Question Sequencing - Complex Example

This document provides a complex example of how to deconstruct norm-text by sequencing questions, focusing on abstract conceptual definitions.

## Example: Stereotype Definition

**Original Norm-text:**
A stereotype is a widely held but oversimplified and generalized belief or assumption about the characteristics, attributes, or behaviors of members of a particular social group—such as those based on gender, race, age, religion, nationality, or profession. Stereotypes often ignore individual variation and nuance, leading to biased expectations or unjust treatment. While some stereotypes may be based on observations of group trends, they become problematic when used rigidly or uncritically, especially in decision-making or social interactions.

**Deconstruction Process:**

**Step 1: Identify the main question**
- What is stereotype?  
  # This step captures the descriptive nature of the norm-text. Since the text describes what a stereotype is and its characteristics, the main question focuses on establishing the identity assignment of the concept.

**Step 2: Generate sub-questions to capture the flow of the norm-text**
- What is stereotype?  
  # This sub-question captures the definition that opens the norm-text.
- Given stereotype is defined, then what happens?  
  # This sub-question captures the immediate consequence that follows the definition.
- Given stereotype has these consequences, then what happens under certain conditions?  
  # This sub-question captures the conditional consequence that follows the immediate consequence.

**Step 3: Rewrite norm-text sentences to directly answer each sub-question**
- A stereotype is a widely held but oversimplified and generalized belief or assumption about the characteristics, attributes, or behaviors of members of a particular social group—such as those based on gender, race, age, religion, nationality, or profession.
  # This answer captures the definition that opens the norm-text, matching the first sub-question.
- Stereotypes often ignore individual variation and nuance, leading to biased expectations or unjust treatment.
  # This answer captures the immediate consequence that follows the definition, matching the second sub-question.
- While some stereotypes may be based on observations of group trends, they become problematic when used rigidly or uncritically, especially in decision-making or social interactions.
  # This answer captures the conditional consequence that follows the immediate consequence, matching the third sub-question.

**Step 4: Rewrite each question with NormCode**
- What is stereotype? → $what?({stereotype}, $=)
  # Question condition: assignment ($=) - establishes identity/definition, Question target: stereotype (object) - the concept being defined
- Given stereotype is defined, then what happens? → $when?($=({stereotype}), @If)  
  # Question condition: judgement sequence (@If) - immediate consequence, Question target: $=({stereotype}) - the defined stereotype concept
- Given stereotype has these consequences, then what happens under certain conditions? → $when?(@If($=({stereotype})), @onlyIf)  
  # Question condition: judgement sequence (@onlyIf) - conditional consequence, Question target: @If($=({stereotype})) - the stereotype with immediate consequences

**Output:**

```json
{
  "norm_text": "A stereotype is a widely held but oversimplified and generalized belief or assumption about the characteristics, attributes, or behaviors of members of a particular social group—such as those based on gender, race, age, religion, nationality, or profession. Stereotypes often ignore individual variation and nuance, leading to biased expectations or unjust treatment. While some stereotypes may be based on observations of group trends, they become problematic when used rigidly or uncritically, especially in decision-making or social interactions.",
  "deconstruction": {
    "level_1": {
      "main_entity": {
        "formal_question": "$what?({stereotype}, $=)",
        "natural_question": "What is stereotype?",
        "natural_answer": "A stereotype is a widely held but oversimplified and generalized belief or assumption about the characteristics, attributes, or behaviors of members of a particular social group—such as those based on gender, race, age, religion, nationality, or profession."
      },
      "immediate_consequence": {
        "formal_question": "$when?($=({stereotype}), @If)",
        "natural_question": "Given stereotype is defined, then what happens?",
        "natural_answer": "Stereotypes often ignore individual variation and nuance, leading to biased expectations or unjust treatment."
      },
      "conditional_consequence": {
        "formal_question": "$when?(@If($=({stereotype})), @onlyIf)",
        "natural_question": "Given stereotype has these consequences, then what happens under certain conditions?",
        "natural_answer": "While some stereotypes may be based on observations of group trends, they become problematic when used rigidly or uncritically, especially in decision-making or social interactions."
      }
    }
  },
  "question_hierarchy": {
    "main_question": "What is stereotype?",
    "sub_questions": [
      "What is stereotype?",
      "Given stereotype is defined, then what happens?",
      "Given stereotype has these consequences, then what happens under certain conditions?"
    ]
  },
  "qa_hierarchy": {
    "main_qa": {
      "formal_question": "$what?({stereotype}, $=)",
      "natural_answer": "A stereotype is a widely held but oversimplified and generalized belief or assumption about the characteristics, attributes, or behaviors of members of a particular social group—such as those based on gender, race, age, religion, nationality, or profession."
    },
    "sub_qa": [
      {
        "formal_question": "$what?({stereotype}, $=)",
        "natural_answer": "A stereotype is a widely held but oversimplified and generalized belief or assumption about the characteristics, attributes, or behaviors of members of a particular social group—such as those based on gender, race, age, religion, nationality, or profession."
      },
      {
        "formal_question": "$when?($=({stereotype}), @If)",
        "natural_answer": "Stereotypes often ignore individual variation and nuance, leading to biased expectations or unjust treatment."
      },
      {
        "formal_question": "$when?(@If($=({stereotype})), @onlyIf)",
        "natural_answer": "While some stereotypes may be based on observations of group trends, they become problematic when used rigidly or uncritically, especially in decision-making or social interactions."
      }
    ]
  },
  "normcode_mapping": {
    "assignment": "$=",
    "judgement_sequence_antecedent": "@If",
    "judgement_sequence_consequence": "@onlyIf"
  }
}
```

## Key Insights from Complex Example

1. **Abstract Concept Handling**: The deconstruction process works for abstract social concepts, not just concrete physical processes or instructions.

2. **Conceptual Definition Pattern**: Abstract concepts follow the same descriptive pattern as concrete entities, establishing identity, characteristics, and consequences.

3. **Social Phenomenon Analysis**: The method can reveal the underlying logical structure of complex social phenomena like stereotypes.

4. **Cause-Effect Relationships**: Complex examples demonstrate how conditional relationships are identified and structured.

5. **Universal Applicability**: The methodology extends beyond simple instructions to complex conceptual definitions.

6. **Semantic Precision**: Even abstract concepts benefit from the systematic breakdown into identity, antecedent, and consequence relationships.

## Comparison with Other Examples

| Example Type | Main Question | Pattern | Complexity |
|--------------|---------------|---------|------------|
| User Account | "How to do?" | Imperative | Simple (single step) |
| Butterfly | "What is butterfly?" | Descriptive | Simple (natural sequence) |
| Cookie Recipe | "How to do?" | Imperative | Complex (multiple steps) |
| Stereotype | "What is stereotype?" | Descriptive | Complex (abstract concept) |

This complex example demonstrates that the norm-text deconstruction methodology is truly universal, capable of handling both simple and complex content across different domains and types of information. 