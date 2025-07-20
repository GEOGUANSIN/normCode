from _concept import Concept
from _reference import Reference, cross_product
from _inference import Inference, register_inference_sequence
from _agentframe import AgentFrame, logger
from _language_models import LanguageModel
from _methods._workspace_demo import all_workspace_demo_methods

def init_concept_with_references():
    """Demonstrate Concept class with actual Reference objects"""
    
    print("=== Concept with References Examples ===\n")

    # Example 1: Mathematical operations with functional concepts
    print("1. {technical_concepts}?:")
    technical_concepts_1_axes = ["technical_concepts_1"]
    technical_concepts_1_shape = (1,)  # 1 technical concept
    technical_concepts_1_ref = Reference(technical_concepts_1_axes, technical_concepts_1_shape)
    
    # Set mathematical operations
    technical_concepts_type = "A technical concept is a concept that is related to a technical problem. It can be difficult to understand for non-technical people."
    technical_concepts_1_ref.set(f"%({technical_concepts_type})", technical_concepts_1=0) 

    technical_concepts_1 = Concept("{technical_concepts}?", "technical_concepts_1", technical_concepts_1_ref, "{}")
 

    print(f"   Concept: {technical_concepts_1.name}")
    print(f"   Type: {technical_concepts_1.type} ({technical_concepts_1.get_type_class()})")
    print(f"   All technical concepts: {technical_concepts_1_ref.get(technical_concepts_1=slice(None))}")
    print()


    # Example 2: Mathematical operations with functional concepts
    print("2. :S_content:({1}?<$({technical_concepts})%_>)")
    technical_concepts_classification_axes = ["technical_concepts_classification"]
    technical_concepts_classification_shape = (1,)  # 1 technical concept
    technical_concepts_classification_ref = Reference(technical_concepts_classification_axes, technical_concepts_classification_shape)
    
    # Set mathematical operations
    technical_concepts_classification_ref.set("%(:S_content:({1}?<$({technical_concepts})%_>))", technical_concepts_classification=0)
    
    technical_concepts_classification_concept = Concept(":S_content:({1}?<$({technical_concepts})%_>)", "technical_concepts_classification", technical_concepts_classification_ref, "::({})")
    print(f"   Concept: {technical_concepts_classification_concept.name}")
    print(f"   Type: {technical_concepts_classification_concept.type} ({technical_concepts_classification_concept.get_type_class()})")
    print(f"   All technical concepts: {technical_concepts_classification_ref.get(technical_concepts_classification=slice(None))}")
    print()

    technical_concepts_2 = Concept("{technical_concepts}", "technical_concepts_2", None, "{}")
    print(f"   Concept: {technical_concepts_2.name}")
    print()

    return technical_concepts_1, technical_concepts_classification_concept, technical_concepts_2
 
def init_working_configuration():
    working_configuration = {
    "{technical_concepts}?": {
        "perception": {
            "mvp": {
                "mode": "formal"
            },
        },
        "actuation": {
        },
        "cognition": {
        }
    },
    ":S_content:({1}?<$({technical_concepts})%_>)": {
        "perception": {
            "asp": {
                "mode": "in-cognition"
            },
            "ap": {
                "mode": "llm_workspace",
                "product": "translated_templated_function",
                "value_order": {
                    "{technical_concepts}?": 0,
                },
                "workspace_object_name_list": ["content"]
            }
        },
        "actuation": {
            "pta": {
                "mode": "in-cognition",
                "value_order": {
                    "{technical_concepts}?": 0,
                }
            },
            "ma": {
                "mode": "formal",
            },
        },  
        "cognition": {
            "rr": {
                "mode": "identity"
            },
        }
    },
    "{technical_concepts}": {
        "perception": {
            "mvp": {
                "mode": "formal"
            },
        },
        },
    }
    return working_configuration



