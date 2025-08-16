"""
Backwards-compatible shim for state models.

The actual implementations now live under `core._new_infra._syntax.state_models`.
This module re-exports their public API so existing imports continue to work:

    from ._state_models import ReferenceInterpretationState, AgentSequenceState, ...

"""

# Re-export everything from the split package
from .state_models import *  # noqa: F401,F403 
