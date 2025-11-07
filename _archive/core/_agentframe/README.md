


### 1. Cognition (`_cognition.py`)
- **Purpose**: Create arrangements and interactions of perception (determined primarily by value concepts) and actuation (determined primarily by function concepts) to complete the transformation of input elements to return output elements for the concept to infer (CTI). 
    1. Name Formality (`_name_formality.py`)
    - concept name formality 
    - element name formality 

### 2. Perception (`_perception.py`)
- **Purpose**: Retrieve and process information from agent's external environment.

### 3. Actuation (`_actuation.py`)
- **Purpose**: Acted upon information about or direclty on agent's external environment.








New Working Congiuration Scheme:
1. Cognition is the key of setting up everthing under the inference - it will confirms 
    1. Concept Level operations 
        - name formality check (NFC)
        - input working configuration and check (IWCC)
        - Other Concept level operations (CLOC)
    2. Sequencing within the Inference for perception and actuation operations, including 
        - perception (MVP)
        - Cross-perception (CP)
        - Specified Perception (SP)
        - actuations (-)
        - on-perception actuations (PA previously realized in cognition)
        - memory actuations (MA)
        - on-perception tool actuations (PTA)
        - veiw change acutations (VCA)
    3. for concept to infer
        1. Working Configuration Output (OWCC)
        2. Return of Reference (RRC)
    4. Determine the structure of seuqencing within the inference
        -  judgement: (IWCC-(NFC-[(MVP-CP)-[(PA)]-(VCA-MA)]-RRC)-OWCC)
        -  imperative: (IWCC-(NFC-[MVP-[CP-[(PTA)-(SP)]-VCA]-MA]-RRC)-OWCC) 
        - 

## Detailed Component Explanations

### Concept Level Operations

#### **Name Formality Check (NFC)**
- **Purpose**: Validates that concept and element names follow proper naming conventions and syntax rules
- **Function**: Ensures concept names like `{user_account}` follow the `{object_name}` pattern, or that imperative names like `::(create_account)` follow the `::(action)` pattern
- **Implementation**: Checks for proper syntax, reserved words, and naming patterns before processing

#### **Input Working Configuration and Check (IWCC)**
- **Purpose**: Validates and processes the input configuration before inference begins
- **Function**: Verifies that all required parameters, LLM models, prompt templates, and variable definitions are properly configured
- **Implementation**: Checks that a concept has the correct `mode`, `llm`, `prompt_template`, and `template_variable_definition_dict` in its working configuration

#### **Other Concept Level Operations (CLOC)**
- **Purpose**: Performs concept-specific processing based on the concept type
- **Function**: Different operations for different concept types (judgement `<>`, imperative `::`, object `{}`, etc.)
- **Implementation**: For judgement concepts, sets up truth condition evaluation; for imperative concepts, involves action sequence planning

### Sequencing Operations

#### **Perception (MVP) - Main Perception**
- **Purpose**: Primary information retrieval from the agent's environment
- **Function**: Uses `_perception_memory_retrieval()` to fetch data from memory storage
- **Implementation**: Retrieves stored information about user accounts, process steps, or previous judgements

#### **Cross-perception (CP)**
- **Purpose**: Cross-references information between different perception sources or concepts
- **Function**: Compares and correlates data from multiple perception operations
- **Implementation**: Compares user account data with permission data to establish relationships

#### **Specified Perception (SP)**
- **Purpose**: Targeted information retrieval for specific, focused queries
- **Function**: More precise perception operations that target specific data points
- **Implementation**: Looks up a specific user's email address or a particular step in a process

#### **Actuations (-)**
- **Purpose**: General actuation operations (placeholder for various forms of environment modification)
- **Function**: Various forms of environment modification and data manipulation
- **Implementation**: Updates memory, modifies data structures, or triggers external actions

#### **On-perception Actuations (PA)**
- **Purpose**: Immediate responses triggered by perception results
- **Function**: Quick reactions to perceived information without waiting for full cognition
- **Implementation**: Immediately logs an error when invalid data is perceived, or triggers an alert

