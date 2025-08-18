from typing import Any, Dict
from infra._agent._models import PromptTool

class Body:
	def __init__(self) -> None:
		self.prompt = PromptTool()
		try:
			from infra._agent._models import LanguageModel as _LM
			self.llm = _LM("qwen-turbo-latest")
		except Exception:
			class _MockLM:
				def create_generation_function(self, prompt_template: str):
					from string import Template as _T
					def _fn(vars: dict | None = None) -> str:
						return _T(prompt_template).safe_substitute(vars or {})
					return _fn
				def generate(self, prompt: str, system_message: str = "") -> str:
					return f"GENERATED[{prompt}]"
			self.llm = _MockLM()
		
		# Add buffer and fn tools to match model_runner_real_demo.py
		class _BufferTool:
			def __init__(self) -> None:
				self._store: Dict[str, Any] = {}

			def write(self, record_name: str, new_record: Any) -> Any:
				self._store[record_name] = new_record
				return new_record

			def read(self, record_name: str) -> Any:
				return self._store.get(record_name)
		
		class _FnTool:
			def invoke(self, fn, vars: Dict[str, Any] | None = None) -> Any:
				return fn(vars or {})
		
		self.buffer = _BufferTool()
		self.fn = _FnTool()
