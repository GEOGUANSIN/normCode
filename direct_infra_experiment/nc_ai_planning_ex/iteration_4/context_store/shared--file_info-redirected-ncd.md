# File Format: Redirected NormCode Draft (`3.2_redirected.ncd`)

The `3.2_redirected.ncd` file represents the plan after the **Redirection** pattern has been applied to the serialized draft. This is a critical step for making the data flow of the pipeline explicit.

**Purpose:**
The primary goal of this file is to define the precise inputs for every imperative (`::()`) in the plan. While the serialized draft shows *what* is created, the redirected draft shows *what is needed* to create it. It "redirects" the flow of data, making all dependencies transparent.

**Key Characteristics:**
-   **Explicit Inputs**: Each imperative is expanded to show its specific dependencies, which are categorized and nested underneath it.
-   **Input Tagging**: Inputs are clearly tagged to show their origin:
    -   `<:{prompt}>`: Indicates the input is a prompt, further annotated with a `%{prompt_location}` to link to its source file.
    -   `<:{1}>`, `<:{2}>`, etc.: Indicates the input is an inherited output from a previous step, using positional markers.
    -   `%{file_location}`: Used for inputs sourced directly from static files.
-   **Data Flow Visibility**: This format makes the entire dependency graph of the plan visible and machine-parsable, which is essential for the final formalization and execution stages.

**Example Snippet:**
```normcode
<- {1.1_instruction_block.md}
    <= ::{%(direct)}({prompt}<$({instruction distillation prompt})%>: {1}<$({input files})%>)
    <- {instruction distillation prompt}<:{prompt}>
        |%{prompt_location}: 1.1_instruction_distillation.md
    <- {input files}<:{1}>
        <= &in
        <- {original prompt}
            |%{file_location}: prompts/0_original_prompt.md
```
This redirected draft is the last step before the plan is stripped of all annotations and assigned flow indices to become the final, formal `.nc` file.
