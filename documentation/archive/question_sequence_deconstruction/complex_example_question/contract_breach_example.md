# Norm-text Deconstruction by Question Sequencing - Legal Case Example

This document provides a complex example of how to deconstruct norm-text by sequencing questions, focusing on legal case analysis and procedural reasoning.

## Example: Contract Breach Analysis

**Original Norm-text:**
To establish a claim for breach of contract, the plaintiff must prove four elements: (1) the existence of a valid contract, (2) the plaintiff's performance or excuse for non-performance, (3) the defendant's breach of the contract, and (4) damages resulting from the breach. A valid contract requires mutual assent, consideration, capacity, and legality. If the plaintiff fails to prove any of these elements by a preponderance of the evidence, the claim will fail. However, if all elements are proven, the court may award compensatory damages, which are designed to place the plaintiff in the position they would have been in had the contract been performed. In cases involving willful breach or fraud, the court may also award punitive damages to deter similar conduct in the future.

**Deconstruction Process:**

**Step 1: Identify the main question**
- What happens to establish a claim for breach of contract?  
  # This step captures the conditional and process-oriented nature of the norm-text. Since the text describes what happens in the process of establishing a breach of contract claim, the main question focuses on the conditions and process under which this establishment occurs.

**Step 2: Generate sub-questions to capture the flow of the norm-text**
- What happens to establish a claim for breach of contract?  
  # This sub-question captures the main process of establishing the claim.
- What are the four elements that must be proven, and what is required for a valid contract?  
  # This sub-question captures the detailed elements and contract validity requirements.
- What happens if the plaintiff fails to prove any of these elements?  
  # This sub-question captures the consequence of failing to meet the burden of proof.
- What happens if all elements are proven, and what additional damages may be available?  
  # This sub-question captures the available remedies and conditional punitive damages.

**Step 3: Rewrite norm-text sentences to directly answer each sub-question**
- To establish a claim for breach of contract, the plaintiff must prove four elements: (1) the existence of a valid contract, (2) the plaintiff's performance or excuse for non-performance, (3) the defendant's breach of the contract, and (4) damages resulting from the breach.
  # This answer captures the main process of establishing the claim, matching the first sub-question.
- The plaintiff must prove four elements: (1) the existence of a valid contract, (2) the plaintiff's performance or excuse for non-performance, (3) the defendant's breach of the contract, and (4) damages resulting from the breach. A valid contract requires mutual assent, consideration, capacity, and legality.
  # This answer captures the detailed elements and contract validity requirements, matching the second sub-question.
- If the plaintiff fails to prove any of these elements by a preponderance of the evidence, the claim will fail.
  # This answer captures the consequence of failing to meet the burden of proof, matching the third sub-question.
- However, if all elements are proven, the court may award compensatory damages, which are designed to place the plaintiff in the position they would have been in had the contract been performed. In cases involving willful breach or fraud, the court may also award punitive damages to deter similar conduct in the future.
  # This answer captures the available remedies and conditional punitive damages, matching the fourth sub-question.

**Step 4: Rewrite each question with NormCode**
- What happens to establish a claim for breach of contract? → $when?(::(establish claim for breach of contract), $=)
  # Question condition: assignment ($=) - establishes identity of the establishment process, Question target: ::(establish claim for breach of contract) (imperative) - the imperative being established
- What are the four elements that must be proven, and what is required for a valid contract? → $what?({breach of contract elements}, $=)  
  # Question condition: assignment ($=) - establishes identity/definition, Question target: breach of contract elements (object) - the elements being defined
- What happens if the plaintiff fails to prove any of these elements? → $when?(<prove element>, @if)  
  # Question condition: judgement sequence (@if) - antecedent condition for proving elements, Question target: <prove element> (judgement) - the proving action
- What happens if all elements are proven, and what additional damages may be available? → $when?(<prove element>, @onlyIf)  
  # Question condition: judgement sequence (@onlyIf) - consequence of proving elements, Question target: <prove element> (judgement) - the proven elements

**Level 2 Deconstruction - Element Analysis:**

**Step 2a: What is element 1?**
- What is element 1?  
  # This question identifies the first element of breach of contract.

**Step 3a: Rewrite to answer what is element 1**
- Element 1 is the existence of a valid contract.
  # This answer specifies the first required element.

