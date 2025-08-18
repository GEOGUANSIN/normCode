from infra._core._inference import Inference
from infra._core._concept import Concept
from infra._states._simple_states import States
from infra._states._common_states import ConceptInfoLite, ReferenceRecordLite
from infra._core._reference import Reference


def input_references(inference: Inference, states: States) -> States:
    """Populate references and concept info into the state from the inference instance."""

    # Function concept (should only be one in this simple demo)
    func = inference.function_concept
    if isinstance(func, Concept):
        states.function = [
            ReferenceRecordLite(
                step_name="IR",  # Or from WI if available
                concept=ConceptInfoLite(
                    id=func.id,
                    name=func.name,
                    type=func.type,
                    context=func.context,
                    axis_name=func.axis_name,
                ),
                reference=func.reference if isinstance(func.reference, Reference) else None,
            )
        ]

    # Value concepts
    states.values = []
    for vc in inference.value_concepts or []:
        if isinstance(vc, Concept):
            states.values.append(
                ReferenceRecordLite(
                    step_name="IR",  # Or from WI if available
                    concept=ConceptInfoLite(
                        id=vc.id,
                        name=vc.name,
                        type=vc.type,
                        context=vc.context,
                        axis_name=vc.axis_name,
                    ),
                    reference=vc.reference if isinstance(vc.reference, Reference) else None,
                )
            )

    # Context concepts (if any)
    states.context = []
    for ctx_concept in inference.context_concepts or []:
        if isinstance(ctx_concept, Concept):
            states.context.append(
                ReferenceRecordLite(
                    step_name="IR",  # Or from WI if available
                    concept=ConceptInfoLite(
                        id=ctx_concept.id,
                        name=ctx_concept.name,
                        type=ctx_concept.type,
                        context=ctx_concept.context,
                        axis_name=ctx_concept.axis_name,
                    ),
                    reference=ctx_concept.reference if isinstance(ctx_concept.reference, Reference) else None,
                )
            )

    states.set_current_step("IR")
    return states 