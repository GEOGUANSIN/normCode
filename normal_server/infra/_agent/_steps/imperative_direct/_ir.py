import logging
from infra._core._inference import Inference
from infra._core._concept import Concept
from infra._states._imperative_states import States
from infra._states._common_states import ConceptInfoLite, ReferenceRecordLite
from infra._core._reference import Reference
from infra._agent._steps._filter_utils import apply_injected_filters


def input_references(inference: Inference, states: States) -> States:
    """Populate references and concept info into the state from the inference instance."""
    # Simplified from simple_sequence_runner, as we just need the raw concepts for now.
    # The working_interpretation will drive which concepts are used where.
    apply_injected_filters(inference, states)
    if inference.function_concept:
        states.function[0].concept = ConceptInfoLite(
            id=inference.function_concept.id,
            name=inference.function_concept.name,
            type=inference.function_concept.type,
            context=inference.function_concept.context,
            axis_name=inference.function_concept.axis_name,
            natural_name=inference.function_concept.natural_name,
        )
        states.function[0].reference = inference.function_concept.reference.copy()

    # Store the concept_to_infer in the 'inference' record for the IR step.
    if inference.concept_to_infer:
        ir_inference_record = next((r for r in states.inference if r.step_name == "IR"), None)
        if ir_inference_record:
            ir_inference_record.concept = ConceptInfoLite(
                id=inference.concept_to_infer.id,
                name=inference.concept_to_infer.name,
                type=inference.concept_to_infer.type,
                context=inference.concept_to_infer.context,
                axis_name=inference.concept_to_infer.axis_name,
                natural_name=inference.concept_to_infer.natural_name,
            )

    for vc in inference.value_concepts or []:
        states.values.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(
                    id=vc.id, name=vc.name, type=vc.type, context=vc.context, axis_name=vc.axis_name, natural_name=vc.natural_name,
                ),
                reference=vc.reference.copy(),
            )
        )

    states.set_current_step("IR")
    logging.debug(f"IR completed. Function state: {states.function}")
    logging.debug(f"IR completed. Values state: {states.values}")
    return states 