**Step 2b: What is element 2?**
- What is element 2?  
  # This question identifies the second element of breach of contract.

**Step 3b: Rewrite to answer what is element 2**
- Element 2 is the plaintiff's performance or excuse for non-performance.
  # This answer specifies the second required element.

**Step 2c: What is element 3?**
- What is element 3?  
  # This question identifies the third element of breach of contract.

**Step 3c: Rewrite to answer what is element 3**
- Element 3 is the defendant's breach of the contract.
  # This answer specifies the third required element.

**Step 2d: What is element 4?**
- What is element 4?  
  # This question identifies the fourth element of breach of contract.

**Step 3d: Rewrite to answer what is element 4**
- Element 4 is damages resulting from the breach.
  # This answer specifies the fourth required element.

**Level 2 Deconstruction - Contract Validity Requirements:**

**Step 2e: What are the requirements for a valid contract?**
- What are the requirements for a valid contract?  
  # This question identifies the components of contract validity.

**Step 3e: Rewrite to answer what are the requirements for a valid contract**
- A valid contract requires mutual assent, consideration, capacity, and legality.
  # This answer specifies the four requirements for contract validity.

**Step 2f: What is mutual assent?**
- What is mutual assent?  
  # This question identifies the first requirement for contract validity.

**Step 3f: Rewrite to answer what is mutual assent**
- Mutual assent is the agreement between parties to the contract terms.
  # This answer specifies what mutual assent means.

**Step 2g: What is consideration?**
- What is consideration?  
  # This question identifies the second requirement for contract validity.

**Step 3g: Rewrite to answer what is consideration**
- Consideration is something of value exchanged between the parties.
  # This answer specifies what consideration means.

**Step 2h: What is capacity?**
- What is capacity?  
  # This question identifies the third requirement for contract validity.

**Step 3h: Rewrite to answer what is capacity**
- Capacity is the legal ability of parties to enter into a contract.
  # This answer specifies what capacity means.

**Step 2i: What is legality?**
- What is legality?  
  # This question identifies the fourth requirement for contract validity.

**Step 3i: Rewrite to answer what is legality**
- Legality is that the contract's purpose must be lawful.
  # This answer specifies what legality means.

**Level 2 Deconstruction - Burden of Proof:**

**Step 2j: What is the burden of proof?**
- What is the burden of proof?  
  # This question identifies the standard of proof required.

**Step 3j: Rewrite to answer what is the burden of proof**
- The burden of proof is preponderance of the evidence.
  # This answer specifies the required standard of proof.

**Step 2k: What happens if burden is not met?**
- What happens if burden is not met?  
  # This question identifies the consequence of failing to meet the burden.

**Step 3k: Rewrite to answer what happens if burden is not met**
- If burden is not met, the claim will fail.
  # This answer specifies the consequence of failing to meet the burden.

**Level 2 Deconstruction - Remedies:**

**Step 2l: What are compensatory damages?**
- What are compensatory damages?  
  # This question identifies the primary remedy available.

**Step 3l: Rewrite to answer what are compensatory damages**
- Compensatory damages are designed to place the plaintiff in the position they would have been in had the contract been performed.
  # This answer specifies the purpose of compensatory damages.

**Step 2m: When are punitive damages available?**
- When are punitive damages available?  
  # This question identifies the conditions for punitive damages.

**Step 3m: Rewrite to answer when are punitive damages available**
- Punitive damages are available in cases involving willful breach or fraud.
  # This answer specifies the conditions for punitive damages.

**Step 2n: What is the purpose of punitive damages?**
- What is the purpose of punitive damages?  
  # This question identifies the purpose of punitive damages.

**Step 3n: Rewrite to answer what is the purpose of punitive damages**
- The purpose of punitive damages is to deter similar conduct in the future.
  # This answer specifies the purpose of punitive damages.

**Step 4: Rewrite each question with NormCode**
- What are the elements of breach of contract? → $what?({breach of contract elements}, $=)
  # Question condition: assignment ($=) - establishes identity/definition, Question target: breach of contract elements (object) - the legal elements being defined
- Given the elements are defined, then what is required for a valid contract? → $when?($=({breach of contract elements}), @If)  
  # Question condition: judgement sequence (@If) - antecedent condition, Question target: $=({breach of contract elements}) - the defined elements
