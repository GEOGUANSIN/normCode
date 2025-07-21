from _concept import Concept
from _reference import Reference, cross_product, element_action, cross_action
from string import Template
import logging
import sys
from typing import Optional
import ast
import re

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

def _raw_element_process(new_element_raw):
    """
    Process raw element output from LLM generation.
    
    Args:
        new_element_raw: The raw output from LLM generation (str or list)
        
    Returns:
        list: A list containing the processed element(s)
        
    Raises:
        ValueError: If the element type is not supported or cannot be parsed
    """
    if isinstance(new_element_raw, list):
        return new_element_raw
    elif isinstance(new_element_raw, str):
        # Handle empty or whitespace-only strings
        if not new_element_raw.strip():
            return [new_element_raw]
        
        # Try to extract list from code blocks (```python ... ```)
        code_block_match = re.search(r'```(?:python)?\s*\n?(.*?)\n?```', new_element_raw, re.DOTALL)
        if code_block_match:
            content = code_block_match.group(1).strip()
            try:
                # Try to evaluate as Python literal
                parsed = ast.literal_eval(content)
                if isinstance(parsed, list):
                    return parsed
            except (ValueError, SyntaxError):
                pass
        
        # Try to extract list from bracket notation [item1, item2, ...]
        bracket_match = re.search(r'\[(.*?)\]', new_element_raw, re.DOTALL)
        if bracket_match:
            content = bracket_match.group(1).strip()
            try:
                # Try to evaluate as Python literal
                parsed = ast.literal_eval(f"[{content}]")
                if isinstance(parsed, list):
                    return parsed
            except (ValueError, SyntaxError):
                pass
        
        # If no list format detected, return as single string element
        return [new_element_raw]
    else:
        raise ValueError(f"Invalid new element type: {type(new_element_raw)}")

def _setup_workspace_context(working_configuration, function_concept, workspace):
    """Setup workspace context and object dictionary"""
    workspace_object_name_list = working_configuration[function_concept.name]["perception"]["ap"]["workspace_object_name_list"]
    logger.debug(f"Workspace: {workspace}")
    logger.debug(f"Workspace object name list: {workspace_object_name_list}")

    workspace_object_dict = {workspace_object_name: workspace[workspace_object_name] for workspace_object_name in workspace_object_name_list}
    logger.debug(f"Workspace object dict: {workspace_object_dict}")
    
    return workspace_object_dict

def _build_context_strings(workspace_object_dict):
    """Build context strings for instruction templates"""
    context_string = ""
    system_message = ""
    if workspace_object_dict:
        for workspace_object_name, workspace_object in workspace_object_dict.items():
            context_string += f"""\nThe above instruction is performed on the following {workspace_object_name}: "{workspace_object}" """
            system_message += f"""You are a helpful assistant that performs instructions on the {workspace_object_name}."""
    return context_string, system_message

def _load_and_configure_templates(llm, concept_type, context_string):
    """Load and configure prompt templates"""
    translation_template = llm.load_prompt_template(f"{concept_type}_translate")
    instruction_template = llm.load_prompt_template("instruction")
    instruction_validation_template = llm.load_prompt_template("instruction_validation")

    instruction_template = Template(instruction_template.template + context_string)
    instruction_validation_template = Template(instruction_validation_template.template + context_string)
    
    logger.debug(f"Instruction template: {instruction_template.template}")
    logger.debug(f"Instruction validation template: {instruction_validation_template}")
    
    return translation_template, instruction_template, instruction_validation_template

