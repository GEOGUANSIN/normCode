# NormCode: A Semi-Formal Language for Context-Isolated AI Planning

**[Authors]**: _To be filled_
Xin Guan - garguan2001@outlook.com - PsylensAI/Center for Long-Term AI

**[Abstract]**
_~150-250 words summarizing: problem, approach, key contributions, and (if available) results_

> **Questions for Abstract:**
> - What is the one-sentence "elevator pitch" for NormCode?
> - Do you have any quantitative results to mention (e.g., "reduced debugging time by X%", "successfully executed Y complex plans")?

**[Abstract - Draft]**
When chaining large language model (LLM) calls in multi-step workflows, accumulated context leads to hallucination and reasoning failures—a problem we term context pollution. We present NormCode, a semi-formal language for constructing plans of inferences: structured decompositions of complex tasks into isolated, auditable steps. Each inference operates in a "sealed room," receiving only explicitly passed inputs, eliminating cross-step contamination.
Unlike monolithic prompt chains where everything blurs together, NormCode enforces a clean separation: semantic operations invoke LLMs (expensive, non-deterministic), while syntactic operations restructure data (instant, guaranteed). This makes AI workflows transparent by construction—every decision is traceable, every cost is visible—positioning NormCode for agentic systems where auditability matters.
We validate the approach through a base-X addition task, where NormCode-orchestrated code generation achieves 100% accuracy. Notably, NormCode's own derivation pipeline is itself implemented as a NormCode plan, demonstrating the framework's capacity for self-hosting complex workflows. The core execution model is fully functional, with the derivation pipeline itself running as a self-hosted NormCode plan—a proof of the framework's expressive power. Compilation tooling continues to mature.
---

## 1. Introduction

### 1.1 The Problem: Context Pollution in AI Workflows
- The gap between natural language instructions and executable AI agent plans
- **Context pollution**: When chaining LLM calls, accumulated context leads to hallucination and reasoning failures
- Current approaches (direct prompting, chain-of-thought, tool-use frameworks) lack: auditability, debuggability, data isolation

> **Questions:**
> - What specific failures or pain points motivated NormCode? Any concrete examples of "this went wrong without structure"?
> - Are there existing systems you're positioning against (e.g., LangChain, AutoGPT, specific agent frameworks)?

### 1.2 The Solution: Plans of Inferences
- NormCode: a semi-formal language for constructing **plans of inferences**—structured breakdowns of complex tasks into isolated, auditable steps
- **Data isolation**: Each inference is a "sealed room"—it only sees what is explicitly passed in
- Key design principles: Dual-Readability, Progressive Formalization, Inference-Based Decomposition

### 1.3 Contributions
1. A novel semi-formal IR design for AI planning with explicit inference structure and data isolation
2. The three-format paradigm (`.ncds` / `.ncd` / `.ncn`) bridging human authoring, machine rigor, and human verification
3. A Reference system based on multi-dimensional tensors with named axes for structured data flow
4. An execution model separating Semantic operations (LLM-driven) from Syntactic operations (deterministic data plumbing)
5. _[If available]_ Implementation of orchestrator and compiler ecosystem

> **Questions:**
> - What would you say are the 3-4 key contributions?
> - Is there a working compiler/orchestrator? What's its status?

**[Intro - Draft]**

Large language models have made it possible to build AI systems that reason, plan, and act. But as these systems grow more ambitious—chaining multiple LLM calls, invoking tools, branching on intermediate results—a quiet failure mode emerges. We call it *context pollution*: as information accumulates across steps, models begin to hallucinate, confuse earlier outputs with later inputs, and lose track of what they were asked to do. The more capable the workflow, the more brittle it becomes.

Current approaches offer little defense. Direct prompting bundles everything into a single context window. Chain-of-thought extends the conversation but doesn't isolate it. Agent frameworks like LangChain and AutoGPT provide orchestration, but the data flow remains implicit—when something goes wrong at step 7, you cannot easily determine what step 7 actually saw.

NormCode takes a different approach: **explicit data isolation by construction**. We introduce *plans of inferences*—structured decompositions where each step is a self-contained logical unit, receiving only what is explicitly passed to it. An inference cannot "see" the raw document from step 1 if you only pass it the extracted summary from step 3. This is not a convention; it is enforced by the language.

The result is a system where AI workflows become *auditable*. You can trace and zoom-in on exactly what each step received, what it produced, and whether it invoked an LLM or simply restructured data. For high-stakes domains—legal analysis, medical reasoning, financial decision-making—this transparency is not a luxury but a requirement.

This paper presents NormCode, a semi-formal language for context-isolated AI planning, and makes the following contributions:

1. **A novel intermediate representation** for AI planning based on inference decomposition and explicit data flow, bridging natural language intent and machine execution.

2. **The semantic/syntactic separation**: a clean distinction between LLM-invoking operations (expensive, non-deterministic) and data-restructuring operations (free, deterministic), enabling precise cost and reliability tracing.

3. **A three-format ecosystem** (`.ncds` / `.ncd` / `.ncn`) that supports human authoring, machine rigor, and human verification within a single coherent pipeline.

4. **A working orchestrator** with dependency-driven scheduling, checkpointing, and loop management, validated through self-hosted execution of NormCode's own derivation pipeline.

