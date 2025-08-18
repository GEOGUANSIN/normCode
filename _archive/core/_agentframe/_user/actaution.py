def _process_input_data(input_mode: str, input_data: Optional[dict[str, Union[Reference, str, dict]]], 
                       input_config: Optional[dict[str, dict[str, dict]]],
                       input_concept_names: List[str], concept_registry: Dict[str, Concept], 
                       agent: Optional[Any] = None, actuation_input: bool = True, debug: bool = False) -> List[Concept]:
    """Process input data and set up concept references.
    
    Returns:
        List of processed concepts with references set
    """
    from core._agentframe import AgentFrame, _create_concept_reference, _prompt_template_dynamic_substitution
    
    if agent is not None and not isinstance(agent, AgentFrame):
        raise ValueError("Agent must be an instance of AgentFrame")
        
    processed_concepts = []
    
    if debug:
        print(f"[DEBUG] Processing input data in mode: {input_mode}")
        print(f"[DEBUG] Input concepts: {input_concept_names}")

    if input_data is not None:
        if not isinstance(input_data, dict):
            raise TypeError("Input data must be a dictionary")

        # Check all required inputs are present
        missing_inputs = set(input_concept_names) - set(input_data.keys())
        if missing_inputs:
            raise ValueError(f"Missing input data for: {', '.join(missing_inputs)}")

        # Process each input concept
        for name in input_concept_names:
            if debug:
                print(f"[DEBUG] Processing concept: {name}")
            
            concept = concept_registry[name]
            concept_type = concept.comprehension["type"]
            input_value = input_data[name]
            working_config = input_config[name] if input_config else {}
            
            if input_mode.startswith("raw"):
                mode_of_explanation = input_mode.split("_", 1)[1] if len(input_mode.split("_")) > 1 else "direct_explanation"

                if mode_of_explanation == "direct_explanation":
                    if isinstance(input_value, str):
                        if debug:
                            print(f"[DEBUG] Converting string input to dict for {name}")
                            print(f"[DEBUG] Input string: {input_value}")
                        try:
                            input_value = json.loads(input_value)
                            if isinstance(input_value, list):
                                input_value = input_value[0]
                        except json.JSONDecodeError as e:
                            if debug:
                                print(f"[DEBUG] JSON parsing failed, trying eval: {e}")
                            # If JSON parsing fails, try eval
                            try:
                                input_value = eval(input_value)
                                if isinstance(input_value, list):
                                    input_value = input_value[0]
                            except Exception as e:
                                if debug:
                                    print(f"[DEBUG] Eval failed: {e}")
                                raise ValueError(f"Failed to parse input for {name}: {e}")

                    if isinstance(input_value, dict):
                        if "Explanation" not in input_value:
                            raise ValueError(f"Raw input for {name} must contain 'Explanation'")
                        if "Summary_Key" not in input_value:
                            raise ValueError(f"Raw input for {name} must contain 'Summary_Key'")
                        reference_explanation = input_value["Explanation"]
                        reference_summary_key = input_value["Summary_Key"]
                    else:
                        raise ValueError(f"Raw input for {name} must be a dictionary")
                
                elif mode_of_explanation == "empty_explanation":
                    reference_explanation = ""
                    reference_summary_key = str(input_value)
                
                elif mode_of_explanation == "replicate_explanation":
                    reference_explanation = str(input_value)
                    reference_summary_key = str(input_value)
                
                elif mode_of_explanation == "template_explanation":
                    template = working_config.get("template", "$input_value")
                    if isinstance(template, str):
                        template = Template(template)
                    elif isinstance(template, Template):
                        pass
                    else:   
                        raise ValueError(f"Template must be a string or Template")

                    reference_explanation = _prompt_template_dynamic_substitution(
                        prompt_template=template,
                        template_variable_definition_dict={
                            "input_value": "input_value",
                            "concept_name": "concept_name",
                            "concept_context": "concept_context",
                            "concept_type": "concept_type"
                        },
                        base_values_dict={"input_value": input_value, 
                                        "concept_name": concept.comprehension["name"],
                                        "concept_context": concept.comprehension["context"],
                                        "concept_type": concept.comprehension["type"]},
                        helper_functions={}
                    )
                    reference_summary_key = str(input_value)
                
                elif mode_of_explanation == "agent_explanation":
                    assert agent is not None
                    template = working_config.get("template", "What does $input_value likely mean? Explain in few sentences.")
                    prompt = _prompt_template_dynamic_substitution(
                        prompt_template=template,
                        template_variable_definition_dict={
                            "input_value": "input_value",
                            "concept_name": "concept_name",
                            "concept_context": "concept_context",
                            "concept_type": "concept_type"
                        },
                        base_values_dict={"input_value": input_value, 
                                        "concept_name": concept.comprehension["name"],
                                        "concept_context": concept.comprehension["context"],
                                        "concept_type": concept.comprehension["type"]},
                        helper_functions={},
                        debug=agent.debug
                    )
                    llm_name = working_config.get("llm", "llm")
                    llm = agent.body[llm_name] 
                    #assert that llm has an invoke method
                    assert hasattr(llm, "invoke")

                    reference_explanation = llm.invoke(prompt).replace("\n", " ").replace('"', "'")
                    reference_summary_key = str(input_value)
                
                else:
                    raise ValueError(f"Invalid mode of explanation: {mode_of_explanation}")

                if debug:
                    print(f"[DEBUG] Creating reference for {name}")
                    print(f"[DEBUG] Explanation: {reference_explanation}")
                    print(f"[DEBUG] Summary Key: {reference_summary_key}")
                
                # Create reference from raw input
                concept.reference = _create_concept_reference(
                    mode_of_remember=agent.working_memory["actuation"]["mode_of_remember"],
                    concept_name=concept.comprehension["name"],
                    explanation=reference_explanation,
                    summary_key=reference_summary_key,
                    concept_type=concept_type
                )

                #the concept must be go through the actuation process of the agent
                if actuation_input:
                    actuation_kwargs = {}
                    actuation_kwargs["perception_working_config"] = working_config["perception"]
                    if "cognition" in working_config:
                        actuation_kwargs["cognition_working_config"] = working_config["cognition"]
                    concept.reference = agent.actuation(
                        concept,
                        **actuation_kwargs
                    )   

                processed_concepts.append(concept)
    
    return processed_concepts 