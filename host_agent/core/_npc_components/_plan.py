from ._concept import Concept
from ._reference import Reference
from typing import Optional, List, Union, Dict, Set, Tuple, Any
import logging
from ._inference import Inference
from ._utils import (
    _get_initial_concepts,
    _build_concept_mappings,
    _build_dependency_graph,
    _topological_sort,
    _validate_topological_order,
    _process_input_data
)


class Plan:
    def __init__(self, debug: bool = False):
        self.agent: Optional[Any] = None
        self.concept_registry: Dict[str, Concept] = {}
        self.inference_registry: Dict[str, Inference] = {}
        self.inference_order: List[Inference] = []
        self.output_concept_name: Optional[str] = None
        self.debug = debug

    def _debug_print(self, message: str):
        if self.debug:
            print(f"[DEBUG] {message}")

    def print_plan(self):
        """Print the plan's structure and details in a formatted way."""
        print("\n=== Plan Structure ===")
        
        # Print I/O Configuration
        print("\nI/O Configuration:")
        print(f"Input Concepts: {', '.join(self.input_concept_names)}")
        print(f"Output Concept: {self.output_concept_name}")
        print(f"Constant Concepts: {', '.join(self.constant_concept_names)}")
        
        # Print Concept Registry
        print("\n=== Concept Registry ===")
        for concept_name, concept in self.concept_registry.items():
            print(f"\nConcept: {concept_name}")
            print(f"Type: {concept.comprehension['type']}")
            print(f"Context: {concept.comprehension['context']}")
            if hasattr(concept, 'reference') and concept.reference is not None:
                print("Has Reference: Yes")
                if hasattr(concept.reference, 'tensor'):
                    print(f"Tensor: {concept.reference.tensor}")
                    print(f"Tensor axes: {concept.reference.axes}")
            else:
                print("Has Reference: No")
        
        # Print Inference Registry
        print("\n=== Inference Registry ===")
        for inf_key, inference in self.inference_registry.items():
            print(f"\nInference Key: {inf_key}")
            print(f"Concept to Infer: {inference.concept_to_infer.comprehension['name']}")
            print("Perception Concepts:")
            for pc in inference.post_actuation_pre_perception_concepts:
                print(f"  - {pc.comprehension['name']}")
            print(f"Cognition Concept: {inference.post_actuation_pre_cognition_concept.comprehension['name']}")
            print(f"View: {inference.view}")
        
        # Print Inference Order
        if self.inference_order:
            print("\n=== Inference Execution Order ===")
            for i, inf in enumerate(self.inference_order):
                print(f"{i+1}. {inf.concept_to_infer.comprehension['name']}")

    def add_concept(self, concept: Optional[Concept] = None, **kwargs):
        if concept is None:
            concept = Concept(**kwargs)
        self.concept_registry[concept.comprehension["name"]] = concept
        return concept

    def add_inference(self, inference: Optional[Inference] = None, **kwargs):
        if inference is None:
            inference = Inference(**kwargs)
        perception_concepts = [c.comprehension["name"] for c in inference.post_actuation_pre_perception_concepts]
        cognition_concept = inference.post_actuation_pre_cognition_concept.comprehension["name"]
        inferred_concept = inference.concept_to_infer.comprehension["name"]
        inference_key = str([perception_concepts, cognition_concept, inferred_concept])
        self.inference_registry[inference_key] = inference
        return inference
    

    def execute(self, agent, input_data: Optional[dict[str, Union[Reference, str, dict]]] = None, input_mode: str = "raw_replicate_explanation", 
                input_config: Optional[dict[str, dict[str, dict]]] = None):
        from core._agentframe import AgentFrame
        if not isinstance(agent, AgentFrame):
            raise ValueError("Agent must be an instance of AgentFrame")
        self.agent = agent
        self._debug_print("Starting plan execution")

        # Validate I/O configuration
        if not self.input_concept_names or not self.output_concept_name:
            raise ValueError("I/O not configured. Call configure_io() first")

        # Process input data and get updated concepts
        processed_concepts = _process_input_data(
            input_mode, input_data, input_config, 
            self.input_concept_names, self.concept_registry, 
            agent, True, self.debug
        )
        
        # Update concept registry with processed concepts
        for concept in processed_concepts:
            self.concept_registry[concept.comprehension["name"]] = concept

        # Verify all input concepts have references
        missing_refs = [
            name for name in self.input_concept_names
            if not self.concept_registry[name].reference
        ]
        if missing_refs:
            raise ValueError(f"Missing references for inputs: {', '.join(missing_refs)}")

        # Renew relevant inferences
        for inf_key, inference in self.inference_registry.items():
            # Check if inference uses any of the input concepts
            if any(concept.comprehension["name"] in self.input_concept_names 
                  for concept in inference.post_actuation_pre_perception_concepts) or \
               inference.post_actuation_pre_cognition_concept.comprehension["name"] in self.input_concept_names:
                # Renew the inference with updated concepts
                perception_concepts = [
                    self.concept_registry[c.comprehension["name"]] 
                    for c in inference.post_actuation_pre_perception_concepts
                ]
                cognition_concept = self.concept_registry[
                    inference.post_actuation_pre_cognition_concept.comprehension["name"]
                ]
                inferred_concept = self.concept_registry[
                    inference.concept_to_infer.comprehension["name"]
                ]
                
                self.inference_registry[inf_key] = Inference(
                    concept_to_infer=inferred_concept,
                    perception_concepts=perception_concepts,
                    cognition_concept=cognition_concept,
                    view=inference.view
                )

        # Execute inference_order in topological order
        if not self.inference_order:
            self.order_inference()

        self._debug_print("Executing inferences in order:")
        for i, inf in enumerate(self.inference_order):
            self._debug_print(f"  {i+1}. Executing inference for {inf.concept_to_infer.comprehension['name']}")
            inf.execute(agent=agent)

        # Retrieve and validate final output
        output_concept = self.concept_registry[self.output_concept_name]
        self._debug_print(f"Retrieving output from {self.output_concept_name}")

        if not output_concept.reference:
            raise RuntimeError(
                f"Output concept '{self.output_concept_name}' "
                "failed to generate a reference"
            )

        return output_concept.reference