**[intro - draft 2]**
LLM Workflow Challenges and the Need for NormCode
Context Pollution in Multi-Step LLM Reasoning
Large Language Models (LLMs) now enable AI systems that can reason, plan, and act by breaking down tasks and coordinating tool use[1]. Frameworks like AutoGen and LangChain show how agents can decompose complex problems and coordinate actions across multiple LLM calls[1]. However, as these workflows grow more ambitious – chaining many LLM outputs, invoking tools, and branching on intermediate results – a quiet failure mode emerges. We call this “context pollution”: as information accumulates across steps, models begin to hallucinate, mix up earlier outputs with later inputs, and lose track of the original task[2][3]. In other words, overloading the LLM’s context (by continually appending new data and history) often leads to poisoned, distracting, or conflicting context that degrades performance[3]. Empirical studies confirm that LLMs struggle with long, complex interactions – they tend to forget or confuse earlier facts in a conversation, resulting in contradictory or incoherent decisions on lengthy tasks[2]. This effect worsens with each additional reasoning step: small errors can rapidly compound through sequential steps, making complex multi-step solutions exponentially more error-prone than simpler ones[4]. In sum, the more powerful and elaborate the LLM-based workflow, the more brittle it becomes in practice[5]. Even state-of-the-art models like GPT-4 or Claude struggle to maintain global consistency on complicated plans, often losing sight of earlier constraints as the context grows[6].
Limitations of Current Approaches
Existing prompting strategies offer little defense against context pollution. Direct prompting (one big prompt with all instructions and data) forces everything into a single context window, which seems convenient but quickly becomes problematic[7]. Simply expanding the context length and dumping all relevant information at once is not a robust solution – research shows that very long prompts can confuse the model or cause it to focus on irrelevant details, actually reducing correctness despite larger windows[3]. Chain-of-Thought (CoT) prompting extends the interaction by having the model think step-by-step, but it does not isolate the context between steps. In typical CoT or “ReAct” agents, the model’s intermediate reasoning is carried in the same conversation that the model sees later, meaning any hallucinated thought can leak forward[8][9]. Unless special measures are taken (e.g. sandboxing the scratchpad), the chain-of-thought is fully visible to the model’s subsequent prompts, so errors or extraneous details in earlier reasoning can infect later steps[9].
Similarly, popular agent frameworks like LangChain, AutoGPT, and others provide orchestration (managing tool calls, memory, etc.), but the data flow remains implicit. These systems do not clearly delineate what each step actually “sees” – all prompts and memory are passed behind the scenes, making it hard to audit or debug. When something goes wrong at, say, step 7 of a 10-step chain, developers often cannot easily determine what step 7’s input was or why it failed[10]. As one practitioner noted, debugging such agents is often “in the dark” – one must reverse-engineer the entire hidden state to find the root cause[10]. Furthermore, current agent frameworks lack robust error isolation or recovery: if a tool call returns unexpected data or a step produces a faulty output, the system may have no systematic way to roll back or correct it[11]. This can leave the overall agent state inconsistent and brittle. In short, today’s LLM chaining techniques do not inherently protect against context pollution or error propagation – they rely on ad-hoc prompting conventions and hidden state, rather than enforcing clear boundaries in the data flow.
Explicit Context Isolation as a Solution
NormCode takes a fundamentally different approach to address these issues: it enforces explicit data isolation by construction. Rather than letting context bleed implicitly from one step to the next, NormCode defines structured “plans of inference” where each step is a self-contained logical unit that only has access to the information explicitly passed into it. In a NormCode workflow, if an early step processes a raw document and later steps only receive a summarized excerpt, then no subsequent inference can accidentally peek at the original document – it simply is not in that step’s input by design. This idea mirrors strategies emerging in advanced agent design: experts suggest isolating context into separate threads or sub-agents, each handling a narrow subtask with only the relevant data, instead of one monolithic agent juggling a huge combined context[12]. By dividing complex problems among multiple isolated contexts, an AI system can effectively work with a larger overall knowledge base without any single step ever seeing more than it needs[12]. Notably, researchers at Washington Univ. have likewise proposed an “execution isolation” architecture to sandbox LLM-based applications, preventing them from freely accessing each other’s data unless authorized[13]. NormCode builds this isolation into the language itself – it’s not just a guideline but a enforced rule of the programming model. Each inference step’s scope of knowledge is explicitly defined, which means a model cannot inadvertently carry over latent information outside of what the plan specifies.
The benefit of this design is that AI workflows become fully auditable and debuggable. With NormCode, one can trace exactly what each step received as input, what it produced as output, and what kind of operation it performed. Every intermediate state is explicit and inspectable, providing process transparency into how a conclusion was reached[14]. This kind of step-by-step traceability is invaluable in high-stakes domains like legal analysis, medicine, or finance. In such settings, transparency is no longer a luxury – it’s a necessity[15]. Regulators and domain experts demand that AI reasoning be interpretable and verifiable, so one must be able to answer why the AI arrived at a given result. By isolating contexts and clearly delineating data flow, NormCode enables the system (or a human auditor) to verify each inference in isolation, dramatically improving trust. Indeed, the push for explainable and accountable AI in critical domains is growing – new policies (e.g. the EU AI Act) require that high-impact AI systems provide decision traceability and justification[16]. NormCode’s design directly serves this need by producing an audit trail of reasoning that can be examined step by step.
NormCode’s Approach and Contributions
In summary, NormCode introduces a semi-formal language and runtime for context-isolated AI planning, with several novel contributions to the LLM workflow paradigm:
1.	Intermediate Representation for AI Planning: NormCode defines a plan-of-inference format that bridges high-level natural language intents and low-level machine execution. This is a structured intermediate representation (IR) of the reasoning process, where complex tasks are broken into discrete, well-defined steps with explicit data passing. Such intermediate representations have shown benefits in other domains – for example, recent work on Abstractions-of-Thought used a structured IR to separate a functional decomposition from the final code syntax when generating hardware designs[17]. By similarly breaking down tasks into an IR, NormCode allows complex reasoning to be represented in a form that is both human-comprehensible and machine-executable. This IR serves as a blueprint of the solution before any actual LLM calls are made.
2.	Separation of Semantic vs. Syntactic Operations: NormCode makes a clear distinction between LLM-driven inferences and deterministic data transformations. In practice, calls to an LLM (which are expensive and non-deterministic) are treated as special kinds of steps, whereas operations that merely restructure or filter data (which are fast and deterministic) are handled separately. This decoupling of workflow logic from generative model calls is key to reliability. A similar principle was employed by Qiu et al. (2025) in the “Blueprint First, Model Second” framework: they first codify an expert-defined procedure as a deterministic program (the “blueprint”) and only invoke the LLM as a specialized tool for bounded sub-tasks[18]. The LLM never decides the control flow – it is called only to handle specific subtasks under strict guidance[18]. NormCode follows this philosophy, enabling precise tracing of which steps used an AI (and could introduce uncertainty) versus which were guaranteed steps of computation. This separation means one can attribute errors or costs in a complex pipeline: if something went wrong, was it a flawed LLM inference or a bug in a deterministic transformation? By logging each type of step distinctly, NormCode supports fine-grained reliability and cost analysis.
3.	Three-Format Ecosystem for Human and Machine Alignment: NormCode workflows are represented in three synchronized formats – for example, a human-readable source file (e.g. .ncds for NormCode Script), a compiled machine-ready form (.ncd for NormCode Deterministic execution), and a narrative log or notebook (.ncn for NormCode Narrative) for human verification. This tri-format design ensures that the same plan can be viewed in different modalities: one optimized for authoring and readability, one for rigorous execution by the orchestrator, and one for reviewing the reasoning after execution. The concept is akin to literate programming, where documentation and code are interwoven, or to modern notebook environments that keep a source and an output log in sync. By keeping the human-intelligible plan and the machine-enforced plan aligned, NormCode makes it easier to validate that the intended reasoning (e.g. as written by a domain expert in natural terms) is exactly what was executed by the system. While this specific three-format pipeline is unique to NormCode, it resonates with broader transparency efforts in AI: for instance, providing process transparency for auditors (a clear logic chain of how data was used) while also allowing a simplified explanation for end-users[14]. In short, NormCode’s ecosystem allows one to author AI reasoning in a controlled natural-like format, execute it with formal rigor, and then inspect the entire provenance in a human-friendly report.
4.	Self-Hosted Orchestration with Advanced Control: Finally, NormCode includes a working orchestrator that executes these plans with features like dependency-driven scheduling, result caching/checkpointing, and loop management. The orchestrator tracks dependencies between inference steps (only running a step when all its inputs are ready and valid) and can reuse results to avoid redundant LLM calls. It also handles iterative loops or conditionals in the plan in a safe, controlled manner (ensuring no infinite loops or uncontrolled recursion). To build confidence in its robustness, the NormCode orchestrator has been used to run NormCode’s own development pipeline, i.e. it can execute the plans that derived NormCode itself. This kind of self-hosting demonstration is a powerful validation: much like a compiler that can compile its own source code, NormCode shows that an AI reasoning system can apply its methods to bootstrap itself, yielding trust in its correctness. Moreover, NormCode’s approach aligns with the goal of verifiable and reliable autonomous agents noted in recent research[19]. By rigorously scheduling and controlling each action (rather than letting an LLM freely decide every step), the system ensures a predictable execution pathway even in complex scenarios. Early experiments in related frameworks underscore the value of this determinism – for example, the Source Code Agent approach achieved higher success and efficiency on complex benchmarks by enforcing a predetermined plan and only calling the LLM for well-scoped tasks[18][20]. NormCode extends this philosophy with a full toolchain: from plan design to execution to audit, all within one coherent and self-consistent workflow.
In conclusion, NormCode addresses the subtle but critical issue of context pollution in multi-step AI reasoning by enforcing explicit data isolation and structured planning. By doing so, it offers a path toward AI systems that are more reliable, transparent, and auditable, which is especially crucial as we entrust LLMs with increasingly high-stakes decisions. The approach is supported by emerging research trends – from context management in LLM agents[3][6] to hybrid frameworks that separate logic from generation[18] – and pushes them further by providing a concrete language and system for safe AI orchestration. This level of granular control and traceability could become a new standard for building complex AI workflows where failure is not an option.
Sources:
1.	Chang, E. et al. (2025). SagaLLM: Context Management, Validation, and Transaction Guarantees for Multi-Agent LLM Planning. Stanford University. (Illustrates challenges with context loss and inconsistent states in LLM-based planning)[2][5]
2.	Breunig, D. (2025). “How Long Contexts Fail.” dbreunig.com Blog. (Describes failure modes when context windows are overloaded in agent applications, e.g. context poisoning, confusion, clash)[3][21]
3.	Patel, M. (2025). “Why LangChain Fails in Production: 7 Hidden Problems.” LinkedIn post. (Notes debugging difficulties due to implicit data flow in agent frameworks; “debugging in the dark” without clear step-by-step trace)[22]
4.	Ruan, J. (2024). “Context Engineering in LLM-Based Agents.” Medium. (Advocates isolating context by using multiple agents or scratchpads; each sub-agent works with only the info it needs, preventing cross-step pollution)[12][9]
5.	Wu, Y. et al. (2025). IsolateGPT: An Execution Isolation Architecture for LLM-Based Agentic Systems. NDSS Symposium 2025. (Proposes sandboxing and information flow control in LLM systems to enhance security and integrity, analogous to NormCode’s enforced isolation)[13]
6.	Wand AI Research (Fatemi, M.). (2025). “Compounding Error Effect in Large Language Models: A Growing Challenge.” Wand AI Blog. (Explains how small errors in sequential LLM reasoning can accumulate into large failures, motivating structured and check-pointed reasoning)[4][23]
7.	IBM Think Blog (Winland, V. & Noble, J.). (2025). “What is LLM Orchestration?” IBM. (Overview of LLM orchestration frameworks; notes that LLMs alone struggle with multi-step tasks due to limited context retention and lack of memory)[24]
8.	DeLorenzo, M. et al. (2025). “Abstractions-of-Thought: Intermediate Representations for LLM Reasoning in Hardware Design.” arXiv:2505.15873. (Introduces a multi-stage prompting framework with an intermediate structured representation to bridge high-level specs and low-level code)[17]
9.	Qiu, L. et al. (2025). “Blueprint First, Model Second: A Framework for Deterministic LLM Workflow.” arXiv:2508.02721. (Demonstrates decoupling of workflow logic from LLM calls by using a source-code “blueprint” executed deterministically, with LLM as a tool – improving reliability in high-stakes use cases)[18][20]
10.	Medium (P. Sai). (2025). “Evaluating AI Transparency: What Do Users Really Need to Understand?” AI/UI Medium Publication. (Argues that in domains like finance or medicine, transparency is a necessity, not a luxury, and suggests providing process-level explanations for accountability)[15][14]
11.	SagaLLM Reference (Modarressi, A. et al., Xiao, G. et al. 2024, etc). Cited in Chang (2025). (Empirical observations that LLMs “forget” earlier content in long conversations and focus on recent tokens, leading to attention narrowing and lost constraints in planning)[25][6]
12.	Wang, P. et al. (2024). AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. COLING 2024. (A multi-agent LLM framework; as noted by SagaLLM[11], it lacks mechanisms for rollback or state recovery on failures, illustrating the need for the transactional integrity that NormCode addresses.)
________________________________________
[1] [2] [5] [6] [11] [25] : Context Management, Validation, and Transaction Guarantees for Multi-Agent LLM Planning
https://arxiv.org/html/2503.11951v1
[3] [7] [8] [21] How Long Contexts Fail
https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html
[4] [23] Compounding Error Effect in Large Language Models: A Growing Challenge
https://wand.ai/blog/compounding-error-effect-in-large-language-models-a-growing-challenge
[9] [12] Context Engineering in LLM-Based Agents | by Jin Tan Ruan, CSE Computer Science - ML Engineer | Medium
https://jtanruan.medium.com/context-engineering-in-llm-based-agents-d670d6b439bc
[10] [22] Why LangChain Fails in Production: 7 Hidden Problems | Manthan Patel posted on the topic | LinkedIn
https://www.linkedin.com/posts/leadgenmanthan_never-use-langchain-in-production-45-of-activity-7367864422226112513-tMI4
[13] Related papers: IsolateGPT: An Execution Isolation Architecture for LLM-Based Agentic Systems
https://fugumt.com/fugumt/paper_check/2403.04960v2_enmode
[14] [15] Evaluating AI Transparency: What Do Users Really Need to Understand? | by pritish.sai | AI/UI | Medium
https://medium.com/ai-ui/evaluating-ai-transparency-what-do-users-really-need-to-understand-b1d31516230a
[16] The AI Explainability Scorecard: Part 1 - Why transparency is the ...
https://aiceberg.ai/blog/the-ai-explainability-scorecard-part-1-why-transparency-is-the-true-measure-of-trust
[17] [2505.15873] Abstractions-of-Thought: Intermediate Representations for LLM Reasoning in Hardware Design
https://arxiv.org/abs/2505.15873
[18] [19] [20] Blueprint First, Model Second: A Framework for Deterministic LLM Workflow
https://www.arxiv.org/pdf/2508.02721
[24] What is LLM Orchestration? | IBM
https://www.ibm.com/think/topics/llm-orchestration

