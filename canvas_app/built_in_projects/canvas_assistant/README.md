# Canvas Assistant

This directory contains the Canvas Assistant - a built-in NormCode plan that drives the chat interface.

## Overview

The Canvas Assistant is a NormCode plan that:
1. Reads user input via **ChatTool** 
2. Processes commands and queries using **LLM**
3. Responds via **ChatTool**
4. Can execute canvas commands via **CanvasDisplayTool**

## Files

```
canvas_assistant/
├── canvas_assistant.normcode-canvas.json  # Project config
├── repos/
│   ├── chat.concept.json                  # Compiled concepts
│   └── chat.inference.json                # Compiled inferences
├── provisions/
│   ├── paradigms/                         # Chat & canvas paradigms
│   │   ├── c_ChatRead-o_Literal.json
│   │   ├── h_Response-c_ChatWrite-o_Status.json
│   │   └── ...
│   ├── prompts/                           # LLM prompts
│   │   ├── classify_command.md
│   │   ├── generate_response.md
│   │   └── judge_terminate.md
│   └── schemas/
│       └── canvas_commands.json
└── compiler.agent.json                    # Agent configuration
```

## Usage

The Canvas Assistant is automatically available in the chat controller selector.
Select it to have an intelligent assistant that can:

- **Explain** NormCode concepts and canvas features
- **Help** with plan creation and debugging
- **Execute** canvas commands on your behalf
- **Guide** you through the NormCode workflow

## Built-in Controllers

This is one of the built-in controllers located in `canvas_app/built_in_projects/`.
All projects in this directory are automatically discovered and available as chat controllers.

## Development

To modify the assistant:
1. Open this project in Canvas App (it appears in controller selector)
2. View and modify the plan's graph
3. Test changes interactively via chat
