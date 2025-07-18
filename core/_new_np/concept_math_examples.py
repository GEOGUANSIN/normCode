from _concept import Concept
from _reference import Reference, cross_product, element_action, cross_action
from _inference import Inference
from _agentframe import AgentFrame, logger, register_inference_sequence
from _language_models import LanguageModel
from string import Template

def _strip_element_wrapper(element: str) -> str:
    """
    Strip %( and ) from a reference element.
    
    Args:
        element (str): A string that may be wrapped in %(...)
        
    Returns:
        str: The element with %( and ) removed if present
        
    Examples:
        >>> _strip_element_wrapper("%(1)")
        "1"
        >>> _strip_element_wrapper("%(::({1}<$({number})%_> add {2}<$({number})%_>))")
        "::({1}<$({number})%_> add {2}<$({number})%_>)"
        >>> _strip_element_wrapper("plain_text")
        "plain_text"
    """
    if element.startswith("%(") and element.endswith(")"):
        return element[2:-1]  # Remove first 2 chars (%() and last char ())
    return element



def demonstrate_concept_with_references():
    """Demonstrate Concept class with actual Reference objects"""
    
    print("=== Concept with References Examples ===\n")

    # Example 1: Mathematical operations with functional concepts
    print("1. Numbers:")
    number1_axes = ["number_1"]
    number1_shape = (2,)  # 2 numbers
    number1_ref = Reference(number1_axes, number1_shape)
    
    # Set mathematical operations
    number1_ref.set("%(1)", number_1=0) 
    number1_ref.set("%(2)", number_1=1) 

    number2_axes = ["number_2"]
    number2_shape = (2,)  # 2 numbers
    number2_ref = Reference(number2_axes, number2_shape)

    # Set mathematical operations
    number2_ref.set("%(3)", number_2=0)   
    number2_ref.set("%(4)", number_2=1) 

    number_1 = Concept("number_1", "Numbers", number1_ref, "{}")
    number_2 = Concept("number_2", "Numbers", number2_ref, "{}")

    print(f"   Concept: {number_1.name}")
    print(f"   Type: {number_1.type} ({number_1.get_type_class()})")
    print(f"   All numbers: {number1_ref.get(number_1=slice(None))}")
    print()

    print(f"   Concept: {number_2.name}")
    print(f"   Type: {number_2.type} ({number_2.get_type_class()})")
    print(f"   All numbers: {number2_ref.get(number_2=slice(None))}")
    print()

    # Example 2: Mathematical operations with functional concepts
    print("2. Mathematical Operation Concept:")
    operation_axes = ["operation"]
    operation_shape = (4,)  # 4 operations
    operation_ref = Reference(operation_axes, operation_shape)
    
    # Set mathematical operations
    operation_ref.set("%(::({1}<$({number})%_> add {2}<$({number})%_>))", operation=0)
    operation_ref.set("%(::({1}<$({number})%_> subtract {2}<$({number})%_>))", operation=1)
    operation_ref.set("%(::({1}<$({number})%_> multiply {2}<$({number})%_>))", operation=2)
    operation_ref.set("%(::({1}<$({number})%_> divide {2}<$({number})%_>))", operation=3)
    
    operation_concept = Concept("::({1}<$({number})%_> operate on {2}<$({number})%_>)", "Basic mathematical operations", operation_ref, "::({})")
    print(f"   Concept: {operation_concept.name}")
    print(f"   Type: {operation_concept.type} ({operation_concept.get_type_class()})")
    print(f"   All operations: {operation_ref.get(operation=slice(None))}")
    print()


    # Answer concept
    answer_axes = ["number_answer"]
    answer_shape = (1,)
    # answer_ref = Reference(answer_axes, answer_shape)
    # answer_ref.set("%(1)", answer=0)
    answer_concept = Concept("number_answer", "Answer", None, "{}")
    print(f"   Concept: {answer_concept.name}")

    return operation_concept, number_1, number_2, answer_concept
 
