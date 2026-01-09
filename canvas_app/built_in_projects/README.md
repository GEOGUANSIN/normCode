# Built-in Projects

This directory contains built-in NormCode projects that serve as chat controllers in Canvas App.

## Structure

Each subdirectory is a complete NormCode project that can be loaded as a chat controller:

```
built_in_projects/
├── canvas_assistant/     # Chat-driven assistant for canvas operations
├── [future_project]/     # Additional built-in projects
└── README.md             # This file
```

## Adding a Built-in Controller

To add a new built-in chat controller:

1. Create a new directory: `built_in_projects/my_controller/`
2. Add a project config file: `my_controller.normcode-canvas.json`
3. Include repositories: `repos/concepts.json`, `repos/inferences.json`
4. Add any paradigms needed in `provisions/paradigms/`

The controller will be automatically discovered and appear in the chat controller selector.

## Requirements for Chat Controllers

A project can serve as a chat controller if it:

1. Has a `*.normcode-canvas.json` config file
2. Uses chat paradigms (`c_ChatRead`, `h_Response-c_ChatWrite`, etc.)
3. Is designed for conversational interaction

## Available Controllers

| Controller | Description |
|-----------|-------------|
| `canvas_assistant` | Chat-driven assistant for NormCode Canvas |
| `placeholder` | Demo responses (virtual, always available) |

## Development

These projects can be opened in Canvas App for viewing and modification.
Use the "View Controller Project" button in the chat panel to see the plan graph.

