# Original Prompt

Execute the five-phase NormCode AI Planning Pipeline to create a self-orchestrating system that can:

1. Take a natural language prompt and system context as input
2. Transform it through multiple compilation phases
3. Produce executable NormCode repositories (.concept.json and .inference.json)
4. Generate a runnable Python script for the orchestrator

The system should be meta-recursive: the NormCode plan itself defines how to create NormCode plans.

## System Context

- Working directory: `direct_infra_experiment/nc_ai_planning_ex/iteration_7/`
- Documentation location: `documentation/current/`
- Infrastructure location: `infra/`
- Available paradigms: Located in `infra/_agent/_models/_paradigms/`
- LLM model: `qwen-plus` (or configured model)

## Key Requirements

1. Use the **updated NormCode syntax** from `documentation/current/`
2. Follow the **compilation pipeline** structure
3. Generate proper **flow indices** with `?{flow_index}:` annotations
4. Include **sequence types** with `?{sequence}:` annotations
5. Add **paradigm specifications** with `%{paradigm}:` annotations
6. Create **context distribution** for LLM prompts

