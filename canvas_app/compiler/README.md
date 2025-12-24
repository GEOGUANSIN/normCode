# NormCode Self-Hosting Compiler

This directory contains the NormCode compiler implemented as a NormCode plan.

## Overview

The compiler is a NormCode plan that:
1. Reads user input via **ChatTool** (`.ncds` draft)
2. Derives structure using **LLM** 
3. Gets user confirmation via **ChatTool**
4. Formalizes using **LLM**
5. Activates into repositories
6. Displays result via **CanvasDisplayTool**

## Files

```
compiler/
├── compiler.ncds              # Draft plan (human-readable)
├── compiler.concept.json      # Compiled concepts (TODO)
├── compiler.inference.json    # Compiled inferences (TODO)
├── paradigms/
│   ├── chat_write.json        # Paradigm for writing to chat
│   ├── chat_read.json         # Paradigm for reading from chat
│   ├── chat_ask.json          # Paradigm for asking questions
│   ├── canvas_show.json       # Paradigm for canvas display
│   └── llm_process.json       # Paradigm for LLM processing
└── prompts/
    ├── derive.md              # Prompt for derivation
    ├── formalize.md           # Prompt for formalization
    └── activate.md            # Prompt for activation
```

## Self-Hosting

The compiler can compile itself:

1. Open this project in Canvas App
2. The compiler's own graph is visible
3. Modify the compiler plan
4. Run to see the effect
5. Use the modified compiler to compile other plans

## Usage

```python
# The compiler plan uses these tools:
Body.chat.write("Welcome!")
Body.chat.read_code("Paste your draft:")
Body.chat.ask("Is this correct?", ["Yes", "No"])
Body.canvas.show_source(code, "ncds")
Body.canvas.load_plan(concepts, inferences)
```

## Status

- [x] Draft plan created
- [ ] Paradigms defined
- [ ] Prompts written
- [ ] Plan compiled
- [ ] End-to-end test

