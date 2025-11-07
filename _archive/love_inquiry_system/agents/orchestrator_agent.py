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
        self.concept_map = self._build_concept_map(plan['root_concept'])

    def _build_concept_map(self, concept_node: dict) -> dict:
        """Recursively builds a map of concept IDs to their full node definitions."""
        concept_map = {}
        # A full concept node should have a 'type'. References might not.
        if 'type' in concept_node:
            concept_map[concept_node['id']] = concept_node
        
        if 'sub_concepts' in concept_node:
            for sub_concept in concept_node['sub_concepts']:
                concept_map.update(self._build_concept_map(sub_concept))
        return concept_map

    def execute(self, state: dict) -> dict:
        """Starts the execution of the plan."""
        print("Orchestrator is starting the inquiry...")
        root_concept = self.plan['root_concept']
        
        # Start the conversation with the root concept's prompt and check for user consent
        response = self.user_interaction_agent.ask_question(root_concept.get('prompt', root_concept['question']))
        # Allow for more flexible positive responses
        if response.lower().strip() not in ['yes', 'y', 'ok', 'okay', 'sure', 'yeah']:
            print("\nOrchestrator: It looks like you'd rather not talk about this right now. Shutting down.")
            return state
        
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
        
        # Resolve the concept node to its full definition if it's a reference.
        full_concept_node = self.concept_map.get(concept_node['id'], concept_node)
        
        # If a specialized agent is defined for this concept, delegate to it.
        # This is where user interaction happens.
        if "agent" in full_concept_node:
            agent = self.agents.get(full_concept_node["agent"])
            if agent:
                state['current_concept_node'] = full_concept_node
                state = agent.execute(state)
                # After an agent gathers info, make a judgement if it's a statement (a condition).
                if full_concept_node.get('type') == 'Statement':
                    state['current_condition_id'] = full_concept_node['id']
                    state = self.judgement_agent.execute(state)
        
        # After (or if not handled by an agent), process decomposition logic which defines how to handle children.
        if 'decomposition' in full_concept_node:
            decomposition = full_concept_node['decomposition']
            operator = decomposition['operator']

            # Handle conditional logic: First traverse the children that define the condition, then judge.
            if operator == '@if':
                condition_id = decomposition['condition_id']
                
                # Find and traverse the sub-concept that defines the condition.
                # This will trigger the necessary questions to satisfy the condition.
                condition_concept_node = None
                for sub_concept in full_concept_node.get('sub_concepts', []):
                    if sub_concept['id'] == condition_id:
                        condition_concept_node = sub_concept
                        break
                
                if condition_concept_node:
                    state = self._traverse_concept(condition_concept_node, state)

            # Handle sequential and other container-like logic across multiple sub-concepts
            elif operator in ['&across', '::{ALL(true)}']:
                 if 'sub_concepts' in full_concept_node:
                    for sub_concept in full_concept_node['sub_concepts']:
                        state = self._traverse_concept(sub_concept, state)

        return state
