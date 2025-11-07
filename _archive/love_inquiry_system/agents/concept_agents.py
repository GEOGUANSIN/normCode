from .base_agent import BaseAgent
from .user_interaction_agent import UserInteractionAgent

class FeelingAgent(BaseAgent):
    """Agent responsible for inquiring about feelings (care, attachment)."""

    def __init__(self):
        self.user_interaction_agent = UserInteractionAgent()

    def execute(self, state: dict) -> dict:
        concept_node = state['current_concept_node']
        
        # Ask the main question for this concept
        response = self.user_interaction_agent.ask_question(concept_node['question'])
        state['responses'][concept_node['id']] = response

        # Traverse sub-concepts for more detailed questions
        if 'sub_concepts' in concept_node:
            for sub_concept in concept_node['sub_concepts']:
                sub_response = self.user_interaction_agent.ask_question(sub_concept['question'])
                state['responses'][sub_concept['id']] = sub_response

        return state

class ActionAgent(BaseAgent):
    """Agent responsible for inquiring about actions (kind acts, sacrifice)."""
    
    def __init__(self):
        self.user_interaction_agent = UserInteractionAgent()

    def execute(self, state: dict) -> dict:
        concept_node = state['current_concept_node']
        response = self.user_interaction_agent.ask_question(concept_node['question'])
        state['responses'][concept_node['id']] = response
        
        if 'sub_concepts' in concept_node:
            for sub_concept in concept_node['sub_concepts'][0]['sub_concepts']: # Dive into {actions}
                sub_response = self.user_interaction_agent.ask_question(sub_concept['question'])
                state['responses'][sub_concept['id']] = sub_response
        return state

class EntitiesAgent(BaseAgent):
    """Agent responsible for inquiring about the entities involved in love."""

    def __init__(self):
        self.user_interaction_agent = UserInteractionAgent()

    def execute(self, state: dict) -> dict:
        concept_node = state['current_concept_node']
        response = self.user_interaction_agent.ask_question(concept_node['question'])
        state['responses'][concept_node['id']] = response

        if 'sub_concepts' in concept_node:
            for sub_concept in concept_node['sub_concepts'][0]['sub_concepts']: # Dive into {entities}
                sub_response = self.user_interaction_agent.ask_question(sub_concept['question'])
                state['responses'][sub_concept['id']] = sub_response
        return state

class MeaningAgent(BaseAgent):
    """Agent responsible for inquiring about the meaning of love."""

    def __init__(self):
        self.user_interaction_agent = UserInteractionAgent()

    def execute(self, state: dict) -> dict:
        concept_node = state['current_concept_node']
        response = self.user_interaction_agent.ask_question(concept_node['question'])
        state['responses'][concept_node['id']] = response
        return state

class DualityAgent(BaseAgent):
    """Agent responsible for inquiring about the dual nature of love."""

    def __init__(self):
        self.user_interaction_agent = UserInteractionAgent()

    def execute(self, state: dict) -> dict:
        concept_node = state['current_concept_node']
        response = self.user_interaction_agent.ask_question(concept_node['question'])
        state['responses'][concept_node['id']] = response

        if 'sub_concepts' in concept_node:
            for sub_concept in concept_node['sub_concepts']:
                sub_response = self.user_interaction_agent.ask_question(sub_concept['question'])
                state['responses'][sub_concept['id']] = sub_response
        return state
