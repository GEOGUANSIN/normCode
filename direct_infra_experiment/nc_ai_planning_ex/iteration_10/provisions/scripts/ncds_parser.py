"""
NCDS Parser Script - Parse .ncds content into structured JSON lines.

Converts NormCode Draft Straightforward text into a list of dictionaries,
each representing a line with flow_index, content, depth, and type info.
"""

import json
import re
from typing import Any, Dict, List, Union


def extract_content(input_value: Any) -> str:
    """
    Extract the actual file content from potentially wrapped input.
    
    Handles:
    - Plain string (file content directly)
    - Dict with 'content' key (from file read result)
    - JSON string of dict with 'content' key (from literal wrapping)
    """
    if input_value is None:
        return ""
    
    # If it's a string, try to parse as JSON first
    if isinstance(input_value, str):
        # Try to parse as JSON (might be wrapped dict)
        try:
            parsed = json.loads(input_value)
            if isinstance(parsed, dict):
                # Extract content from dict
                return str(parsed.get('content', parsed.get('data', input_value)))
            elif isinstance(parsed, str):
                # It was a JSON-encoded string
                return parsed
            else:
                # Some other JSON value, convert to string
                return str(parsed)
        except (json.JSONDecodeError, TypeError):
            # Not JSON, use as-is (this is the actual file content)
            return input_value
    
    # If it's a dict, extract content
    if isinstance(input_value, dict):
        return str(input_value.get('content', input_value.get('data', str(input_value))))
    
    # Fallback: convert to string
    return str(input_value)


def calculate_depth(line: str) -> int:
    """Calculate indentation depth (4 spaces = 1 level)."""
    stripped = line.lstrip()
    spaces = len(line) - len(stripped)
    return spaces // 4


def detect_concept_type(content: str) -> Dict[str, Any]:
    """Detect the concept type from content."""
    result = {
        'inference_marker': None,
        'concept_type': None,
        'operator_type': None,
        'concept_name': None,
    }
    
    content = content.strip()
    if not content:
        return result
    
    # Extract inference marker
    inference_markers = [':<:', ':>:', '<=', '<-', '<*']
    remaining = content
    for marker in inference_markers:
        if content.startswith(marker):
            result['inference_marker'] = marker
            remaining = content[len(marker):].strip()
            break
    
    # Operators
    if remaining.startswith('$.'):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'specification'
    elif remaining.startswith('$%'):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'abstraction'
    elif remaining.startswith('&['):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'grouping'
    elif remaining.startswith("@:'") or remaining.startswith('@:!'):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'timing'
    elif remaining.startswith('*.'):
        result['concept_type'] = 'operator'
        result['operator_type'] = 'looping'
    # Semantic concepts
    elif remaining.startswith('::'):
        if '::<{' in remaining:
            result['concept_type'] = 'judgement'
            match = re.search(r'::<\{([^}]+)\}>', remaining)
            if match:
                result['concept_name'] = match.group(1)
        else:
            result['concept_type'] = 'imperative'
            match = re.search(r'::\(([^)]*)\)', remaining)
            if match:
                result['concept_name'] = match.group(1)
    elif remaining.startswith('<') and '>' in remaining:
        result['concept_type'] = 'proposition'
        match = re.match(r'^<([^>]+)>', remaining)
        if match:
            result['concept_name'] = match.group(1)
    elif remaining.startswith('[') and ']' in remaining:
        result['concept_type'] = 'relation'
        match = re.match(r'^\[([^\]]+)\]', remaining)
        if match:
            result['concept_name'] = match.group(1)
    elif remaining.startswith('{') and '}' in remaining:
        result['concept_type'] = 'object'
        match = re.match(r'^\{([^}]+)\}', remaining)
        if match:
            result['concept_name'] = match.group(1)
    elif remaining.startswith('/:') or remaining.startswith('?:'):
        result['concept_type'] = 'comment'
    
    return result


def parse_ncds(input_1: Union[str, dict], body=None) -> List[Dict[str, Any]]:
    """
    Parse NCDS content into a list of structured line dictionaries.
    
    Args:
        input_1: The .ncds file content as a string
                 (may be wrapped in dict with 'content' key from file read,
                  or JSON string of such dict from literal wrapping)
        body: Optional Body instance (not used)
        
    Returns:
        List of dicts, each with:
        - flow_index: str (e.g., "1.2.3")
        - content: str (the line content, stripped)
        - depth: int (indentation level)
        - type: str ("main" or "comment")
        - inference_marker: str or None
        - concept_type: str or None
        - concept_name: str or None
    """
    # Extract actual file content from potentially wrapped input
    file_content = extract_content(input_1)
    
    # Debug: if content looks like it might still be wrapped, try one more extraction
    if file_content.startswith('{') and '"content"' in file_content:
        try:
            parsed = json.loads(file_content)
            if isinstance(parsed, dict) and 'content' in parsed:
                file_content = str(parsed['content'])
        except (json.JSONDecodeError, TypeError):
            pass
    
    lines = file_content.splitlines()
    parsed_lines = []
    indices = []
    
    for raw_line in lines:
        if not raw_line.strip():
            continue
        
        depth = calculate_depth(raw_line)
        content = raw_line.strip()
        
        # Determine if this is a concept line
        concept_prefixes = [':<:', ':>:', '<=', '<-', '<*', '$', '&[', '@:', '*:', '::']
        is_concept = any(content.startswith(p) for p in concept_prefixes)
        
        # Handle inline comments
        main_part = content
        if '|' in content and not content.startswith('|'):
            main_part = content.split('|', 1)[0].strip()
        
        # Calculate flow index for concepts
        flow_index = None
        if is_concept:
            while len(indices) <= depth:
                indices.append(0)
            indices = indices[:depth + 1]
            indices[depth] += 1
            flow_index = ".".join(map(str, indices))
        else:
            # Inherit flow index from previous concept
            for prev in reversed(parsed_lines):
                if prev.get('type') == 'main' and prev.get('flow_index'):
                    flow_index = prev['flow_index']
                    break
        
        # Detect concept type
        concept_info = detect_concept_type(main_part) if is_concept else {}
        
        line_entry = {
            "flow_index": flow_index,
            "content": content,
            "depth": depth,
            "type": "main" if is_concept else "comment",
            "inference_marker": concept_info.get("inference_marker"),
            "concept_type": concept_info.get("concept_type"),
            "concept_name": concept_info.get("concept_name"),
        }
        
        parsed_lines.append(line_entry)
    
    return parsed_lines


# Alias for paradigm compatibility
def main(input_1: Union[str, dict], body=None) -> List[Dict[str, Any]]:
    """Alias for paradigm compatibility."""
    return parse_ncds(input_1, body)