#### **Memory Actuations (MA)**
- **Purpose**: Persistent storage operations to save information for future use
- **Function**: Uses `_remember_in_concept_name_location_dict()` to store data with location awareness
- **Implementation**: Saves the result of a judgement evaluation or stores a new user account

#### **On-perception Tool Actuations (PTA)**
- **Purpose**: Tool-based responses triggered by perception
- **Function**: Invokes external tools or services based on perceived information
- **Implementation**: Calls an API to validate an email address or sends a notification

#### **View Change Actuations (VCA)**
- **Purpose**: Modifies how data is viewed or presented without changing the underlying data
- **Function**: Changes data perspectives, filters, or presentation formats
- **Implementation**: Switches from a detailed view to a summary view, or filters data by specific criteria

### Concept to Infer Operations

#### **Working Configuration Output (OWCC)**
- **Purpose**: Validates and finalizes the output configuration after inference
- **Function**: Ensures the inference result is properly formatted and configured for downstream use
- **Implementation**: Verifies that a judgement result has the correct format (TRUE/FALSE/N/A) and is ready for storage

#### **Return of Reference (RRC)**
- **Purpose**: Maintains referential integrity by returning properly structured references
- **Function**: Ensures that the inference result maintains proper connections to its source concepts and data
- **Implementation**: Returns a judgement result that maintains links to the original concepts that were evaluated

### Sequencing Patterns

#### **Judgement Pattern**: `(IWCC-((NFC-CLOC)-[(MVP-CP)-[(PA)]-(VCA-MA)]-RRC)-OWCC)`
- **Flow**: Input validation → Name/Concept validation → Main perception with cross-perception → Parallel on-perception actuations with view/memory actuations → Reference return → Output validation
- **Characteristics**: Emphasizes parallel processing of immediate responses (PA) with view/memory operations

#### **Imperative Pattern**: `(IWCC-((NFC-CLOC)-[MVP-[CP-[(PTA)-(SP)]-VCA]-MA]-RRC)-OWCC)`
- **Flow**: Input validation → Name/Concept validation → Main perception → Cross-perception → Parallel tool actuations with specified perception → View changes → Memory actuations → Reference return → Output validation
- **Characteristics**: Emphasizes sequential processing with tool-based actuations and targeted perception

### Key Architectural Insights

1. **Sequential vs Parallel Processing**: Judgement operations prioritize parallel processing (PA in parallel with VCA-MA), while imperative operations use sequential processing with tool-based actuations.

2. **Memory-Centric Design**: Heavy emphasis on memory operations (MA, VCA) suggests this is designed for persistent, stateful agents that maintain knowledge across multiple interactions.

3. **Tool Integration**: PTA indicates the framework is designed to integrate with external tools and services, making it suitable for real-world applications.

4. **Configuration Management**: IWCC and OWCC bookend the process, ensuring proper setup and cleanup of working configurations.

5. **Reference Management**: RRC appears in both patterns, indicating the framework's focus on maintaining referential integrity throughout the inference process. 

Inference
    - determine the inference by concept type of the function concept
        - this is in fact determined by the agent - so there is an overall agent configuration that will pre-resolve all the inference sequence.
        - This will require an agent.inference_sequence_config dictionary from the agent_frame -> this wil be in the working memory
    - The customization of the sequencing will be done through this miminal inference_seqeunce_config. process will be stored in the Inference Working configuration
    - Given this, I think the better design is actaully having having the sequence coded in the cogintion configuration of the concept
Working Cofiguration
    -> A configuration for each of the concept
        -> a concept has three configurations
        -> cognition configuration
            -> inference sequence
            -> concept related configuration that is in the inference sequence, ususally include:
               -> working configuraion input  (must include and not customizable)
               -> formal name Self-referential (concept-level  - no need to be customized)
               -> Return of Reference (element-level) -  specified what to return
               -> working configuraion ouput - specifed what is changed by the concept (This is only useful during the cognition of syntatical concepts )