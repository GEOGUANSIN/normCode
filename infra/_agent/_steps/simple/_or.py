from typing import List, Optional
from infra._states._simple_states import States
from infra._core._reference import Reference, cross_product


def output_reference(states: States) -> States:
    """Set OR reference. For demo: cross product of function and value references if present, else first available."""
    refs: List[Reference] = []
    if states.function and isinstance(states.function[0].reference, Reference):
        refs.append(states.function[0].reference)
    for v in states.values:
        ref = v.reference
        if isinstance(ref, Reference):
            refs.append(ref)

    final_ref: Optional[Reference] = None
    if len(refs) == 1:
        final_ref = refs[0]
    elif len(refs) > 1:
        final_ref = cross_product(refs)

    states.set_or_reference(final_ref)
    states.set_current_step("OR")
    return states 