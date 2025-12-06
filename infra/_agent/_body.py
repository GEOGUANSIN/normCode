from typing import Any, Dict, Callable
from infra._agent._models import (
    PromptTool,
    FileSystemTool,
    PythonInterpreterTool,
    FormatterTool,
    CompositionTool,
    UserInputTool,
)


class Body:
    def __init__(self, llm_name: str = "qwen-turbo-latest", base_dir: str | None = None, new_user_input_tool: bool = True, paradigm_tool: Any = None) -> None:
        self.base_dir = base_dir
        self.prompt_tool = PromptTool(base_dir=base_dir)
        # Backwards-compatible alias
        self.prompt = PromptTool(base_dir=base_dir)
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
                from typing import Dict as _Dict, Any as _Any

                def input_fn(vars: _Dict[str, _Any] | None = None) -> str:
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

        self.user_input = UserInputTool() if new_user_input_tool else _UserInputTool()
        self.file_system = FileSystemTool(base_dir=base_dir)
        self.python_interpreter = PythonInterpreterTool()
        # Attach a back-reference so the interpreter can inject Body into scripts when appropriate
        setattr(self.python_interpreter, "body", self)

        self.formatter_tool = FormatterTool()
        self.composition_tool = CompositionTool()

        # Set up paradigm tool - default to Paradigm class if not provided
        if paradigm_tool is None:
            from infra._agent._models._paradigms import Paradigm
            # Create a wrapper that provides a load method
            class _DefaultParadigmTool:
                def load(self, paradigm_name: str):
                    return Paradigm.load(paradigm_name)
            self.paradigm_tool = _DefaultParadigmTool()
        else:
            self.paradigm_tool = paradigm_tool

        # Pass the body's tool instances to the llm to ensure they share the same context (e.g., base_dir)
        if hasattr(self.llm, "file_tool"):
            self.llm.file_tool = self.file_system
        if hasattr(self.llm, "python_interpreter"):
            self.llm.python_interpreter = self.python_interpreter