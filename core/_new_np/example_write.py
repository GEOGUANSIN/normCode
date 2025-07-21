from _concept import Concept
from _reference import Reference, cross_product
from _inference import Inference, register_inference_sequence
from _agentframe import AgentFrame, logger
from _language_models import LanguageModel
from _methods._workspace_demo import all_workspace_demo_methods

def _log_concept_details(concept, reference=None, example_number=None, concept_name=None):
    """Helper function to log concept details in a consistent format"""
    if example_number and concept_name:
        logger.info(f"{example_number}. {concept_name}:")
    
    logger.info(f"   Concept: {concept.name}")
    logger.info(f"   Type: {concept.type} ({concept.get_type_class()})")
    
    if reference:
        # Get all values from the reference using slice(None) for all axes
        slice_params = {axis: slice(None) for axis in reference.axes}
        all_values = reference.get(**slice_params)
        logger.info(f"   All values: {all_values}")

def create_concept_with_reference(concept_name, concept_id, reference_value, concept_type="{}", reference_axes=None, reference_shape=None):
    """
    Create a concept with an associated reference object.
    
    Args:
        concept_name (str): The name of the concept (e.g., "{technical_concepts}?")
        concept_id (str): The internal identifier for the concept
        reference_value (str): The value to set in the reference
        concept_type (str): The type format for the concept (default: "{}")
        reference_axes (list): List of axis names for the reference (default: [concept_id])
        reference_shape (tuple): Shape of the reference tensor (default: (1,))
    
    Returns:
        tuple: (concept, reference) - The created concept and its reference
    """
    # Set default values if not provided
    if reference_axes is None:
        reference_axes = [concept_id]
    if reference_shape is None:
        reference_shape = (1,)
    
    # Create reference
    reference = Reference(reference_axes, reference_shape)
    
    # Set the reference value
    reference.set(f"%({reference_value})", **{concept_id: 0})
    
    # Create concept
    concept = Concept(concept_name, concept_id, reference, concept_type)
    
    return concept, reference

def create_simple_concept(concept_name, concept_id, concept_type="{}"):
    """
    Create a simple concept without a reference object.
    
    Args:
        concept_name (str): The name of the concept
        concept_id (str): The internal identifier for the concept
        concept_type (str): The type format for the concept (default: "{}")
    
    Returns:
        Concept: The created concept
    """
    return Concept(concept_name, concept_id, None, concept_type)

