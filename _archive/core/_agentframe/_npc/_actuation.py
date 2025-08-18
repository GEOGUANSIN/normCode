def _create_concept_reference(concept_name: str, explanation: str, summary_key: Optional[str] = None, mode_of_remember: str = "memory_bullet", concept_type: Optional[str] = None, axes_name: Optional[str] = None) -> Reference:
    """Create a reference for a concept with an explicit value.
    
    Args:
        concept: The name of the concept
        value: The explicit value to assign to the concept
        summary: Optional summary for the reference. If None, uses value
        mode_of_remember: The mode of remember to use for the reference
        concept_type: The type of the concept
        axes_name: The name of the axes to use for the reference

    Returns:
        A Reference object containing the concept reference with the specified value
    """
    # at least one of explanation or summary_key must be provided
    if (explanation is None or explanation == "") and (summary_key is None or summary_key == ""):
        raise ValueError("At least one of explanation or summary_key must be provided")
    
    if summary_key is None or summary_key == "":
        summary_key = explanation

    if axes_name is None or axes_name == "":
        axes_name = concept_name

    if mode_of_remember == "memory_bullet":
        return Reference(
            axes=[axes_name],
            shape=(1,),
            initial_value=f"[{explanation} : {summary_key}]"
        )
    elif mode_of_remember == "memory_json_bullet":
        return Reference(
            axes=[axes_name],
            shape=(1,),
            initial_value=f'{{"Explanation": "{explanation}", "Summary_Key": "{summary_key}"}}'
        )
    else:
        raise ValueError(f"Unknown mode of remember: {mode_of_remember}")


def direct_reference_to_concept(self, agent, input_mode: str = "raw", input_data: Optional[dict[str, Union[Reference, str, dict]]] = None, 
            input_config: Optional[dict[str, dict[str, dict]]] = None):
    """Process constants and update the inference registry."""
    from normalign_stereotype.core._agent_frame._agent_main import AgentFrame
    if not isinstance(agent, AgentFrame):
        raise ValueError("Agent must be an instance of AgentFrame")
    self.agent = agent
    self._debug_print("Starting direct reference.")

    # Check if all constant concepts are registered
    unregistered_concepts = [name for name in input_data.keys() if name not in self.concept_registry.keys()]
    if unregistered_concepts:
        raise ValueError(f"Some constant concepts are not registered: {', '.join(unregistered_concepts)}")

    # Add constant concepts to the list
    self.constant_concept_names.extend([
        name for name in input_data.keys()
        if name not in self.constant_concept_names
    ])

    # Process constants and get updated concepts
    processed_concepts = _process_input_data(
        input_mode, input_data, input_config, 
        self.constant_concept_names, self.concept_registry, 
        agent, True, self.debug
    )
    
    # Update concept registry with processed concepts
    for concept in processed_concepts:
        self.concept_registry[concept.comprehension["name"]] = concept
        
    # Verify all constants have references
    missing_refs = [
        name for name in self.constant_concept_names
        if not self.concept_registry[name].reference
    ]
    if missing_refs:
        raise ValueError(f"Missing references for constants: {', '.join(missing_refs)}")

    # Renew relevant inferences
    for inf_key, inference in self.inference_registry.items():
        # Check if inference uses any of the constant concepts
        if any(concept.comprehension["name"] in self.constant_concept_names 
                for concept in inference.post_actuation_pre_perception_concepts) or \
            inference.post_actuation_pre_cognition_concept.comprehension["name"] in self.constant_concept_names:
            # Renew the inference with updated concepts
            perception_concepts = [
                self.concept_registry[c.comprehension["name"]] 
                for c in inference.post_actuation_pre_perception_concepts
            ]
            cognition_concept = self.concept_registry[
                inference.post_actuation_pre_cognition_concept.comprehension["name"]
            ]
            inferred_concept = self.concept_registry[
                inference.concept_to_infer.comprehension["name"]
            ]
            
            self.inference_registry[inf_key] = Inference(
                concept_to_infer=inferred_concept,
                perception_concepts=perception_concepts,
                cognition_concept=cognition_concept,
                view=inference.view
            )

    return self