- Given a valid contract exists, then what happens if elements are not proven? → $when?(@If($=({breach of contract elements})), @onlyIf)  
  # Question condition: judgement sequence (@onlyIf) - restrictive consequence, Question target: @If($=({breach of contract elements})) - the elements with antecedent conditions
- Given all elements are proven, then what remedies are available? → $when?(@onlyIf(@If($=({breach of contract elements}))), @If)  
  # Question condition: judgement sequence (@If) - available remedies, Question target: @onlyIf(@If($=({breach of contract elements}))) - the proven elements
- Given compensatory damages are awarded, then what additional damages may be available? → $when?(@If(@onlyIf(@If($=({breach of contract elements})))), @onlyIf)  
  # Question condition: judgement sequence (@onlyIf) - conditional additional remedies, Question target: @If(@onlyIf(@If($=({breach of contract elements})))) - the awarded compensatory damages

**Level 2 NormCode Translations:**
- What is element 1? → $what?({breach of contract element_1}, $=)  
  # Question condition: assignment ($=) - establishes identity, Question target: breach of contract element_1 (object) - the first element
- What is element 2? → $what?({breach of contract element_2}, $=)  
  # Question condition: assignment ($=) - establishes identity, Question target: breach of contract element_2 (object) - the second element
- What is element 3? → $what?({breach of contract element_3}, $=)  
  # Question condition: assignment ($=) - establishes identity, Question target: breach of contract element_3 (object) - the third element
- What is element 4? → $what?({breach of contract element_4}, $=)  
  # Question condition: assignment ($=) - establishes identity, Question target: breach of contract element_4 (object) - the fourth element
- What are the requirements for a valid contract? → $what?({valid contract requirements}, $=)  
  # Question condition: assignment ($=) - establishes identity, Question target: valid contract requirements (object) - the requirements
- What is the burden of proof? → $what?({burden of proof}, $=)  
  # Question condition: assignment ($=) - establishes identity, Question target: burden of proof (object) - the standard
- What happens if burden is not met? → $when?($=({burden of proof}), @onlyIf)  
  # Question condition: judgement sequence (@onlyIf) - consequence of failure, Question target: burden of proof (object) - the standard
- What are compensatory damages? → $what?({compensatory damages}, $=)  
  # Question condition: assignment ($=) - establishes identity, Question target: compensatory damages (object) - the remedy
- When are punitive damages available? → $when?($=({compensatory damages}), @onlyIf)  
  # Question condition: judgement sequence (@onlyIf) - conditional availability, Question target: compensatory damages (object) - the primary remedy
- What is the purpose of punitive damages? → $what?({punitive damages purpose}, $=)  
  # Question condition: assignment ($=) - establishes identity, Question target: punitive damages purpose (object) - the purpose

**Output:**

