1.output|:<:({result files})
1.1.grouping|<= &across
1.2.object|<- {Phase 1: Confirmation of Instruction}
1.2.1.assigning|<= $.([{1.2_initial_context_registerd.json}, {1.1_instruction_block.md}, {context/raw--*.md}])
1.2.2.object|<- {1.1_instruction_block.md}
1.2.2.1.imperative|<= ::{%(direct)}({prompt}<$({instruction distillation prompt})%>: {1}<$({ipnut files})%>)
1.2.2.2.object_%{prompt_location}:instruction_distillation_prompt.md|<- {instruction distillation prompt}<:{prompt}>
1.2.2.3.object|<- {input files}<:{1}>
1.2.2.3.1.grouping|<= &in
1.2.2.3.2.object_%{file_location}:original_user_prompt.md|<- {original prompt}
1.2.2.3.3.object|<- {other input files}
1.2.2.3.3.1.imperative|<= :>:{%(file_location)}({prompt}<$({location of related files prompt})%>)
1.2.2.3.3.2.object_%{prompt_location}:location_of_related_files_prompt.md|<- {location of related files}<:{prompt}>
1.2.3.object|<- [{1.2_initial_context_registerd.json}, {context/raw--*.md}]
1.2.3.1.imperative|<= ::{%(direct)}({prompt}<$({context registration prompt})%>: {1}<$({input files})%>)
1.2.3.2.object_%{prompt_location}:context_registration_prompt.md|<- {context registration prompt}<:{prompt}>
1.2.3.3.object|<- {input files}<:{1}>
1.2.3.3.1.grouping|<= &in
1.2.3.3.2.object|<- {original prompt}
1.2.3.3.3.object|<- {other input files}
1.2.4.object|<- [{1.2_initial_context_registerd.json}, {1.1_instruction_block.md}, {context/raw--*.md}]
1.2.4.1.imperative|<= :>:{%(with-canvas)}({prompt}<$({manual review of confirmation prompt})%>: {1})
1.2.4.2.object_%{prompt_location}:manual_review_of_confirmation_prompt.md|<- {manual review of confirmation prompt}<:{prompt}>
1.2.4.3.object|<- [{1.2_initial_context_registerd.json}, {1.1_instruction_block.md}, {context/raw--*.md}]<:{1}>
1.2.4.3.1.grouping|<= &in
1.2.4.3.2.object|<- [{1.2_initial_context_registerd.json}, {context/raw--*.md}]
1.2.4.3.3.object|<- {1.1_instruction_block.md}
1.3.object|<- {Phase 2: Deconstruction and Plan Formalization}
1.3.1.assigning|<= $.([{2.1_deconstruction_draft.ncd}, {2.2_natural_translation.ncn}, {2.3_plan_formalization.nc}])
1.3.2.object|<- {2.1_deconstruction_draft.ncd}
1.3.2.1.imperative|<= ::{%(direct)}({prompt}<$({normcode deconstruction prompt})%>: {1}<$({1.1_instruction_block.md})%>)
1.3.2.2.object_%{prompt_location}:normcode_deconstruction_prompt.md|<- {normcode deconstruction prompt}<:{prompt}>
1.3.2.3.object|<- {1.1_instruction_block.md}<:{1}>
1.3.3.object|<- {2.2_natural_translation.ncn}
1.3.3.1.imperative|<= ::{%(direct)}({prompt}<$({natural language translation prompt})%>: {1}<$({2.1_deconstruction_draft.ncd})%>)
1.3.3.2.object_%{prompt_location}:natural_language_translation_prompt.md|<- {natural language translation prompt}<:{prompt}>
1.3.3.3.object|<- {2.1_deconstruction_draft.ncd}<:{1}>
1.3.4.object|<- {2.3_plan_formalization.nc}
1.3.4.1.imperative|<= ::{%(direct)}({prompt}<$({plan formalization prompt})%>: {1}<$({2.1_deconstruction_draft.ncd})%>)
1.3.4.2.object_%{prompt_location}:plan_formalization_prompt.md|<- {plan formalization prompt}<:{prompt}>
1.3.4.3.object|<- {2.1_deconstruction_draft.ncd}<:{1}>
1.3.5.object|<- [{2.4_manual_review_of_deconstruction.md}, {2.3_plan_formalization.nc}, {2.2_natural_translation.ncn}]
1.3.5.1.imperative|<= :>:{%(with-canvas)}({prompt}<$({manual review of deconstruction prompt})%>: {1})
1.3.5.2.object_%{prompt_location}:manual_review_of_deconstruction_prompt.md|<- {manual review of deconstruction prompt}<:{prompt}>
1.3.5.3.object|<- [{2.3_plan_formalization.nc}, {2.2_natural_translation.ncn}]<:{1}>
1.3.5.3.1.grouping|<= &in
1.3.5.3.2.object|<- {2.3_plan_formalization.nc}
1.3.5.3.3.object|<- {2.2_natural_translation.ncn}
1.4.object|<- {Phase 3: Contextualization}
1.4.1.assigning|<= $.({3.1_context_distribution.md})
1.4.2.object|<- [{3.1_context_manifest.json}, {context/shared--*.md}, {context/_flow_index_--*.md}]
1.4.2.1.imperative|<= ::{%(direct)}({prompt}<$({context distribution prompt})%>: {1})
1.4.2.2.object_%{prompt_location}:context_distribution_prompt.md|<- {context distribution prompt}<:{prompt}>
1.4.2.3.object|<- [{2.3_plan_formalization.nc}, {1.2_initial_context_registerd.json}, all {context/raw--*.md}]<:{1}>
1.4.2.3.1.grouping|<= &in
1.4.2.3.2.object|<- {2.3_plan_formalization.nc}
1.4.2.3.3.object|<- {1.2_initial_context_registerd.json}
1.4.2.3.4.object|<- [all {context/raw--*.md}]
1.4.2.3.4.1.grouping|<= &across
1.4.2.3.4.2.object|<- {context/raw--*.md}
1.4.3.object|<- [{3.1_context_manifest.json}, {context/shared--*.md}, {context/_flow_index_--*.md}]
1.4.3.1.imperative|<= :>:{%(with-canvas)}({prompt}<$({manual review of contextualization prompt})%>: {1})
1.4.3.2.object_%{prompt_location}:manual_review_of_contextualization_prompt.md|<- {manual review of contextualization prompt}<:{prompt}>
1.4.3.3.object|<- [{3.1_context_manifest.json}, {context/shared--*.md}, {context/_flow_index_--*.md}]<:{1}>
1.5.object|<- {Phase 4: Materialization into an Executable Script}
1.5.1.assigning|<= $.({4.1_automated_script_generation.py})
1.5.2.object|<- {4.1_automated_script_generation.py}
1.5.2.1.imperative|<= ::{%(direct)}({prompt}<$({automated script generation prompt})%>: {1})
1.5.2.2.object_%{prompt_location}:automated_script_generation_prompt.md|<- {automated script generation prompt}<:{prompt}>
1.5.2.3.object|<- [{2.3_plan_formalization.nc}, {1.2_initial_context_registerd.json}, all {context/raw--*.md}]<:{1}>
1.5.2.3.1.grouping|<= &in
1.5.2.3.2.object|<- {2.3_plan_formalization.nc}
1.5.2.3.3.object|<- {3.1_context_manifest.json}
1.5.2.3.4.object|<- [all {context/shared--*.md}]
1.5.2.3.4.1.grouping|<= &across
1.5.2.3.4.2.object|<- {context/shared--*.md}
1.5.2.3.5.object|<- [all {context/_flow_index_--*.md}]
1.5.2.3.5.1.grouping|<= &across
1.5.2.3.5.2.object|<- {context/_flow_index_--*.md}
1.5.3.object|<- [{4.1_automated_script_generation.py}]
1.5.3.1.imperative|<= :>:{%(with-canvas)}({prompt}<$({manual review of materialization prompt})%>: {1})
1.5.3.2.object_%{prompt_location}:manual_review_of_materialization_prompt.md|<- {manual review of materialization prompt}<:{prompt}>
1.5.3.3.object|<- {4.1_automated_script_generation.py}<:{1}>
