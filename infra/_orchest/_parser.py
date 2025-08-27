from infra._logger import logger
from typing import Dict, Any
import re


from typing import Any, Dict, List, Optional, Union
from typing import Literal
from pydantic import BaseModel, Field, model_validator, ConfigDict

class GrouperInfo(BaseModel):
    """Information for grouping behavior such as AND IN / OR ACROSS patterns."""

    type: str
    marker: Optional[Literal["in", "across", "only"]] = None
    by_axes: Optional[Any] = None
    annotation_list: Optional[List[str]] = None
    template: Optional[Any] = None



def _parse_normcode_grouping(expr):
    """
    Parse a NormCode grouping expression to extract:
      - GroupMarker (after &)
      - Values in parentheses, separated by ;
      - By axis after %:
    Each value in parentheses and each axis after %: is treated as a whole (including braces).
    """
    # Match the GroupMarker and the values in parentheses
    match = re.match(r"&(\w+)\(([^)]*)\)", expr)
    if not match:
        raise ValueError("Invalid NormCode grouping expression format")
    group_marker = match.group(1)
    values_str = match.group(2)
    # Split values by ; and strip whitespace
    values = [v.strip() for v in values_str.split(';') if v.strip()]
    # Find the by_axis after %: (always in format %:[...])
    by_axis_match = re.search(r"%:(\[.*\])", expr)
    if by_axis_match:
        # Extract the content inside brackets and split by semicolon
        bracket_content = by_axis_match.group(1)[1:-1]  # Remove [ and ]
        by_axis = [axis.strip() for axis in bracket_content.split(';') if axis.strip()]
    else:
        by_axis = []
    return {
        "marker": group_marker,
        "values": values,
        "by_axes": by_axis,
    }


def _parse_normcode_quantifying(expr: str) -> dict:
    """

    Parse a NormCode quantification expression and extract its main components:

      - LoopBaseConcept: the main concept being iterated over (inside the parentheses after *every)
      - ViewAxis: one or more axes to view, specified in square brackets after %: (e.g., %:[axis1;axis2])
      - ConceptToInfer: one or more concepts to infer, specified in square brackets after the dot (e.g., .[concept1;concept2])
      - LoopIndex: (optional) a loop index, specified after @ (e.g., @(2))
      - InLoopConcept: (optional) a concept within the loop, specified after ^ (e.g., ^(concept))
      - CarryoverCondition: (optional) a carryover condition, specified after <* (e.g., <*1>)

    Each axis or concept is treated as a whole, including any braces or special characters.
    Multiple axes or concepts are separated by semicolons (;).

    
    Args:
        expr (str): The quantification expression to parse
        
    Returns:
        dict: Dictionary containing parsed components
    
    Examples:
        >>> _parse_normcode_quantification("*every({loop_base})%:[{view_axis1};{view_axis2}].[{concept1}?;{concept2}?]@(2)^({concept3}<*1>)")
        {
            "LoopBaseConcept": "{loop_base}",
            "ViewAxis": ["{view_axis1}", "{view_axis2}"],
            "ConceptToInfer": ["{concept1}?", "{concept2}?"],
            "LoopIndex": "2",
            "InLoopConcept": {"*{concept3}": 1}
        }
    """
    logger.debug(f"Parsing quantification expression: {expr}")
    
    # Initialize result dictionary
    result: Dict[str, Any] = {
        "LoopBaseConcept": None,
        "ViewAxis": [],
        "ConceptToInfer": [],
        "LoopIndex": None,
        "InLoopConcept": None
    }
    try:
        # Match the basic *every pattern: *every(loopBaseConcept)%:[viewAxis].[conceptToInfer]
        basic_pattern = r"\*every\(([^)]+)\)%:\[([^\]]+)\]\.\[([^\]]+)\]"
        basic_match = re.match(basic_pattern, expr)
        if not basic_match:
            raise ValueError(f"Invalid quantification expression format: {expr}")
        # Extract basic components
        result["LoopBaseConcept"] = basic_match.group(1).strip()
        # Extract ViewAxis and split by semicolon
        view_axis_str = basic_match.group(2).strip()
        if view_axis_str.startswith('[') and view_axis_str.endswith(']'):
            view_axis_content = view_axis_str[1:-1]  # Remove [ and ]
            result["ViewAxis"] = [axis.strip() for axis in view_axis_content.split(';') if axis.strip()]
        else:
            result["ViewAxis"] = [view_axis_str]
        # Extract ConceptToInfer and split by semicolon
        concept_to_infer_str = basic_match.group(3).strip()
        if concept_to_infer_str.startswith('[') and concept_to_infer_str.endswith(']'):
            concept_content = concept_to_infer_str[1:-1]  # Remove [ and ]
            result["ConceptToInfer"] = [concept.strip() for concept in concept_content.split(';') if concept.strip()]
        else:
            result["ConceptToInfer"] = [concept_to_infer_str]
        logger.debug(f"Basic components extracted: LoopBaseConcept={result['LoopBaseConcept']}, ViewAxis={result['ViewAxis']}, ConceptToInfer={result['ConceptToInfer']}")
        # Check for optional LoopIndex after @
        loop_index_pattern = r"@\\(([^)]+)\\)"
        loop_index_match = re.search(loop_index_pattern, expr)
        if loop_index_match:
            result["LoopIndex"] = loop_index_match.group(1).strip()
            logger.debug(f"LoopIndex extracted: {result['LoopIndex']}")
        # Check for optional InLoopConcept and CarryoverCondition after ^
        # Example: ^({concept3}<*1>)
        in_loop_pattern = r"\\^\\(([^<)]+)(?:<\\*([0-9]+)>)?\\)"
        in_loop_match = re.search(in_loop_pattern, expr)
        if in_loop_match:
            in_loop_concept = in_loop_match.group(1).strip()
            carryover = in_loop_match.group(2)
            if carryover is not None:
                # Return as a dict: {"*{concept3}": 1}
                result["InLoopConcept"] = {f"*{in_loop_concept}": int(carryover)}
            else:
                result["InLoopConcept"] = in_loop_concept
            logger.debug(f"InLoopConcept extracted: {result['InLoopConcept']}")
        logger.debug(f"Final parsed result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error parsing quantification expression '{expr}': {str(e)}")
        raise ValueError(f"Failed to parse quantification expression: {expr}")


