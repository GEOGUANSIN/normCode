from __future__ import annotations
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field, model_validator
from typing import Literal
from pydantic import ConfigDict

# Backward-compatible imports from split modules
from .quantifier_spec import QuantifierSpec
from .grouper_spec import GrouperSpec
from .memory_spec import MemorySpec
from .model_step_spec import ModelStepSpec
from .model_env_spec import ModelEnvSpec
from .model_sequence_spec import ModelSequenceSpec

__all__ = [
	"QuantifierSpec",
	"GrouperSpec",
	"MemorySpec",
	# New exports
	"ModelStepSpec",
	"ModelEnvSpec",
	"ModelSequenceSpec",
]

# Resolve forward references for Pydantic v2
try:
	from .tools import ToolSpec as _ToolSpec  # noqa: F401
	ModelEnvSpec.model_rebuild()
except Exception:
	pass 