import os

def check_prompt_file():
    file_path = r'c:\Users\ProgU\PycharmProjects\normCode\infra\_agent\_models\prompts\prompts\multiply_prompt.txt'
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            prompt = f.read()
        return prompt
    else:
        raise FileNotFoundError(f"Prompt file not found at {file_path}")

# Example usage:
try:
    prompt = check_prompt_file()
    print("Prompt loaded successfully:", prompt)
except FileNotFoundError as e:
    print(e)