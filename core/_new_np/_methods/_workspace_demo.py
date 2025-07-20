from _concept import Concept
from _reference import Reference, cross_product, element_action, cross_action
from string import Template
import logging
import sys
from typing import Optional

def setup_logging(level=logging.INFO, log_file=None):
    """Setup logging configuration for the inference module"""
    # Create formatter
    # formatter = logging.Formatter(
    #     '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    # )
    formatter = logging.Formatter(
        '[%(levelname)s] %(message)s - %(asctime)s - %(name)s'
    )

    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def all_workspace_demo_methods(sequence_name: str) -> dict:

    if sequence_name == "imperative":
        return {    
        "input_working_configurations": input_working_configurations,
        "output_working_configurations": output_working_configurations,
        "memorized_values_perception": memorized_values_perception,
        "actuator_perception": actuator_perception,
        "on_perception_tool_actuation": on_perception_tool_actuation,
        "action_specification_perception": action_specification_perception,
        "memory_actuation": memory_actuation,
        "return_reference": return_reference
    }
    else:
        return {}


def strip_element_wrapper(element: str) -> str:
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

def wrap_element_wrapper(element: str) -> str:
    """
    Wrap an element in %(...)
    """
    return f"%({element})"


def input_working_configurations(value_concepts:list[Concept], function_concept:Concept, concept_to_infer:Concept, all_working_configuration:dict):
    active_working_configuration = {}  

    for concept in value_concepts:
        active_working_configuration[concept.name] = all_working_configuration[concept.name]

    active_working_configuration[function_concept.name] = all_working_configuration[function_concept.name]

    active_working_configuration[concept_to_infer.name] = all_working_configuration[concept_to_infer.name]

    logger.debug(f"Active working configuration: {active_working_configuration}")

    return active_working_configuration

def output_working_configurations(concept_to_infer_with_reference):
    pass


def memorized_values_perception(working_configuration, value_concepts, function_concept):
    """Perform the memorized values perception"""
    logger.debug(f"Executing MVP step with value concepts: {value_concepts}")
    value_order = working_configuration[function_concept.name]["actuation"]["pta"]["value_order"]
    logger.debug(f"Value order: {value_order}")
    value_concepts_references: list[Optional[Reference | None]] = len(value_order) * [None] # type: ignore
    logger.debug(f"Value concepts references: {value_concepts_references}")

    for value_concept in value_concepts:
        raw_concept_reference = value_concept.reference
        logger.debug(f"Raw concept reference: {raw_concept_reference.tensor}")
        value_concept_index = int(value_order[value_concept.name])
        logger.debug(f"Value concept index: {value_concept_index}")
        concept_reference = element_action(strip_element_wrapper, [raw_concept_reference])
        logger.debug(f"Concept reference: {concept_reference.tensor}")
        value_concepts_references[value_concept_index] = concept_reference
    logger.debug(f"Value concepts: {[concept.name for concept in value_concepts]}")
    logger.debug(f"Value concepts references: {value_concepts_references}")
    return value_concepts_references