---

## 2. Background and Related Work

### 2.1 AI Planning and Agent Frameworks
- Traditional AI planning (STRIPS, PDDL, HTN)
- Modern LLM-based agent frameworks (ReAct, LangChain, AutoGPT, etc.)

> **Questions:**
> - What prior work influenced NormCode's design?
> - How does NormCode relate to classical planning languages (PDDL, HTN)?
> - Are there specific agent frameworks you see as related (ReAct, Reflexion, LangGraph, etc.)?

### 2.2 Intermediate Representations in AI/ML
- IR in compilers (LLVM IR, etc.)
- Structured reasoning in LLMs (chain-of-thought, tree-of-thought, graph-of-thought)

### 2.3 Formal Methods and Semi-Formal Approaches
- The spectrum from natural language to formal specification
- Why "semi-formal" is the right balance for LLM-based systems

> **Questions:**
> - What's the theoretical heritage? (Philosophy of language? Formal semantics? Something else?)
> - The naming suggests normative/deontic logic influences — is that intentional?

**[Background and Related Work - Draft]**
2. Background and Related Work
2.1 AI Planning and Agent Frameworks
Classical Planning Languages: NormCode’s design is influenced by the long history of AI planning formalisms. The seminal STRIPS system (Fikes et al., 1971) introduced representing actions with preconditions and effects for goal-directed problem solving[1]. Building on STRIPS-style operators, the Planning Domain Definition Language (PDDL) emerged as a standardized, declarative way to encode planning domains and problems[2]. PDDL is “one of the most widely used formalisms for encoding planning tasks,” providing a structured symbolic blueprint (with predicates, actions, etc.) that planners can use to generate valid plans[2][3]. Hierarchical Task Network (HTN) planning is another key influence – it represents tasks in a hierarchy of goals and subtasks (compound vs. primitive tasks) and has been a cornerstone of practical planning systems since the 1970s[1][4]. In HTN approaches, high-level goals are recursively decomposed into lower-level actions, an idea NormCode relates to if it supports breaking complex tasks into structured sub-goals or “norms.” By drawing on these classical paradigms (STRIPS, PDDL, HTN), NormCode positions itself as a structured task description language, aiming to marry the expressiveness and rigor of planning languages with the flexibility of modern learned agents.
Modern LLM-Based Agent Frameworks: Recent AI agents leverage large language models (LLMs) to plan and act, providing inspiration and context for NormCode. For example, the ReAct framework (Reason+Act prompting) interleaves reasoning steps with action outputs, allowing an LLM to “generate both reasoning traces and task-specific actions in an interleaved manner”[5]. This improves the model’s ability to break down problems and interface with tools or environments as needed[6]. Likewise, the Reflexion framework extends this idea by having agents reflect on feedback: after each trial, an LLM agent produces self-evaluation notes and stores them as an episodic memory to improve subsequent decisions[7]. This “linguistic self-feedback” approach enables learning from failures without weight updates[8], achieving notable gains in complex tasks (e.g. exceeding GPT-4 on a coding benchmark by iteratively self-correcting)[9]. Such frameworks demonstrate the power of intermediate reasoning and feedback loops, which NormCode can leverage by providing a structured “language” for those intermediate steps.
In the broader ecosystem, a number of agentic systems have explored letting LLMs iteratively plan and execute sub-tasks. Notably, AutoGPT (2023) and similar open-source agents showed that an LLM can spawn goals and actions in a loop until a high-level objective is completed – essentially using the LLM as a planner, code executor, and reasoner in one. This trend highlighted both the potential and challenges of autonomous LLM agents (e.g. propensity to go off-track without structured guidance). Developer frameworks like LangChain emerged to facilitate such agents by chaining LLM calls with tools, and have since evolved to more advanced orchestration. For instance, LangGraph (by LangChain) explicitly represents an agent’s reasoning workflow as a directed graph of nodes (decisions, tool uses, etc.), rather than a simple chain. LangGraph is an open-source framework that “uses graph-based architectures to model and manage the intricate relationships between components of an AI agent workflow”[10]. This graph-based approach increases the transparency and controllability of agent behavior (states, memory, and branching logic)[11][12]. NormCode is related in spirit – it can be seen as defining a graph or sequence of normative steps for an agent, analogous to how planning frameworks or LangGraph define structured workflows. In summary, NormCode draws on prior planning languages for formal task representation, while also aligning with modern LLM agent paradigms (ReAct, Reflexion, AutoGPT, LangChain/LangGraph) that emphasize intermediate reasoning, tool use, and structured control over an LLM’s actions.
2.2 Intermediate Representations in AI/ML
A core idea behind NormCode is the use of an intermediate representation (IR) to bridge high-level intents and low-level execution. This concept has deep roots in computer science: in compilers, an IR is the internal code between source and machine code, designed to be easily manipulated and optimized[13]. For example, LLVM IR is a well-known intermediate code that abstracts away machine details, enabling multiple optimization passes and transformations independent of the source language[13]. A “good” IR is accurate (captures all essential information) and language-agnostic[13] – exactly the properties one might want in an AI planning context, where the IR should faithfully represent the task without being tied to any single module or backend. NormCode serves a similar purpose: it is a semi-structured language for representing tasks/goals in a way that’s both human-interpretable and machine-actionable. By providing a layer between the user’s natural language instructions and the agent’s low-level actions, NormCode can enable systematic reasoning and verification (much like a compiler IR enables systematic optimization).
In recent machine learning research, structured reasoning traces have proven valuable for improving performance and interpretability of LLMs. Chain-of-Thought (CoT) prompting is a prime example: it encourages the model to produce a step-by-step reasoning sequence in natural language, which significantly improves the ability to solve complex problems[14]. As Wei et al. (2022) showed, “chain-of-thought prompting enables models to generate intermediate reasoning steps” that break down multi-step arithmetic or logical tasks[14]. This idea has been extended in more structured ways: Tree-of-Thought (ToT) prompting generalizes CoT by exploring a branching tree of possible thought sequences and evaluating outcomes before committing to a solution[15]. Yao et al. (2023) introduce ToT as a framework that allows an LLM to consider multiple reasoning paths, backtrack when necessary, and make deliberate decisions by looking ahead, leading to big gains on tasks requiring planning or search[16][17]. Going a step further, researchers have proposed Graph-of-Thought (GoT) reasoning, which treats thought steps as nodes in a graph to capture non-linear thinking[18]. In GoT, an LLM can potentially explore a network of ideas or sub-goals in parallel, rather than a single sequence, reflecting how human problem-solving often isn’t strictly sequential[19]. All these approaches – CoT, ToT, GoT – highlight the benefit of having an intermediate, structured space (whether a list, tree, or graph of thoughts) in which reasoning can be done explicitly and systematically.
NormCode can be viewed as part of this trend of making thought processes explicit. It provides a representation akin to a mini-“language” or pseudocode that the agent uses internally (or shares with the user) while planning and reasoning. This is analogous to how an IR in a compiler or a computation graph in a neural network serves as an intermediate layer that can be inspected or optimized. By using NormCode, an LLM-based agent isn’t forced to either free-form everything in natural language or jump directly to code or API calls; instead, it can output a semi-formal plan that structures its chain-of-thought. The approach is also reminiscent of “high-level action languages” in classical AI (like STRIPS operators or PDDL plans) but adapted to LLMs – e.g., NormCode might specify a sequence of steps or conditions that the LLM then realizes in detail. Recent work on LLMs + planning indeed follows this pattern: some methods have LLMs generate PDDL or other planning scripts from natural language[20][21], or use LLMs to produce intermediate pseudocode which is then executed or verified. The key takeaway is that an intermediate representation like NormCode can impose structure and clarity on the reasoning process, potentially improving correctness (by enabling checks or self-consistency) and facilitating collaboration between the human and AI (since the IR can be reviewed or edited). This aligns with high-impact findings that inserting a structured reasoning phase (plans, sketches, or logic) between problem and solution often leads to more reliable AI behavior[22][23].
2.3 Formal Methods and Semi-Formal Approaches
NormCode sits at an interesting point on the spectrum between natural language and formal specification. On one end, pure natural language (e.g. plain English instructions or free-form chain-of-thought) is very expressive and accessible, but also ambiguous and not directly machine-verifiable. On the other end, fully formal languages (logical formulas, code, PDDL, etc.) are unambiguous and checkable, but rigid – they require precise syntax and semantics, which can be brittle for generative models and hard for humans to write or understand without training. In software and requirements engineering, it’s long been noted that “from natural language to formal specification languages, almost all kinds of languages have been proposed”[24], and many practitioners recognize the need for something in-between. Semi-formal languages (or notations) strike a balance: they impose structure and clear semantics to reduce ambiguity, but remain closer to natural language or intuitive diagrams so that humans and machines can both work with them. A classic example is UML in requirements engineering – UML diagrams are not as strict as code, but they add enough formal structure to allow some automated consistency checks while staying understandable to stakeholders[25][26]. In fact, semi-formal notations are explicitly described as occupying “the middle of the spectrum between the use of natural and formal languages”, offering a compromise between human readability and machine verifiability[26].
Why “semi-formal” for LLM-based systems? Large language models excel at producing natural language and even pseudo-code, but they are prone to small errors when asked to output fully formal code or specifications (e.g. a slight syntax mistake can render a program invalid). By using a semi-formal format like NormCode, we give the LLM a guideline to structure its output (making it easier to interpret and less ambiguous) without the unforgiving exactness of a formal language. In other words, NormCode’s design likely recognizes that LLMs need a bit of forgiveness in format while still guiding them toward precise semantics. The theoretical heritage here connects to the philosophy of language and formal semantics. Ever since Montague’s work in the 1970s, AI researchers have tried to map natural language into formal representations of meaning – NormCode can be seen as a modern, pragmatic twist on that, where the “meaning representation” is not a full logical calculus, but a controlled language that an LLM can both generate and follow. There is also a nod to deontic (normative) logic in the name “NormCode.” Deontic logic is the branch of logic dealing with norms – what is permitted, obligated, or forbidden[27] – and has been used to formalize rules in legal and ethical domains. While NormCode may not explicitly encode deontic modalities, the spirit of “norms” suggests rules or guidelines that the agent should follow (possibly akin to obligations and prohibitions in code form). Indeed, normative reasoning in AI has seen renewed interest, for example evaluating LLMs’ consistency in handling obligations and permissions[28][29]. The intentional naming implies that NormCode might draw inspiration from these ideas – providing a language of “shoulds and shouldn’ts” for the AI agent in a semi-formal way.
In summary, NormCode’s philosophy is to hit the sweet spot between natural language’s ease and formal methods’ rigor. It embodies the insight that semi-formal is often the right balance for AI systems: we constrain the AI’s reasoning enough to be checkable and clear, but not so much that we lose the flexibility and intuitiveness that make LLMs powerful. This balance is what allows NormCode to leverage formal methods (like logical consistency, rule-based verification) without sacrificing the adaptability of natural language understanding. By incorporating just enough structure (influenced by formal semantics and perhaps normative logics), NormCode enables LLM agents to reason in a way that is both interpretable to humans and grounded in machine-verifiable steps. This approach resonates with high-impact work in AI safety and reliability, which often advocates for “interpretable reasoning traces” and structured decision-making as means to ensure AI systems do what we intend, and do so in a traceable manner. NormCode can be seen as a tangible realization of those principles, informed by decades of thought on how to represent knowledge and norms in a form that bridges brains and silicon.
________________________________________
[1] [4] aips-94.dvi
https://www.cs.umd.edu/~nau/papers/erol1994umcp.pdf
[2] [3] [20] [21] aclanthology.org
https://aclanthology.org/2025.findings-acl.1291.pdf
[5] [6] [22] [2210.03629] ReAct: Synergizing Reasoning and Acting in Language Models
https://arxiv.org/abs/2210.03629
[7] [8] [9] [2303.11366] Reflexion: Language Agents with Verbal Reinforcement Learning
https://arxiv.org/abs/2303.11366
[10] [11] [12] What is LangGraph? | IBM
https://www.ibm.com/think/topics/langgraph
[13] Intermediate representation - Wikipedia
https://en.wikipedia.org/wiki/Intermediate_representation
[14] Chain-of-Thought Prompting Elicits Reasoning in Large Language Models | OpenReview
https://openreview.net/forum?id=_VjQlMeSB_J
[15] [16] [17] [23] [2305.10601] Tree of Thoughts: Deliberate Problem Solving with Large Language Models
https://arxiv.org/abs/2305.10601
[18] [19] [2305.16582] Beyond Chain-of-Thought, Effective Graph-of-Thought Reasoning in Language Models
https://arxiv.org/abs/2305.16582
[24] [25] [26] A Sea of Description Languages - António Rito Silva
https://antonioritosilva.org/software-engineering-companion/requirements-engineering/a-sea-of-description-languages/
[27]  Deontic Logic (Stanford Encyclopedia of Philosophy) 
https://plato.stanford.edu/entries/logic-deontic/
[28] [29] aclanthology.org
https://aclanthology.org/2025.blackboxnlp-1.17.pdf
Classical Planning and AI Planning Languages

