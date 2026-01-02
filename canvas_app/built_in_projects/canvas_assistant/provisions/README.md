# Compiler Provisions

This directory contains all the resources needed to execute the self-hosted NormCode compiler (`compiler_pf.ncd`).

## Directory Structure

```
provisions/
├── prompts/                    # LLM prompt templates
│   ├── classify_command.md     # Parse user message → command
│   ├── generate_response.md    # Generate user-facing response
│   └── judge_terminate.md      # Judge if session should end
│
├── schemas/                    # JSON schemas
│   └── canvas_commands.json    # Valid canvas command schema
│
├── paradigms/                  # Execution paradigms
│   ├── c_ChatRead-o_Literal.json
│   ├── c_ChatSessionClose-o_Status.json
│   ├── h_Command-c_CanvasExecute-o_Status.json
│   ├── h_Memo-v_Prompt-c_LLMGenerate-o_Command.json
│   ├── h_Memo-v_Prompt-c_LLMGenerate-o_Truth.json
│   ├── h_Message_Status-v_Prompt-c_LLMGenerate-o_Memo.json
│   └── h_Response-c_ChatWrite-o_Status.json
│
└── README.md                   # This file
```

## Paradigm Reference

| Paradigm | Body Faculty | Purpose |
|----------|--------------|---------|
| `c_ChatRead-o_Literal` | `chat` | Block and wait for user message |
| `c_ChatSessionClose-o_Status` | `chat` | Close the chat session |
| `h_Command-c_CanvasExecute-o_Status` | `canvas` | Execute a parsed canvas command |
| `h_Memo-v_Prompt-c_LLMGenerate-o_Command` | `llm` | Parse message as command using LLM |
| `h_Memo-v_Prompt-c_LLMGenerate-o_Truth` | `llm` | Make boolean judgement using LLM |
| `h_Message_Status-v_Prompt-c_LLMGenerate-o_Memo` | `llm` | Generate response text using LLM |
| `h_Response-c_ChatWrite-o_Status` | `chat` | Send response to user |

## Body Faculties Required

The compiler requires three body faculties to be available:

### `chat` Faculty
Handles interactive I/O with the user:
- `read_message()` - Blocks until user sends a message
- `write_message(message)` - Sends a message to the user
- `close_session()` - Ends the chat session

### `canvas` Faculty
Handles graph canvas operations:
- `execute_command(command_type, command_params)` - Executes node/edge/view operations

### `llm` Faculty
Handles language model inference:
- `generate(prompt)` - Generates text from a prompt

## Prompt Template Variables

### `classify_command.md`
- `{1}` - User message text
- `{2}` - Command schema JSON

### `generate_response.md`
- `{1}` - User message
- `{2}` - Command execution status

### `judge_terminate.md`
- `{1}` - Current user message
- `{2}` - Conversation history

## Usage with compiler_pf.ncd

The `compiler_pf.ncd` file references these provisions via annotations:

```ncd
<= ::(understand the user message as a canvas command)
    | %{norm_input}: h_Memo-v_Prompt-c_LLMGenerate-o_Command
    | %{v_input_provision}: provisions/prompts/classify_command.md
    | %{body_faculty}: llm
```

When activated, the orchestrator:
1. Loads the paradigm from `provisions/paradigms/`
2. Loads the prompt template from `provisions/prompts/`
3. Uses the `llm` body faculty to execute

