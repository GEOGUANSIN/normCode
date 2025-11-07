from multi_agent_experiement2.love_inquiry_system.concepts import NormCodeConcept
from multi_agent_experiement2.love_inquiry_system.agents.base_agent import BaseAgent
# Import other agents as they are created
from multi_agent_experiement2.love_inquiry_system.agents.judgement_agent import JudgementAgent
from multi_agent_experiement2.love_inquiry_system.agents.input_agent import InputAgent

class OrchestratorAgent(BaseAgent):
    """
    The main agent that traverses the NormCode concept tree and delegates tasks.
    """
    def __init__(self, root_concept: NormCodeConcept):
        self.root_concept = root_concept
        self.agents = {
            "Judgement": JudgementAgent(),
            "Input": InputAgent(),
            # "Imperative": ImperativeAgent(),
        }

    def execute(self, concept: NormCodeConcept = None, orchestrator: 'OrchestratorAgent' = None):
        """
        Starts the execution of the NormCode plan from the root concept.
        """
        print("\n--- Starting Orchestrator Execution ---")
        self.run(self.root_concept)
        print("\n--- Orchestrator Execution Finished ---")
        return self.root_concept

    def run(self, concept: NormCodeConcept):
        """
        Recursively traverses the concept tree and processes each node.
        """
        # Process the current concept
        self._process_concept(concept)

        # Recursively process children
        for child in concept.children:
            self.run(child)

    def _process_concept(self, concept: NormCodeConcept):
        """
        Determines the type of a concept and delegates it to the appropriate agent.
        """
        print(f"Orchestrator visiting: {concept.name} ({concept.concept_type})")

        # More robust agent dispatching logic
        agent = None
        if concept.concept_type == "Judgement":
            agent = self.agents.get("Judgement")
        # Check for the input operator explicitly
        elif concept.operator and concept.operator.startswith(':>:'):
            agent = self.agents.get("Input")
        else:
            agent = self.agents.get(concept.concept_type)


        if agent:
            print(f"  -> Dispatching to {agent.__class__.__name__}...")
            agent.execute(concept, self)
        else:
            # If no specific agent, the orchestrator handles it (e.g., syntactical ops)
            self._handle_syntactical_operator(concept)

    def _handle_syntactical_operator(self, concept: NormCodeConcept):
        """
        Handles the logic for syntactical operators like @if, &across, etc.
        """
        if not concept.is_functional_concept or not concept.operator:
            return

        print(f"  -> Handling syntactical operator: {concept.operator}")

        # This is where the logic for @if, &across, $., etc. will go.
        # For now, we just print that we've identified it.
        pass
