from .base_agent import BaseAgent
from .data_agent import DataAgent
from .input_agent import InputAgent
from .judgement_agent import JudgementAgent
from ..execution_state import ExecutionState


class ControllerAgent(BaseAgent):
    def __init__(self):
        super().__init__("ControllerAgent")
        self.data_agent = DataAgent()
        self.input_agent = InputAgent()
        self.judgement_agent = JudgementAgent()
        self.state = ExecutionState()

    def run(self, text_input: str):
        # Step 0: Extract concepts from the input text.
        self.state.log_action(
            step="0",
            agent=self.input_agent.name,
            details="Extracting concepts from the provided text using an LLM.",
            data={"text_input": text_input}
        )
        extracted_data = self.input_agent.extract_concepts(text_input)
        self.state.record("0", "{extracted concepts}", extracted_data)

        # Pull initial data from the extraction result.
        care = extracted_data.get("care")
        attachment = extracted_data.get("attachment")
        target = extracted_data.get("target")
        kind_acts = extracted_data.get("kind acts")
        sacrifice = extracted_data.get("sacrifice")
        caring_happiness = extracted_data.get("caring about another person's happiness")
        partners = extracted_data.get("partners")
        family = extracted_data.get("family")
        emotion = extracted_data.get("emotion")
        decision = extracted_data.get("decision")

        # Step 1.2.1: Group care and attachment to define the core feeling.
        self.state.log_action(
            step="1.2.1",
            agent=self.data_agent.name,
            details="Grouping '{care}' and '{attachment}' to form the core feeling.",
            data={"care": care, "attachment": attachment}
        )
        deep_feeling = self.data_agent.group_across(care, attachment)
        self.state.record("1.2.1", "{deep feeling}", deep_feeling)

        # Step 1.2.2: Judge if the feeling is directed towards a target.
        self.state.log_action(
            step="1.2.2",
            agent=self.judgement_agent.name,
            details="Evaluating judgment: <towards someone or something>",
            data={"feeling": deep_feeling, "target": target}
        )
        shows_towards_target = self.judgement_agent.is_towards(deep_feeling, target)
        self.state.record("1.2.2", "<towards someone or something>", shows_towards_target)

        # Step 1.3: Judge if the feeling is shown through actions.
        actions = self.data_agent.group_across(kind_acts, sacrifice, caring_happiness)
        self.state.log_action(
            step="1.3",
            agent=self.judgement_agent.name,
            details="Evaluating judgment: <shows through actions>",
            data={"feeling": deep_feeling, "actions": actions}
        )
        shows_through_actions = self.judgement_agent.shows_through(deep_feeling, actions)
        self.state.record("1.3", "<shows through actions>", shows_through_actions)

        # Step 1.4: Judge if the feeling can exist between various entities.
        entities = self.data_agent.group_across(partners, family)
        self.state.log_action(
            step="1.4",
            agent=self.judgement_agent.name,
            details="Evaluating judgment: <can be between various entities>",
            data={"feeling": deep_feeling, "entities": entities}
        )
        can_be_between_entities = self.judgement_agent.exists_between(deep_feeling, entities)
        self.state.record("1.4", "<can be between various entities>", can_be_between_entities)

        # Step 1.5: Judge if the feeling implies acceptance and wanting happiness.
        self.state.log_action(
            step="1.5",
            agent=self.judgement_agent.name,
            details="Evaluating judgment: <means acceptance and wanting happiness>",
            data={"someone": target, "feeling": deep_feeling}
        )
        means_acceptance = self.judgement_agent.is_accepting_and_wants_happiness(target, deep_feeling)
        self.state.record("1.5", "<means acceptance and wanting happiness>", means_acceptance)

        # Step 1.6: Judge if the concept has a dual nature.
        self.state.log_action(
            step="1.6",
            agent=self.judgement_agent.name,
            details="Evaluating judgment: <is a dual concept>",
            data={"feeling": deep_feeling, "emotion": emotion, "decision": decision}
        )
        is_dual_concept = self.judgement_agent.has_dual_nature(deep_feeling, emotion, decision)
        self.state.record("1.6", "<is a dual concept>", is_dual_concept)

        # Step 1.1.1: Group all the individual conditions for the final check.
        self.state.log_action(
            step="1.1.1",
            agent=self.data_agent.name,
            details="Grouping all individual conditions for final evaluation.",
            data={
                "<shows through actions>": shows_through_actions,
                "<can be between various entities>": can_be_between_entities,
                "<means acceptance and wanting happiness>": means_acceptance,
                "<is a dual concept>": is_dual_concept
            }
        )
        individual_conditions = self.data_agent.group_across(
            shows_through_actions,
            can_be_between_entities,
            means_acceptance,
            is_dual_concept
        )
        self.state.record("1.1.1", "{individual conditions}", individual_conditions)

        # Step 1.1: Final judgment: check if all conditions are satisfied.
        self.state.log_action(
            step="1.1",
            agent=self.judgement_agent.name,
            details="Evaluating final judgment: <definition satisfied>",
            data={"conditions": individual_conditions}
        )
        definition_satisfied = self.judgement_agent.check_all_true(individual_conditions)
        self.state.record("1.1", "<definition satisfied>", definition_satisfied)

        # Step 1: Define the final concept of {Love}.
        love_definition_text = "A deep feeling of care or attachment, defined by the satisfaction of all conditions."
        love_result = {"definition": love_definition_text, "is_love": definition_satisfied}
        self.state.record("1", "{Love}", love_result)

        self.state.save_trace()
        return love_result
