from multi_agent_experiement2.love_inquiry_system.concepts import NormCodeConcept
from multi_agent_experiement2.love_inquiry_system.agents.base_agent import BaseAgent
from multi_agent_experiement2.love_inquiry_system.simple_model_runner import SimpleModelRunner
from multi_agent_experiement2.love_inquiry_system.prompt import Prompt

class JudgementAgent(BaseAgent):
    """
    An agent responsible for evaluating Judgement concepts using an LLM.
    """
    def __init__(self):
        # Initialize the model runner and the prompt
        self.prompt = Prompt("multi_agent_experiement2/_models/prompts/judgement_prompt.txt")
        self.model_runner = SimpleModelRunner()

    def execute(self, concept: NormCodeConcept, orchestrator: 'OrchestratorAgent') -> NormCodeConcept:
        """
        Processes a Judgement concept by calling an LLM.
        """
        print(f"    [JudgementAgent]: Evaluating concept '{concept.name}'.")
        
        # 1. Gather context and the statement to evaluate
        context = self._gather_context(concept)
        statement = concept.question

        if not context or not statement:
            print("    [JudgementAgent]: Could not find sufficient context or a statement to evaluate.")
            concept.value = False
            return concept
            
        # 2. Format the prompt
        self.prompt.format(context=context, statement=statement)
        
        # 3. Run the model
        print(f"    [JudgementAgent]: Querying LLM with statement: '{statement}'")
        raw_result = self.model_runner.run_prompt(str(self.prompt))
        
        # 4. Parse the result
        result = self._parse_result(raw_result)
        concept.value = result
        
        print(f"    [JudgementAgent]: Evaluation complete. LLM Result: '{raw_result.strip()}' -> Parsed: {result}")
        
        return concept

    def _gather_context(self, concept: NormCodeConcept) -> str:
        """
        Walks up the concept tree to gather source_text from parent concepts.
        This provides the LLM with the necessary context to make a judgement.
        """
        context_parts = []
        current = concept
        while current:
            if current.source_text:
                context_parts.append(current.source_text)
            current = current.parent
        
        # Reverse to have the context in top-down order
        return "\n---\n".join(reversed(context_parts))

    def _parse_result(self, result: str) -> bool:
        """
        Parses the LLM's string output into a boolean.
        """
        return "true" in result.strip().lower()
