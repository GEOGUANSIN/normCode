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

## Paradigm Library (An incomplete list)

#### `h_PromptTemplate_SavePath-c_GenerateThinkJson-Extract-Save-o_FileLocation.json`
-   **Purpose**: An end-to-end workflow that takes a prompt template and a save path, generates a JSON response from an LLM, extracts the "answer" from it, and saves that answer to the specified path. The final output is the location of the saved file.
-   **Replaces**: This is the successor to the monolithic `thinking_save_and_wrap.json`.

#### `h_PromptTemplateInputOther_SaveDir-c_GenerateThinkJson-Extract-Save-o_FileLocation.json`
-   **Purpose**: An advanced variant of the standard prompt-and-save paradigm. It includes a "smart substitution" feature: any input variables provided to the paradigm that are *not* explicitly used in the prompt template are automatically bundled together and injected into the `$input_other` variable.
-   **Use Case**: Ideal for tasks where you have a primary instruction (mapped to `$input_1`) and a variable number of context files that should all be included as background information without needing to manually map each one in the template.

#### `h_PromptTemplate_ScriptLocation-c_Retrieve_or_GenerateThinkJson_ExtractPy_Execute-o_Normal.json`
-   **Purpose**: A flexible paradigm that executes Python code. It takes a prompt and a script location. If the script already exists, it executes it. If not, it uses the LLM to generate the code, saves it, and then executes it. The final output is the raw result from the Python function, wrapped in the standard typeless format.
-   **Replaces**: `py_exec_horizontal_prompt.json`.

#### `v_PromptTemplate-h_ScriptLocation-c_Retrieve_or_GenerateThinkJson_ExtractPy_Execute-o_Normal.json`
-   **Purpose**: A vertical variant of the paradigm above. It performs the same complex conditional logic: if a script exists, it executes it; otherwise, it uses an LLM to generate Python code from a JSON response, saves it, and then executes it. Its primary prompt template is provided vertically at composition time from the agent's state.
-   **Replaces**: `py_exec_vertical_prompt.json`.

#### `h_UserPrompt-c_Ask-o_Normal.json`
-   **Purpose**: A simple and direct paradigm that takes a prompt, displays it to the user in an interactive session, and returns the user's typed response as its output, wrapped in the standard `Normal` format. It is the primary mechanism for interactively asking a user for input.

#### `h_UserPrompt-c_AskForFilePath-o_FileLocation.json`
-   **Purpose**: A specialized variant of the user prompt paradigm that asks the user for a file path and wraps the string output in the standard `%{file_location}` format.

#### `h_UserPrompt-c_AskForMultipleFiles-o_FileLocationList.json`
-   **Purpose**: A specialized user prompt paradigm that opens a native file selection dialog, allowing the user to select multiple files. It features a persistent GUI window where users can add or remove files in multiple steps before confirming their final selection. The output is a list of file paths.

#### `h_InitialText-c_EditText-o_Normal.json`
-   **Purpose**: Presents the user with a text editor GUI pre-filled with initial text. The user can modify the text and confirm. The paradigm returns the final, modified text as a standard `Normal` output.

#### `h_InitialText_SavePath-c_EditText_Save-o_FileLocation.json`
-   **Purpose**: An extension of the text editor paradigm. It takes initial text and a save path, allows the user to modify the text in a GUI, saves the final content to the specified path, and returns the wrapped `%{file_location}`.