import re
import ast
from pathlib import Path
from string import Template

from ...._agentframe import AgentFrame
from ...._llm_tools import ConfiguredLLM, JsonBulletLLM, JsonStructuredLLM
from ...._npc_components import Plan
from ...._npc_components import (
    Concept, 
    CONCEPT_TYPE_CLASSIFICATION, 
    CONCEPT_TYPE_JUDGEMENT, 
    CONCEPT_TYPE_OBJECT, 
    CONCEPT_TYPE_ASSIGNMENT, 
    CONCEPT_TYPE_RELATION, 
    CONCEPT_TYPE_SENTENCE
)
from ...._npc_components._utils import _process_input_data
from ....examples._dev_expriement.metaphor_dot import metaphor_dot

# Default prompt template for metaphor explanation
DEFAULT_METAPHOR_PROMPT_TEMPLATE = Template("""
    Given the context: $concept_context

    In few sentences, define faithfully the meaning and significance of the concept '$concept_name'. Be clear about its purpose of use, and make sure the important context is included such that it is intelligible without any prior knowledge of the context.
    """)

def _identify_base_concepts(plan: Plan):
    # Get all concepts that are used as inferred concepts in inferences
    inferred_concepts = set()
    for inference in plan.inference_registry.values():
        inferred_concepts.add(inference.concept_to_infer.comprehension["name"])
    
    # Base concepts are those that are not used as inferred concepts
    base_concepts = [
        concept_name for concept_name in plan.concept_registry.keys()
        if concept_name not in inferred_concepts
    ]
    return base_concepts

def _identify_object_base_concepts(plan: Plan):
    base_concepts = _identify_base_concepts(plan)
    object_base_concepts = [
        concept for concept in base_concepts 
        if plan.concept_registry[concept].comprehension["type"] == CONCEPT_TYPE_OBJECT
    ]
    return object_base_concepts

def _set_plan_io_from_base_concepts(plan: 'Plan') -> 'Plan':
    """
    Set input/output concepts for a plan where:
    - Inputs are all object base concepts
    - Outputs are concepts without any output inferences
    
    Args:
        plan: The plan to configure
        
    Returns:
        The configured plan
    """
    # Get all base concepts
    base_concepts = _identify_base_concepts(plan)
    
    # Get object base concepts
    object_base_concepts = [
        concept for concept in base_concepts 
        if plan.concept_registry[concept].comprehension["type"] == CONCEPT_TYPE_OBJECT
    ]
    
    # Get concepts that are not used as inferred concepts in any inference
    concepts_with_output_inferences = set()
    for inference in plan.inference_registry.values():
        concepts_with_output_inferences.add(inference.concept_to_infer.comprehension["name"])
    
    output_concepts = [
        concept for concept in plan.concept_registry.keys()
        if concept not in concepts_with_output_inferences
    ]
    
    if not output_concepts:
        raise ValueError("No output concepts found - all concepts are used in inferences")
    
    # Set input/output concepts
    plan.set_input_output_concepts(
        input_names=object_base_concepts,
        output_name=output_concepts[0]  # Use first available output concept
    )
    
    return plan

