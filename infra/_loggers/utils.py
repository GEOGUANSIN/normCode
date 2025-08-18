def log_states_progress(states: States, step_name: str, step_filter: str | None = None):
    logger = logging.getLogger(__name__)
    logger.info(f"\n--- States after {step_name} (Filtered by: {step_filter if step_filter else 'None'}) ---")
    logger.info(f"Current Step: {states.sequence_state.current_step}")
    
    def _log_record_list(label: str, record_list: List[ReferenceRecordLite]):
        logger.info(f"{label}:")
        filtered_records = [item for item in record_list if step_filter is None or item.step_name == step_filter]
        if not filtered_records:
            logger.info("  (Empty or no matching records for filter)")
            return
        for item in filtered_records:
            logger.info(f"  Step Name: {item.step_name}")
            if item.concept:
                logger.info(f"    Concept ID: {item.concept.id}, Name: {item.concept.name}, Type: {item.concept.type}, Context: {item.concept.context}, Axis: {item.concept.axis_name}")
            if item.reference and isinstance(item.reference, Reference):
                logger.info(f"    Reference Axes: {item.reference.axes}")
                logger.info(f"    Reference Shape: {item.reference.shape}")
                logger.info(f"    Reference Tensor: {item.reference.tensor}")
            if item.model:
                logger.info(f"    Model: {item.model}")

    _log_record_list("Function", states.function)
    _log_record_list("Values", states.values)
    _log_record_list("Context", states.context)
    _log_record_list("Inference", states.inference)

    logger.info("-----------------------------------")



def _log_concept_details(concept, reference=None, example_number=None, concept_name=None):
    """Helper function to log concept details in a consistent format"""
    if example_number and concept_name:
        logger.info(f"{example_number}. {concept_name}:")
    
    logger.info(f"   Concept: {concept.name}")
    logger.info(f"   Type: {concept.type} ({concept.get_type_class()})")
    
    if reference and isinstance(reference, Reference):
        # Get all values from the reference using slice(None) for all axes
        slice_params = {axis: slice(None) for axis in reference.axes}
        all_values = reference.get(**slice_params)
        logger.info(f"   All values: {all_values}")
        logger.info(f"   All values without skip values: {reference.get_tensor(ignore_skip=True)}")
        logger.info(f"   Axes: {reference.axes}")

def _log_inference_result(result_concept, value_concepts, function_concept):
    """Log the inference result and related information"""
    if result_concept.reference:
        logger.info(f"Answer concept reference: {result_concept.reference.tensor}")
        logger.info(f"Answer concept reference without skip values: {result_concept.reference.get_tensor(ignore_skip=True)}")
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
            logger.info(f"All info reference without skip values: {all_info_reference.get_tensor(ignore_skip=True)}")
            logger.info(f"All info axes: {all_info_reference.axes}")
    else:
        logger.warning("Answer concept reference is None")