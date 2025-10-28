from multiagent_experiment._models._language_models import LanguageModel

# Initialize the LanguageModel once to be shared across tool modules.
# This assumes a model named 'qwen-turbo-latest' is configured in your project's settings.yaml,
# or the LanguageModel class will fall back to a mock mode.
llm = LanguageModel("qwen-turbo-latest")
