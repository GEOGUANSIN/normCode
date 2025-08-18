# @by Syntactical Concept Implementation

## Overview
This directory contains the implementation of the "@by" syntactical concept within the NormCode framework. The "@by" concept represents **imperative sequencing** - it defines how one imperative action is executed "by" another action or process.

## Purpose
The "@by" concept is a flow control operator that sequences imperatives. It creates a relationship where one imperative is executed through/by means of another imperative, establishing a dependency or method relationship between actions.

## Implementation Components


### 1. Cognition (`_cognition.py`)
- **Purpose**: Create arrangements and interactions of perception (determined primarily by value concepts) and actuation (determined primarily by function concepts) to complete the transformation of input elements to return output elements for the concept to infer (CTI). 
- **Functionality**:
    - concept name formality 
        - **Structure**: Triple format `(flow_control_mode, imperative_base, variable_citations)`
        - **Flow Control Mode**: Always "by" for this concept
        - **Imperative base**: The main imperative to be returned among the value cocnepts.
        - **Variable citations**: The extra value concepts coming from the concept-to-infer's inference setting. 
  - Process concept name for to configure the concnept to infer.  
  - Return functon element that can be congnitized as an imperative with variable citation.
  - Update 

### 2. Perception (`_perception.py`)
- **Purpose**: Retrieve and process information from agent's external environment.
- **Functionality**: 
  - No information is required from externality for the @by concept which is purely syntatical. Syntatical concepts will always be function concept in inference.


### 3. Actuation (`_actuation.py`)
- **Purpose**: Acted upon information about or direclty on agent's external environment.
- **Functionality**:
  - No action is required for the @by concepet which is purely syntatical. Syntatical concepts will always be self-sufficient in information and contained within the agent.

### Overall
Hence the overall process for this inference should look like this :
1. check the name formality of @by concept and analyze it. 
2. initiate reference tensor of concept to infer, the axes of the reference tensor should be based on that of the imperative base concept 
3. update the working memory regarding the working configuration of the target.  

- Coginition methods should include 
    - name formality check and decomposition
    - generate wokring configuration that is different from the usual imperative using variables in local inference. 
    - generate reference 
    - 


New Working Congiuration Scheme:
1. Cognition will primarily handle 
    1. Working Configuration 
    2. Return of Values 
    3. Operations within the 
    4. Sequencing within the Inference 