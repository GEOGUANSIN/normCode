import logging
from infra._core._inference import Inference
from infra._states._grouping_states import States
from infra._states._common_states import ConceptInfoLite, ReferenceRecordLite
from infra._agent._steps._filter_utils import apply_injected_filters


def input_references(inference: Inference, states: States) -> States:
    """Populate references and concept info into the state from the inference instance."""

    apply_injected_filters(inference, states)
    if inference.function_concept:
        states.function.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(
                    id=inference.function_concept.id,
                    name=inference.function_concept.name,
                    type=inference.function_concept.type,
                    context=inference.function_concept.context,
                    axis_name=inference.function_concept.axis_name,
                    natural_name=inference.function_concept.natural_name,
                ),
                reference=inference.function_concept.reference.copy()
                if inference.function_concept.reference
                else None,
            )
        )

    for vc in inference.value_concepts or []:
        states.values.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(
                    id=vc.id, name=vc.name, type=vc.type, context=vc.context, axis_name=vc.axis_name, natural_name=vc.natural_name,
                ),
                reference=vc.reference.copy() if vc.reference else None,
            )
        )

    for cc in inference.context_concepts or []:
        states.context.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(
                    id=cc.id, name=cc.name, type=cc.type, context=cc.context, axis_name=cc.axis_name, natural_name=cc.natural_name,
                ),
                reference=cc.reference.copy() if cc.reference else None,
            )
        )

    states.set_current_step("IR")
    logging.debug(f"IR completed. Loaded {len(states.values)} value and {len(states.context)} context concepts.")
    return states 