Erol, K., Hendler, J., & Nau, D. S. (1994). HTN planning: Complexity and expressivity. Proceedings of the 12th National Conference on Artificial Intelligence (AAAI-94), 1123–1128.
Retrieved from https://www.cs.umd.edu/~nau/papers/erol1994umcp.pdf

Modern LLM Agent Frameworks

Yao, S., Zhao, J., Yu, D., Narasimhan, K., Zhao, D., & Cao, Y. (2022). ReAct: Synergizing reasoning and acting in language models. arXiv preprint arXiv:2210.03629.
https://arxiv.org/abs/2210.03629

Shinn, N., Labash, A., Liu, E., Prystawski, B., Park, C. H., & Raffel, C. (2023). Reflexion: Language agents with verbal reinforcement learning. arXiv preprint arXiv:2303.11366.
https://arxiv.org/abs/2303.11366

IBM. (n.d.). What is LangGraph? IBM Think. Retrieved December 2025, from https://www.ibm.com/think/topics/langgraph

Intermediate Representations and Structured Reasoning

Wikipedia contributors. (n.d.). Intermediate representation. Wikipedia. Retrieved December 11, 2025, from https://en.wikipedia.org/wiki/Intermediate_representation

Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., ... & Le, Q. (2022). Chain-of-thought prompting elicits reasoning in large language models. In Proceedings of the International Conference on Learning Representations (ICLR 2023).
https://openreview.net/forum?id=_VjQlMeSB_J

Yao, S., Zhao, J., Yu, D., Narasimhan, K., Zhao, D., & Cao, Y. (2023). Tree of Thoughts: Deliberate problem solving with large language models. arXiv preprint arXiv:2305.10601.
https://arxiv.org/abs/2305.10601

Han, X., & Zhao, D. (2023). Beyond chain-of-thought: Effective graph-of-thought reasoning in language models. arXiv preprint arXiv:2305.16582.
https://arxiv.org/abs/2305.16582

Semi-Formal Languages and Normative Reasoning

Silva, A. R. (n.d.). A sea of description languages. In Software Engineering Companion: Requirements Engineering. Retrieved from https://antonioritosilva.org/software-engineering-companion/requirements-engineering/a-sea-of-description-languages/

Stanford Encyclopedia of Philosophy. (2021). Deontic Logic. In E. N. Zalta (Ed.), The Stanford Encyclopedia of Philosophy (Fall 2021 Edition).
https://plato.stanford.edu/entries/logic-deontic/

Normative Reasoning and LLM Behavior

Sordoni, A., Proulx, J., Gupta, M., Maillard, J., & Pineau, J. (2025). Are language models deontologically aligned? Findings of the Association for Computational Linguistics (ACL 2025).
https://aclanthology.org/2025.blackboxnlp-1.17.pdf
---

## 3. The NormCode Language

**[NormCode Language - Draft]**

NormCode is designed around a single fundamental unit: the *inference*. An inference is not just a function call; it is a structured assertion that "Concept A is obtained by performing Operation B on Inputs C and D." This structure enforces the isolation required for reliable AI planning.

### 3.1 Core Syntax: The Inference Structure
A NormCode plan is a hierarchy of inferences. We define two primary concept markers:
*   `<=` (**Functional Concept**): Defines the operation (the "verb"). It triggers an agent sequence.
*   `<-` (**Value Concept**): Defines the data (the "noun"). It holds the input or output state.

A typical inference looks like this in `.ncds` (NormCode Draft Straightforward):

```ncds
<- summary
    <= summarize the text
    <- raw document
```

This is read bottom-up: "The `raw document` is used to `summarize the text`, producing the `summary`." The indentation defines the dependency: the parent (`summary`) cannot be resolved until its children (`summarize...`) are complete.

### 3.2 The Three-Format Ecosystem
NormCode acknowledges that humans, compilers, and reviewers have different needs. The language exists in three isomorphic formats:

1.  **.ncds (Draft Straightforward)**: The human authoring format. It uses natural language with minimal structural markers (`<-`, `<=`). It prioritizes speed and readability.
2.  **.ncd (Draft)**: The formal intermediate representation generated by the compiler. It resolves all ambiguities—assigning types (`<$({number})%>`), fixing value orders (`<:{1}>`), and generating unique flow indices (`1.2.1`). This is the "machine-readable" truth.
3.  **.ncn (Natural)**: A compiler-generated narrative that translates the formal `.ncd` back into plain English (e.g., "(OUTPUT) The summary (ACTION) is obtained by..."). This allows non-technical domain experts to verify the plan's logic before execution.