class WriteAgent(AgentFrame):
    def __init__(self, name, llm, working_configuration, **body):
        super().__init__(name, llm, working_configuration)
        self.body.update(body)
        self.body["workspace"] = {
            "content": "The new cloud architecture reduces latency by 35% through optimized edge caching and parallel processing. Enterprise customers can now deploy AI models with sub-100ms response times."
        } 
        self._norm_code_setup()

    def _norm_code_setup(self):
        logger.debug(f"Setting up norm code for model: {self.AgentFrameModel}")
        if self.AgentFrameModel == "demo":
            logger.info("Setting up demo configuration")
            # Judgement
            self._set_up_judgement_demo()   
            # Imperative
            self._set_up_imperative_demo()
        elif self.AgentFrameModel == "workspace_demo":
            logger.info("Setting up workspace demo configuration")
            # Judgement
            self._set_up_imperative_workspace_demo()
        else:
            logger.warning(f"Unknown AgentFrameModel: {self.AgentFrameModel}")

    def configure(self, inference_instance: Inference, inference_sequence: str, **kwargs):
        logger.info(f"Configuring inference instance with sequence: {inference_sequence}")
        if self.AgentFrameModel == "workspace_demo":
            if inference_sequence == "imperative":
                logger.debug("Configuring imperative demo")
                methods = all_workspace_demo_methods("imperative")
                self._configure_imperative_workspace_demo(inference_instance, **methods)
            else:
                logger.warning(f"Unknown inference sequence: {inference_sequence}")
        else:
            logger.warning(f"Configuration not supported for model: {self.AgentFrameModel}")


    def _set_up_imperative_workspace_demo(self):
        logger.debug("Setting up imperative demo sequence")
        all_working_configuration = self.working_configuration
        llm = self.body["llm"]
        workspace = self.body["workspace"]
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
                llm=llm,
                workspace=workspace
            )
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

    def _configure_imperative_workspace_demo(self, inference_instance: Inference, **methods):
        logger.debug("Configuring imperative demo steps")
        @inference_instance.register_step("IWC")
        def input_working_configurations(**fkwargs):
            """Validate that input contains two numbers"""
            logger.debug("Executing IWC step")
            function = methods.get("input_working_configurations", self._input_working_configurations)
            return function(**fkwargs) 
        
        @inference_instance.register_step("OWC")
        def output_working_configurations(**fkwargs):
            """Perform the output working configurations"""
            logger.debug(f"Executing OWC step with concepts: {fkwargs['concept_to_infer_with_reference'].name}")
            function = methods.get("output_working_configurations", self._output_working_configurations)
            return function(**fkwargs)
        
        @inference_instance.register_step("RR")
        def return_reference(**fkwargs):
            """Perform the return reference"""
            logger.debug(f"Executing RR step with concepts: {fkwargs['concept_to_infer'].name}")
            function = methods.get("return_reference", self._return_reference)
            return function(**fkwargs)
        
        @inference_instance.register_step("MVP")
        def memorized_values_perception(**fkwargs):
            """Perform the memorized values perception"""
            logger.debug(f"Executing MVP step with value concepts: {[concept.name for concept in fkwargs['value_concepts']]}")
            function = methods.get("memorized_values_perception", self._memorized_values_perception)
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
            function = methods.get("actuator_perception", self._actuator_perception)
            return function(**fkwargs)
        
        @inference_instance.register_step("PTA")
        def on_perception_tool_actuation(**fkwargs):
            """Perform the on-perception tool actuation"""
            logger.debug(f"Executing PTA step with actuated functional reference: {fkwargs['actuated_functional_reference'].tensor}")
            function = methods.get("on_perception_tool_actuation", self._on_perception_tool_actuation)
            return function(**fkwargs)
        
        @inference_instance.register_step("ASP")
        def action_specification_perception(**fkwargs):
            """Perform the action specification perception"""
            logger.debug(f"Executing ASP step with function concept: {fkwargs['function_concept'].name}")
            function = methods.get("action_specification_perception", self._action_specification_perception)
            return function(**fkwargs)
        
        @inference_instance.register_step("MA") 
        def memory_actuation(**fkwargs):
            """Perform the memory actuation"""
            logger.debug("Executing MA step")
            function = methods.get("memory_actuation", self._memory_actuation)
            return function(**fkwargs)

if __name__ == "__main__":

    # Initialize concepts and inference
    technical_concepts_1, technical_concepts_classification_concept, technical_concepts_2 = init_concept_with_references()   
    classification_inference = Inference(
        sequence_name="imperative", 
        concept_to_infer=technical_concepts_2,
        value_concepts=[technical_concepts_1],
        function_concept=technical_concepts_classification_concept
    )

    # Initialize agent
    llm = LanguageModel("qwen-turbo-latest")
    agent = WriteAgent("workspace_demo", llm, init_working_configuration())
    agent.configure(
        inference_instance=classification_inference, 
        inference_sequence="imperative",
    )

    # Execute inference
    technical_concepts_2 = classification_inference.execute()

    # Print answer
    if technical_concepts_2.reference:
        print(f"Answer concept reference: {technical_concepts_2.reference.tensor}")
        print(f"Answer concept axes: {technical_concepts_2.reference.axes}")
        all_info_reference = cross_product([technical_concepts_1.reference, technical_concepts_classification_concept.reference, technical_concepts_2.reference])
        print(f"All info reference: {all_info_reference.tensor}")
        print(f"All info axes: {all_info_reference.axes}")
    else:
        print("Answer concept reference is None")
