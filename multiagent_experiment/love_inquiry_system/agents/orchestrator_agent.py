from .base_agent import BaseAgent
from .concept_agents import FeelingAgent, ActionAgent, EntitiesAgent, MeaningAgent, DualityAgent
from .judgement_agent import JudgementAgent
from .user_interaction_agent import UserInteractionAgent

class OrchestratorAgent(BaseAgent):
    """Orchestrates the overall flow of the conversation based on the plan."""

    def __init__(self, plan: dict):
        self.plan = plan
        self.user_interaction_agent = UserInteractionAgent()
        self.judgement_agent = JudgementAgent()
        self.agents = {
            "FeelingAgent": FeelingAgent(),
            "ActionAgent": ActionAgent(),
            "EntitiesAgent": EntitiesAgent(),
            "MeaningAgent": MeaningAgent(),
            "DualityAgent": DualityAgent(),
        }

    def execute(self, state: dict) -> dict:
        """Starts the execution of the plan."""
        print("Orchestrator is starting the inquiry...")
        root_concept = self.plan['root_concept']
        
        # Start the conversation with the root concept's prompt
        self.user_interaction_agent.ask_question(root_concept.get('prompt', root_concept['question']))
        
        state = self._traverse_concept(root_concept, state)
        
        # Final judgement on the overall concept
        state['current_condition_id'] = "<definition satisfied>"
        state = self.judgement_agent.execute(state)
        love_defined = state['judgements'].get("<definition satisfied>", False)
        
        if love_defined:
            print("\nOrchestrator: Based on your responses, we have formed a comprehensive definition of love.")
        else:
            print("\nOrchestrator: It seems some aspects of the definition were not fully met. Love is indeed complex.")

        print("\n--- Inquiry Complete ---")
        print("Final State:", state)
        return state

    def _traverse_concept(self, concept_node: dict, state: dict) -> dict:
        """Recursively traverses the concept tree."""
        
        # If a specialized agent is defined for this concept, delegate to it.
        # This is where user interaction happens.
        if "agent" in concept_node:
            agent = self.agents.get(concept_node["agent"])
            if agent:
                state['current_concept_node'] = concept_node
                state = agent.execute(state)
                # After an agent gathers info, make a judgement if it's a statement (a condition).
                if concept_node['type'] == 'Statement':
                    state['current_condition_id'] = concept_node['id']
                    state = self.judgement_agent.execute(state)
        
        # After (or if not handled by an agent), process decomposition logic which defines how to handle children.
        if 'decomposition' in concept_node:
            decomposition = concept_node['decomposition']
            operator = decomposition['operator']

            # Handle conditional logic: First traverse the children that define the condition, then judge.
            if operator == '@if':
                condition_id = decomposition['condition_id']
                
                # Find and traverse the sub-concept that defines the condition.
                # This will trigger the necessary questions to satisfy the condition.
                condition_concept_node = None
                for sub_concept in concept_node.get('sub_concepts', []):
                    if sub_concept['id'] == condition_id:
                        condition_concept_node = sub_concept
                        break
                
                if condition_concept_node:
                    state = self._traverse_concept(condition_concept_node, state)

            # Handle sequential logic across multiple sub-concepts
            elif operator == '&across':
                 if 'sub_concepts' in concept_node:
                    for sub_concept in concept_node['sub_concepts']:
                        state = self._traverse_concept(sub_concept, state)

        return state
