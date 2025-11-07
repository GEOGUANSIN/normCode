from __future__ import annotations
from typing import Any, Dict, List
from dataclasses import dataclass, field


# Spec and reference dataclasses centralized here for reuse by demos/runtimes

@dataclass
class AffordanceSpecLite:
	"""Affordance declaration with executable code string.
	- affordance_name: e.g., "substitute", "generate"
	- call_code: Python statements that compute a variable named `result` or a
	  named `output` variable configured below. Executed with locals: states, tool, params, result
	- params: static params merged with runtime params
	- output: name of the variable to read from call_code locals (defaults to "result")
	"""
	affordance_name: str
	call_code: str
	params: Dict[str, Any] = field(default_factory=dict)
	output: str = "result"


@dataclass
class ToolSpecLite:
	"""Tool declaration listing its affordances.
	- tool_name: namespace (e.g., "prompt", "llm", "buffer")
	- affordances: list of affordance specs bound to this tool
	"""
	tool_name: str
	affordances: List[AffordanceSpecLite] = field(default_factory=list)


@dataclass
class ModelEnvSpecLite:
	"""Environment spec holding well-known tools (model/prompt) and additional tools."""
	model: ToolSpecLite | None = None
	prompt: ToolSpecLite | None = None
	tools: List[ToolSpecLite] = field(default_factory=list)


@dataclass
class ModelStepSpecLite:
	"""Single step spec describing an affordance invocation.
	- step_index: ordering key
	- affordance: qualified name, e.g., "prompt.substitute"
	- params: dict with values, may include MetaValue/AffordanceValue placeholders
	- result_key: optional meta key to store the result into
	"""
	step_index: int
	affordance: str
	params: Dict[str, Any] = field(default_factory=dict)
	result_key: str | None = None


@dataclass
class ModelSequenceSpecLite:
	"""Sequence of steps to run in a given environment."""
	env: ModelEnvSpecLite
	steps: List[ModelStepSpecLite] = field(default_factory=list)


@dataclass
class MetaValue:
	"""Reference to a value resolved from meta store or from states via dotted path.
	- key: either a meta key, or a dotted path starting with "states.".
	  When startswith("states."), it's resolved via getattr chain on the states object.
	"""
	key: str


@dataclass
class AffordanceValue:
	"""Reference to an affordance handle to be passed as a callable param."""
	qualified_affordance: str


__all__ = [
	"AffordanceSpecLite",
	"ToolSpecLite",
	"ModelEnvSpecLite",
	"ModelStepSpecLite",
	"ModelSequenceSpecLite",
	"MetaValue",
	"AffordanceValue",
] 