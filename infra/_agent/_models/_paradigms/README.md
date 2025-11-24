# Composition Paradigms

This directory contains pre-defined, reusable composition paradigms stored in a declarative JSON format. These paradigms can be loaded by an agent sequence to execute complex, multi-step functions.

## Naming Convention

To ensure that a paradigm's function is completely clear from its name, all paradigms must follow a structured naming convention. The name is broken into three parts, separated by hyphens, describing the inputs, the composition logic, and the outputs.

**Structure:** `[inputs]-[composition]-[outputs].json`

**1. Inputs (`h_...` or `v_...`):**
-   Describes the primary inputs for the paradigm, prefixed with `h_` for **Horizontal** (runtime) inputs or `v_` for **Vertical** (composition-time) inputs.
-   Multiple inputs are separated by underscores.
-   **Example:** `h_PromptTemplate_SavePath`

**2. Composition (`c_...`):**
-   Describes the sequence of actions inside the paradigm's execution plan, prefixed with `c_`.
-   Actions are hyphenated.
-   **Example:** `c_GenerateThinkJson-Extract-Save`

**3. Outputs (`o_...`):**
-   Describes the final output of the paradigm, prefixed with `o_`.
-   **Example:** `o_FileLocation`

**Full Example:**
`h_PromptTemplate_SavePath-c_GenerateThinkJson-Extract-Save-o_FileLocation.json`

This name provides a complete, self-documenting summary of the paradigm's entire workflow.

## Paradigm Library

#### `h_PromptTemplate_SavePath-c_GenerateThinkJson-Extract-Save-o_FileLocation.json`
-   **Purpose**: An end-to-end workflow that takes a prompt template and a save path, generates a JSON response from an LLM, extracts the "answer" from it, and saves that answer to the specified path. The final output is the location of the saved file.
-   **Replaces**: This is the successor to the monolithic `thinking_save_and_wrap.json`.

#### `h_PromptTemplate_ScriptLocation-c_Retrieve_or_GenerateThinkJson_ExtractPy_Execute-o_Normal.json`
-   **Purpose**: A flexible paradigm that executes Python code. It takes a prompt and a script location. If the script already exists, it executes it. If not, it uses the LLM to generate the code, saves it, and then executes it. The final output is the raw result from the Python function, wrapped in the standard typeless format.
-   **Replaces**: `py_exec_horizontal_prompt.json`.

#### `v_PromptTemplate-h_ScriptLocation-c_Retrieve_or_GenerateThinkJson_ExtractPy_Execute-o_Normal.json`
-   **Purpose**: A vertical variant of the paradigm above. It performs the same complex conditional logic: if a script exists, it executes it; otherwise, it uses an LLM to generate Python code from a JSON response, saves it, and then executes it. Its primary prompt template is provided vertically at composition time from the agent's state.
-   **Replaces**: `py_exec_vertical_prompt.json`.

#### `h_UserPrompt-c_Ask-o_Normal.json`
-   **Purpose**: A simple and direct paradigm that takes a prompt, displays it to the user in an interactive session, and returns the user's typed response as its output, wrapped in the standard `Normal` format. It is the primary mechanism for interactively asking a user for input.