def _process_non_object_base_concepts(plan: Plan, agent: AgentFrame, reference_mode: str = "llm_default", input_mode: str = None, input_data: dict = None, default_prompt_template: str = DEFAULT_METAPHOR_PROMPT_TEMPLATE) -> Plan:
    """
    Process non-object base concepts in a plan using constant reference.
    
    Args:
        plan: The plan containing the concepts to process
        agent: The agent frame to use for processing
        reference_mode: The reference mode to use (default: "llm_default")
        input_mode: The input mode to use
        input_data: Optional input data for concepts
        default_prompt_template: The default prompt template to use
        
    Returns:
        The processed plan
    """
    # Get all base concepts
    base_concepts = _identify_base_concepts(plan)
    
    # Get object base concepts
    object_base_concepts = _identify_object_base_concepts(plan)
    
    # Get non-object base concepts
    non_object_base_concepts = [
        concept for concept in base_concepts 
        if concept not in object_base_concepts
    ]
    
    if not non_object_base_concepts:
        return plan
        
    # Prepare input data for constant reference
    constant_data = {}
    for concept_name in non_object_base_concepts:
        concept = plan.concept_registry[concept_name]
        if input_data and concept_name in input_data:
            constant_data[concept_name] = input_data[concept_name]
        else:
            # Default behavior if no input data provided
            constant_data[concept_name] = concept_name
    
    if reference_mode == "llm_default":
        input_mode = "raw_agent_explanation"
        # Create input config with default template
        input_config = {
            concept_name: {
                "template": default_prompt_template,
                "llm": "llm"
            }
            for concept_name in non_object_base_concepts
        }
    else:
        raise ValueError(f"Invalid reference_mode: {reference_mode}")
        
    # Process the concepts
    processed_concepts = _process_input_data(
        input_mode=input_mode,
        input_data=constant_data,
        input_config=input_config,
        input_concept_names=non_object_base_concepts,
        concept_registry=plan.concept_registry,
        agent=agent,
        cognition_input=True,
        debug=plan.debug
    )
    
    # Update the concept registry with processed concepts
    for concept in processed_concepts:
        plan.concept_registry[concept.comprehension["name"]] = concept
    
    return plan

