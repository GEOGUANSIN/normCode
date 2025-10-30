import os
from multiagent_experiment._models._language_models import LanguageModel

class BlueprintAgent:
    def __init__(self):
        """
        Initializes the BlueprintAgent, setting up the language model
        to generate NormCode plans.
        """
        prompts_dir = "multiagent_experiment/nc_compiler/prompts"
        # We rely on the LanguageModel's mock_mode if settings.yaml or API keys are not found.
        self.llm = LanguageModel("qwen-turbo-latest", prompts_dir=prompts_dir)

    def run(self, normtext: str) -> str:
        """
        Translates raw normtext into a structured NormCode plan using an LLM.

        This is the core logic for Phase 1. It calls an LLM with a specialized
        prompt to perform the decomposition and generate the .nc plan.
        """
        print("BlueprintAgent: Running Phase 1 - Translating normtext to NormCode plan via LLM...")
        
        # Use the LLM to generate the NormCode plan from the normtext
        generated_plan = self.llm.run_prompt(
            "generate_normcode_plan",
            normtext=normtext
        )

        # In a real system, you might add validation or cleaning steps here.
        
        # Save the generated plan to a file
        output_path = "multiagent_experiment/nc_compiler/generated_plan.nc"
        with open(output_path, "w") as f:
            f.write(generated_plan)

        print(f"BlueprintAgent: Successfully generated and saved NormCode plan at '{output_path}'")
        return output_path