def _validate_and_retry_generation(llm, instruction, instruction_validation_template, system_message, concept_to_infer_name=None, max_retries=5):
    """Validate generated output and retry if needed"""
    for i in range(max_retries):
        new_element_raw = llm.generate(instruction, system_message=system_message)
        logger.debug(f"New element raw: {new_element_raw}")
        
        if concept_to_infer_name:
            instruction_validation_prompt = instruction_validation_template.safe_substitute(
                instruction=instruction, output=new_element_raw, concept_to_infer=concept_to_infer_name
            )
        else:
            instruction_validation_prompt = instruction_validation_template.safe_substitute(
                instruction=instruction, output=new_element_raw
            )
        
        # logger.debug(f"Instruction validation prompt: {instruction_validation_prompt}")
        validity = llm.generate(instruction_validation_prompt, system_message="")
        logger.debug(f"Instruction validation raw: {validity}")
        
        if validity.startswith("Yes"):
            break
        else:
            if i == max_retries - 1:
                new_element_raw = "@#SKIP#@"
            new_instruction = str(instruction) + f"(Notice that {new_element_raw} is incorrect in format.)"
            instruction = Template(new_instruction)
            continue
    
    return new_element_raw

def _create_actuator_function(actuator_translated_template, instruction_template, instruction_validation_template,
                                 system_message, concept_to_infer_name, input_length, llm):
    """Create generation function for multiple inputs"""
    def _generation_function_n(input_list):
        input_dict = {}
        for i in range(input_length):
            input_dict[f"input_{i+1}"] = input_list[i]
            input_dict["output"] = concept_to_infer_name
        logger.debug(f"Input dict: {input_dict}")

        valued_actuator_prompt = str(actuator_translated_template.safe_substitute(**input_dict))
        logger.debug(f"Valued actuator prompt: {valued_actuator_prompt}")
        instruction = instruction_template.safe_substitute(input=valued_actuator_prompt)
        logger.debug(f"Instruction: {instruction}")
        
        new_element_raw = _validate_and_retry_generation(
            llm, instruction, instruction_validation_template, system_message, concept_to_infer_name
        )

        new_element = _raw_element_process(new_element_raw)

        return new_element
    return _generation_function_n

def _create_activation_function(translation_template, instruction_template, instruction_validation_template,
                             system_message, concept_to_infer_name, input_length, llm):
    """Create the main actuator function"""
    def _strip_translate_and_instruct_validate_validate_actuator(actuator_element):
        stripped_actuator_element = strip_element_wrapper(actuator_element)
        actuator_translation_template = translation_template.safe_substitute(input_normcode=stripped_actuator_element)
        actuator_translated_raw = llm.generate(actuator_translation_template, system_message="")
        actuator_translated_template = Template(actuator_translated_raw)
        
        if input_length < 1:
            raise ValueError(f"Input length must be 1 or greater, got {input_length}")
        
        return _create_actuator_function(
            actuator_translated_template, instruction_template, instruction_validation_template,
            system_message, concept_to_infer_name, input_length, llm
        )
    
    return _strip_translate_and_instruct_validate_validate_actuator

def actuator_perception(working_configuration, function_concept, concept_type, concept_to_infer, llm, **paras):
    """Perform the actuator perception"""
    logger.debug(f"Executing AP step with function concept: {function_concept}")
    
    if working_configuration[function_concept.name]["perception"]["ap"]["mode"] == "llm_workspace":
        # Setup workspace context
        workspace = paras["workspace"]
        workspace_object_dict = _setup_workspace_context(working_configuration, function_concept, workspace)
        
        if working_configuration[function_concept.name]["perception"]["ap"]["product"] == "translated_templated_function":
            input_length = len(working_configuration[function_concept.name]["perception"]["ap"]["value_order"])
            concept_to_infer_name = concept_to_infer.name
            
            # Build context strings
            context_string, system_message = _build_context_strings(workspace_object_dict)
            logger.debug(f"System message: {system_message}")
            
            # Load and configure templates
            translation_template, instruction_template, instruction_validation_template = _load_and_configure_templates(
                llm, concept_type, context_string
            )
            
            # Create actuator function
            activation_function = _create_activation_function(
                translation_template, instruction_template, instruction_validation_template,
                system_message, concept_to_infer_name, input_length, llm
            )
            
            # Apply actuator function to function concept reference
            _functional_actuator_reference = element_action(activation_function, [function_concept.reference])
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
    elif working_configuration[function_concept.name]["actuation"]["pta"]["mode"] == "in-workspace":
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