```json
{
  "norm_text": "To establish a claim for breach of contract, the plaintiff must prove four elements: (1) the existence of a valid contract, (2) the plaintiff's performance or excuse for non-performance, (3) the defendant's breach of the contract, and (4) damages resulting from the breach. A valid contract requires mutual assent, consideration, capacity, and legality. If the plaintiff fails to prove any of these elements by a preponderance of the evidence, the claim will fail. However, if all elements are proven, the court may award compensatory damages, which are designed to place the plaintiff in the position they would have been in had the contract been performed. In cases involving willful breach or fraud, the court may also award punitive damages to deter similar conduct in the future.",
  "deconstruction": {
    "level_1": {
      "main_process": {
        "formal_question": "$when?(::(establish claim for breach of contract), @if)",
        "natural_question": "What happens to establish a claim for breach of contract?",
        "natural_answer": "To establish a claim for breach of contract, the plaintiff must prove four elements: (1) the existence of a valid contract, (2) the plaintiff's performance or excuse for non-performance, (3) the defendant's breach of the contract, and (4) damages resulting from the breach."
      },
      "elements_definition": {
        "formal_question": "$what?({breach of contract elements}, $=)",
        "natural_question": "What are the breach of contract elements?",
        "natural_answer": "The four elements are (1) the existence of a valid contract, (2) the plaintiff's performance or excuse for non-performance, (3) the defendant's breach of the contract, and (4) damages resulting from the breach. A valid contract requires mutual assent, consideration, capacity, and legality."
      },
      "failure_consequence": {
        "formal_question": "$when?(<the claim fails>, @if)",
        "natural_question": "What happens to fail the claim?",
        "natural_answer": "If the plaintiff fails to prove any of these elements by a preponderance of the evidence, the claim will fail."
      },
      "success_remedies": {
        "formal_question": "$when?(<prove element>, @if)",
        "natural_question": "What happens to all elements proven?",
        "natural_answer": "However, if all elements are proven, the court may award compensatory damages, which are designed to place the plaintiff in the position they would have been in had the contract been performed. In cases involving willful breach or fraud, the court may also award punitive damages to deter similar conduct in the future."
      }
    },
    "level_2": {
      "element_breakdown": {
        "element_1": {
          "formal_question": "$what?({breach of contract element_1}, $=)",
          "natural_question": "What is breach of contract element 1?",
          "natural_answer": "Element 1 is the existence of a valid contract."
        },
        "element_2": {
          "formal_question": "$what?({breach of contract element_2}, $=)",
          "natural_question": "What is breach of contract element 2?",
          "natural_answer": "Element 2 is the plaintiff's performance or excuse for non-performance."
        },
        "element_3": {
          "formal_question": "$what?({breach of contract element_3}, $=)",
          "natural_question": "What isbreach of contract element 3?",
          "natural_answer": "Element 3 is the defendant's breach of the contract."
        },
        "element_4": {
          "formal_question": "$what?({breach of contract element_4}, $=)",
          "natural_question": "What is breach of contract element 4?",
          "natural_answer": "Element 4 is damages resulting from the breach."
        }
      },
      "success_remedies_breakdown": {
        "compensatory_damages": {
          "formal_question": "$what?({compensatory damages}, $=)",
          "natural_question": "What are compensatory damages?",
          "natural_answer": "Compensatory damages are designed to place the plaintiff in the position they would have been in had the contract been performed."
        },
        "punitive_damages": {
          "formal_question": "$when?(<punitive damages available>, @if)",
          "natural_question": "When are punitive damages available?",
          "natural_answer": "Punitive damages are available in cases involving willful breach or fraud."
        }
      }
    }
  },
  "question_hierarchy": {
    "main_question": "What happens to establish a claim for breach of contract?",
    "sub_questions": [
      "What happens to establish a claim for breach of contract?",
      "What are the breach of contract elements?",
      "What happens to fail the claim?",
      "What happens to all elements proven?"
    ],
    "level_2_questions": {
      "element_breakdown": [
        "What is breach of contract element 1?",
        "What is breach of contract element 2?",
        "What isbreach of contract element 3?",
        "What is breach of contract element 4?"
      ],
      "success_remedies_breakdown": [
        "What are compensatory damages?",
        "When are punitive damages available?"
      ]
    }
  },
  "qa_hierarchy": {
    "main_qa": {
      "formal_question": "$when?(::(establish claim for breach of contract), @if)",
      "natural_answer": "To establish a claim for breach of contract, the plaintiff must prove four elements: (1) the existence of a valid contract, (2) the plaintiff's performance or excuse for non-performance, (3) the defendant's breach of the contract, and (4) damages resulting from the breach."
    },
    "sub_qa": [
      {
        "formal_question": "$when?(::(establish claim for breach of contract), @if)",
        "natural_answer": "To establish a claim for breach of contract, the plaintiff must prove four elements: (1) the existence of a valid contract, (2) the plaintiff's performance or excuse for non-performance, (3) the defendant's breach of the contract, and (4) damages resulting from the breach."
      },
      {
        "formal_question": "$what?({breach of contract elements}, $=)",
        "natural_answer": "The four elements are (1) the existence of a valid contract, (2) the plaintiff's performance or excuse for non-performance, (3) the defendant's breach of the contract, and (4) damages resulting from the breach. A valid contract requires mutual assent, consideration, capacity, and legality."
      },
      {
        "formal_question": "$when?(<the claim fails>, @if)",
        "natural_answer": "If the plaintiff fails to prove any of these elements by a preponderance of the evidence, the claim will fail."
      },
      {
        "formal_question": "$when?(<prove element>, @if)",
        "natural_answer": "However, if all elements are proven, the court may award compensatory damages, which are designed to place the plaintiff in the position they would have been in had the contract been performed. In cases involving willful breach or fraud, the court may also award punitive damages to deter similar conduct in the future."
      }
    ],
    "level_2_qa": {
      "$what?({breach of contract elements}, $=)": [
        {
          "formal_question": "$what?({breach of contract element_1}, $=)",
          "natural_question": "What is breach of contract element 1?",
          "natural_answer": "Element 1 is the existence of a valid contract."
        },
        {
          "formal_question": "$what?({breach of contract element_2}, $=)",
          "natural_question": "What is breach of contract element 2?",
          "natural_answer": "Element 2 is the plaintiff's performance or excuse for non-performance."
        },
        {
          "formal_question": "$what?({breach of contract element_3}, $=)",
          "natural_question": "What isbreach of contract element 3?",
          "natural_answer": "Element 3 is the defendant's breach of the contract."
        },
        {
          "formal_question": "$what?({breach of contract element_4}, $=)",
          "natural_question": "What is breach of contract element 4?",
          "natural_answer": "Element 4 is damages resulting from the breach."
        }
      ],
      "$when?(<prove element>, @if)": [
        {
          "formal_question": "$what?({compensatory damages}, $=)",
          "natural_question": "What are compensatory damages?",
          "natural_answer": "Compensatory damages are designed to place the plaintiff in the position they would have been in had the contract been performed."
        },
        {
          "formal_question": "$when?(<punitive damages available>, @if)",
          "natural_question": "When are punitive damages available?",
          "natural_answer": "Punitive damages are available in cases involving willful breach or fraud."
        }
      ]
    }
  },
  "normcode_mapping": {
    "assignment": "$=",
    "judgement_sequence_antecedent": "@if",
    "nominalization": "$::"
  }
}
```