### 3.3 Semantic Concept Types (The "Meaning")
NormCode types are semantic, not just structural. They tell the agent *what* the data represents in the world.
*   **Entities (Non-Functional)**:
    *   **Objects `{}`**: Discrete items (e.g., `{file}`, `{user query}`).
    *   **Propositions `<>`**: Boolean states or facts (e.g., `<file exists>`).
    *   **Relations `[]`**: Collections or mappings (e.g., `[all files]`).
    *   **Subjects `:S:`**: Active agents (e.g., `:coder_agent:`).
*   **Operations (Functional)**:
    *   **Imperative `({})`**: Commands that change state (e.g., `::(calculate sum)`). These invoke the **Imperative Sequence**.
    *   **Judgement `<{}>`**: Evaluations that return a truth value (e.g., `::(number is positive)<is all false>`). These invoke the **Judgement Sequence**.

### 3.4 Syntactic Concept Types (The "Structure")
While semantic concepts invoke AI reasoning, syntactic concepts manage the plan's data flow deterministically.
*   **Assigning**: `$=` (Identity), `$.` (Specification), `$+` (Continuation). Used to select outputs or carry state.
*   **Grouping**: `&in` (Group into a dictionary/relation), `&across` (Flatten into a list/collection). Used to structure multiple inputs.
*   **Timing**: `@if` / `@if!` (Branching), `@after` (Sequencing). Used to control execution order.
*   **Looping**: `*every` (Iteration). Used to process collections item-by-item.

### 3.5 Plan Addressability
Every step in a NormCode plan is assigned a unique **Flow Index** (e.g., `1.2.3`) based on its indentation depth. This index serves as a permanent address for that inference, enabling:
1.  **Precise Debugging**: "The error occurred at step 1.4.2."
2.  **Targeted Intervention**: "Pause execution before step 2.1 starts."
3.  **Auditing**: "Show me the inputs for step 3.2."

### 3.6 Semi-Formality and Flexibility
NormCode is explicitly "semi-formal." This definition carries two distinct meanings that enable its flexibility:

1.  **Conceptual Preservation (Progressive Sense)**: NormCode allows natural language concepts to be preserved within the formal structure. In `.ncds`, a user can write `::(summarize the text)` without immediately defining the Python function or prompt template. The structure formalizes *how* the concept relates to others (it is an action, it depends on input X), while leaving the *content* flexible until execution time. This supports **Progressive Formalization**, where a plan starts as a rough sketch of intent and is iteratively refined into rigorous logic.

2.  **Strictness only where Necessary (Structural Sense)**: The formalism is not pedantic for its own sake. Syntax is strict only to the extent required to make **Activation Compilation** possible. The compiler needs just enough structure to:
    *   Establish unique identities for concepts (Who am I?)
    *   Resolve data flow dependencies (Where do I get my input?)
    *   Extract a working interpretation (Which agent sequence do I invoke?)
    
    As long as these conditions are met, the "semantic payload" of the concept can remain loose natural language. This balance prevents the rigidity of traditional formal methods while providing enough structure for reliable orchestration.

---

## 4. The Reference System

### 4.1 References as Multi-Dimensional Tensors
- A **Reference** is the container where concept data is stored
- Named axes (e.g., `['student', 'assignment']`) instead of numeric indices
- Shape and structure explicitly defined

### 4.2 Perceptual Signs: Lightweight Data Pointers
- Elements are often **Perceptual Signs**: `%{Norm}ID(Signifier)`
- **Norm of Perception**: Tells the agent which faculty to use (e.g., `file_location`, `prompt_location`)
- **Transmutation**: Signs are resolved to actual objects only when needed (during MVP step)

### 4.3 Reference Operations
- **Basic**: `get`, `set`, `copy`, `tensor`
- **Reshaping**: `slice` (project onto axes), `append` (extend along axis)
- **Combining**: `cross_product` (align + combine), `join` (stack along new axis), `cross_action` (apply functions to values)
- **Key Insight**: Syntactic operations restructure data without LLM; Semantic operations use `cross_action` to apply LLM-prepared functions

> **Questions:**
> - How mature is the reference system implementation?
> - Is the "multi-dimensional tensor" backing actually implemented?

**[Reference System - Draft]**

While concepts define the *meaning* of data, the **Reference System** provides the machinery for storing and manipulating it. In NormCode, every piece of data—from a single file path to a collection of user queries—is stored in a **Reference**, a structure inspired by multi-dimensional tensors.

### 4.1 References as Tensors with Named Axes
Unlike standard lists or dictionaries, a Reference organizes data along named axes (e.g., `['student', 'assignment']` rather than `[0, 1]`). This allows operations to be robust to changes in data shape. A collection of documents is not just a list; it is a tensor with a `document` axis. If we process each document to extract three features, the result is automatically a 2D tensor with `['document', 'feature']` axes. This explicit structure prevents the "shape mismatch" errors common in ad-hoc prompt chains.

### 4.2 Perceptual Signs: The "Lazy Evaluation" of AI
Carrying large data payloads (e.g., full text of books) through every step of a plan is inefficient and creates context pollution. NormCode solves this with **Perceptual Signs**: lightweight pointers that represent data without loading it.

A sign follows the format `%{Norm}ID(Signifier)`. For example:
`%{file_location}a1b(data/contract.pdf)`

This tells the agent: "There is an object here (ID `a1b`). To perceive it, use your `FileSystem` faculty (the `file_location` norm) on the path `data/contract.pdf`." The actual data is only loaded ("transmuted") at the exact moment an inference needs to operate on it (the **MVP** step). Until then, the system passes around the lightweight sign, ensuring efficiency.

### 4.3 Semantic vs. Syntactic Operations on References
The distinction between semantic and syntactic operations is implemented at the Reference level through a layered algebra:

1.  **Syntactic Operations (Data Plumbing)**:
    *   **Reshaping**: `slice` (project onto axes), `append` (extend along axis).
    *   **Combining**: `cross_product` (align shared axes), `join` (stack tensors).
    *   These operations manipulate the *structure* of the tensor without ever looking at the content. They are instant, deterministic, and cost zero tokens.

2.  **Semantic Operations (AI Reasoning)**:
    *   **Cross-Action**: The bridge between structure and meaning. It applies a function (prepared by an LLM) to values (held in a Reference).
    *   `cross_action(functions_ref, values_ref)`: This applies the LLM's logic to the data, element-by-element. This step is named actuation. 

By restricting LLMs to `cross_action` and handling all other data movement via syntactic operators, NormCode ensures that AI reasoning is applied only where strictly necessary.

---

## 5. Design Philosophy

**[Design Philosophy - Draft]**

NormCode's design is guided by three core principles: **Dual-Readability**, **Progressive Formalization**, and **Semantic/Syntactic Separation**. Together, these principles address a fundamental tension in AI systems: the need for human oversight in processes that are increasingly automated.

### 5.1 Dual-Readability: Bridging Human and Machine

AI planning systems face a dilemma. Humans think in natural language; machines require unambiguous instructions. Most systems resolve this by forcing humans to write in a machine format (tedious, error-prone) or by letting machines interpret natural language (opaque, unauditable).

NormCode sidesteps this dilemma with **three isomorphic formats**:

| Format | Audience | Purpose |
|--------|----------|---------|
| `.ncds` | Human authors | Fast, intuitive authoring in natural language |
| `.ncd` | Compiler / Orchestrator | Unambiguous, machine-executable representation |
| `.ncn` | Human reviewers | Readable narrative for verification before execution |

The key insight is that **these formats are not translations**—they are the same plan at different levels of explicitness. An author writes `.ncds`, the compiler enriches it to `.ncd` (adding types, bindings, flow indices), and a reviewer reads `.ncn` to verify the logic. No information is lost; no ambiguity is introduced. This allows domain experts (who may not understand the formal syntax) to audit AI workflows before they run.

### 5.2 Progressive Formalization: From Sketch to Structure

Traditional formal methods demand rigor upfront: you must specify everything before you can execute anything. This is impractical for AI workflows, where the "right" structure often emerges through experimentation.

NormCode supports **Progressive Formalization**—a lifecycle where plans start loose and tighten over time:

1.  **Exploration Phase**: Write a rough `.ncds` sketch. Concepts can be vague ("process the document somehow"). The structure captures dependencies, not details.
2.  **Refinement Phase**: Run the plan. Observe failures. Tighten specific inferences—add type constraints, fix value orderings, make concepts explicit.
3.  **Production Phase**: The plan is now rigorous. Every step is auditable. Checkpointing and resumption are reliable.

This lifecycle is enabled by the semi-formal nature of NormCode (Section 3.6): the formalism only demands what the compiler needs. Everything else can remain flexible until you choose to lock it down.

**Intervenability** is a key feature. Because every step has a unique flow index, a user (or an automated system) can:
*   Pause execution before a specific step.
*   Inspect the inputs a step will receive.
*   Modify a concept's reference before resuming.
*   Fork a run to explore alternative branches.

### 5.3 Semantic vs. Syntactic Separation: Cost and Reliability Tracing

Perhaps the most practically important design decision in NormCode is the clean separation between operations that invoke AI reasoning and operations that simply move data around.

