import json
import re
import logging
import ast
from string import Template
import copy

# Configure logging
logger = logging.getLogger(__name__)





def _safe_eval(s):
    """Safely evaluate a string representation of a list or other Python literal."""
    try:
        return ast.literal_eval(s)
    except:
        return s

def _format_bullet_points(cn_list, n_list, v_list):
    """Format lists into bullet points."""
    bullets = []
    for cn, n, v in zip(cn_list, n_list, v_list):
        bullets.append(f" - {cn}: {n} (context: {v})")
    return "\n".join(bullets)

def _replace_placeholders_with_values(template, values):
    """Replace numbered placeholders in a template with values."""
    for i, value in enumerate(values, 1):
        template = template.replace(f"{{{i}}}", str(value))
        template = template.replace("_", " ")
    return template

def _clean_parentheses(text):
    """Remove parentheses content then clean up spaces."""
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def _prompt_template_dynamic_substitution(
    prompt_template: str | Template,
    template_variable_definition_dict: dict[str, str],
    base_values_dict: dict,
    helper_functions: dict,
    debug: bool = False
) -> str:
    """
    Substitutes only variables that can be resolved with available locals.
    Leaves unresolved variables in the template unchanged.
    
    Args:
        prompt_template: The template string or Template object
        template_variable_definition_dict: Dictionary mapping variable names to code snippets
        base_values_dict: Dictionary of base values available for substitution
        helper_functions: Dictionary of helper functions available for substitution
        debug: If True, prints detailed debug information about the substitution process
    """
    func_name = "_prompt_template_dynamic_substitution"
    substitutions = {}
    
    if debug:
        logger.debug(f"\n{'='*50}")
        logger.debug(f"DEBUG: {func_name}")
        logger.debug(f"{'='*50}")
        logger.debug(f"\n[{func_name}] Template Variables:")
        logger.debug(f"[{func_name}] Base values available: {list(base_values_dict.keys())}")
        logger.debug(f"[{func_name}] Helper functions available: {list(helper_functions.keys())}")
    
    # Convert string to Template if needed
    if isinstance(prompt_template, str):
        template = Template(prompt_template)
        if debug:
            logger.debug(f"\n[{func_name}] Original template string:")
            logger.debug(f"[{func_name}] {prompt_template}")
    else:
        template = prompt_template
        if debug:
            logger.debug(f"\n[{func_name}] Original template object:")
            logger.debug(f"[{func_name}] {template.template}")
    
    # Get all variables present in the template
    template_variables = template.get_identifiers()
    if debug:
        logger.debug(f"\n[{func_name}] Variables found in template:")
        for var in template_variables:
            logger.debug(f"[{func_name}]   - {var}")
    
    for var in template_variables:
        if var not in template_variable_definition_dict:
            if debug:
                logger.debug(f"\n[{func_name}] Skipping {var}: No code snippet defined")
            continue  # No code snippet for this variable
            
        code = template_variable_definition_dict[var]
        if debug:
            logger.debug(f"\n[{func_name}] Processing variable: {var}")
            logger.debug(f"[{func_name}] Code snippet: {code}")
        
        # Create execution environment with both base values and helper functions
        exec_env = copy.deepcopy(base_values_dict)
        exec_env.update(helper_functions)
        
        try:
            # Execute code in isolated environment with helper functions available
            exec(code, {}, exec_env)
            
            # Use the variable name itself as the key
            if var in exec_env:
                substitutions[var] = exec_env[var]
                if debug:
                    logger.debug(f"[{func_name}] Successfully substituted {var} = {exec_env[var]}")
            else:
                if debug:
                    logger.warning(f"[{func_name}] {var} not found in execution environment after code execution")
        except Exception as e:
            if debug:
                logger.error(f"[{func_name}] Error processing {var}: {str(e)}")
            # Skip substitution if any error occurs
            continue
            
    # Use safe_substitute to leave unresolved variables unchanged
    result = template.safe_substitute(substitutions)
    
    if debug:
        logger.debug(f"\n[{func_name}] Final substitutions:")
        for var, value in substitutions.items():
            logger.debug(f"[{func_name}]   {var} = {value}")
        logger.debug(f"\n[{func_name}] Final result:")
        logger.debug(f"[{func_name}] {result}")
        logger.debug(f"\n[{func_name}] {'='*50}")
    
    return result

def _cognition_llm_prompt_two_replacement(to_cognitize_name, prompt_template, variable_definitions,
                                            cognitized_llm, memory_location, to_cognitize_concept_name = None, perception_concept_name = None, index_dict=None, recollection=None):
    """Create a cognitized function that processes perceptions using the given template and definitions."""

    memory = eval(open(memory_location).read())

    base_values_dict = {}

    # Get to_cognitize_value with location awareness using nested recollection
    concept_name_list = [to_cognitize_concept_name] if to_cognitize_concept_name else []
    to_cognitize_value = _recollect_nested(memory, to_cognitize_name, concept_name_list, index_dict, recollection)
    if to_cognitize_value is None:
        to_cognitize_value = to_cognitize_name

    def cognitized_func(input_perception):
        perception_name = _clean_parentheses(str(input_perception[0]))
        perception_value = str(input_perception[1])
        
        base_values_dict["cog_v"] = to_cognitize_value
        base_values_dict["cog_n"] = to_cognitize_name
        base_values_dict["cog_cn"] = to_cognitize_concept_name if to_cognitize_concept_name is not None else "cog_cn"
        base_values_dict["perc_cn"] = perception_concept_name if perception_concept_name is not None else "perc_cn"
        base_values_dict["perc_n"] = perception_name
        base_values_dict["perc_v"] = perception_value

        # Define helper functions to pass to template substitution
        helper_functions = {
            '_safe_eval': _safe_eval,
            '_format_bullet_points': _format_bullet_points,
            '_replace_placeholders_with_values': _replace_placeholders_with_values,
            '_clean_parentheses': _clean_parentheses
        }

        cognitized_prompt = _prompt_template_dynamic_substitution(
            prompt_template, 
            variable_definitions, 
            base_values_dict,
            helper_functions
        )

        return eval(cognitized_llm.invoke(cognitized_prompt))

    return cognitized_func 