## Key Insights from Legal Case Example

1. **Legal Element Analysis**: The deconstruction process effectively breaks down complex legal doctrines into their constituent elements, making the structure explicit and analyzable.

2. **Procedural Logic**: Legal procedures follow clear conditional relationships that can be systematically identified and structured using the question sequencing methodology.

3. **Burden of Proof Handling**: The method naturally captures the concept of burden of proof and its consequences, which are fundamental to legal reasoning.

4. **Remedy Hierarchy**: Legal remedies can be structured hierarchically, showing primary remedies and conditional additional remedies.

5. **Multi-Level Deconstruction**: Complex legal concepts benefit from multiple levels of deconstruction, breaking down elements into sub-elements and requirements.

6. **Conditional Relationships**: Legal reasoning heavily relies on conditional relationships (if-then statements) that are clearly captured by the judgement sequence operators.

7. **Standard of Proof**: The methodology can handle abstract legal concepts like "preponderance of the evidence" and their practical implications.

8. **Legal Terminology**: Even specialized legal terminology can be systematically broken down and structured using the question sequencing approach.

## Comparison with Other Examples

| Example Type | Main Question | Pattern | Complexity | Legal Relevance |
|--------------|---------------|---------|------------|-----------------|
| User Account | "How to do?" | Imperative | Simple | Low |
| Butterfly | "What is butterfly?" | Descriptive | Simple | Low |
| Cookie Recipe | "How to do?" | Imperative | Complex | Low |
| Stereotype | "What is stereotype?" | Descriptive | Complex | Medium |
| Addition Algorithm | "What are the steps?" | Procedural | Complex | Low |
| **Legal Case** | "What are the elements?" | Legal Analysis | Complex | **High** |

## Legal Application Benefits

1. **Case Analysis**: Lawyers can systematically break down complex legal cases into analyzable components.

2. **Legal Research**: The method provides a structured approach to understanding legal doctrines and their requirements.

3. **Client Communication**: Complex legal concepts can be explained in a structured, question-based format.

4. **Legal Education**: Law students can use this method to understand and memorize legal elements and procedures.

5. **Legal Writing**: The structured approach can improve the clarity and organization of legal documents.

6. **Case Strategy**: The hierarchical breakdown helps identify which elements need to be proven and in what order.

This legal case example demonstrates that the norm-text deconstruction methodology is particularly well-suited for legal analysis, where structured reasoning, conditional relationships, and hierarchical organization are essential components of effective legal thinking and communication. 