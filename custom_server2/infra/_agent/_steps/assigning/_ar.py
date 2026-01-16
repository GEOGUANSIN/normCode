import logging
from infra._core import Reference, element_action
from infra._states._assigning_states import States
from infra._syntax import Assigner
from infra._syntax._assigner import UnpackedList


def assigning_references(states: States) -> States:
    """Perform assignment based on syntax marker."""
    syntax_marker = states.syntax.marker
    
    if not syntax_marker:
        logging.error("AR failed: 'marker' must be specified in syntax.")
        states.set_current_step("AR")
        return states

    assigner = Assigner()
    output_ref = None
    
    # Build value concepts map for lookups
    value_concepts_map = {rec.concept.name: rec for rec in states.values}

    # ========== IDENTITY ($=) ==========
    if syntax_marker == "=":
        # Identity is a concept-level operation that needs blackboard
        canonical_concept = states.syntax.canonical_concept
        alias_concept = states.syntax.alias_concept
        
        if not canonical_concept or not alias_concept:
            logging.error("AR failed for identity (=): 'canonical_concept' and 'alias_concept' must be specified.")
            states.set_current_step("AR")
            return states
        
        # Identity requires blackboard access at orchestrator level
        # Store instruction for orchestrator to handle
        logging.info(f"Identity operation (=): '{alias_concept}' will be aliased to '{canonical_concept}'")
        # Note: Actual identity registration happens at orchestrator level via blackboard
        # We signal this by setting a special flag or returning metadata
        states.syntax.identity_pending = True
        states.set_current_step("AR")
        return states

    # ========== ABSTRACTION ($%) ==========
    elif syntax_marker == "%":
        face_value = states.syntax.face_value
        axis_names = states.syntax.axis_names
        
        if face_value is None:
            logging.error("AR failed for abstraction (%): 'face_value' must be specified.")
            states.set_current_step("AR")
            return states
        
        logging.info(f"Performing abstraction (%): Creating reference from face value.")
        output_ref = assigner.abstraction(
            face_value=face_value,
            axis_names=axis_names
        )
    
    # ========== SPECIFICATION ($.) ==========
    elif syntax_marker == ".":
        assign_source_name = states.syntax.assign_source
        assign_destination_name = states.syntax.assign_destination
        
        if not assign_source_name:
            logging.error("AR failed for specification (.): 'assign_source' must be specified.")
            states.set_current_step("AR")
            return states
        
        dest_record = value_concepts_map.get(assign_destination_name) if assign_destination_name else None
        dest_ref = dest_record.reference if dest_record else None
        
        source_refs = []
        if isinstance(assign_source_name, list):
            source_refs = [
                value_concepts_map.get(name).reference if value_concepts_map.get(name) else None 
                for name in assign_source_name
            ]
            logging.info(f"Performing specification (.) with source candidates: {assign_source_name} for destination '{assign_destination_name}'.")
        else:
            source_record = value_concepts_map.get(assign_source_name)
            if not source_record:
                logging.error(f"AR failed: Could not find source concept '{assign_source_name}' in value concepts.")
                states.set_current_step("AR")
                return states
            source_refs = [source_record.reference]
            logging.info(f"Performing specification (.): Assigning '{assign_source_name}' reference to '{assign_destination_name if assign_destination_name else 'result'}'.")
        
        output_ref = assigner.specification(source_refs, dest_ref)
    
    # ========== CONTINUATION ($+) ==========
    elif syntax_marker == "+":
        assign_source_name = states.syntax.assign_source
        assign_destination_name = states.syntax.assign_destination
        
        if not assign_source_name or not assign_destination_name:
            logging.error("AR failed for continuation (+): Both 'assign_source' and 'assign_destination' must be specified.")
            states.set_current_step("AR")
            return states
        
        if isinstance(assign_source_name, list):
            logging.error(f"AR failed for continuation (+): 'assign_source' must be a single concept, not a list.")
            states.set_current_step("AR")
            return states
        
        source_record = value_concepts_map.get(assign_source_name)
        if not source_record:
            logging.error(f"AR failed: Could not find source concept '{assign_source_name}' in value concepts.")
            states.set_current_step("AR")
            return states
        
        dest_record = value_concepts_map.get(assign_destination_name)
        dest_ref = dest_record.reference if dest_record else None
        
        source_ref = source_record.reference
        logging.info(f"Performing continuation (+): Adding '{source_record.concept.name}' reference to '{assign_destination_name}'.")
        output_ref = assigner.continuation(source_ref, dest_ref, by_axes=states.syntax.by_axes)
    
    # ========== DERELATION ($-) ==========
    elif syntax_marker == "-":
        assign_source_name = states.syntax.assign_source
        selector = states.syntax.selector
        
        if not assign_source_name:
            logging.error("AR failed for derelation (-): 'assign_source' must be specified.")
            states.set_current_step("AR")
            return states
        
        if not selector:
            logging.error("AR failed for derelation (-): 'selector' must be specified.")
            states.set_current_step("AR")
            return states
        
        source_record = value_concepts_map.get(assign_source_name)
        if not source_record:
            logging.error(f"AR failed: Could not find source concept '{assign_source_name}' in value concepts.")
            states.set_current_step("AR")
            return states
        
        source_ref = source_record.reference
        logging.info(f"Performing derelation (-): Selecting from '{assign_source_name}' with selector {selector}.")
        
        # Get the selector function
        selector_fn = assigner.derelation(selector)
        
        # Apply selector to the source reference
        output_ref = element_action(selector_fn, [source_ref])
        
        # Handle UnpackedList special case - flatten the result
        if output_ref and output_ref.tensor:
            flat_tensor = output_ref.tensor
            if isinstance(flat_tensor, list) and len(flat_tensor) > 0:
                # Check if any elements are UnpackedList
                unpacked_elements = []
                for item in flat_tensor:
                    if isinstance(item, UnpackedList):
                        unpacked_elements.extend(item)
                    else:
                        unpacked_elements.append(item)
                
                # If we had any unpacked lists, rebuild the reference
                if any(isinstance(item, UnpackedList) for item in flat_tensor):
                    output_ref = Reference.from_data(unpacked_elements)
                    logging.debug(f"Derelation: Flattened unpacked list, new shape: {output_ref.shape}")

    else:
        logging.warning(f"Unknown syntax marker: '{syntax_marker}'. No assignment performed.")
        # Try to return destination reference as fallback
        assign_destination_name = states.syntax.assign_destination
        if assign_destination_name:
            dest_record = value_concepts_map.get(assign_destination_name)
            if dest_record and dest_record.reference:
                output_ref = dest_record.reference.copy()

    # Store the output reference
    if output_ref:
        states.set_reference("inference", "AR", output_ref)
        logging.debug(f"AR completed. Output reference shape: {output_ref.shape}, axes: {output_ref.axes}")
    else:
        logging.warning("AR completed with no output reference.")

    states.set_current_step("AR")
    return states
