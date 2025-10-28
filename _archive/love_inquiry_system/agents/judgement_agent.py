from .base_agent import BaseAgent
import json

# Attempt to import the LanguageModel, handling the path difference
try:
    from infra._agent._models import LanguageModel
except ImportError:
    import sys
    from pathlib import Path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent # Adjust path to go up to normCode
    sys.path.insert(0, str(project_root))
    from infra._agent._models import LanguageModel

class JudgementAgent(BaseAgent):
    """Agent responsible for evaluating user input against plan conditions using an LLM."""

    def __init__(self):
        self.llm = LanguageModel("qwen-turbo-latest")
        # A simple mapping from the plan's condition ID to a more natural question for the LLM
        self.condition_prompts = {
            "<shows through actions>": "Does the user's statement describe how love is shown through actions (like kindness, sacrifice, or support)?",
            "<can be between various entities>": "Does the user's statement describe the kinds of relationships where love can exist (like between partners, family, or friends)?",
            "<means acceptance and wanting happiness>": "Does the user's statement touch upon the idea that love involves acceptance and wanting the other person to be happy?",
            "<is a dual concept>": "Does the user's statement acknowledge that love can be both a feeling and a conscious decision or commitment?"
        }


    def execute(self, state: dict) -> dict:
        """
        Evaluates the user's responses using an LLM.
        Returns the state with the judgement result.
        """
        condition_id = state['current_condition_id']
        
        # For the overall definition, check if all sub-conditions were met
        if condition_id == "<definition satisfied>":
            all_conditions_met = all(
                state['judgements'].get(sub_id, False) for sub_id in self.condition_prompts.keys()
            )
            state['judgements'][condition_id] = all_conditions_met
            return state

        # Get the specific user response and the condition prompt for the LLM
        user_response = state['responses'].get(condition_id, "")
        condition_prompt = self.condition_prompts.get(condition_id)

        if not user_response or not condition_prompt:
            state['judgements'][condition_id] = False
            return state
        
        # Run the LLM to get a judgement
        llm_response_str = self.llm.run_prompt(
            "love_judgement",
            condition=condition_prompt,
            user_response=user_response
        )

        try:
            # The LLM should return a JSON string, so we parse it
            llm_response_json = json.loads(llm_response_str)
            is_satisfied = llm_response_json.get("judgement", False)
            reasoning = llm_response_json.get("reasoning", "No reasoning provided.")
        except (json.JSONDecodeError, AttributeError):
            is_satisfied = False
            reasoning = "The LLM provided an invalid response."

        state['judgements'][condition_id] = is_satisfied
        
        print(f"JudgementAgent: Evaluated condition '{condition_id}'. Result: {is_satisfied} ({reasoning})")
        
        return state
