from __future__ import annotations
from typing import Any, Dict, Optional, Tuple, Callable

# Import spec dataclasses with fallback for direct usage from this folder
try:
	from .model_state import (
		AffordanceSpecLite,
		ToolSpecLite,
		ModelEnvSpecLite,
		ModelStepSpecLite,
		ModelSequenceSpecLite,
		MetaValue,
		AffordanceValue,
	)
except Exception:
	import sys, pathlib
	here = pathlib.Path(__file__).parent
	sys.path.insert(0, str(here))
	from model_state import (  # type: ignore
		AffordanceSpecLite,
		ToolSpecLite,
		ModelEnvSpecLite,
		ModelStepSpecLite,
		ModelSequenceSpecLite,
		MetaValue,
		AffordanceValue,
	)


class ModelEnv:
	"""Runtime environment materialized from a spec-like object.

	- Binds tool affordances (e.g., "prompt.substitute") to executable callables.
	- Provides `execute(qualified_affordance, params)` to invoke affordances.
	- Provides `get_affordance(qualified_affordance)` to obtain a callable handle,
	  which can be passed as a parameter to other affordances (e.g., expansion hooks).
	
	Expected `spec` shape at minimum (via ModelEnvSpecLite):
	  model?: ToolSpecLite(tool_name, affordances)
	  prompt?: ToolSpecLite
	  tools:  list[ToolSpecLite]
	
	The `call_code` for each affordance executes in a local namespace containing:
	  - states: the provided states object
	  - tool: the resolved tool provider (e.g., states.body.prompt)
	  - params: the merged parameter dict for this invocation
	  - result: a default variable to collect output if not otherwise specified
	The returned value is taken from affordance `output` (defaults to "result").
	"""

	def __init__(self, states: Any, spec: ModelEnvSpecLite):
		self._states = states
		self._spec = spec
		self._registry: Dict[str, Tuple[str, str, Dict[str, Any], str]] = {}
		self._build_registry()

	def execute(self, qualified_affordance: str, params: Optional[Dict[str, Any]] = None) -> Any:
		"""Execute an affordance by its qualified name, e.g. "prompt.substitute"."""
		handle = self.get_affordance(qualified_affordance)
		return handle(params or {})

	def get_affordance(self, qualified_affordance: str) -> Callable[[Dict[str, Any]], Any]:
		"""Return a callable that executes the bound affordance."""
		try:
			tool_name, call_code, static_params, output_var = self._resolve(qualified_affordance)
		except KeyError as exc:
			raise KeyError(f"Affordance not found: {qualified_affordance}") from exc

		def _runner(runtime_params: Dict[str, Any]) -> Any:
			merged_params = {**static_params, **(runtime_params or {})}
			local_vars: Dict[str, Any] = {
				"states": self._states,
				"tool": self._get_tool_provider(tool_name),
				"params": merged_params,
				"result": None,
			}
			exec(call_code, {}, local_vars)
			return local_vars.get(output_var, local_vars.get("result"))

		return _runner

	def list_affordances(self) -> Dict[str, Dict[str, Any]]:
		out: Dict[str, Dict[str, Any]] = {}
		for key, (tool_name, _, static_params, output_var) in self._registry.items():
			out[key] = {
				"tool": tool_name,
				"static_params": static_params,
				"output": output_var,
			}
		return out

	def _build_registry(self) -> None:
		tools: Dict[str, Any] = {}
		model_spec = getattr(self._spec, "model", None)
		if model_spec is not None:
			tools[model_spec.tool_name] = model_spec
		prompt_spec = getattr(self._spec, "prompt", None)
		if prompt_spec is not None:
			tools[prompt_spec.tool_name] = prompt_spec
		for tool_spec in (getattr(self._spec, "tools", []) or []):
			if tool_spec is not None:
				tools[tool_spec.tool_name] = tool_spec

		for tool_name, tool_spec in tools.items():
			for aff in getattr(tool_spec, "affordances", []) or []:
				qualified = f"{tool_name}.{aff.affordance_name}"
				output_var = getattr(aff, "output", None) or "result"
				static_params = dict(getattr(aff, "params", None) or {})
				call_code = getattr(aff, "call_code")
				self._registry[qualified] = (tool_name, call_code, static_params, output_var)

	def _resolve(self, qualified_affordance: str) -> Tuple[str, str, Dict[str, Any], str]:
		tool_name, call_code, static_params, output_var = self._registry[qualified_affordance]
		return tool_name, call_code, static_params, output_var

	def _get_tool_provider(self, tool_name: str) -> Any:
		body = getattr(self._states, "body", None)
		if body is not None and hasattr(body, tool_name):
			return getattr(body, tool_name)
		if hasattr(self._states, tool_name):
			return getattr(self._states, tool_name)
		raise AttributeError(f"Tool provider not found for '{tool_name}'. Expected at states.body.{tool_name} or states.{tool_name}.")


class ModelSequenceRunner:
	"""Executes a ModelSequenceSpecLite using a ModelEnv, with a simple meta store.

	- Resolves MetaValue to meta keys or states dotted paths
	- Resolves AffordanceValue to a callable affordance handle
	- Merges params and executes in step order, storing results by result_key
	"""

	def __init__(self, states: Any, sequence_spec: ModelSequenceSpecLite) -> None:
		self.states = states
		self.sequence_spec = sequence_spec
		self.env = ModelEnv(states, sequence_spec.env)
		self.meta: Dict[str, Any] = {}

	def _resolve_value(self, value: Any) -> Any:
		if isinstance(value, MetaValue):
			key = value.key
			if key.startswith("states."):
				path = key.split(".")[1:]
				obj: Any = self.states
				for part in path:
					obj = getattr(obj, part)
				return obj
			return self.meta.get(key)
		if isinstance(value, AffordanceValue):
			return self.env.get_affordance(value.qualified_affordance)
		if isinstance(value, dict):
			return {k: self._resolve_value(v) for k, v in value.items()}
		if isinstance(value, list):
			return [self._resolve_value(v) for v in value]
		return value

	def _resolve_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
		return self._resolve_value(params)

	def run(self) -> Dict[str, Any]:
		for step in sorted(self.sequence_spec.steps, key=lambda s: s.step_index):
			resolved_params = self._resolve_params(step.params)
			result = self.env.execute(step.affordance, resolved_params)
			if step.result_key:
				self.meta[step.result_key] = result
		return self.meta


__all__ = ["ModelEnv", "ModelSequenceRunner"] 