def init_concept_with_references():
    """Demonstrate Concept class with actual Reference objects"""
    
    logger.info("=== Concept with References Examples ===")

    # Example 1: Technical concepts question concept
    technical_concepts_type = "a mentioned concept that is related to a technical problem, and can be difficult to understand for non-technical people."
    technical_concepts_1, technical_concepts_1_ref = create_concept_with_reference(
        concept_name="{technical_concepts}?",
        concept_id="technical_concepts_1",
        reference_value=technical_concepts_type,
        concept_type="{}"
    )
    _log_concept_details(technical_concepts_1, technical_concepts_1_ref, "1", "{technical_concepts}?")

    # Example 2: Content-based technical concepts classification concept
    technical_concepts_classification_concept, technical_concepts_classification_ref = create_concept_with_reference(
        concept_name=":S_read_content:({1}?<$({technical_concepts})%_>)",
        concept_id="technical_concepts_classification",
        reference_value=":S_read_content:({1}?<$({technical_concepts})%_>)",
        concept_type="::({})"
    )
    _log_concept_details(technical_concepts_classification_concept, technical_concepts_classification_ref, "2", ":S_read_content:({1}?<$({technical_concepts})%_>)")

    # Example 3: Simple technical concepts concept (no reference)
    technical_concepts_2 = create_simple_concept(
        concept_name="{technical_concepts}",
        concept_id="technical_concepts_2"
    )
    _log_concept_details(technical_concepts_2, None, "3", "{technical_concepts}")

    # Example 4: Relatable ideas operation
    relatable_ideas_operation_concept, relatable_ideas_operation_ref = create_concept_with_reference(
        concept_name="::(make {1}<$({technical_concepts})%_> into {2}?<$({relatable_ideas})%_> using everyday analogies)",
        concept_id="relatable_ideas_operation",
        reference_value="::(make {1}<$({technical_concepts})%_> into {2}?<$({relatable_ideas})%_> using everyday analogies)",
        concept_type="::({})"
    )
    _log_concept_details(relatable_ideas_operation_concept, relatable_ideas_operation_ref, "4", "::({})")

    # Example 5: Relatable ideas concept
    relatable_ideas_type = "a related expression that is related to a specific technical concept."
    relatable_ideas_concept, relatable_ideas_ref = create_concept_with_reference(
        concept_name="{relatable_ideas}?",
        concept_id="relatable_ideas",
        reference_value=relatable_ideas_type,
        concept_type="{}"
    )
    _log_concept_details(relatable_ideas_concept, relatable_ideas_ref, "5", "{relatable_ideas}?")

    # Example 6: Relatable ideas concept
    relatable_ideas_concept_2  = create_simple_concept(
        concept_name="{relatable_ideas}",
        concept_id="relatable_ideas_2",
        concept_type="{}"
    )
    _log_concept_details(relatable_ideas_concept, None, "6", "{relatable_ideas}")


    # Example 7: Write content concept
    write_content_concept, write_content_ref = create_concept_with_reference(
        concept_name=":S_write_content:(transform {1}<$({technical_concepts})%_> into {2}?<$({relatable_ideas})%_>)",
        concept_id="write_content",
        reference_value=":S_write_content:(transform {1}<$({technical_concepts})%_> into {2}?<$({relatable_ideas})%_>)",
        concept_type="::({})"
    )
    _log_concept_details(write_content_concept, write_content_ref, "7", ":S_write_content:(transform {1}<$({technical_concepts})%_> into {2}?<$({relatable_ideas})%_>)")

    # Example 8: Content concept
    content_concept = create_simple_concept(
        concept_name="{content}",
        concept_id="content",
        concept_type="{}"
    )
    _log_concept_details(content_concept, None, "8", "{content}")


    return (
        technical_concepts_1, 
        technical_concepts_classification_concept, 
        technical_concepts_2,
        relatable_ideas_operation_concept,
        relatable_ideas_concept,
        relatable_ideas_concept_2,
        write_content_concept,
        content_concept
    )
 
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
    ":S_read_content:({1}?<$({technical_concepts})%_>)": {
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
    "::(make {1}<$({technical_concepts})%_> into {2}?<$({relatable_ideas})%_> using everyday analogies)": {
        "perception": {
            "ap": {
                "mode": "llm_formal",
                "product": "translated_templated_function",
                "value_order": {
                    "{technical_concepts}": 0,
                    "{relatable_ideas}?": 1,
                },
            },
            "asp": {
                "mode": "in-cognition"
            }
        },
        "actuation": {
            "pta": {
                "mode": "in-cognition",
                "value_order": {
                    "{technical_concepts}": 0,
                    "{relatable_ideas}?": 1,
                }
            },
            "ma": {
                "mode": "formal"
            }
        },
        "cognition": {
            "rr": {
                "mode": "identity"
            }
        }
    },
    "{relatable_ideas}?": {
        "perception": {
            "mvp": {
                "mode": "formal"
            },
        },
        "actuation": {},
        "cognition": {}
    },
    "{relatable_ideas}": {
        "perception": {
            "mvp": {
                "mode": "formal"
            },
        },
        "actuation": {},
        "cognition": {}
    },
    ":S_write_content:(transform {1}<$({technical_concepts})%_> into {2}?<$({relatable_ideas})%_>)": {
        "perception": {
            "ap": {
                "mode": "llm_workspace",
                "product": "translated_templated_function",
                "value_order": {
                    "{technical_concepts}": 0,
                    "{relatable_ideas}": 1,
                },
                "workspace_object_name_list": ["content"]
            },
            "asp": {
                "mode": "in-cognition"
            }
        },
        "actuation": {
            "pta": {
                "mode": "in-cognition",
                "value_order": {
                    "{technical_concepts}": 0,
                    "{relatable_ideas}": 1,
                }
            },
            "ma": {
                "mode": "formal"
            }
        },
        "cognition": {
            "rr": {
                "mode": "identity",
            }
        },
    },
    "{content}": {
        "perception": {
            "mvp": {
                "mode": "formal"
            },
        },
        "actuation": {},
        "cognition": {}
        },  
    }
    return working_configuration



