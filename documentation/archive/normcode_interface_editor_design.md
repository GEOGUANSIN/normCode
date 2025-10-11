# Normcode Interface Editor: Design Document

## 1. Introduction

The Normcode Interface Editor is a visual tool designed to streamline the creation, modification, and understanding of `normcode` programs. It provides a graphical user interface to manage concepts, define inferences, and visualize the overall computational graph, abstracting away much of the boilerplate Python code required to define `ConceptEntry` and `InferenceEntry` objects.

## 2. Core `normcode` Concepts

A `normcode` program is fundamentally composed of three parts:

*   **Concepts**: These represent the data nodes in the computational graph. They can be inputs (ground concepts), outputs (final concepts), intermediate data, or functions.
*   **Inferences**: These define the operations and relationships between concepts, acting as the directed edges of the graph. An inference connects input concepts to an output concept via a function concept.
*   **Normcode Text**: A high-level, human-readable description of the process, which can be in natural language or a structured, indented format. This text often serves as the specification from which the concepts and inferences are derived.

## 3. High-Level Design & UI Components

The editor will be a desktop application with a multi-panel layout, providing a comprehensive workspace for `normcode` development.

![UI Mockup](https://i.imgur.com/your-mockup-image.png)  <!-- A placeholder for a UI mockup image -->

The main window will be divided into four key areas:

*   **Left Panel (Explorer)**: A hierarchical view of all concepts and inferences within the current project.
*   **Center Panel (Canvas)**: A dynamic, interactive graph visualization where the `normcode` program is constructed and visualized.
*   **Right Panel (Inspector)**: A context-sensitive panel to view and edit the detailed properties of any selected element (concept or inference).
*   **Bottom Panel (Normcode Editor)**: An integrated text editor for writing and referencing the `normcode` natural language or structured text.

## 4. Detailed Component Descriptions

### 4.1. Explorer Panel

This panel acts as the project's inventory.

*   **Tree View**: Displays all `ConceptEntry` objects, logically grouped by their role (e.g., Ground, Intermediate, Function, Final).
*   **Actions**:
    *   **Create**: Buttons to add new concepts. A dialog would prompt for the essential details like `concept_name` and `type`.
    *   **Search/Filter**: Quickly find concepts by name.
    *   **Drag-and-Drop**: Concepts can be dragged from the Explorer onto the Canvas to add them to the visual graph.

### 4.2. Canvas Panel

This is the primary workspace for building the computational graph.

*   **Visual Representation**:
    *   Concepts are rendered as distinct nodes, perhaps with different shapes or colors based on their type.
    *   Inferences are represented as directed edges connecting the nodes, clearly indicating the flow of data.
*   **Interactivity**:
    *   **Drag-and-Drop**: Create inferences by dragging a connection from a function concept to a concept to be inferred. The editor would then prompt to connect the required value and context concepts.
    *   **Manipulation**: Users can pan, zoom, and rearrange nodes to organize the graph for clarity.
    *   **Context Menu**: Right-clicking on a node or edge provides quick access to actions like "Edit in Inspector," "Find Usages," or "Delete."

### 4.3. Inspector Panel

This panel provides a detailed view of the selected element.

*   **Concept View**: When a concept node is selected on the canvas or in the explorer:
    *   Displays all fields of the `ConceptEntry` (`id`, `concept_name`, `type`, `description`, etc.).
    *   Provides user-friendly form elements (text inputs, dropdowns, checkboxes for booleans like `is_final_concept`) to edit these properties.
    *   For `reference_data`, it could offer a simple table or JSON editor for structured data.
*   **Inference View**: When an inference edge is selected:
    *   Displays all fields of the `InferenceEntry`.
    *   Uses dropdowns populated with existing concepts to select the `concept_to_infer`, `function_concept`, `value_concepts`, and `context_concepts`. This prevents typos and ensures graph integrity.
    *   Provides a text area or structured editor for the `working_interpretation` dictionary.

### 4.4. Normcode Editor Panel

This panel links the high-level description to the implementation.

*   **Text Editor**: A dedicated space for the `Normcode_raw_paragraph` or the structured `Normcode` text.
*   **Syntax Highlighting**: Custom syntax highlighting can be developed to improve the readability of the structured `normcode` format.
*   **(Advanced) Code Generation**:
    *   **Text-to-Graph**: A feature to parse the structured `normcode` text and automatically generate a skeleton of the concepts and inferences on the canvas.
    *   **Graph-to-Text**: A feature to generate a structured `normcode` text representation from the visual graph.

## 5. Example Workflow

A user wants to create the "digit counting" program from `ex_orchest_add.py`.

1.  **Create Concepts**: In the **Explorer**, the user clicks "New Concept" to create the necessary concepts: `{number}`, `{index}*`, `{digit}*`, `[all {index} and {digit} of number]`, `::(get ...)` etc. They fill in the names and types.
2.  **Build the Graph**: The user drags these concepts onto the **Canvas**. They select the `::(get ...)` function concept and create an inference edge pointing to the `{digit}*` concept.
3.  **Configure Inferences**: With the new inference selected, the user goes to the **Inspector**. They use the dropdowns to select `{number}*` and `{unit place digit}?` as `value_concepts`. They fill in the `flow_info` and `working_interpretation`.
4.  **Set Initial Data**: The user selects the `{number}` concept and, in the **Inspector**, sets its `is_ground_concept` flag to true and provides its initial `reference_data`.
5.  **Write Description**: In the **Normcode Editor**, the user writes or pastes the natural language description of the process for documentation.
6.  **Export**: Once the graph is complete, the user clicks an "Export to Python" button. The editor generates a `.py` file containing the `create_sequential_repositories` function, populated with all the `ConceptEntry` and `InferenceEntry` objects defined visually.

## 6. Proposed Technology Stack

*   **Framework**: **Electron** to create a cross-platform desktop application using web technologies.
*   **Frontend**: **React** or **Svelte** for building the user interface components.
*   **Graph Visualization**: A library like **React Flow** or **D3.js** to render and manage the interactive canvas.
*   **Backend/Core Logic**: The core `normcode` Python libraries can be interfaced with the Electron app via a child process or a local server, handling tasks like code generation and validation.
