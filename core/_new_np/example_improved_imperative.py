from typing import List, Tuple, Optional
from unicodedata import digit
from _concept import Concept
from _reference import Reference, cross_product, element_action
from _inference import Inference, register_inference_sequence, _log_inference_result
from _agentframe import AgentFrame, logger, _log_concept_details, _log_inference_result, create_concept_with_reference, create_simple_concept
from _language_models import LanguageModel
from _methods._quantification_demo import all_quantification_demo_methods
from _methods._grouping_demo import all_grouping_demo_methods
from _methods._workspace_demo import all_workspace_demo_methods
from _methods._demo_improved import all_demo_methods_improved

class AgentFrame_improved(AgentFrame):
    def __init__(self, name, working_configuration, **body):
        super().__init__(name, working_configuration=working_configuration, **body)
        self.body = body
        self._norm_code_setup()

    def _norm_code_setup(self):
        logger.debug(f"Setting up norm code for model: {self.AgentFrameModel}")
        if self.AgentFrameModel == "demo_improved":
            logger.info("Setting up demo_improved configuration")
            # Imperative
            self._set_up_imperative_demo()
        else:
            logger.warning(f"Unknown AgentFrameModel: {self.AgentFrameModel}")

    def configure(self, inference_instance: Inference, inference_sequence: str, **kwargs):
        logger.info(f"Configuring inference instance with sequence: {inference_sequence}")
        if self.AgentFrameModel == "demo_improved":
            if inference_sequence == "imperative":
                logger.debug("Configuring imperative demo")
                methods = all_demo_methods_improved("imperative")
                self._configure_imperative_demo(inference_instance, **methods)
            else:
                logger.warning(f"Unknown inference sequence: {inference_sequence}")
        else:
            logger.warning(f"Configuration not supported for model: {self.AgentFrameModel}")


    def _set_up_imperative_demo(self):
        logger.debug("Setting up imperative demo sequence")
        all_working_configuration = self.working_configuration
        llm = self.body["llm"]
        @register_inference_sequence("imperative")
        def imperative(self: Inference, input_data: dict):
            """`(IWC-[(MVP-CP)-[AP-PTA-ASP]-MA)]-RR-OWC)`"""
            logger.info("Executing imperative sequence")
            
            # 1. Input Working Configuration
            logger.debug("Step 1: Input Working Configuration (IWC)")
            working_configuration = self.IWC(
                value_concepts=self.value_concepts, 
                function_concept=self.function_concept, 
                concept_to_infer=self.concept_to_infer, 
                all_working_configuration=all_working_configuration
            )
            # 2. Memorized Values Perception
            logger.debug("Step 2: Memorized Values Perception (MVP)")
            perception_references = self.MVP(
                working_configuration=working_configuration, 
                value_concepts=self.value_concepts, 
                function_concept=self.function_concept
            )
            # 3. Cross Perception
            logger.debug("Step 3: Cross Perception (CP)")
            crossed_perception_reference = self.CP(
                perception_references=perception_references
            )
            # 4. Apply Perception
            logger.debug("Step 4: Actuator Perception (AP)")
            actuated_functional_reference = self.AP(
                working_configuration=working_configuration, 
                function_concept=self.function_concept, 
                concept_type="imperative", 
                concept_to_infer=self.concept_to_infer, 
                llm=llm)
            # 5. On-Perception Tool Actuation
            logger.debug("Step 5: On-Perception Tool Actuation (PTA)")
            applied_reference = self.PTA(
                working_configuration=working_configuration, 
                actuated_functional_reference=actuated_functional_reference, 
                crossed_perception_reference=crossed_perception_reference, 
                function_concept=self.function_concept, 
                concept_to_infer=self.concept_to_infer
            )
            # 6. Action Specification Perception
            logger.debug("Step 6: Action Specification Perception (ASP)")
            action_specification_perception = self.ASP(
                working_configuration=working_configuration, 
                applied_reference=applied_reference, 
                function_concept=self.function_concept
            )
            # 7. Memory Actuation
            logger.debug("Step 7: Memory Actuation (MA)")
            action_specification_perception = self.MA(
                action_specification_perception=action_specification_perception
            )
            # 8. Return Reference
            logger.debug("Step 8: Return Reference (RR)")
            concept_to_infer_with_reference = self.RR(
                action_specification_perception=action_specification_perception, 
                concept_to_infer=self.concept_to_infer
            )
            # 9. Output Working Configuration
            logger.debug("Step 9: Output Working Configuration (OWC)")
            self.OWC(
                concept_to_infer_with_reference=concept_to_infer_with_reference
            )

            logger.info("Imperative sequence completed")
            return concept_to_infer_with_reference

    def _configure_imperative_demo(self, inference_instance: Inference, **kwargs):
        logger.debug("Configuring imperative demo steps")
        @inference_instance.register_step("IWC")
        def input_working_configurations(**fkwargs):
            """Validate that input contains two numbers"""
            logger.debug("Executing IWC step")
            function = kwargs.get("input_working_configurations", self._input_working_configurations)
            return function(**fkwargs) 
        
        @inference_instance.register_step("OWC")
        def output_working_configurations(**fkwargs):
            """Perform the output working configurations"""
            logger.debug(f"Executing OWC step with concepts: {fkwargs['concept_to_infer_with_reference'].name}")
            function = kwargs.get("output_working_configurations", self._output_working_configurations)
            return function(**fkwargs)
        
        @inference_instance.register_step("RR")
        def return_reference(**fkwargs):
            """Perform the return reference"""
            logger.debug(f"Executing RR step with concepts: {fkwargs['concept_to_infer'].name}")
            function = kwargs.get("return_reference", self._return_reference)
            return function(**fkwargs)
        
        @inference_instance.register_step("MVP")
        def memorized_values_perception(**fkwargs):
            """Perform the memorized values perception"""
            logger.debug(f"Executing MVP step with value concepts: {[concept.name for concept in fkwargs['value_concepts']]}")
            function = kwargs.get("memorized_values_perception", self._memorized_values_perception)
            return function(**fkwargs)
        
        @inference_instance.register_step("CP")
        def cross_perception(perception_references):
            """Perform the cross perception"""
            logger.debug("Executing CP step")
            logger.debug(f"Perception references: {[reference.tensor for reference in perception_references]}")
            crossed_perception_reference = cross_product(perception_references)
            logger.debug(f"Crossed perception reference: {crossed_perception_reference.tensor}")
            return crossed_perception_reference
        
        @inference_instance.register_step("AP")
        def actuator_perception(**fkwargs):
            """Perform the apply perception"""
            logger.debug("Executing AP step")
            function = kwargs.get("actuator_perception", self._actuator_perception)
            return function(**fkwargs)
        
        @inference_instance.register_step("PTA")
        def on_perception_tool_actuation(**fkwargs):
            """Perform the on-perception tool actuation"""
            logger.debug(f"Executing PTA step with actuated functional reference: {fkwargs['actuated_functional_reference'].tensor}")
            function = kwargs.get("on_perception_tool_actuation", self._on_perception_tool_actuation)
            return function(**fkwargs)
        
        @inference_instance.register_step("ASP")
        def action_specification_perception(**fkwargs):
            """Perform the action specification perception"""
            logger.debug(f"Executing ASP step with function concept: {fkwargs['function_concept'].name}")
            function = kwargs.get("action_specification_perception", self._action_specification_perception)
            return function(**fkwargs)
        
        @inference_instance.register_step("MA") 
        def memory_actuation(**fkwargs):
            """Perform the memory actuation"""
            logger.debug("Executing MA step")
            function = kwargs.get("memory_actuation", self._memory_actuation)
            return function(**fkwargs)

    def _input_working_configurations(self, *args, **kwargs):
        """Perform the input working configurations"""
        logger.warning("Executing IWC step: This will do nothing.")
        pass
    
    def _output_working_configurations(self, *args, **kwargs):
        """Perform the output working configurations"""
        logger.warning("Executing OWC step: This will do nothing.")
        pass

    def _return_reference(self, *args, **kwargs):
        """Perform the return reference"""
        logger.warning("Executing RR step: This will do nothing.")
        pass
    
    def _memorized_values_perception(self, *args, **kwargs):
        """Perform the memorized values perception"""
        logger.warning("Executing MVP step: This will do nothing.")
        pass
    
    def _cross_perception(self, *args, **kwargs):
        """Perform the cross perception"""
        logger.warning("Executing CP step: This will do nothing.")
        pass
    
    def _actuator_perception(self, *args, **kwargs):
        """Perform the actuator perception"""
        logger.warning("Executing AP step: This will do nothing.")
        pass
    
    def _on_perception_tool_actuation(self, *args, **kwargs):
        """Perform the on-perception tool actuation"""
        logger.warning("Executing PTA step: This will do nothing.")
        pass    
    
    def _action_specification_perception(self, *args, **kwargs):
        """Perform the action specification perception"""
        logger.warning("Executing ASP step: This will do nothing.")
        pass
    
    def _memory_actuation(self, *args, **kwargs):
        """Perform the memory actuation"""
        logger.warning("Executing MA step: This will do nothing.")
        pass

    def _formal_actuator_perception(self, *args, **kwargs):
        """ Placeholder for formal actuator perception"""
        logger.warning(f"Executing Placeholder FAP step: This will do nothing.")
        pass


    def _syntatical_perception_actuation(self, *args, **kwargs):
        """ Placeholder for syntatical perception actuation"""
        logger.warning(f"Executing Placeholder SPA step: This will do nothing.")
        pass

