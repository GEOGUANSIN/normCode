import os
import logging
from core._agentframe._agent_main import _get_default_working_config
from ._reference import Reference, cross_action, cross_product, element_action
from ._concept import Concept
from typing import Optional, List, Union

import logging 
# Configure logging
logger = logging.getLogger(__name__)


def _get_default_working_config(concept_type):
    """Get default actuation configuration based on concept type."""
    func_name = "_get_default_working_config"
    logger.debug(f"[{func_name}] Getting default config for concept type: {concept_type}")
    
    perception_config = {
        "mode": "memory_retrieval"
    }
    cognition_config = {}

    default_variable_definition_dict = {
        "cog_n": "cog_n",
        "cog_cn": "cog_cn",
        "cog_cn_classification_base": "cog_cn[:-1]",
        "cog_v": "cog_v",
        "perc_n": "perc_n",
        "perc_cn": "perc_cn",
        "perc_v": "perc_v",
        "perc_cn_n_v_bullets": "cn_list, n_list, v_list = _safe_eval(perc_cn), _safe_eval(perc_n), _safe_eval(perc_v); perc_cn_n_v_bullets = _format_bullet_points(cn_list, n_list, v_list)",
        "cog_n_with_perc_n": "name_elements = _safe_eval(perc_n); cog_n_with_perc_n = _replace_placeholders_with_values(cog_n, name_elements)",
        "cog_v_with_perc_n": "name_elements = _safe_eval(perc_n); cog_v_with_perc_n = _replace_placeholders_with_values(cog_v, name_elements)"
    }

    if concept_type == "?":
        logger.debug(f"[{func_name}] Creating classification prompt template")
        classification_prompt = Template("""Your task is to find instances of "$cog_cn_classification_base" from a specific text about an instance of "$perc_cn".
    
What finding "$cog_cn_classification_base" means: "$cog_v"

**Find from "$perc_cn": "$perc_n"**

(context for "$perc_n": "$perc_v")

Your output should start with some context, reasonings and explanations of the existence of the instance. Your summary key should be an instance of "$cog_n".""")
        
        cognition_config = {
            "mode": "llm_prompt_two_replacement",
            "llm": "structured_llm",
            "prompt_template": classification_prompt,
            "template_variable_definition_dict": default_variable_definition_dict,
        }
        
    elif concept_type == "<>":
        logger.debug(f"[{func_name}] Creating judgement prompt template")
        judgement_prompt = Template("""Your task is to judge if "$cog_n_with_perc_n" is true or false.

What each of the component in "$cog_n_with_perc_n" refers to: 
$perc_cn_n_v_bullets
                            
**Truth conditions to judge if it is true or false that "$cog_n_with_perc_n":** 
    "$cog_v_with_perc_n"

When judging **quote** the specific part of the Truth conditions you mentioned to make the judgement in your output, this is to make sure you are not cheating and the answer is intelligible without the Truth conditions.
                            
Now, judge if "$cog_n_with_perc_n" is true or false based **strictly** on the above Truth conditions, and quote the specific part of the Truth conditions you mentioned to make the judgement in your output.

Your output should be a JSON object with Explanation and Summary_Key fields. The Explanation should contain your reasoning and the specific part of the Truth conditions you mentioned. The Summary_Key should be either "TRUE", "FALSE", or "N/A" (if not applicable).""")

        cognition_config = {
            "mode": "llm_prompt_two_replacement",
            "llm": "bullet_llm",
            "prompt_template": judgement_prompt,
            "template_variable_definition_dict": default_variable_definition_dict
        }

    return perception_config, cognition_config



class Inference:
    def __init__(
        self, 
        concept_to_infer: Concept,
        perception_concepts: Union[List[Concept], Concept],
        cognition_concept: Concept,
        view: Optional[List[str]] = None,
    ):
        """Initialize an Inference instance with all necessary components.
        
        Args:
            concept_to_infer: The concept to be inferred
            perception_concepts: List of Concept objects for perception
            cognition_concept: Single Concept object for cognition
            view: Optional list of axes to keep in the view
        """
        self.concept_to_infer: Concept = concept_to_infer
        self.agent = None
        # self.view = view or []  # Direct list of axes to keep
        self.post_actuation_pre_perception_concepts: List[Concept] = perception_concepts
        self.post_actuation_pre_cognition_concept: Concept = cognition_concept
        self.combined_pre_perception_concept: Optional[Concept] = None
        self.perception_configuration = None 
        self.cognition_configuration = None
        self.actuation_configuration = None

        # Validate perception concept
        if not isinstance(perception_concepts, (list, tuple)):
            perception_concepts = [perception_concepts]

        if not all(isinstance(c, Concept) for c in perception_concepts):
            raise TypeError("All perception inputs must be Concept instances")
        
    def working_configuration(self, perception_working_config, cognition_working_config, actuation_working_config):
        default_perception_working_config, default_cognition_working_config = _get_default_working_config(self.post_actuation_pre_perception_concepts)
        self.perception_configuration = perception_working_config or self.perception_configuration or default_perception_working_config
        self.cognition_configuration = cognition_working_config or self.cognition_configuration or default_cognition_working_config
        self.actuation_configuration = actuation_working_config or self.actuation_configuration or default_actuation_working_config
        

    def execute(self, agent, shape_view=True):
        from core._agentframe._agent_main import AgentFrame
        if not isinstance(agent, AgentFrame):
            raise ValueError("Agent must be an instance of AgentFrame")
        """Execute pipeline with direct axis selection and optional custom configuration.
        
        Args:
            agent: AgentFrame instance required for execution
            actuation: Whether to apply actuation to the reference
            perception_config_to_give: Optional custom perception configuration
            cognition_config_to_give: Optional custom cognition configuration
            shape_view: Whether to apply view shaping to the reference
        """
        self.agent = agent  # Set the agent for this execution

        # Combine perception concepts using the utility function
        # self.combined_pre_perception_concept = agent.perception_combination(self.post_actuation_pre_perception_concepts, agent)

        perception_ref = agent.perception(self.combined_pre_perception_concept, self.perception_configuration)
        cognition_ref = agent.cognition(self.post_actuation_pre_cognition_concept, self.cognition_configuration)

        if agent.debug:
            logging.debug("===========================")
            logging.debug("Now processing inference execution: %s", self)
            logging.debug("     concept to infer %s", self.concept_to_infer.comprehension["name"])
            logging.debug("     perception %s", self.combined_pre_perception_concept.comprehension["name"])
            logging.debug("     cognition %s", self.post_actuation_pre_cognition_concept.comprehension["name"])

            logging.debug("!! cross-actioning references:")
            logging.debug("     cog: %s %s", cognition_ref.axes, cognition_ref.tensor)
            logging.debug("     perc %s %s", perception_ref.axes, perception_ref.tensor)

        pre_actuation_reference = cross_action(
            cognition_ref,
            perception_ref,
            self.concept_to_infer.comprehension["name"]
        )

        self.concept_to_infer.reference = agent.actuation(pre_actuation_reference, self.actuation_configuration, self.concept_to_infer)

        if agent.debug:
            logging.debug(" raw_result %s %s", self.concept_to_infer.reference.axes, self.concept_to_infer.reference.tensor)

        # if shape_view:
        #     self.concept_to_infer.reference = self.concept_to_infer.reference.shape_view(self.view)

        return self.concept_to_infer
