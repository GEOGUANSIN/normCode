1.output|:<:({result files})
1.1.grouping|<= &across
1.2.object|<- {Phase 1: Confirmation of Instruction}
1.2.1.assigning|<= $.([{1.1_instruction_block.md}, {1.2_initial_context_registerd.json}, {context_store/raw--*.md}])
1.2.2.object_%{file_location}:1.1_instruction_block.md|<- {1.1_instruction_block.md}
1.2.2.1.imperative_::{%(composition)}|<= ({prompt}<$({instruction distillation prompt})%>: {1}<$({input files})%>; {output}<$({output file location of instruction distillation})%>)
1.2.2.2.object_%{prompt_location}:prompts/1.1_instruction_distillation.md|<- {instruction distillation prompt}<:{prompt}>
1.2.2.3.object|<- {input files}<:{1}>
1.2.2.4.object_%{location_string}:1.1_instruction_block.md|<- {output file location of instruction distillation}<:{output}>
1.2.2.5.grouping|<= &in
1.2.2.6.object_%{file_location}:prompts/0_original_prompt.md|<- {original prompt}
1.2.2.7.object|<- {other input files}
1.2.2.7.1.imperative|<= :>:{%(file_location)}({prompt}<$({location of related files prompt})%>)
1.2.2.7.2.object_%{prompt_location}:location_of_related_files_prompt.md|<- {location of related files}<:{prompt}>
1.2.3.object_%{file_location}:1.2_initial_context_registerd.json, context_store/raw--*.md|<- [{1.2_initial_context_registerd.json}, {context_store/raw--*.md}]
1.2.3.1.imperative_::{%(composition)}|<= ({prompt}<$({context registration prompt})%>: {1}<$({input files})%>; {output}<$({output file locations of context registration})%>)
1.2.3.2.object_%{prompt_location}:prompts/1.2_context_registration.md|<- {context registration prompt}<:{prompt}>
1.2.3.3.object|<- {input files}<:{1}>
1.2.3.4.object_%{location_string}:1.2_initial_context_registerd.json, context_store/raw--*.md|<- {output file locations of context registration}<:{output}>
1.2.4.object|<- [{1.1_instruction_block.md}, {1.2_initial_context_registerd.json}, {context_store/raw--*.md}]
1.2.4.1.imperative|<= :>:{%(with-canvas)}({prompt}<$({manual review prompt})%>: {1})
1.2.4.2.object_%{prompt_location}:1.3_manual_review.md|<- {manual review prompt}<:{prompt}>
1.2.4.3.object|<- [{1.1_instruction_block.md}, {1.2_initial_context_registerd.json}]<:{1}>
1.3.object|<- {Phase 2: Deconstruction into NormCode Plan}
1.3.1.assigning|<= $.([{2.1_deconstruction_draft.ncd}, {2.2_deconstruction_draft.ncn}])
1.3.2.object_%{file_location}:2.1_deconstruction_draft.ncd|<- {2.1_deconstruction_draft.ncd}
1.3.2.1.imperative_::{%(composition)}|<= ({prompt}<$({deconstruction prompt})%>: {1}<$({1.1_instruction_block.md})%>; {output}<$({output file location of deconstruction})%>)
1.3.2.2.object_%{prompt_location}:prompts/2.1_deconstruction.md|<- {deconstruction prompt}<:{prompt}>
1.3.2.3.object|<- {1.1_instruction_block.md}<:{1}>
1.3.2.4.object_%{location_string}:2.1_deconstruction_draft.ncd|<- {output file location of deconstruction}<:{output}>
1.3.3.object_%{file_location}:2.2_deconstruction_draft.ncn|<- {2.2_deconstruction_draft.ncn}
1.3.3.1.imperative_::{%(composition)}|<= ({prompt}<$({natural language translation prompt})%>: {1}<$({2.1_deconstruction_draft.ncd})%>; {output}<$({output file location of ncn})%>)
1.3.3.2.object_%{prompt_location}:prompts/2.2_natural_language_translation.md|<- {natural language translation prompt}<:{prompt}>
1.3.3.3.object|<- {2.1_deconstruction_draft.ncd}<:{1}>
1.3.3.4.object_%{location_string}:2.2_deconstruction_draft.ncn|<- {output file location of ncn}<:{output}>
1.3.4.object|<- [{2.1_deconstruction_draft.ncd}, {2.2_deconstruction_draft.ncn}]
1.3.4.1.imperative|<= :>:{%(with-canvas)}({prompt}<$({manual review prompt})%>: {1})
1.3.4.2.object_%{prompt_location}:2.3_manual_review.md|<- {manual review prompt}<:{prompt}>
1.3.4.3.object|<- [{2.1_deconstruction_draft.ncd}, {2.2_deconstruction_draft.ncn}]<:{1}>
1.4.object|<- {Phase 3: Plan Formalization and Redirection}
1.4.1.assigning|<= $.([{3.1_serialized.ncd}, {3.2_redirected.ncd}, {3.3_formalized.nc}, {3.4_natural_translation.ncn}])
1.4.2.object_%{file_location}:3.1_serialized.ncd|<- {3.1_serialized.ncd}
1.4.2.1.imperative_::{%(composition)}|<= ({prompt}<$({serialization prompt})%>: {1}<$({2.1_deconstruction_draft.ncd})%>; {output}<$({output file location of serialization})%>)
1.4.2.2.object_%{prompt_location}:prompts/3.1_serialization.md|<- {serialization prompt}<:{prompt}>
1.4.2.3.object|<- {2.1_deconstruction_draft.ncd}<:{1}>
1.4.2.4.object_%{location_string}:3.1_serialized.ncd|<- {output file location of serialization}<:{output}>
1.4.3.object_%{file_location}:3.2_redirected.ncd|<- {3.2_redirected.ncd}
1.4.3.1.imperative_::{%(composition)}|<= ({prompt}<$({redirection prompt})%>: {1}<$({3.1_serialized.ncd})%>; {output}<$({output file location of redirection})%>)
1.4.3.2.object_%{prompt_location}:prompts/3.2_redirection.md|<- {redirection prompt}<:{prompt}>
1.4.3.3.object|<- {3.1_serialized.ncd}<:{1}>
1.4.3.4.object_%{location_string}:3.2_redirected.ncd|<- {output file location of redirection}<:{output}>
1.4.4.object_%{file_location}:3.3_formalized.nc|<- {3.3_formalized.nc}
1.4.4.1.imperative_::{%(composition)}|<= ({prompt}<$({formalization prompt})%>: {1}<$({3.2_redirected.ncd})%>; {output}<$({output file location of formalization})%>)
1.4.4.2.object_%{prompt_location}:prompts/3.3_formalization.md|<- {formalization prompt}<:{prompt}>
1.4.4.3.object|<- {3.2_redirected.ncd}<:{1}>
1.4.4.4.object_%{location_string}:3.3_formalized.nc|<- {output file location of formalization}<:{output}>
1.4.5.object_%{file_location}:3.4_natural_translation.ncn|<- {3.4_natural_translation.ncn}
1.4.5.1.imperative_::{%(composition)}|<= ({prompt}<$({natural language translation prompt})%>: {1}<$({3.2_redirected.ncd})%>; {output}<$({output file location of ncn 2})%>)
1.4.5.2.object_%{prompt_location}:prompts/3.4_natural_language_translation.md|<- {natural language translation prompt}<:{prompt}>
1.4.5.3.object|<- {3.2_redirected.ncd}<:{1}>
1.4.5.4.object_%{location_string}:3.4_natural_translation.ncn|<- {output file location of ncn 2}<:{output}>
1.4.6.object|<- [{3.3_formalized.nc}, {3.2_redirected.ncd}, {3.1_serialized.ncd}, {3.4_natural_translation.ncn}]
1.4.6.1.imperative|<= :>:{%(with-canvas)}({prompt}<$({manual review prompt})%>: {1})
1.4.6.2.object_%{prompt_location}:3.5_manual_review.md|<- {manual review prompt}<:{prompt}>
1.4.6.3.object|<- [{3.3_formalized.nc}, {3.2_redirected.ncd}, {3.1_serialized.ncd}, {3.4_natural_translation.ncn}]<:{1}>
1.5.object|<- {Phase 4: Contextualization and Prompt Assembly}
1.5.1.assigning|<= $.([{4.1_context_manifest.json}, {context_store/__flow_index__--*.md}, {context_store/shared--*.md}, {prompts/[__flow_index__]*.md}])
1.5.2.object_%{file_location}:4.1_context_manifest.json, context_store/__flow_index__--*.md, context_store/shared--*.md|<- [{4.1_context_manifest.json}, {context_store/__flow_index__--*.md}, {context_store/shared--*.md}]
1.5.2.1.imperative_::{%(composition)}|<= ({prompt}<$({context distribution prompt})%>: {1}; {output}<$({output file locations of context distribution})%>)
1.5.2.2.object_%{prompt_location}:prompts/4.1_context_distribution.md|<- {context distribution prompt}<:{prompt}>
1.5.2.3.object|<- [{3.3_formalized.nc}, {1.2_initial_context_registerd.json}, {context_store/raw--*.md}]<:{1}>
1.5.2.4.object_%{location_string}:4.1_context_manifest.json, context_store/__flow_index__--*.md, context_store/shared--*.md|<- {output file locations of context distribution}<:{output}>
1.5.3.object_%{file_location}:prompts/[__flow_index__]*.md|<- {prompts/[__flow_index__]*.md}
1.5.3.1.imperative_::{%(composition)}|<= ({prompt}<$({prompt generation prompt})%>: {1}<$({4.1_context_manifest.json})%>; {output}<$({output file location of prompts})%>)
1.5.3.2.object_%{prompt_location}:prompts/4.2_prompt_generation.md|<- {prompt generation prompt}<:{prompt}>
1.5.3.3.object|<- {4.1_context_manifest.json}<:{1}>
1.5.3.4.object_%{location_string}:prompts/[__flow_index__]*.md|<- {output file location of prompts}<:{output}>
1.5.4.object|<- [{4.1_context_manifest.json}, {context_store/__flow_index__--*.md}, {context_store/shared--*.md}, {prompts/[__flow_index__]*.md}]
1.5.4.1.imperative|<= :>:{%(with-canvas)}({prompt}<$({manual review prompt})%>: {1})
1.5.4.2.object_%{prompt_location}:4.3_manual_review.md|<- {manual review prompt}<:{prompt}>
1.5.4.3.object|<- [{4.1_context_manifest.json}, {context_store/__flow_index__--*.md}, {context_store/shared--*.md}, {prompts/[__flow_index__]*.md}]<:{1}>
1.6.object|<- {Phase 5: Materialization into an Executable Script}
1.6.1.assigning|<= $.([{concept_repo.json}, {inference_repo.json}, {5.1_executable_script.py}])
1.6.2.object_%{file_location}:concept_repo.json, inference_repo.json, 5.1_executable_script.py|<- [{concept_repo.json}, {inference_repo.json}, {5.1_executable_script.py}]
1.6.2.1.imperative_::{%(composition)}|<= ({prompt}<$({script generation prompt})%>: {1}; {output}<$({output file locations of script gen})%>)
1.6.2.2.object_%{prompt_location}:prompts/5.1_script_generation.md|<- {script generation prompt}<:{prompt}>
1.6.2.3.object|<- [{3.3_formalized.nc}, {4.1_context_manifest.json}, {context_store/__flow_index__--*.md}, {context_store/shared--*.md}]<:{1}>
1.6.2.4.object_%{location_string}:concept_repo.json, inference_repo.json, 5.1_executable_script.py|<- {output file locations of script gen}<:{output}>
1.6.3.object|<- [{concept_repo.json}, {inference_repo.json}, {5.1_executable_script.py}]
1.6.3.1.imperative|<= :>:{%(with-canvas)}({prompt}<$({manual review prompt})%>: {1})
1.6.3.2.object_%{prompt_location}:5.2_manual_review.md|<- {manual review prompt}<:{prompt}>
1.6.3.3.object|<- [{concept_repo.json}, {inference_repo.json}, {5.1_executable_script.py}]<:{1}>