| Type | Operations | LLM? | Cost | Determinism |
|------|------------|------|------|-------------|
| **Semantic** | Imperative, Judgement | Yes | Tokens | Non-deterministic |
| **Syntactic** | Grouping, Assigning, Timing, Looping | No | Free | 100% Deterministic |

In a typical NormCode plan, the majority of steps are syntactic. They collect inputs, select outputs, iterate over collections, and branch on conditions—all without any AI involvement. Only the "thinking" steps (imperatives and judgements) invoke an LLM.

This separation provides:

1.  **Cost Visibility**: You know exactly which steps burn tokens. Optimization efforts can focus on the expensive steps.
2.  **Reliability Mapping**: Syntactic steps never fail unexpectedly. If a plan fails, the cause is localized to a semantic step.
3.  **Auditability**: For any plan execution, you can generate a report: "Steps 1.1, 1.3, 2.2 called the LLM; all other steps were deterministic data routing."

For high-stakes domains (legal, medical, financial), this transparency is often a regulatory requirement. NormCode makes it structural rather than aspirational.

### 5.4 When to Use NormCode

NormCode adds structure, and structure has costs. The framework is not appropriate for every use case:

| Scenario | Use NormCode? | Rationale |
|----------|---------------|-----------|
| Multi-step workflow (5+ LLM calls) | ✅ Yes | Isolation and debuggability pay off |
| Auditable AI (legal, medical, finance) | ✅ Yes | You must prove what each step saw |
| Long-running, resumable workflows | ✅ Yes | Built-in checkpointing |
| Quick prototype (1-2 LLM calls) | ❌ No | Overhead exceeds benefit |
| Simple Q&A chatbot | ❌ No | Just prompt the model directly |

**The sweet spot**: Complex, multi-step workflows where you need to know exactly what happened at each step—and where a failure in step 7 should not corrupt the reasoning in step 12.

---

## 6. The Execution Model

**[Execution Model - Draft]**

While the NormCode language defines *what* a plan should do, the **Execution Model** defines *how* and *when* it happens. This section describes the Orchestrator (the central engine), Agent Sequences (the pipelines that execute each inference type), and Paradigms (the configuration layer for agent behavior).

### 6.1 The Orchestrator

The Orchestrator is the runtime engine of NormCode. It manages the execution of a plan by tracking dependencies, scheduling inferences, and maintaining state.

**Core Components:**

1.  **Waitlist**: A prioritized queue of all inferences in the plan, sorted by flow index. This defines the *structural order* of execution.
2.  **Blackboard**: A real-time state tracker. Every concept and inference has a status: `pending`, `in_progress`, `completed`, or `skipped`. The Blackboard is the "single source of truth" for what has happened and what is ready to run.
3.  **Repositories**: The **Concept Repository** stores data (References) for each concept. The **Inference Repository** stores the configuration for each inference (which sequence to run, which paradigm to use).

**Execution Cycle:**

The Orchestrator runs in cycles. In each cycle, it:
1.  **Scans** the Waitlist for `pending` inferences whose dependencies are met (all input concepts are `completed`).
2.  **Executes** the inference by invoking the appropriate Agent Sequence.
3.  **Updates** the Blackboard and Concept Repository with the result.

This **dependency-driven scheduling** ensures that inferences run only when their inputs are ready, and that failures in one branch do not corrupt unrelated branches.

### 6.2 Persistence and Checkpointing

For long-running or resumable workflows, the Orchestrator provides a robust checkpointing system backed by SQLite.

*   **Run ID**: Every execution is assigned a unique identifier. This allows multiple runs to be tracked and compared.
*   **Snapshots**: The full state (Blackboard, References, Workspace) is saved at the end of each cycle.
*   **Resume**: A run can be continued from where it left off. If the code has changed, the Orchestrator uses "reconciliation modes":
    *   `PATCH` (default): Smart merge. Re-runs inferences whose definitions have changed; keeps valid states.
    *   `OVERWRITE`: Trusts the checkpoint entirely.
    *   `FILL_GAPS`: Only populates missing data.
*   **Fork**: Load a past state but start a new run history. Useful for "what if" experiments or retrying from a specific point.

### 6.3 Agents and the AgentFrame

In NormCode, an **Agent** is not just an abstract actor—it is a concrete container of capability, represented by the **Subject Concept** (`:S:`). When a functional concept executes, it does so *within* an Agent's context.

The **AgentFrame** class realizes this in the implementation:

*   **Body**: The agent's "toolbox"—a registry of available tools (e.g., `FileSystemTool`, `LLM_API`, `PythonExecutor`).
*   **Sequences**: The pipelines the agent can run (e.g., `imperative`, `judgement`, `grouping`).
*   **Mode**: The interpretation style (e.g., `composition` mode uses paradigm-driven execution).

This design enables **multi-agent planning**: different Subjects (e.g., `:coder_agent:`, `:reviewer_agent:`) can have different tool bodies and capabilities, even within the same plan.

### 6.4 Agent Sequences: The Execution Pipelines

Each inference type triggers a specific **Agent Sequence**—a standardized pipeline of steps.

**Semantic Sequences (LLM-Invoking):**

| Sequence | Steps | Purpose |
|----------|-------|---------|
| `imperative` | IWI → IR → MFP → MVP → TVA → OR → OWI | Execute commands/actions |
| `judgement` | IWI → IR → MFP → MVP → TVA → TIA → OR → OWI | Evaluate conditions (adds truth assertion) |

The key steps are:
*   **MFP (Model Function Perception)**: Resolves the "vertical" input—the instruction or paradigm—into an executable function.
*   **MVP (Memory Value Perception)**: Retrieves and prepares the "horizontal" inputs—the actual data values.
*   **TVA (Tool Value Actuation)**: Applies the function (from MFP) to the values (from MVP). This is where the LLM is actually invoked.

**Syntactic Sequences (Deterministic):**

| Sequence | Key Step | Purpose |
|----------|----------|---------|
| `assigning` | AR | Select, specify, or accumulate values |
| `grouping` | GR | Collect inputs into relations or lists |
| `timing` | T | Check conditions, enforce ordering |
| `looping` | LR | Iterate over collections, manage workspace |

These sequences manipulate Reference structures without any AI involvement. They are instant, free, and 100% deterministic.

### 6.5 Paradigms: Configuring Agent Behavior

A **Paradigm** is a declarative JSON specification that configures *how* an agent executes a semantic inference. It bridges the gap between abstract intent ("summarize this document") and concrete execution (which prompt template, which LLM, which output format).

**The Vertical/Horizontal Split:**

Paradigms separate configuration into two phases:

1.  **Vertical Steps (Construction-Time)**: Handled during **MFP**. These resolve tool affordances (e.g., "use GPT-4 with this prompt template") into a callable function. The result is an `instruction_fn` stored in the functional Reference.

2.  **Horizontal Steps (Runtime)**: Handled during **TVA**. These pass the actual data values through the pre-configured function.

**Mathematical Formalization:**

Let $\mathcal{S}$ be the Agent's state, $V_{spec}$ be the vertical specification (paradigm), and $H_{plan}$ be the horizontal plan. Let $\mathcal{V}$ be the runtime values.

$$\mathcal{O} = [F_C(F_V(\mathcal{S}, V_{spec}), H_{plan})](\mathcal{V})$$

Where:
*   $F_V$: The vertical function (MFP phase) → produces tool handles $\mathcal{T}$
*   $F_C$: The composition function → compiles $\mathcal{T}$ and $H_{plan}$ into a single function $\Phi$
*   $\Phi(\mathcal{V})$: The horizontal execution (TVA phase) → produces output $\mathcal{O}$

This clean separation allows paradigms to be reused across different inferences and agents.

### 6.6 Tooling

NormCode provides two primary interfaces for running and monitoring orchestrations:

1.  **CLI** (`cli_orchestrator.py`):
    *   `run`: Start a fresh execution.
    *   `resume`: Continue from the latest checkpoint.
    *   `fork`: Branch from a past state with a new run ID.
    *   `list-runs`: Show all tracked executions.

2.  **Streamlit App**: A visual interface that displays:
    *   The plan hierarchy as a tree.
    *   Real-time status updates (pending/running/done).
    *   Click-to-inspect for any concept's current value.
    *   Controls to pause, resume, or reset runs.

---

## 7. The Compiler Ecosystem

**[Compiler Ecosystem - Draft]**

The NormCode compiler ecosystem transforms human-authored plans into executable artifacts. This transformation occurs in stages, each serving a distinct purpose: progressively adding rigor while preserving human oversight.

### 7.1 The Five-Phase Pipeline (Abstract)

The current implementation follows a five-phase pipeline that transforms a natural language instruction into an executable NormCode plan. Notably, **this pipeline is itself implemented as a NormCode plan**—a form of self-hosting that validates the framework's expressive power.

| Phase | Input | Output | Purpose |
|-------|-------|--------|---------|
| **1. Confirmation** | Raw prompt | Instruction Block + Context Manifest | Distill intent; register context |
| **2. Deconstruction** | Instruction Block | `.ncd` Draft + `.ncn` Translation | Parse into hierarchical inferences |
| **3. Formalization** | `.ncd` Draft | Serialized + Redirected `.ncd` | Add flow indices, explicit data flow |
| **4. Contextualization** | Formalized `.ncd` + Context | Prompt files + Context Manifest | Distribute context to each step |
| **5. Materialization** | Final `.ncd` + Context | JSON Repos + Runner Script | Generate executable artifacts |

Each phase includes an opportunity for **manual review**, enabling human intervention before the next stage proceeds. This supports the Progressive Formalization philosophy: the plan tightens incrementally, not all at once.