def actuator_perception(working_configuration, function_concept, concept_type, concept_to_infer, llm, **paras):
    """Perform the actuator perception"""
    logger.debug(f"Executing AP step with function concept: {function_concept}")
    
    if working_configuration[function_concept.name]["perception"]["ap"]["mode"] == "llm_workspace":

        workspace = paras["workspace"]
        workspace_object_name_list = working_configuration["workspace_object_name_list"]
        logger.debug(f"Workspace: {workspace}")
        logger.debug(f"Workspace object name list: {workspace_object_name_list}")

        workspace_object_dict = {workspace_object_name: workspace[workspace_object_name] for workspace_object_name in workspace_object_name_list}
        
        logger.debug(f"Workspace object dict: {workspace_object_dict}")

        if working_configuration[function_concept.name]["perception"]["ap"]["product"] == "translated_templated_function":
            input_length = len(working_configuration[function_concept.name]["perception"]["ap"]["value_order"])
            concept_to_infer_name = concept_to_infer.name
            
            translation_template = llm.load_prompt_template(f"{concept_type}_translate")
            instruction_template = llm.load_prompt_template("instruction")
            instruction_validation_template = llm.load_prompt_template("instruction_validation")

            context_string = ""
            system_message = ""
            if workspace_object_dict:
                for workspace_object_name, workspace_object in workspace_object_dict.items():
                    context_string += f"""\n
                    The above instruction is performed on the following {workspace_object_name}: "{workspace_object}"
                    """
                    system_message += f"""
                    You are a helpful assistant that performs instructions on the {workspace_object_name}.
                    """
            instruction_template = Template(instruction_template.template + context_string)
            logger.debug(f"Instruction template: {instruction_template}")
            instruction_validation_template = Template(instruction_validation_template.template + context_string)
            logger.debug(f"Instruction validation template: {instruction_validation_template}")

            logger.debug(f"System message: {system_message}")

            def _strip_translate_and_instruct_validate_validate_actuator(actuator_element):

                    stripped_actuator_element = strip_element_wrapper(actuator_element)
                    actuator_translation_template = translation_template.safe_substitute(input_normcode=stripped_actuator_element)
                    actuator_translated_raw = llm.generate(actuator_translation_template, system_message="")
                    actuator_translated_template = Template(actuator_translated_raw)
                    if input_length == 1:
                        def _generation_function_1(input_1):
                            valued_actuator_prompt = str(actuator_translated_template.safe_substitute(input_1=input_1, output=concept_to_infer_name))
                            instruction= instruction_template.safe_substitute(input=valued_actuator_prompt)
                            for i in range(5):
                                new_element_raw = llm.generate(instruction, system_message=system_message)
                                logger.debug(f"New element raw: {new_element_raw}")
                                instruction_validation_prompt = instruction_validation_template.safe_substitute(instruction=instruction, output=new_element_raw)
                                logger.debug(f"Instruction validation prompt: {instruction_validation_prompt}")
                                validity = llm.generate(instruction_validation_prompt, system_message="")
                                logger.debug(f"Instruction validation raw: {validity}")
                                if validity.startswith("Yes"):
                                    break
                                else:
                                    new_instruction = str(instruction) + f"(Notice that {new_element_raw} is incorrect in format.)"
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
                                new_element_raw = llm.generate(instruction, system_message=system_message)
                                logger.debug(f"New element raw: {new_element_raw}")
                                instruction_validation_prompt = instruction_validation_template.safe_substitute(instruction=valued_actuator_prompt, output=new_element_raw, concept_to_infer=concept_to_infer.name)
                                logger.debug(f"Instruction validation prompt: {instruction_validation_prompt}")
                                validity = llm.generate(instruction_validation_prompt, system_message="")
                                logger.debug(f"Instruction validation raw: {validity}")
                                if validity.startswith("Yes"):
                                    break
                                else:
                                    if i == 4:
                                        new_element_raw = "@#SKIP#@"
                                    new_instruction = str(instruction) + f"(Notice that {new_element_raw} is incorrect in format.)"
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

            _functional_actuator_reference = element_action(_strip_translate_and_instruct_validate_validate_actuator, [function_concept.reference])
            logger.debug(f"Functional actuator reference: {_functional_actuator_reference.tensor}")
            return _functional_actuator_reference
    else:
        raise ValueError(f"Invalid mode: {working_configuration[function_concept.name]['perception']['ap']['mode']}")

def on_perception_tool_actuation(working_configuration, actuated_functional_reference, crossed_perception_reference, function_concept, concept_to_infer):
    """Perform the on-perception tool actuation"""
    logger.debug(f"Executing PTA step with actuated functional reference: {actuated_functional_reference}")

    if working_configuration[function_concept.name]["actuation"]["pta"]["mode"] == "in-cognition":
        new_reference = cross_action(actuated_functional_reference, crossed_perception_reference, concept_to_infer.name)
        logger.debug(f"New reference: {new_reference.tensor}")
        return new_reference
    else:
        raise ValueError(f"Invalid mode: {working_configuration[function_concept.name]['actuation']['pta']['mode']}")

def action_specification_perception(working_configuration, applied_reference, function_concept):
    """Perform the action specification perception"""
    logger.debug(f"Executing ASP step with function concept: {function_concept}")
    if working_configuration[function_concept.name]["perception"]["asp"]["mode"] == "in-cognition":
        return applied_reference
    else:
        raise ValueError(f"Invalid mode: {working_configuration[function_concept.name]['perception']['asp']['mode']}")

def memory_actuation(action_specification_perception):
    """Perform the memory actuation"""
    logger.debug("Executing MA step")
    action_specification_perception_wrapped = element_action(wrap_element_wrapper, [action_specification_perception])
    logger.debug(f"Action specification perception wrapped: {action_specification_perception_wrapped.tensor}")
    return action_specification_perception_wrapped  

def return_reference(action_specification_perception, concept_to_infer):
    """Perform the return reference"""
    logger.debug("Executing RR step")
    concept_to_infer.reference = action_specification_perception
    logger.debug(f"Concept to infer reference: {concept_to_infer.reference.tensor}")
    return concept_to_infer


if __name__ == "__main__":
    pass