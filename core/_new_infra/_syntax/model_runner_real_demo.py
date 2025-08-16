from __future__ import annotations
from typing import Any, Dict

# Import spec dataclasses and runner with fallback for direct script execution
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
    from ._model_runner import ModelEnv, ModelSequenceRunner
    from ._prompt import PromptTool
    from ._language_models import LanguageModel
except Exception:
    import sys, pathlib
    here = pathlib.Path(__file__).parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    parent = here.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))
    from model_state import (  # type: ignore
        AffordanceSpecLite,
        ToolSpecLite,
        ModelEnvSpecLite,
        ModelStepSpecLite,
        ModelSequenceSpecLite,
        MetaValue,
        AffordanceValue,
    )
    from _model_runner import ModelEnv, ModelSequenceRunner  # type: ignore
    from _prompt import PromptTool  # type: ignore
    from _language_models import LanguageModel  # type: ignore


# ---- Real tools and states ----------------------------------------------------
class BufferTool:
    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}

    def write(self, record_name: str, new_record: Any) -> Any:
        self._store[record_name] = new_record
        return new_record

    def read(self, record_name: str) -> Any:
        return self._store.get(record_name)


class FnTool:
    def invoke(self, fn, vars: Dict[str, Any] | None = None) -> Any:
        return fn(vars or {})


class RealStates:
    class Function:
        class Concept:
            def __init__(self) -> None:
                self.name = "ConceptX"
        def __init__(self) -> None:
            self.concept = RealStates.Function.Concept()
            self.buffer_record_name = "rec1"
            # Provide inputs for templates
            self.input_normcode = "::({1}<$(${number})%_> multiply {2}<$(${number})%_>)"
            self.input_1 = "5"
            self.input_2 = "2"

    class Body:
        def __init__(self) -> None:
            self.prompt = PromptTool()
            self.llm = LanguageModel("qwen-turbo-latest")
            self.buffer = BufferTool()
            self.fn = FnTool()

    def __init__(self) -> None:
        self.body = RealStates.Body()
        self.function = RealStates.Function()


# ---- Build env spec and sequence --------------------------------------------

env_spec = ModelEnvSpecLite(
    model=ToolSpecLite(
        tool_name="llm",
        affordances=[
            AffordanceSpecLite(
                affordance_name="generate",
                call_code="result = tool.generate(params['prompt'], system_message=params.get('system_message', ''))",
            ),
            AffordanceSpecLite(
                affordance_name="create_generation_function",
                call_code="result = tool.create_generation_function(params['prompt_template'])",
            ),
            AffordanceSpecLite(
                affordance_name="expand_generation_function",
                call_code="result = tool.expand_generation_function(params['base_generation_function'], params['expansion_function'], params.get('expansion_params', {}))",
            ),
        ]
    ),
    prompt=ToolSpecLite(
        tool_name="prompt",
        affordances=[
            AffordanceSpecLite(
                affordance_name="read",
                call_code="result = tool.read(params['template_name'])",
            ),
            AffordanceSpecLite(
                affordance_name="render",
                call_code="result = tool.render(params['template_name'], params.get('variables', {}))",
            ),
            AffordanceSpecLite(
                affordance_name="substitute",
                call_code="result = tool.substitute(params['template_name'], params.get('variables', {}))",
            ),
        ]
    ),
    tools=[
        ToolSpecLite(
            tool_name="fn",
            affordances=[
                AffordanceSpecLite(
                    affordance_name="invoke",
                    call_code="result = tool.invoke(params['fn'], params.get('vars', {}))",
                ),
            ]
        ),
        ToolSpecLite(
            tool_name="buffer",
            affordances=[
                AffordanceSpecLite(
                    affordance_name="write",
                    call_code="result = tool.write(params['record_name'], params['new_record'])",
                ),
                AffordanceSpecLite(
                    affordance_name="read",
                    call_code="result = tool.read(params['record_name'])",
                ),
            ]
        ),
    ]
)

sequence_spec = ModelSequenceSpecLite(
    env=env_spec,
    steps=[
        # 1) Read and render imperative_translate with input_normcode
        ModelStepSpecLite(
            step_index=1,
            affordance="prompt.read",
            params={"template_name": "imperative_translate"},
            result_key="imperative_template",
        ),
        ModelStepSpecLite(
            step_index=2,
            affordance="prompt.render",
            params={
                "template_name": "imperative_translate",
                "variables": {"input_normcode": MetaValue("states.function.input_normcode")},
            },
            result_key="imperative_prompt",
        ),
        # 2) Generate raw natural-language template from LLM
        ModelStepSpecLite(
            step_index=3,
            affordance="llm.generate",
            params={"prompt": MetaValue("imperative_prompt"), "system_message": ""},
            result_key="nl_normcode_raw",
        ),
        # 3) Turn raw template into a generation function and invoke with inputs
        ModelStepSpecLite(
            step_index=4,
            affordance="llm.create_generation_function",
            params={"prompt_template": MetaValue("nl_normcode_raw")},
            result_key="nl_normcode_fn",
        ),
        ModelStepSpecLite(
            step_index=5,
            affordance="fn.invoke",
            params={
                "fn": MetaValue("nl_normcode_fn"),
                "vars": {"input_1": MetaValue("states.function.input_1"), "input_2": MetaValue("states.function.input_2")},
            },
            result_key="nl_normcode",
        ),
        # 4) Read and render instruction with the filled NL normcode
        ModelStepSpecLite(
            step_index=6,
            affordance="prompt.read",
            params={"template_name": "instruction"},
            result_key="instruction_template",
        ),
        ModelStepSpecLite(
            step_index=7,
            affordance="prompt.render",
            params={
                "template_name": "instruction",
                "variables": {"input": MetaValue("nl_normcode")},
            },
            result_key="instruction_prompt",
        ),
        # 5) Final LLM generation
        ModelStepSpecLite(
            step_index=8,
            affordance="llm.generate",
            params={"prompt": MetaValue("instruction_prompt"), "system_message": ""},
            result_key="final_answer",
        ),
    ]
)


def run_demo() -> None:
    states = RealStates()
    runner = ModelSequenceRunner(states, sequence_spec)
    meta = runner.run()

    def _preview(value: Any, max_len: int = 400) -> str:
        if callable(value):
            return f"<callable {value.__name__ if hasattr(value, '__name__') else 'fn'}>"
        text = str(value).replace("\r\n", "\n").replace("\r", "\n")
        if len(text) > max_len:
            return text[:max_len] + "... [truncated]"
        return text

    print("=== Sequence Execution ===")
    for step in sorted(sequence_spec.steps, key=lambda s: s.step_index):
        label = f"Step {step.step_index}: {step.affordance}"
        print(label)
        if step.result_key:
            val = meta.get(step.result_key)
            print(f"  -> {step.result_key}: {_preview(val)}")
        else:
            print("  -> (no result_key)")

    print("\n=== Final Output ===")
    print(_preview(meta.get("final_answer")))


if __name__ == "__main__":
    run_demo() 
