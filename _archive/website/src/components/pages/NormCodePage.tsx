import React from 'react';
import ReactMarkdown from 'react-markdown';
import './NormCodePage.css';

const normCodeGuide = `
# NormCode: The Easy Guide

## 1. What is NormCode?

Imagine you have a complex task, like baking a cake. You wouldn't just throw all the ingredients in a bowl. Instead, you'd follow a recipe: a step-by-step plan.

**NormCode is a way to write a "recipe" for thinking.** It's a language for breaking down a big task into a series of small, logical steps called **inferences**. This creates a clear **plan of inferences** that a computer or an AI can follow to get the job done.

Think of it as creating a detailed to-do list for a reasoning process.

## 2. The Core Idea: An Inference

The basic unit in NormCode is an **inference**. An inference is just one step in your plan. Every inference has two main parts:

1.  **The Action (\`<=\`)**: This is the "verb" of the step. It defines the main job or function to be performed. We call this the **Functional Concept**.
2.  **The Ingredients (\`<-\`)**: These are the "nouns" of the step. They are the data, inputs, or outputs that the action works with. We call these **Value Concepts**.

**A Simple Recipe Analogy:**

\`\`\`
Make the cake batter   // The overall goal of this step
    <= Mix the ingredients   // The ACTION to perform (Functional Concept)
    <- Flour                // An INGREDIENT (Value Concept)
    <- Eggs                 // Another INGREDIENT
    <- Sugar
\`\`\`

**A Real NormCode Example:**

This inference tells the system to calculate a \`{digit sum}\`.

\`\`\`Normcode
<- {digit sum} // The goal is to get a digit sum
    <= ::(sum {1} and {2})  // The ACTION is to sum two things
    <- [all digits] <:{1}>  // INGREDIENT 1: a list of digits
    <- {carry-over}  <:{2}>  // INGREDIENT 2: a carry-over number
\`\`\`

-   \`<= ::(sum {1} and {2})\` is the **Action**. It's a command to add things.
-   \`<- [all digits]\` and \`<- {carry-over}\` are the **Ingredients** needed for the sum.

## 3. The Building Blocks: Concepts

Concepts are the words we use in NormCode. They represent the different ideas, data, and actions in our plan. They are easily recognizable by their brackets.

Here are the most common types:

| Symbol | Name     | What it is (in simple terms)                | Example                               |
| :----- | :------- | :------------------------------------------ | :------------------------------------ |
| \`{}\`   | Object   | A thing, a variable, or a piece of data.    | \`{user name}\`, \`{final result}\`       |
| \`<>\`   | Statement| A statement that can be true or false.      | \`<all numbers are zero>\`              |
| \`[]\`   | Relation | A group or collection of things.            | \`[all user emails]\`                   |
| \`::()\` | Imperative| A command or an action to be done.          | \`::(calculate the total price)\`       |
| \`<...>\`| Judgement| A question or a check that gives a yes/no.  | \`<is the {user} an administrator?>\` |

## 4. Controlling the Plan: The Operators

Operators are special symbols that help control the logic and flow of our plan. They act like instructions in a recipe.

Here are the most important ones:

#### Looping (\`*every\`)

The \`*every\` operator is for creating loops. It means "do this for every item in a collection."

\`\`\`Normcode
// This is the main loop for our addition algorithm.
// It will run for every place value (units, tens, etc.).
<= *every({number pair})
\`\`\`

#### Grouping (\`&across\` and \`&in\`)

-   \`&across\`: This operator goes through a collection and pulls out a specific piece of information from each item.

\`\`\`Normcode
// Go ACROSS each number in the {number pair}
// and get the {unit place value} from each one.
<= &across({unit place value}:{number pair})
\`\`\`

-   \`&in\`: This operator is used to create a new group from a list of items you provide.

#### Timing and Conditions (\`@if\`, \`@if!\`, \`@after\`)

These operators control *when* a step should run.

-   \`@if\`: Run this step **if** a condition is true.
-   \`@if!\`: Run this step **if** a condition is **not** true.
-   \`@after\`: Run this step only **after** another step is finished.

\`\`\`Normcode
// This step will only run IF the statement <all numbers are zero> is NOT true.
<= @if!(<all numbers are zero>)
\`\`\`

## 5. How the Plan Runs: The Orchestrator

So how does a NormCode plan actually get executed? A component called the **Orchestrator** manages the whole process.

Think of the Orchestrator as a project manager at a factory assembly line.

1.  **The To-Do List (\`Waitlist\`)**: The Orchestrator has a list of all the steps (inferences) in the plan, neatly organized in order.
2.  **The Status Board (\`Blackboard\`)**: It also has a big board that tracks the status of every single concept (ingredient) and inference (step). Everything starts as \`pending\`.
3.  **The "Ready Check"**: The Orchestrator constantly scans the Status Board. It looks for any step whose ingredients are all marked as \`complete\`.
4.  **Execution**: As soon as a step is ready (all its inputs are \`complete\`), the Orchestrator runs it.
5.  **Update the Board**: Once the step is done, the Orchestrator updates the Status Board, marking the step and its outputs as \`complete\`.

This cycle repeats. As more items become \`complete\`, they unlock the next steps in the plan that depend on them. This continues in a bottom-up fashion until the final goal of the plan is achieved.

This dependency-driven system ensures that every step is executed at exactly the right time, without needing complex manual scheduling.
`;

const NormCodePage: React.FC = () => {
  return (
    <div className="normcode-page">
      <ReactMarkdown>{normCodeGuide}</ReactMarkdown>
    </div>
  );
};

export default NormCodePage;
