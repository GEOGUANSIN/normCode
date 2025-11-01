import yaml
import os
import logging
from openai import OpenAI
from string import Template
try:
	from infra._constants import CURRENT_DIR, PROJECT_ROOT 
except Exception:
	import sys, pathlib
	here = pathlib.Path(__file__).parent
	parent = here.parent
	if str(parent) not in sys.path:
		sys.path.insert(0, str(parent))
	from infra._constants import CURRENT_DIR, PROJECT_ROOT

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
        self.mock_mode = False

        # Load settings (fallback to mock mode if unavailable)
        self.settings = {}
        try:
            with open(settings_path, 'r') as f:
                self.settings = yaml.safe_load(f) or {}
        except FileNotFoundError:
            self.mock_mode = True
        except Exception:
            self.mock_mode = True

        # Validate model exists in settings
        if not self.mock_mode and model_name not in self.settings:
            self.mock_mode = True

        self.api_key = None
        self.base_url = self.settings.get('BASE_URL', "https://dashscope.aliyuncs.com/compatible-mode/v1") if self.settings else None

        if not self.mock_mode:
            self.api_key = self.settings[model_name].get('DASHSCOPE_API_KEY')
            if not self.api_key:
                self.mock_mode = True

        # Initialize OpenAI client (or stay in mock mode)
        if not self.mock_mode:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None

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
        if self.mock_mode:
            return f"GENERATED[{prompt}]"
        client = self.client
        assert client is not None, "OpenAI client must be initialized when not in mock mode"
        response = client.chat.completions.create(
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
        if self.mock_mode:
            return f"GENERATED[{prompt}]"

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
        client = self.client
        assert client is not None, "OpenAI client must be initialized when not in mock mode"
        response = client.chat.completions.create(**request_params)

        return response.choices[0].message.content

    def create_generation_function(self, prompt_template: str):
        """Return a simple generation function that formats the template with vars."""
        logger.debug(f"Creating generation function with template: {prompt_template[:100]}...")
        
        def _generate_with(vars: dict | None = None) -> str:
            vars = vars or {}
            logger.debug(f"Generating with vars: {vars}")
            
            formatted_prompt = Template(prompt_template).safe_substitute(vars)
            logger.debug(f"Formatted prompt: {formatted_prompt[:100]}...")
            
            result = self.generate(formatted_prompt)
            logger.debug(f"Generation completed, result type: {type(result).__name__}, length: {len(result) if result else 0}")
            
            return result
        return _generate_with

    def create_generation_function_with_template_in_vars(self, template_key="prompt_template"):
        """Return a generation function that finds the template within the vars dictionary."""
        logger.debug(f"Creating a generation function that expects template in vars with key: '{template_key}'")

        def _generate_with_template_in_vars(vars: dict | None = None) -> str:
            vars = vars or {}
            logger.debug(f"Generating with template in vars: {vars}")

            if template_key not in vars:
                error_msg = f"ERROR: Template key '{template_key}' not found in provided variables."
                logger.error(error_msg)
                return error_msg

            prompt_template = vars[template_key]
            
            # The rest of the vars are for substitution
            substitution_vars = {k: v for k, v in vars.items() if k != template_key}

            formatted_prompt = Template(str(prompt_template)).safe_substitute(substitution_vars)
            logger.debug(f"Formatted prompt from vars: {formatted_prompt[:100]}...")

            result = self.generate(formatted_prompt)
            logger.debug(f"Generation completed, result type: {type(result).__name__}, length: {len(result) if result else 0}")

            return result
        return _generate_with_template_in_vars

    def create_generation_function_with_template_in_vars_with_thinking(self, template_key="prompt_template"):
        """Return a generation function that finds the template within the vars dictionary and expects a JSON output with thinking."""
        import json
        logger.debug(f"Creating a generation function with thinking that expects template in vars with key: '{template_key}'")

        def _generate_with_template_in_vars_with_thinking(vars: dict | None = None) -> dict:
            vars = vars or {}
            logger.debug(f"Generating with thinking, with template in vars: {vars}")

            if template_key not in vars:
                error_msg = f"ERROR: Template key '{template_key}' not found in provided variables."
                logger.error(error_msg)
                return {"error": error_msg}

            prompt_template = vars[template_key]
            
            # The rest of the vars are for substitution
            substitution_vars = {k: v for k, v in vars.items() if k != template_key}

            formatted_prompt = Template(str(prompt_template)).safe_substitute(substitution_vars)
            logger.debug(f"Formatted prompt from vars for thinking JSON: {formatted_prompt[:100]}...")

            # Use response_format to ensure JSON output
            logger.debug("Calling generate with JSON response format")
            raw_response = self.generate(
                prompt=formatted_prompt,
                response_format={"type": "json_object"}
            )
            logger.debug(f"Raw JSON response received, length: {len(raw_response) if raw_response else 0}")
            
            try:
                # Parse the response as JSON (should be valid due to response_format)
                logger.debug("Parsing JSON response")
                parsed_response = json.loads(raw_response)
                logger.debug(f"JSON parsed successfully, keys: {list(parsed_response.keys()) if isinstance(parsed_response, dict) else 'not a dict'}")
                
                # If the response is a dict with an 'answer' key, extract and return the answer directly.
                if isinstance(parsed_response, dict) and 'answer' in parsed_response:
                    return parsed_response['answer']
                
                return parsed_response
            except json.JSONDecodeError as e:
                # Fallback in case JSON parsing still fails
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Raw response that failed to parse: {raw_response}")
                fallback_result = {
                    "raw_response": raw_response,
                    "error": "Failed to parse JSON response"
                }
                logger.debug(f"Returning fallback result: {fallback_result}")
                return fallback_result

        return _generate_with_template_in_vars_with_thinking

    def create_generation_function_thinking_json(self, prompt_template: str):
        """Return a generation function that formats the template with vars and extracts JSON thinking/output."""
        import json
        
        logger.debug(f"Creating thinking JSON generation function with template: {prompt_template[:100]}...")
        
        def _generate_with_thinking(vars: dict | None = None) -> dict:
            vars = vars or {}
            logger.debug(f"Generating thinking JSON with vars: {vars}")
            
            formatted_prompt = Template(prompt_template).safe_substitute(vars)
            logger.debug(f"Formatted prompt for JSON generation: {formatted_prompt[:10000]}...")
            
            # Use response_format to ensure JSON output
            logger.debug("Calling generate with JSON response format")
            raw_response = self.generate(
                prompt=formatted_prompt,
                response_format={"type": "json_object"}
            )
            logger.debug(f"Raw JSON response received, length: {len(raw_response) if raw_response else 0}")
            
            try:
                # Parse the response as JSON (should be valid due to response_format)
                logger.debug("Parsing JSON response")
                parsed_response = json.loads(raw_response)
                logger.debug(f"JSON parsed successfully, keys: {list(parsed_response.keys()) if isinstance(parsed_response, dict) else 'not a dict'}")
                
                # Extract thinking and output from the JSON
                answer = parsed_response.get("answer", [])
                logger.debug(f"Extracted answer from JSON, type: {type(answer).__name__}, length: {len(answer) if hasattr(answer, '__len__') else 'N/A'}")
                
                return answer
            except json.JSONDecodeError as e:
                # Fallback in case JSON parsing still fails
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Raw response that failed to parse: {raw_response}")
                fallback_result = {
                    "analysis": "",
                    "answer": [],
                    "raw_response": raw_response,
                    "error": "Failed to parse JSON response"
                }
                logger.debug(f"Returning fallback result: {fallback_result}")
                return fallback_result
        
        return _generate_with_thinking

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

    nl_normcode_raw = llm.run_prompt("imperative_translate", input_normcode="::({1}<$(${number})%_> multiply {2}<$(${number})%_>)")
    print(nl_normcode_raw)

    if nl_normcode_raw:
        nl_normcode_template = Template(nl_normcode_raw)
        nl_normcode = str(nl_normcode_template.safe_substitute(input_1="5", input_2="2"))

    instruction_template = llm.load_prompt_template("instruction")
    instruction = instruction_template.safe_substitute(input=nl_normcode)  # type: ignore
    print(instruction)

    result = llm.generate(instruction, system_message="")
    print(result)