from typing import Any, Dict, Callable
from infra._agent._models import PromptTool, FileSystemTool, PythonInterpreterTool

class Body:
	def __init__(self, llm_name="qwen-turbo-latest") -> None:
		self.prompt = PromptTool()
		try:
			from infra._agent._models import LanguageModel as _LM
			self.llm = _LM(llm_name)
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
		
		# User input tool for imperative_input sequence
		class _UserInputTool:
			def create_input_function(self, prompt_key: str = "prompt_text") -> Callable:
				"""
				Creates a function that prompts the user for input.
				The function expects a dict with 'prompt_text' and optional context keys.
				"""
				from typing import Dict, Any
				def input_fn(vars: Dict[str, Any] | None = None) -> str:
					vars = vars or {}
					prompt_text = vars.get(prompt_key, "Enter input: ")
					context = {k: v for k, v in vars.items() if k.startswith("context_")}
					
					# Build the full prompt message
					if context:
						context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
						full_prompt = f"{prompt_text}\n{context_str}\n> "
					else:
						full_prompt = f"{prompt_text}\n> "
					
					# Prompt the user and return their response
					return input(full_prompt)
				return input_fn
		
		self.user_input = _UserInputTool()
		self.file_system = FileSystemTool()
		self.python_interpreter = PythonInterpreterTool()