### 7.2 Deconstruction: Natural Language to Structure

The deconstruction phase is the most LLM-intensive. It uses a recursive decomposition algorithm:

1.  **Initialize**: Wrap the entire instruction as a top-level concept with a `...:` (source text) annotation.
2.  **Loop**: While any concept has un-decomposed `...:` annotations:
    *   Identify the first un-decomposed concept.
    *   Formulate a **question** about its source text (e.g., "How is this action performed?").
    *   Classify the question type (e.g., Methodology Declaration, Conditional Dependency).
    *   Construct the appropriate **functional concept** (`<=`) and **child concepts** (`<-`).
    *   Distribute remaining source text to children or mark concepts as definitive (`/:`).
3.  **Terminate**: When no `...:` annotations remain, the draft is complete.

This process is guided by a taxonomy of question types that map to specific NormCode operators (e.g., "Methodology Declaration" → `@by`, "Conditional Dependency" → `@if`).

### 7.3 Formalization: Adding Rigor

Once the structure is established, formalization adds the precision required for execution:

*   **Serialization**: Each step is reframed as an output-effect relationship (`{output} <= ::(action)`).
*   **Redirection**: Abstract references are linked to concrete implementations (prompts, scripts, file locations) via annotations like `%{prompt_location}`.
*   **Flow Index Generation**: Every line receives a unique address (e.g., `1.3.2.1`) based on indentation depth.

The result is a `.ncd` file where every inference has explicit inputs, explicit outputs, and a unique identity.

### 7.4 Activation Compilation: `.ncd` → JSON Repositories

The final compilation stage transforms the formalized `.ncd` into executable JSON repositories:

**Concept Repository** (`concept_repo.json`):
*   One entry per unique concept.
*   Fields: `concept_name`, `type` (`{}`, `[]`, `<>`), `is_ground_concept`, `is_final_concept`, `reference_data`, `reference_axis_names`.
*   Ground concepts have pre-populated references (e.g., file paths, prompt locations).

**Inference Repository** (`inference_repo.json`):
*   One entry per inference.
*   Fields: `flow_index`, `inference_sequence`, `concept_to_infer`, `function_concept`, `value_concepts`, `context_concepts`, `working_interpretation`.
*   The **Working Interpretation** is the critical field: it encodes all implicit syntax into explicit configuration (e.g., loop structure, condition sources, value orderings).

### 7.5 Translation: `.ncd` → `.ncn`

For human verification, the system can generate a **Natural Language NormCode** (`.ncn`) file. This strips the formal markers and presents the plan as readable prose:

**`.ncd` input:**
```ncd
<- {Phase 1: Confirmation of Instruction}
    <= &across
    <- {step 1.1: Automated Instruction Distillation}
    <- {step 1.2: Automated Context Registration}
```

**`.ncn` output:**
```ncn
The first phase is Confirmation of Instruction.
    <= This phase is specified as a series of steps.
    <- The first step is Automated Instruction Distillation.
    <- The second step is Automated Context Registration.
```

This enables domain experts (who may not understand the formal syntax) to verify the plan's logic before execution.

### 7.6 Current Status and Limitations

The compiler ecosystem is functional but still maturing:

*   **Working**: The deconstruction loop, formalization, and activation compilation have been validated on the self-hosted derivation pipeline.
*   **In Progress**: The NL → `.ncd` deconstruction relies on carefully designed prompts and is sensitive to instruction complexity.
*   **Future Work**: Automated prompt generation, more robust error recovery, and tighter integration with the orchestrator.

---

## 8. Evaluation / Case Studies

**[Evaluation - Draft]**

NormCode's validation comes primarily from two sources: the **self-hosted derivation pipeline** (demonstrating expressive power) and the **base-X addition task** (demonstrating correctness).

### 8.1 Case Study 1: The Self-Hosted Derivation Pipeline

The most significant validation of NormCode is that **its own compiler pipeline is implemented as a NormCode plan**.

*   **The Task**: Transform a high-level natural language instruction into an executable NormCode plan, complete with context distribution and prompt generation.
*   **The Plan**: A five-phase, ~50-inference NormCode structure covering distillation, deconstruction, formalization, contextualization, and materialization.
*   **The Execution**: The orchestrator successfully executes this plan, producing the JSON repositories and runner scripts needed for downstream tasks.

This self-hosting demonstrates:
1.  **Expressive Completeness**: NormCode can represent complex, multi-phase workflows with loops, conditionals, and human-in-the-loop steps.
2.  **Practical Viability**: The orchestrator, checkpointing, and paradigm systems work together to execute real plans.
3.  **Recursive Validation**: Any improvement to NormCode can be tested by re-running its own derivation pipeline.

### 8.2 Case Study 2: Base-X Addition (Correctness Validation)

To validate the correctness of NormCode-orchestrated execution, we implemented a base-X addition algorithm. This serves as a controlled benchmark where correctness can be unambiguously verified.

*   **The Task**: Add two arbitrary-base numbers (base-10, base-12, etc.) digit-by-digit, handling carry-over correctly across arbitrary digit lengths.
*   **The NormCode Plan**: The plan decomposes into ~25 inferences organized around three nested loops:
    1.  An outer `*every` loop over number pairs in the collection
    2.  An inner loop extracting unit-place digits from each number
    3.  A parallel loop generating the "number pair to append" (digits shifted right)

*   **The Concept Repository**: 50+ concepts covering ground data (`{number pair}`), intermediate states (`{digit sum}`, `{carry-over number}*1`, `{remainder}`), and control predicates (`<all number is 0>`, `<carry-over number is 0>`).
*   **Key Mechanisms Demonstrated**:
    *   **Loop Quantification**: `*every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]` — the outer loop iterates until termination, carrying state between iterations.
    *   **Conditional Branching**: `@if!(<all number is 0>)` nested with `@if(<carry-over number is 0>)` — stops appending when both numbers are exhausted and no carry remains.
    *   **Grouping**: `&across({unit place value}:{number pair}*1)` — collects digits from both numbers into a single collection for summation.
    *   **Timing Dependencies**: `@after({digit sum})` — ensures quotient and remainder are computed only after the sum is available.

*   **The Result**: The orchestrator achieves **100% accuracy** on the addition task across test suites of varying digit lengths (validated up to 150-digit numbers).

Because NormCode ultimately generates code (via paradigms that invoke Python execution), the final output is deterministic. The role of NormCode is to structure the *derivation* of that code—ensuring each step receives exactly the correct context and the overall logic is auditable. The full repository files (concepts, inferences, inputs) are provided in **Appendix A**.

### 8.3 Quantitative Observations

Formal experiments are pending, but qualitative observations include:

| Dimension | Observation |
|-----------|-------------|
| **Debuggability** | Flow indices enable precise localization of failures (e.g., "Step 1.3.2 failed because input X was empty"). |
| **Token Efficiency** | Perceptual signs reduce token cost by passing pointers instead of full data. Syntactic operations are free. |
| **Resumability** | Checkpointing allows runs to be paused and resumed, or forked for experimentation. |
| **Auditability** | Every inference's inputs and outputs are logged, enabling post-hoc analysis of AI decisions. |

Comparative evaluation against direct prompting and other frameworks (LangChain, etc.) is planned for future work.

---

## 9. Discussion

### 9.1 Strengths and When to Use NormCode
- High-stakes, auditable AI decisions (legal, medical, financial)
- Complex multi-step reasoning with data isolation
- Human-AI collaborative planning with intervenability
- Long-running, resumable workflows

### 9.2 Limitations and Honest Tradeoffs
- **Syntax density**: The `.ncd` markers create "punctuation soup"
- **Verbosity**: Simple operations can expand to multiple lines of structure
- **Fragility**: Manual editing of `.ncd` is error-prone (indentation-sensitive)
- **Overhead**: For 1-2 step tasks, structure may not justify itself
- **Tooling dependency**: Requires the compiler/orchestrator ecosystem

### 9.3 Lessons Learned

> **Questions:**
> - What surprised you during development?
> - What would you do differently if starting over?
> - What's the biggest remaining unsolved problem?

---

## 10. Future Work

- Compiler maturation (especially NL → `.ncd`)
- Tooling (IDE support, visualization, debugging interfaces)
- Multi-agent planning (multiple Subjects with different tool bodies)
- Broader evaluation across domains
- Community/ecosystem development

> **Questions:**
> - What's the roadmap?
> - Are there specific domains you want to target (legal, medical, financial)?
> - Any plans for open-sourcing?

---

## 11. Conclusion

_Summary of contributions, significance, and future directions._

---

## References

_To be populated based on related work section._

---

## Appendix A: Base-X Addition Repository

This appendix provides the complete NormCode repository for the base-X addition case study described in Section 8.2.

### A.1 Input Specification

The input to the addition plan is a simple JSON structure:

```json
{
  "{number pair}": {
    "data": [["%(123)", "%(98)"]],
    "axes": ["number pair", "number"]
  }
}
```

The `%()` syntax wraps raw values as perceptual signs, deferring their interpretation until needed.

### A.2 NormCode Plan (`.ncds` Format)

The human-readable plan structure (formal syntax):

### A.2.1 Natural Language Translation (`.ncn` Format)

For verification by domain experts, the same plan translates to:

```ncn
[1] (OUTPUT) The new number pair
    (ACTION) is obtained by iterating through every number pair in the collection.
    (MECHANISM) Each iteration carries forward the current carry-over number.
    
    [1.1] (OUTPUT) The result of each iteration
        (ACTION) is assigned from the remainder.
        
        [1.1.2] (OUTPUT) The digit sum
            (ACTION) is computed by summing the unit place values of all numbers 
                     together with the current carry-over number.
            (INPUT 1) All unit place values of the numbers in the current pair.
            (INPUT 2) The current carry-over number (initially 0).
            (YIELDS) The sum.
            
            [1.1.2.4] (OUTPUT) All unit place values of numbers
                (ACTION) is collected by grouping across the current number pair.
                
                [1.1.2.4.2] (OUTPUT) Each unit place value
                    (ACTION) is obtained by iterating through each number in the current pair.
                    
                    [1.1.2.4.2.1] (OUTPUT) The loop result
                        (ACTION) is assigned from the single unit place value.
                        
                        [1.1.2.4.2.1.2] (OUTPUT) The single unit place value
                            (ACTION) is extracted by getting the unit place digit of the number.
                            (INPUT) The current number from the pair.
                            (YIELDS) The extracted digit.

        [1.1.3] (OUTPUT) The number pair collection
            (ACTION) is updated by appending a new number pair.
            (CONDITION) This append happens ONLY IF NOT all numbers are zero,
                        AND IF the carry-over number is zero.
            
            [1.1.3.2] (OUTPUT) The number pair to append
                (ACTION) is constructed by iterating through each number in the current pair.
                
                [1.1.3.2.1] (OUTPUT) The loop result
                    (ACTION) is assigned from the number with last digit removed.
                    
                    [1.1.3.2.1.2] (OUTPUT) The number with last digit removed
                        (ACTION) is computed by: if the number is less than 10, output 0; 
                                 otherwise, remove the unit place digit.
                        (INPUT) The current number.
                        (YIELDS) The shifted number.

            [1.1.3.3] (OUTPUT) The proposition "all numbers are 0"
                (ACTION) is evaluated by checking if each number in the pair to append is 0.
                (TIMING) This check occurs after the number pair to append is ready.
                (CONDITION) True if ALL numbers satisfy: the number is 0.

            [1.1.3.4] (OUTPUT) The proposition "carry-over number is 0"
                (ACTION) is evaluated by checking if the carry-over number is 0.
                (TIMING) This check occurs after the number pair to append is ready.
                
                [1.1.3.4.2] (OUTPUT) The updated carry-over number
                    (ACTION) is computed from the previous carry-over and new quotient.
                    
                    [1.1.3.4.2.2] (OUTPUT) The new carry-over value
                        (ACTION) is found by computing the quotient of the digit sum divided by 10.
                        (TIMING) This occurs after the digit sum is available.
                        (INPUT) The digit sum.
                        (YIELDS) The quotient (new carry).

        [1.1.4] (OUTPUT) The remainder
            (ACTION) is computed by getting the remainder of the digit sum divided by 10.
            (TIMING) This occurs after the digit sum is available.
            (INPUT) The digit sum.
            (YIELDS) The remainder (the digit to output).

    (INPUT) The initial number pair collection.
```

**Reading Guide**: 
- **(OUTPUT)** = What this step produces
- **(ACTION)** = How it's produced  
- **(INPUT)** = What data flows in
- **(YIELDS)** = The specific result extracted
- **(TIMING)** = Dependency on prior steps
- **(CONDITION)** = When the action is executed
- **[X.Y.Z]** = Flow index (unique address for debugging)

### A.2.2 Formal Syntax (`.ncd` Format)

```ncd
{new number pair} | 1. quantifying
    <= *every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>] | 1.1. assigning
        <= $.({remainder}) 
        
        <- {digit sum} | 1.1.2. imperative
            <= ::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)
            <- {sum}?<:{3}>
            <- {carry-over number}*1<:{2}> 
            <- [all {unit place value} of numbers]<:{1}> | 1.1.2.4. grouping
                <= &across({unit place value}:{number pair}*1)
                <- {unit place value} | 1.1.2.4.2. quantifying
                    <= *every({number pair}*1)%:[{number}]@(2) | 1.1.2.4.2.1. assigning
                        <= $.({single unit place value})
                        <- {single unit place value} | 1.1.2.4.2.1.2. imperative
                            <= ::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)
                            <- {unit place digit}?<:{2}>
                            <- {number pair}*1*2
                    <- {number pair}*1

        <- {number pair}<$={1}> | 1.1.3. assigning
            <= $+({number pair to append}:{number pair})%:[{number pair}] | 1.1.3.1. timing
                <= @if!(<all number is 0>) | 1.1.3.1.1. timing
                    <= @if(<carry-over number is 0>)

            <- {number pair to append}<$={1}> | 1.1.3.2. quantifying
                <= *every({number pair}*1)%:[{number}]@(3) | 1.1.3.2.1. assigning
                    <= $.({number with last digit removed}) 
                    <- {number with last digit removed} | 1.1.3.2.1.2. imperative
                        <= ::(output 0 if {1}<$({number})%_> is less than 10, otherwise remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>) 
                        <- {unit place digit}?<:{2}> 
                        <- {number pair}*1*3<:{1}>
                <- {number pair}*1

            <- <all number is 0> | 1.1.3.3. judgement
                <= :%(True):<{1}<$({number})%_> is 0> | 1.1.3.3.1. timing
                    <= @after({number pair to append}<$={1}>)
                <- {number pair to append}<$={1}><:{1}>

            <- <carry-over number is 0> | 1.1.3.4. judgement
                <= :%(True):<{1}<$({carry-over number})%_> is 0> | 1.1.3.4.1. timing
                    <= @after({number pair to append}<$={1}>)
                <- {carry-over number}*1 | 1.1.3.4.2. grouping
                    <= &across({carry-over number}*1:{carry-over number}*1<--<!_>>)
                    <- {carry-over number}*1 | 1.1.3.4.2.2. imperative
                        <= ::(find the {1}?<$({quotient})%_> of {2}<$({digit sum})%_> divided by 10) | 1.1.3.4.2.2.1. timing
                            <= @after({digit sum})
                        <- {quotient}?<:{1}>
                        <- {digit sum}<:{2}>

        <- {remainder} | 1.1.4. imperative
            <= ::(get the {1}?<$({remainder})%_> of {2}<$({digit sum})%_> divided by 10) | 1.1.4.1. timing
                <= @after({digit sum})
            <- {remainder}?<:{1}>
            <- {digit sum}<:{2}>

    <- {number pair}<$={1}>
```

### A.3 Concept Repository (Selected Entries)

The concept repository defines 50+ concepts. Representative examples:

**Ground Concepts** (with pre-populated references):

| Concept Name | Type | Reference Data |
|--------------|------|----------------|
| `{number pair}` | `{}` | `[["%(123)", "%(98)"]]` |
| `{carry-over number}*1` | `{}` | `["%(0)"]` |
| `{unit place digit}?` | `{}` | `"1 digit counting from the right"` |

**Functional Concepts** (operations):

| Concept Name | Type | Description |
|--------------|------|-------------|
| `*every({number pair})%:[{number pair}]@(1)^[...]` | `*every` | Outer loop with carry state |
| `&across({unit place value}:{number pair}*1)` | `&across` | Group digits across numbers |
| `::(sum {1}<...> and {2}<...> to get {3}?<...>)` | `::({})`| Imperative: digit summation |
| `:%(True):<{1}<$({number})%_> is 0>` | `<{}>` | Judgement: check if zero |

### A.4 Inference Repository (Selected Entries)

The inference repository contains 23 inference entries. Key examples:

**Outer Loop (flow_index: 1)**:
```json
{
  "inference_sequence": "quantifying",
  "concept_to_infer": "{new number pair}",
  "function_concept": "*every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]",
  "value_concepts": ["{number pair}"],
  "context_concepts": ["{number pair}*1", "{carry-over number}*1"],
  "working_interpretation": {
    "syntax": {
      "marker": "every",
      "quantifier_index": 1,
      "LoopBaseConcept": "{number pair}",
      "CurrentLoopBaseConcept": "{number pair}*1",
      "group_base": "number pair",
      "InLoopConcept": {"{carry-over number}*1": 1},
      "ConceptToInfer": ["{new number pair}"]
    }
  }
}
```

**Digit Summation (flow_index: 1.1.2)**:
```json
{
  "inference_sequence": "imperative_python",
  "concept_to_infer": "{digit sum}",
  "function_concept": "::(sum {1}<...> and {2}<...> to get {3}?<...>)",
  "value_concepts": ["[all {unit place value} of numbers]", "{carry-over number}*1", "{sum}?"],
  "working_interpretation": {
    "is_relation_output": false,
    "with_thinking": true,
    "value_order": {
      "[all {unit place value} of numbers]": 1,
      "{carry-over number}*1": 2,
      "{sum}?": 3
    }
  }
}
```

**Conditional Termination (flow_index: 1.1.3.1.1)**:
```json
{
  "inference_sequence": "timing",
  "concept_to_infer": "@if!(<all number is 0>)",
  "function_concept": "@if(<carry-over number is 0>)",
  "working_interpretation": {
    "syntax": {
      "marker": "if",
      "condition": "<carry-over number is 0>"
    }
  }
}
```

### A.5 Repository Files

The complete repository files are available in the codebase:
*   `infra/examples/add_examples/repo/addition_concepts.json` (935 lines)
*   `infra/examples/add_examples/repo/addition_inferences.json` (656 lines)
*   `infra/examples/add_examples/repo/addition_inputs.json` (12 lines)
*   `infra/examples/add_examples/ex_add_complete_12_base.py` (Python runner with validation)

---

