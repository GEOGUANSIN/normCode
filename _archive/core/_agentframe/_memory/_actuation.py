import json
import logging
import re
from core._npc_components._concept import Concept, CONCEPT_TYPE_CLASSIFICATION, CONCEPT_TYPE_JUDGEMENT, CONCEPT_TYPE_RELATION, CONCEPT_TYPE_OBJECT, CONCEPT_TYPE_SENTENCE, CONCEPT_TYPE_ASSIGNMENT
from core._npc_components._reference import cross_product
from core._agentframe._llm._cognition import _get_default_working_config
from core._npc_components._reference import Reference
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)


def _remember_in_concept_name_location_dict(name, value, concept_name, memory_location, index_dict=None):
    """Persist data to JSON file using concept_name|name|location format"""
    # Create a key with pipe separator and sorted location info
    if index_dict:
        # Sort indices for consistent key format
        sorted_indices = '::'.join(f"{k}_{v}" for k, v in sorted(index_dict.items()))
        key = f"{concept_name}|{name}|{sorted_indices}"
    else:
        key = f"{concept_name}|{name}"
    
    with open(memory_location, 'r+') as f:
        data = json.load(f)
        data[key] = value
        f.seek(0)
        json.dump(data, f)
        f.truncate()


def _actuation_memory_bullet(bullet, concept_name, memory_location, index_dict, remember):
    value, name = bullet.rsplit(':', 1)
    remember(name.strip(), value.strip(), concept_name, memory_location, index_dict)
    return name

def _actuation_memory_json_bullet(json_bullet, concept_name, memory_location, index_dict, remember):
    """Process JSON bullet points and update memory with location awareness.
    Accepts either a JSON string or a Python object (dict or list)."""
    try:
        # Handle both JSON strings and Python objects
        if isinstance(json_bullet, str):
            bullets = json.loads(json_bullet)
        else:
            bullets = json_bullet
            
        # Handle both list and dict inputs
        if isinstance(bullets, dict):
            # If it's a single dict, use it directly
            bullet = bullets
        elif isinstance(bullets, list) and len(bullets) > 0:
            # If it's a list, take the first item
            bullet = bullets[0]
        else:
            raise ValueError("Invalid format: must be a dictionary or non-empty list")
            
        if not isinstance(bullet, dict):
            raise ValueError("Invalid bullet format: must be a dictionary")
            
        name = bullet.get("Summary_Key", "")
        value = bullet.get("Explanation", "")
        
        if not name or not value:
            raise ValueError("Missing required fields: Summary_Key or Explanation")

        # Clean up the name by removing parentheses and extra spaces
        name = re.sub(r'[()]', '', name).strip()
        
        # Update memory with index information
        remember(name, value.strip(), concept_name, memory_location, index_dict)
        return name
        
    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing error: {str(e)}")
        logging.error(f"JSON string: {json_bullet}")
        return None
    except Exception as e:
        logging.error(f"Error processing JSON bullet: {str(e)}")
        logging.error(f"Input: {json_bullet}")
        return None