def _parse_normcode_assigning(expr: str) -> dict:
    """
    Parse a NormCode assigning expression to extract:
      - Assignment marker (after $, e.g., . or +)
      - Source concept (first concept in parentheses)
      - Destination concept (second concept in parentheses, after :)
    
    Args:
        expr (str): The assigning expression to parse (e.g., "$.(_a_:_b_)" or "$+(_a_:_b_)")
        
    Returns:
        dict: Dictionary containing parsed components
        
    Examples:
        >>> _parse_normcode_assigning("$.(_a_:_b_)")
        {
            "marker": ".",
            "assign_source": "_a_",
            "assign_destination": "_b_"
        }
        >>> _parse_normcode_assigning("$+(_source_:_dest_)")
        {
            "marker": "+",
            "assign_source": "_source_",
            "assign_destination": "_dest_"
        }
    """
    logger.debug(f"Parsing assigning expression: {expr}")
    
    # Initialize result dictionary
    result: Dict[str, Any] = {
        "marker": None,
        "assign_source": None,
        "assign_destination": None
    }
    
    try:
        # Match the pattern: $marker(source:destination)
        # The marker can be . or + (specification or continuation)
        pattern = r"\$([.+])\(([^:]+):([^)]+)\)"
        match = re.match(pattern, expr)
        
        if not match:
            raise ValueError(f"Invalid assigning expression format: {expr}")
        
        # Extract components
        result["marker"] = match.group(1).strip()
        result["assign_source"] = match.group(2).strip()
        result["assign_destination"] = match.group(3).strip()
        
        logger.debug(f"Parsed assigning expression: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error parsing assigning expression '{expr}': {str(e)}")
        raise ValueError(f"Failed to parse assigning expression: {expr}")


def _parse_normcode_timing(expr: str) -> dict:
    """
    Parse a NormCode timing expression to extract:
      - marker (e.g., "after")
      - condition (the concept to check)

    Args:
        expr (str): The timing expression to parse (e.g., "@after(data_loaded)")

    Returns:
        dict: Dictionary containing parsed components

    Examples:
        >>> _parse_normcode_timing("@after(data_loaded)")
        {
            "marker": "after",
            "condition": "data_loaded"
        }
    """
    logger.debug(f"Parsing timing expression: {expr}")

    # Initialize result dictionary
    result: Dict[str, Any] = {
        "marker": None,
        "condition": None,
    }

    try:
        # Match the pattern: @marker(condition)
        pattern = r"@(\w+)\(([^)]+)\)"
        match = re.match(pattern, expr)

        if not match:
            raise ValueError(f"Invalid timing expression format: {expr}")

        # Extract components
        result["marker"] = match.group(1).strip()
        result["condition"] = match.group(2).strip()

        logger.debug(f"Parsed timing expression: {result}")
        return result

    except Exception as e:
        logger.error(f"Error parsing timing expression '{expr}': {str(e)}")
        raise ValueError(f"Failed to parse timing expression: {expr}") 