class DOTParser:
    def __init__(self, dot_string):
        self.dot_string = dot_string
        self.plan = None
        self.context_pattern: str = r'^###(.*?)(?=digraph|$)'
        self.node_pattern: str = r'\s*"([^"]+)"\s*\[xlabel\s*=\s*"([^"]+)"\](?:\s*;)?'
        self.edge_pattern: str = r'"([^"]+)"\s*->\s*"([^"]+)"\s*\[label="(\w+)"\]'
        self.context: str = ""
        self.nodes: dict[str, dict] = {}


        self.context = self._parse_context()
        self.nodes = self._parse_node()
        self.nodes = self._parse_edge()

    def _parse_context(self):
        context_match = re.match(self.context_pattern, self.dot_string)
        if context_match:
            self.context = context_match.group(1).strip()
            self.dot_string = self.dot_string[context_match.end():].strip()
        return self.context
    
    def _node_type_and_context_annotation(self, node):
        if node.startswith("<") and node.endswith(">"):
            concept_name = node[1:-1]
            concept_type = CONCEPT_TYPE_JUDGEMENT
            concept_context_annotation = f"{node} is a judgement concept for {concept_name}. This means that {node} is a judgement about {concept_name}. It is extracted from the context {self.context}."
        elif node.endswith("?"):
            concept_name = node[:-1]
            concept_type = CONCEPT_TYPE_CLASSIFICATION
            concept_context_annotation = f"{node} is a classification concept for {concept_name}. This means that when {node} is done, it will extract instances of {concept_name} by their names from the relevant input."
        # if the node is in the form of [concept_name]..., then it is a relation concept.
        elif node.startswith("["):   
            concept_name = node[1:-1]
            concept_type = CONCEPT_TYPE_RELATION
            concept_context_annotation = f"{node} is a relation concept for {concept_name}. This means that {node} is a relation between {concept_name}. It is extracted from the context {self.context}."
        elif node.startswith("<") and node.endswith(r"\^\d+"):
            concept_name = node.rsplit("^", 1)[0][1:-1]
            concept_type = CONCEPT_TYPE_SENTENCE
            concept_context_annotation = f"{node} is a sentence concept for {concept_name}. This means that {node} is a sentence with specific truth values about {concept_name}. It is extracted from the context {self.context}."
        elif node.startswith("@"):
            concept_name = node[1:]
            concept_type = CONCEPT_TYPE_ASSIGNMENT
            concept_context_annotation = f"{node} is an assignment concept for {concept_name}. This means that {node} assigns a value to other concepts related to {concept_name}. It is extracted from the context {self.context}."
        elif node.startswith("{"):
            concept_name = node[1:]
            concept_type = CONCEPT_TYPE_OBJECT
            concept_context_annotation = f"{node} is an object concept for {concept_name}. This means that {node} refers to specific objects with a name. It is extracted from the context {self.context}."
        else:
            concept_name = node
            concept_type = CONCEPT_TYPE_OBJECT
            concept_context_annotation = f"{node} is an object concept for {concept_name}. This means that {node} refers to specific objects with a name. It is extracted from the context {self.context}."

        return concept_type, concept_context_annotation

    def _parse_node(self):
        nodes = re.findall(self.node_pattern, self.dot_string)

        for node, view  in nodes:

            concept_type, concept_context_annotation = self._node_type_and_context_annotation(node)
            concept_context = self.context + concept_context_annotation

            self.nodes[node] = {
                "name": node,
                "type": concept_type,
                "context": concept_context,
                "view": view
            }

        return self.nodes
    

    def _parse_edge(self):
        edges = re.findall(self.edge_pattern, self.dot_string)
        for source, target, label in edges:
            # Initialize inferences for target if not exists
            if "inferences" not in self.nodes[target]:
                self.nodes[target]["inferences"] = [{
                    "perception_concepts": [],
                    "cognition_concept": None
                }]
            
            # Get the first inference entry for this target
            inference = self.nodes[target]["inferences"][0]
            
            if label == "perc":
                if source not in inference["perception_concepts"]:
                    inference["perception_concepts"].append(source)
            elif label == "cog":
                inference["cognition_concept"] = source
            else:
                raise ValueError(f"Invalid edge label: {label}")
                
        return self.nodes

    def make_plan_in_concepts(self):
        # Create a new plan with debug mode
        plan = Plan(debug=True)

        # Add all nodes as concepts to the plan
        for node_name, node_data in self.nodes.items():
            concept = plan.add_concept(
                name=node_name,
                context=node_data["context"],
                type=node_data["type"]
            )

        # Add inferences based on edges
        for node_name, node_data in self.nodes.items():
            if "inferences" in node_data:
                for inference_data in node_data["inferences"]:
                    # Only create inference if we have both perception and cognition concepts
                    if (inference_data["perception_concepts"] and 
                        inference_data["cognition_concept"] is not None):
                        perception_concepts = [
                            plan.concept_registry[concept_name]
                            for concept_name in inference_data["perception_concepts"]
                        ]
                        cognition_concept = plan.concept_registry[inference_data["cognition_concept"]]
                        concept_to_infer = plan.concept_registry[node_name]

                        plan.add_inference(
                            concept_to_infer=concept_to_infer,
                            perception_concepts=perception_concepts,
                            cognition_concept=cognition_concept,
                            view=node_data["view"]  
                        )
        self.plan = _set_plan_io_from_base_concepts(plan)

        return self.plan


if __name__ == "__main__":
    # Create agent with memory location and debug mode
    llm_model_name = "qwen-turbo-latest"
    memory_location = str(Path.cwd() / "memory.json")
    open(memory_location, "w").write("{}")

    agent = AgentFrame(
        body={
            'memory_location': memory_location,
            'llm': ConfiguredLLM(model_name=llm_model_name),
            "bullet_llm": JsonBulletLLM(model_name=llm_model_name),
            "structured_llm": JsonStructuredLLM(model_name=llm_model_name),
        },
        debug=True  # Ensure debug mode is enabled
    )

    dot_parser = DOTParser(metaphor_dot)
    plan = dot_parser.make_plan_in_concepts()
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("============================Plan 1============================")
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    plan.print_plan()

    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("============================Plan 2============================")
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    plan = _process_non_object_base_concepts(plan, agent)
    plan.print_plan()
    # Prepare input data for execution
    input_data = {
        "extract": "Time is a thief that steals our moments away."
    }

    # Execute the plan
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("============================Plan 3============================")
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    result = plan.execute(agent, input_data=input_data)
    plan.print_plan()

    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("============================Result============================")
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Plan execution result:", result.tensor)
    print("Result axes:", result.axes)