class MathAgentFrame(AgentFrame):
    def __init__(self, AgentFrameModel: str):
        super().__init__(AgentFrameModel)  
        self.working_configuration = {
            "number_1": {
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
            "number_2": {
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
            "::({1}<$({number})%_> operate on {2}<$({number})%_>)": {
                "perception": {
                    "asp": {
                        "mode": "in-cognition"
                    },
                    "ap": {
                        "mode": "llm_formal",
                        "product": "translated_templated_function",
                        "value_order": {
                            "number_1": 0,
                            "number_2": 1
                        }
                    }
                },
                "actuation": {
                    "pta": {
                        "mode": "in-cognition",
                        "value_order": {
                            "number_1": 0,
                            "number_2": 1
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
            "number_answer": {
                "perception": {
                    "mvp": {
                        "mode": "formal"
                    },
                },
            }
        }
        self.body["llm"] = LanguageModel("qwen-turbo-latest")



    def _set_up_imperative_demo(self):
        logger.debug("Setting up imperative demo sequence")
        @register_inference_sequence("imperative")
        def imperative(self: Inference, input_data: dict):
            """`(IWC-[(MVP-CP)-[AP-PTA-ASP]-MA)]-RR-OWC)`"""
            logger.info("Executing imperative sequence")
            
            # 1. Input Working Configuration
            logger.debug("Step 1: Input Working Configuration (IWC)")
            working_configuration = self.IWC(self.value_concepts, self.function_concept, self.concept_to_infer)
            # 2. Memorized Values Perception
            logger.debug("Step 2: Memorized Values Perception (MVP)")
            perception_references = self.MVP(working_configuration, self.value_concepts, self.function_concept)
            # 3. Cross Perception
            logger.debug("Step 3: Cross Perception (CP)")
            crossed_perception_reference = self.CP(perception_references)
            # 4. Apply Perception
            logger.debug("Step 4: Actuator Perception (AP)")
            actuated_functional_reference = self.AP(working_configuration, self.function_concept, "imperative", self.concept_to_infer)
            # 5. On-Perception Tool Actuation
            logger.debug("Step 5: On-Perception Tool Actuation (PTA)")
            applied_reference = self.PTA(working_configuration, actuated_functional_reference, crossed_perception_reference, self.function_concept, self.concept_to_infer)
            # 6. Action Specification Perception
            logger.debug("Step 6: Action Specification Perception (ASP)")
            action_specification_perception = self.ASP(applied_reference, self.function_concept) 
            # 7. Memory Actuation
            logger.debug("Step 7: Memory Actuation (MA)")
            self.MA(action_specification_perception)
            # 8. Return Reference
            logger.debug("Step 8: Return Reference (RR)")
            self.RR(actuated_functional_reference, self.concept_to_infer)
            # 9. Output Working Configuration
            logger.debug("Step 8: Output Working Configuration (OWC)")
            self.OWC(self.concept_to_infer)

            logger.info("Imperative sequence completed")

    def _configure_imperative_demo(self, inference_instance: Inference):
        logger.debug("Configuring imperative demo steps")
        @inference_instance.register_step("IWC")
        def input_working_configurations(value_concepts:list[Concept], function_concept:Concept, concept_to_infer:Concept):
            """Validate that input contains two numbers"""
            logger.debug("Executing IWC step")
            return self._input_working_configurations(value_concepts, function_concept, concept_to_infer)
        
        @inference_instance.register_step("OWC")
        def output_working_configurations(concepts_to_infer):
            """Perform the output working configurations"""
            logger.debug(f"Executing OWC step with concepts: {concepts_to_infer}")
            return self._output_working_configurations()
        
        @inference_instance.register_step("RR")
        def return_reference(actuated_reference, concepts_to_infer):
            """Perform the return reference"""
            logger.debug(f"Executing RR step with concepts: {concepts_to_infer}")
            pass    
        
        @inference_instance.register_step("MVP")
        def memorized_values_perception(working_configuration, value_concepts, function_concept):
            """Perform the memorized values perception"""
            logger.debug(f"Executing MVP step with value concepts: {value_concepts}")
            return self._memorized_values_perception(working_configuration, value_concepts, function_concept)
        
        @inference_instance.register_step("CP")
        def cross_perception(perception_references):
            """Perform the cross perception"""
            logger.debug("Executing CP step")
            logger.debug(f"Perception references: {[reference.tensor for reference in perception_references]}")
            crossed_perception_reference = cross_product(perception_references)
            logger.debug(f"Crossed perception reference: {crossed_perception_reference.tensor}")
            return crossed_perception_reference
        
        @inference_instance.register_step("AP")
        def actuator_perception(working_configuration, function_concept, concept_type, concept_to_infer):
            """Perform the apply perception"""
            logger.debug("Executing AP step")
            return self._actuator_perception(working_configuration, function_concept, concept_type, concept_to_infer)
        
        @inference_instance.register_step("PTA")
        def on_perception_tool_actuation(working_configuration, actuated_functional_reference, crossed_perception_reference, function_concept, concept_to_infer):
            """Perform the on-perception tool actuation"""
            logger.debug(f"Executing PTA step with actuated functional reference: {actuated_functional_reference}")
            return self._on_perception_tool_actuation(working_configuration, actuated_functional_reference, crossed_perception_reference, function_concept, concept_to_infer)
        
        @inference_instance.register_step("ASP")
        def action_specification_perception(actuated_reference, function_concept):
            """Perform the action specification perception"""
            logger.debug(f"Executing ASP step with function concept: {function_concept}")
            pass
        
        @inference_instance.register_step("MA") 
        def memory_actuation(actuated_reference):
            """Perform the memory actuation"""
            logger.debug("Executing MA step")
            pass

    def _input_working_configurations(self, value_concepts:list[Concept], function_concept:Concept, concept_to_infer:Concept):
        active_working_configuration = {}  

        for concept in value_concepts:
            active_working_configuration[concept.name] = self.working_configuration[concept.name]

        active_working_configuration[function_concept.name] = self.working_configuration[function_concept.name]

        active_working_configuration[concept_to_infer.name] = self.working_configuration[concept_to_infer.name]

        logger.debug(f"Active working configuration: {active_working_configuration}")

        return active_working_configuration

    def _output_working_configurations(self):


        return self.working_configuration

    def _memorized_values_perception(self, working_configuration, value_concepts, function_concept):
        """Perform the memorized values perception"""
        logger.debug(f"Executing MVP step with value concepts: {value_concepts}")
        value_order = working_configuration[function_concept.name]["actuation"]["pta"]["value_order"]
        logger.debug(f"Value order: {value_order}")
        value_concepts_references = len(value_order) * [None]
        logger.debug(f"Value concepts references: {value_concepts_references}")

        for value_concept in value_concepts:
            raw_concept_reference = value_concept.reference
            logger.debug(f"Raw concept reference: {raw_concept_reference.tensor}")
            value_concept_index = value_order[value_concept.name]
            logger.debug(f"Value concept index: {value_concept_index}")
            concept_reference = element_action(_strip_element_wrapper, [raw_concept_reference])
            logger.debug(f"Concept reference: {concept_reference.tensor}")
            value_concepts_references[value_concept_index] = concept_reference
        logger.debug(f"Value concepts: {value_concepts}")
        logger.debug(f"Value concepts references: {value_concepts_references}")
        return value_concepts_references

    def _actuator_perception(self, working_configuration, function_concept, concept_type, concept_to_infer):
        """Perform the actuator perception"""
        logger.debug(f"Executing AP step with function concept: {function_concept}")
        
        if working_configuration[function_concept.name]["perception"]["ap"]["mode"] == "llm_formal":
            if working_configuration[function_concept.name]["perception"]["ap"]["product"] == "translated_templated_function":
                
                input_length = len(working_configuration[function_concept.name]["perception"]["ap"]["value_order"])
                concept_to_infer_name = concept_to_infer.name
                
                llm = self.body["llm"]

                translation_template = llm.load_prompt_template(f"{concept_type}_translate")
                instruction_template = llm.load_prompt_template("instruction")
                instruction_validation_template = llm.load_prompt_template("instruction_validation")

                def _strip_translate_and_instruct_actuator(actuator_element):

                        stripped_actuator_element = _strip_element_wrapper(actuator_element)
                        actuator_translation_template = translation_template.safe_substitute(input_normcode=stripped_actuator_element)
                        actuator_translated_raw = llm.generate(actuator_translation_template, system_message="")
                        actuator_translated_template = Template(actuator_translated_raw)
                        if input_length == 1:
                            def _generation_function_1(input_1):
                                valued_actuator_prompt = str(actuator_translated_template.safe_substitute(input_1=input_1, output=concept_to_infer_name))
                                instruction= instruction_template.safe_substitute(input=valued_actuator_prompt)
                                for i in range(5):
                                    new_element_raw = llm.generate(instruction, system_message="")
                                    logger.debug(f"New element raw: {new_element_raw}")
                                    instruction_validation_prompt = instruction_validation_template.safe_substitute(instruction=instruction, output=new_element_raw)
                                    logger.debug(f"Instruction validation prompt: {instruction_validation_prompt}")
                                    validity = llm.generate(instruction_validation_prompt, system_message="")
                                    logger.debug(f"Instruction validation raw: {validity}")
                                    if validity == "Yes":
                                        break
                                    else:
                                        new_instruction = instruction.template + f"(Notice that {new_element_raw} is incorrect in format.)"
                                        instruction = Template(new_instruction)
                                        if i == 4:
                                            new_element_raw = "@#SKIP#@"
                                        continue
                                if isinstance(new_element_raw, str):
                                    new_element = [new_element_raw]
                                elif isinstance(new_element_raw, list):
                                    new_element = new_element_raw
                                else:
                                    raise ValueError(f"Invalid new element type: {type(new_element_raw)}")
                                return new_element
                            return _generation_function_1
                        elif input_length > 1:
                            def _generation_function_n(input_list):
                                input_dict = {}
                                for i in range(input_length):
                                    input_dict[f"input_{i+1}"] = input_list[i]
                                logger.debug(f"Input dict: {input_dict}")

                                for i in range(5):
                                    valued_actuator_prompt = str(actuator_translated_template.safe_substitute(**input_dict))
                                    logger.debug(f"Valued actuator prompt: {valued_actuator_prompt}")
                                    instruction= instruction_template.safe_substitute(input=valued_actuator_prompt)
                                    logger.debug(f"Instruction: {instruction}")
                                    new_element_raw = llm.generate(instruction, system_message="")
                                    logger.debug(f"New element raw: {new_element_raw}")
                                    instruction_validation_prompt = instruction_validation_template.safe_substitute(instruction=valued_actuator_prompt, output=new_element_raw, concept_to_infer=concept_to_infer.name)
                                    logger.debug(f"Instruction validation prompt: {instruction_validation_prompt}")
                                    validity = llm.generate(instruction_validation_prompt, system_message="")
                                    logger.debug(f"Instruction validation raw: {validity}")
                                    if validity == "Yes":
                                        break
                                    else:
                                        if i == 4:
                                            new_element_raw = "@#SKIP#@"
                                        new_instruction = instruction.template + f"(Notice that {new_element_raw} is incorrect in format.)"
                                        instruction = Template(new_instruction)
                                        continue

                                if isinstance(new_element_raw, str):
                                    new_element = [new_element_raw]
                                elif isinstance(new_element_raw, list):
                                    new_element = new_element_raw
                                else:
                                    raise ValueError(f"Invalid new element type: {type(new_element_raw)}")

                                return new_element

                            return _generation_function_n
                        else:
                            raise ValueError(f"Input length must be 1 or greater, got {input_length}")   

                _functional_actuator_reference = element_action(_strip_translate_and_instruct_actuator, [function_concept.reference])
                logger.debug(f"Functional actuator reference: {_functional_actuator_reference.tensor}")
                return _functional_actuator_reference
        else:
            raise ValueError(f"Invalid mode: {working_configuration[function_concept.name]['perception']['ap']['mode']}")


    def _on_perception_tool_actuation(self, working_configuration, actuated_functional_reference, crossed_perception_reference, function_concept, concept_to_infer):
        """Perform the on-perception tool actuation"""
        logger.debug(f"Executing PTA step with actuated functional reference: {actuated_functional_reference}")

        if working_configuration[function_concept.name]["actuation"]["pta"]["mode"] == "in-cognition":
            new_reference = cross_action(actuated_functional_reference, crossed_perception_reference, concept_to_infer.name)
            logger.debug(f"New reference: {new_reference.tensor}")
            return new_reference
        else:
            raise ValueError(f"Invalid mode: {working_configuration[function_concept.name]['actuation']['pta']['mode']}")

    

if __name__ == "__main__":
    operation_concept, number_1, number_2, answer_concept = demonstrate_concept_with_references()   
    agent = MathAgentFrame("demo")

    operation_inference = Inference(
        "imperative", 
        answer_concept,
        [number_1, number_2],
        operation_concept
    )


    agent.configure(operation_inference, "imperative")

    operation_inference.execute(input_data={})