def _log_inference_result(result_concept, value_concepts, function_concept):
    """Log the inference result and related information"""
    if result_concept.reference:
        logger.info(f"Answer concept reference: {result_concept.reference.tensor}")
        logger.info(f"Answer concept axes: {result_concept.reference.axes}")
        
        # Create list of all references for cross product
        all_references = [result_concept.reference]
        if value_concepts:
            all_references.extend([concept.reference for concept in value_concepts if concept.reference])
        if function_concept and function_concept.reference:
            all_references.append(function_concept.reference)
        
        if len(all_references) > 1:
            all_info_reference = cross_product(all_references)
            logger.info(f"All info reference: {all_info_reference.tensor}")
            logger.info(f"All info axes: {all_info_reference.axes}")
    else:
        logger.warning("Answer concept reference is None")


class WriteAgent(AgentFrame):
    def __init__(self, name, working_configuration, **body):
        super().__init__(name, working_configuration=working_configuration, **body)
        self.body = body
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
            logger.debug(f"£$£$the workspace: {workspace}")
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
    (technical_concepts_1, 
    technical_concepts_classification_concept, 
    technical_concepts_2, 
    relatable_ideas_operation_concept, 
    relatable_ideas_concept,
    relatable_ideas_concept_2,
    write_content_concept,
    content_concept) = init_concept_with_references()   
    first_inference = Inference(
        sequence_name="imperative", 
        concept_to_infer=technical_concepts_2,
        value_concepts=[technical_concepts_1],
        function_concept=technical_concepts_classification_concept
    )
    second_inference = Inference(
        sequence_name="imperative", 
        concept_to_infer=relatable_ideas_concept_2,
        value_concepts=[technical_concepts_2, relatable_ideas_concept],
        function_concept=relatable_ideas_operation_concept
    )
    third_inference = Inference(
        sequence_name="imperative", 
        concept_to_infer=content_concept,
        value_concepts=[technical_concepts_2, relatable_ideas_concept_2],
        function_concept=write_content_concept
    )

    # Initialize agent
    llm = LanguageModel("qwen-plus")
    workspace = {
        "content": "The new cloud architecture reduces latency by 35% through optimized edge caching and parallel processing. Enterprise customers can now deploy AI models with sub-100ms response times."
    } 
    # Initialize content agent
    content_agent = WriteAgent(
        "workspace_demo",
        init_working_configuration(),
        llm=llm,
        workspace=workspace)

    # Configure content agent and update value concepts
    content_agent.configure(
        inference_instance=first_inference, 
        inference_sequence="imperative",
    )
    technical_concepts_2 = first_inference.execute()

    print("========== First inference completed ==========")

    # Initialize formal agent
    formal_agent = AgentFrame(
        "demo",
        init_working_configuration(),
        llm=llm,
        workspace=workspace)

    # Configure formal agent and update value concepts
    second_inference.value_concepts = [technical_concepts_2, relatable_ideas_concept]
    formal_agent.configure(
        inference_instance=second_inference, 
        inference_sequence="imperative",
    )
    relatable_ideas_concept_2 = second_inference.execute()

    print("========== Second inference completed ==========")

    # Initialize content agent
    write_content_agent = WriteAgent(
        "workspace_demo",
        init_working_configuration(),
        llm=llm,
        workspace=workspace)

    third_inference.value_concepts = [technical_concepts_2, relatable_ideas_concept_2]
    write_content_agent.configure(
        inference_instance=third_inference, 
        inference_sequence="imperative",
    )
    content_concept = third_inference.execute()
    print("========== Third inference completed ==========")




    # Log answer
    print("========== First inference result ==========")
    _log_inference_result(
        result_concept=technical_concepts_2,
        value_concepts=[technical_concepts_1],
        function_concept=technical_concepts_classification_concept
    )
    print("========== Second inference result ==========")
    _log_inference_result(
        result_concept=relatable_ideas_concept_2,
        value_concepts=[technical_concepts_2, relatable_ideas_concept],
        function_concept=relatable_ideas_operation_concept
    )
    print("========== Third inference result ==========")
    _log_inference_result(
        result_concept=content_concept,
        value_concepts=[technical_concepts_2, relatable_ideas_concept_2],
        function_concept=write_content_concept
    )

