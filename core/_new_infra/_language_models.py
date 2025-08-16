import yaml
import os
from openai import OpenAI
from string import Template
from _constants import CURRENT_DIR, PROJECT_ROOT


class LanguageModel:
    """
    Factory class to create LLM instances based on model name and configuration
    """

    def __init__(self, model_name, settings_path=os.path.join(PROJECT_ROOT, "settings.yaml")):
        """
        Initialize LLM with specified model from settings

        Args:
            model_name (str): Name of the model to use
            settings_path (str): Path to the settings YAML file
        """
        self.model_name = model_name

        # Load settings
        with open(settings_path, 'r') as f:
            self.settings = yaml.safe_load(f)

        # Validate model exists in settings
        if model_name not in self.settings:
            raise ValueError(f"Model '{model_name}' not found in settings")

        # Get API key for the specified model
        self.api_key = self.settings[model_name].get('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError(f"API key not found for model '{model_name}'")

        self.base_url = self.settings.get('BASE_URL', "https://dashscope.aliyuncs.com/compatible-mode/v1")

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def load_prompt_template(self, template_name):
        """
        Load a prompt template using the Template module

        Args:
            template_name (str): Name of the prompt template file (without .txt extension)

        Returns:
            Template: A string.Template object with the loaded template
        """
        prompt_template_path = os.path.join(CURRENT_DIR, "prompts", f"{template_name}.txt")

        if not os.path.exists(prompt_template_path):
            raise FileNotFoundError(f"Template file '{template_name}.txt' not found in prompts directory")

        # Force fresh read with explicit encoding and file handle management
        f = None
        try:
            f = open(prompt_template_path, 'r', encoding='utf-8')
            template_content = f.read()
        finally:
            if f:
                f.close()

        return Template(template_content)

    def run_prompt(self, prompt_template_name, **kwargs):
        """
        Run a prompt through the LLM using a template

        Args:
            prompt_template_name (str): name of the prompt template file
            **kwargs: Variables to substitute in the template

        Returns:
            str: The LLM response
        """
        # Load prompt template using Template module
        template = self.load_prompt_template(prompt_template_name)

        # Substitute variables in template
        prompt = template.safe_substitute(kwargs)

        # Run the prompt through the LLM
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "system", "content": ""},
                      {"role": "user", "content": prompt}],
            temperature=0.0
        )

        return response.choices[0].message.content

    def generate(self, prompt, system_message="You are a helpful assistant.", response_format=None):
        """
        Generate a response from the LLM using a direct prompt

        Args:
            prompt (str): The prompt to send to the LLM
            system_message (str): Optional system message to set context
            response_format (dict): Optional response format specification, can be json_object or json_schema

        Returns:
            str: The LLM response
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]

        # Prepare request parameters
        request_params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.0
        }

        # Add response format if specified
        if response_format:
            request_params["response_format"] = response_format

        # Run the prompt through the LLM
        response = self.client.chat.completions.create(**request_params)

        return response.choices[0].message.content

    def create_generation_function(self, prompt_template: str):
        """Return a function that formats a template with vars and then runs generation."""
        def _generate_with(vars: dict | None = None) -> str:
            vars = vars or {}
            # First, substitute the variables into the template to create the final prompt.
            final_prompt = Template(prompt_template).safe_substitute(vars)
            # Then, run the generation with the final prompt.
            return self.generate(final_prompt, system_message="")
        return _generate_with

    def expand_generation_function(self, base_generation_function, expansion_function, expansion_params: dict | None = None):
        """Return a function that calls base_generation_function, then passes the result
        to an expansion_function (typically an affordance handle) with provided params."""
        expansion_params = dict(expansion_params or {})
        def _expanded(vars: dict | None = None):
            base_out = base_generation_function(vars or {})
            params = {**expansion_params, "new_record": base_out}
            return expansion_function(params)
        return _expanded


if __name__ == "__main__":
    llm = LanguageModel("qwen-turbo-latest")

    print(llm.load_prompt_template("imperative_translate").template)

    nl_normcode_raw = llm.run_prompt("imperative_translate", input_normcode="::({1}<$({number})%_> multiply {2}<$({number})%_>)")
    print(nl_normcode_raw)

    if nl_normcode_raw:
        nl_normcode_template = Template(nl_normcode_raw)
        nl_normcode = str(nl_normcode_template.safe_substitute(input_1="5", input_2="2"))

    instruction_template = llm.load_prompt_template("instruction")
    instruction = instruction_template.safe_substitute(input=nl_normcode)  # type: ignore
    print(instruction)


    result = llm.generate(instruction, system_message="")
    print(result)