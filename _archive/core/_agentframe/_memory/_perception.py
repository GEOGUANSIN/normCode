import logging

# Configure logging
logger = logging.getLogger(__name__)

def _recollect_nested(memory, name, concept_name_list, index_dict, recollection, debug=False):
    """Helper function to handle nested list recollection"""
    if debug:
        logger.debug(f"Recollecting nested for name: {name}")
        logger.debug(f"Memory content: {memory}")
        logger.debug(f"Index dict content: {index_dict}")
    
    if isinstance(name, list):
        return [_recollect_nested(memory, n, concept_name_list, index_dict, recollection, debug) for n in name]
    result = recollection(memory, name, concept_name_list, index_dict)
    if debug:
        logger.debug(f"Recollection result for {name}: {result}")
    return result


def _recollect_by_concept_name_location_dict(memory, name, concept_name_list, indices, debug=True):
    """Retrieve value from memory using concept_name|name|location format
    
    Args:
        memory: Dictionary containing memory entries
        name: Name to search for
        indices: Dictionary of indices to match
        debug: If True, enables debug logging
    """
    if debug:
        logger.debug(f"Starting recollection for name: {name}")
        logger.debug(f"Concept name list: {concept_name_list}")
        logger.debug(f"Indices to match: {indices}")
        logger.debug(f"Memory keys: {list(memory.keys())}")
    
    # Create target indices set
    target_indices = {f"{k}_{v}" for k, v in indices.items()}
    if debug:
        logger.debug(f"Target indices set: {target_indices}")
    
    # Find matching keys and check their indices
    for key in memory:
            
        # Get indices part if it exists
        key_parts = [part for part in key.split('|') if part]  # Filter out empty parts
        if len(key_parts) != 3:
            if debug:
                logger.debug(f"Skipping key (parsing key parts mistake): {key}")
            continue
        
        # Check if the first part of the key is in the concept_name_list
        if key_parts[0] not in concept_name_list:
            if debug:
                logger.debug(f"Skipping key (concept name mismatch): {key}")
            continue

        # Check if the name matches the second part of the key
        if key_parts[1] != name:
            if debug:
                logger.debug(f"Skipping key (name mismatch): {key}")
            continue
            
        # Check if target indices are a subset of stored indices or vice versa
        stored_indices = set(part for part in key_parts[2].split('::') if part)  # Filter out empty parts
        if debug:
            logger.debug(f"Checking key: {key}")
            logger.debug(f"Stored indices: {stored_indices}")
            logger.debug(f"Target indices subset check: {target_indices.issubset(stored_indices)}")
            logger.debug(f"Sorted indices subset check: {stored_indices.issubset(target_indices)}")
            
        if target_indices.issubset(stored_indices) or stored_indices.issubset(target_indices):
            if debug:
                logger.debug(f"Found matching key: {key}")
                logger.debug(f"Returning value: {memory[key]}")
            return memory[key]
            
    if debug:
        logger.debug("No matching key found")
    return None

def _combine_pre_perception_concepts_by_two_lists(pre_perception_concepts, agent):
    """Combine multiple perception concepts into a single concept for processing."""
    # Use cross-product to make the only perception concept for processing
    the_pre_perception_concept_name = (
        str([pc.comprehension["name"] for pc in pre_perception_concepts])
        if len(pre_perception_concepts) > 1
        else pre_perception_concepts[0].comprehension["name"]
    )
    the_pre_perception_reference = (
        cross_product(
            [pc.reference for pc in pre_perception_concepts]
        )
        if len(pre_perception_concepts) > 1
        else pre_perception_concepts[0].reference
    )

    the_pre_perception_concept_type = "[]"

    agent.working_memory['perception'][the_pre_perception_concept_name], _ = \
        _get_default_working_config(the_pre_perception_concept_type)

    return Concept(
        name = the_pre_perception_concept_name,
        context = "",
        type = the_pre_perception_concept_type,
        reference = the_pre_perception_reference,
    ) 


def _perception_memory_retrieval(name_may_list, concept_name_may_list, index_dict, recollection, memory_location, debug=False):
    """File-based value retrieval from JSONL storage with location awareness
    
    Args:
        name_may_list: Name or list of names to retrieve
        index_dict: Dictionary for indexing
        recollection: Function to perform the recollection
        memory_location: Path to the memory file
        debug: If True, enables debug logging
    """
    if debug:
        logger.debug(f"Starting memory retrieval for name_may_list: {name_may_list}")
        logger.debug(f"Memory location: {memory_location}")
        logger.debug(f"Index dictionary: {index_dict}")
    
    try:
        with open(memory_location, 'r', encoding='utf-8') as f:
            memory = eval(f.read())
            if debug:
                logger.debug(f"Successfully loaded memory from {memory_location}")
                logger.debug(f"Memory content type: {type(memory)}")
                logger.debug(f"Full memory content: {memory}")


            if isinstance(concept_name_may_list, str):
                concept_name_may_list = [concept_name_may_list]
            
            concept_name_list = concept_name_may_list

            if isinstance(name_may_list, str):
                name_may_list = [name_may_list]
            
            if isinstance(name_may_list, list):
                name_list = name_may_list
                if debug:
                    logger.debug(f"Processing list of names: {name_list}")
                value_list = _recollect_nested(memory, name_list, concept_name_list, index_dict, recollection, debug)
                if debug:
                    logger.debug(f"Retrieved values: {value_list}")
                return [name_list, value_list]
    except Exception as e:
        logger.error(f"Error during memory retrieval: {str(e)}", exc_info=True)
        raise 

