"""
Utility functions for the NPC (Neural Processing Core) package.

This module contains helper functions used across the NPC package for processing
concepts, building dependency graphs, and handling input data.
"""

from typing import Optional, List, Union, Dict, Set, Tuple, Any
from collections import defaultdict
from collections import deque
import ast
import json
from string import Template
import logging

from ._concept import Concept
from ._reference import Reference
from ._inference import Inference

def _get_initial_concepts(input_concept_names: List[str], concept_registry: Dict[str, Any]) -> Set[str]:
    """Get the set of initial concepts (inputs + referenced concepts)."""
    initial_concepts = set(input_concept_names)
    initial_concepts.update(
        name for name, concept in concept_registry.items()
        if hasattr(concept, 'reference') and concept.reference is not None
    )
    return initial_concepts

def _build_concept_mappings(inference_registry: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[Any, Tuple[Set[str], str]], Dict[Any, str]]:
    """Build mappings between inferences and their components.
    
    Returns:
        tuple containing:
        - concept_producers: dict mapping concept names to their producer inferences
        - inf_to_components: dict mapping inferences to their (input_concepts, output_concept)
        - inf_to_key: dict mapping inferences to their registry keys
    """
    concept_producers = {}
    inf_to_components = {}
    inf_to_key = {v: k for k, v in inference_registry.items()}

    for inf in inference_registry.values():
        key = inf_to_key[inf]
        components = ast.literal_eval(key)
        perception_names, actuation_name, inferred_name = components

        if inf.concept_to_infer.comprehension["name"] != inferred_name:
            raise ValueError(f"Inference registry mismatch for {inf}")

        input_concepts = set(perception_names) | {actuation_name}
        inf_to_components[inf] = (input_concepts, inferred_name)

        if inferred_name in concept_producers:
            raise ValueError(f"Multiple producers for {inferred_name}")
        concept_producers[inferred_name] = inf

    return concept_producers, inf_to_components, inf_to_key

def _build_dependency_graph(initial_concepts: Set[str], concept_producers: Dict[str, Any], 
                          inf_to_components: Dict[Any, Tuple[Set[str], str]],
                          inference_registry: Dict[str, Any]) -> Tuple[defaultdict, defaultdict]:
    """Build the dependency graph for topological sorting.
    
    Args:
        initial_concepts: Set of initial concept names
        concept_producers: Dict mapping concept names to their producer inferences
        inf_to_components: Dict mapping inferences to their (input_concepts, output_concept)
        inference_registry: Dict containing all registered inferences
        
    Returns:
        tuple containing:
        - graph: adjacency list representation of the dependency graph
        - in_degree: dict mapping nodes to their in-degree
    """
    graph = defaultdict(list)
    in_degree = defaultdict(int)

    for inf in inference_registry.values():
        input_concepts, _ = inf_to_components[inf]
        dependencies = set()

        for concept in input_concepts:
            if concept not in initial_concepts:
                if concept not in concept_producers:
                    raise ValueError(f"Unresolvable dependency: {concept}")
                dependencies.add(concept_producers[concept])

        for dep_inf in dependencies:
            graph[dep_inf].append(inf)
            in_degree[inf] += 1

        if inf not in in_degree:
            in_degree[inf] = 0

    return graph, in_degree

def _topological_sort(graph: defaultdict, in_degree: defaultdict, 
                     inference_registry: Dict[str, Any]) -> List[Any]:
    """Perform topological sort using Kahn's algorithm.
    
    Args:
        graph: Adjacency list representation of the dependency graph
        in_degree: Dict mapping nodes to their in-degree
        inference_registry: Dict containing all registered inferences
        
    Returns:
        List of inferences in topological order
    """
    queue = deque([
        inf for inf in inference_registry.values()
        if in_degree[inf] == 0
    ])
    ordered = []

    while queue:
        current = queue.popleft()
        ordered.append(current)

        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return ordered

def _validate_topological_order(ordered: List[Any], inf_to_components: Dict[Any, Tuple[Set[str], str]], 
                              inference_registry: Dict[str, Any]) -> None:
    """Validate that the topological sort includes all inferences."""
    if len(ordered) != len(inference_registry):
        remaining = set(inference_registry.values()) - set(ordered)
        cycle_info = [
            f"{inf_to_components[inf][1]} (requires {inf_to_components[inf][0]})"
            for inf in remaining
        ]
        raise ValueError(
            f"Cyclic/missing dependencies detected in: {cycle_info}"
        )

def order_inference(self):
    """Order inferences based on their dependencies using topological sorting."""
    # 1. Get initial concepts
    initial_concepts = _get_initial_concepts(self.input_concept_names, self.concept_registry)

    # 2. Build concept mappings
    concept_producers, inf_to_components, _ = _build_concept_mappings(self.inference_registry)

    # 3. Build dependency graph
    graph, in_degree = _build_dependency_graph(
        initial_concepts, concept_producers, inf_to_components, self.inference_registry
    )

    # 4. Perform topological sort
    ordered = _topological_sort(graph, in_degree, self.inference_registry)

    # 5. Validate and update pipeline
    _validate_topological_order(ordered, inf_to_components, self.inference_registry)

    self.inference_order = ordered
    return self