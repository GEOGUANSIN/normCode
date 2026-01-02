"""
Value Service - Value overrides and dependency tracking.

This service handles:
- Getting reference data for concepts
- Overriding concept values
- Finding dependents and descendants
- Selective re-run support
"""

import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ValueService:
    """
    Service for managing concept values and dependencies.
    
    Provides methods to:
    - Get reference data for concepts
    - Override concept values
    - Find dependent and descendant nodes
    """
    
    def get_reference_data(
        self,
        concept_repo: Any,
        concept_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get reference data for a concept from the concept repository.
        
        Returns the current reference data (tensor) for a concept, including:
        - data: The tensor data (nested lists)
        - axes: The axis names
        - shape: The tensor shape
        
        Returns None if concept not found or has no reference data.
        """
        if concept_repo is None:
            return None
        
        try:
            # Get the concept entry from the repository
            concept_entry = concept_repo.get_concept(concept_name)
            if concept_entry is None:
                return None
            
            # Get the actual Concept object from the entry
            concept = concept_entry.concept if hasattr(concept_entry, 'concept') else None
            if concept is None:
                return None
            
            # Check if concept has a reference
            if not hasattr(concept, 'reference') or concept.reference is None:
                return None
            
            ref = concept.reference
            
            # Extract reference data
            result = {
                "concept_name": concept_name,
                "has_reference": True,
            }
            
            # Get tensor data
            if hasattr(ref, 'tensor'):
                result["data"] = ref.tensor
            elif hasattr(ref, 'data'):
                result["data"] = ref.data
            else:
                result["data"] = None
            
            # Get axis names
            if hasattr(ref, 'axes') and ref.axes:
                result["axes"] = [axis.name if hasattr(axis, 'name') else str(axis) for axis in ref.axes]
            else:
                result["axes"] = []
            
            # Calculate shape from tensor
            # IMPORTANT: Limit depth to number of axes to avoid treating
            # nested list VALUES as additional dimensions.
            if result["data"] is not None:
                shape = []
                current = result["data"]
                axes_count = len(result["axes"]) if result["axes"] else 0
                
                # If we have axes info, use it to limit shape depth
                if axes_count > 0:
                    while isinstance(current, list) and len(shape) < axes_count:
                        shape.append(len(current))
                        if len(current) > 0:
                            current = current[0]
                        else:
                            break
                # else: No axes - treat as scalar (shape=[])
                
                result["shape"] = shape
            else:
                result["shape"] = []
            
            return result
            
        except Exception as e:
            logger.warning(f"Error getting reference for {concept_name}: {e}")
            return None
    
    def get_all_reference_data(
        self,
        concept_repo: Any
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get reference data for all concepts that have references.
        
        Returns a dict mapping concept_name -> reference_data for concepts
        that have been computed or are ground concepts.
        """
        if concept_repo is None:
            return {}
        
        result = {}
        try:
            # Iterate through all concepts in the repo
            for concept_entry in concept_repo.get_all_concepts():
                concept_name = concept_entry.concept_name
                ref_data = self.get_reference_data(concept_repo, concept_name)
                if ref_data and ref_data.get("has_reference"):
                    result[concept_name] = ref_data
        except Exception as e:
            logger.warning(f"Error getting all references: {e}")
        
        return result
    
    def find_dependents(
        self,
        inference_repo: Any,
        concept_name: str
    ) -> List[str]:
        """
        Find all flow_indices of inferences that depend on a given concept.
        
        This finds all inferences that use the concept as:
        - value_concepts
        - context_concepts
        """
        if inference_repo is None:
            return []
        
        dependents = []
        
        for inf_entry in inference_repo.inferences:
            flow_index = inf_entry.flow_info.get('flow_index', '')
            if not flow_index:
                continue
            
            # Check if this inference uses the concept
            is_dependent = False
            
            # Check value concepts
            if hasattr(inf_entry, 'value_concepts') and inf_entry.value_concepts:
                for vc in inf_entry.value_concepts:
                    vc_name = vc.concept_name if hasattr(vc, 'concept_name') else str(vc)
                    if vc_name == concept_name:
                        is_dependent = True
                        break
            
            # Check context concepts
            if not is_dependent and hasattr(inf_entry, 'context_concepts') and inf_entry.context_concepts:
                for cc in inf_entry.context_concepts:
                    cc_name = cc.concept_name if hasattr(cc, 'concept_name') else str(cc)
                    if cc_name == concept_name:
                        is_dependent = True
                        break
            
            if is_dependent:
                dependents.append(flow_index)
        
        return dependents
    
    def find_descendants(
        self,
        inference_repo: Any,
        concept_repo: Any,
        flow_index: str
    ) -> List[str]:
        """
        Find all nodes that are downstream from a given flow_index.
        
        This traverses the inference graph to find all nodes that directly or
        indirectly depend on the specified node.
        """
        if inference_repo is None or concept_repo is None:
            return []
        
        # Build a mapping from flow_index to concept_name
        flow_to_concept: Dict[str, str] = {}
        for inf_entry in inference_repo.inferences:
            fi = inf_entry.flow_info.get('flow_index', '')
            if fi and hasattr(inf_entry, 'concept_to_infer'):
                flow_to_concept[fi] = inf_entry.concept_to_infer.concept_name
        
        # Get the concept name for the starting flow_index
        start_concept = flow_to_concept.get(flow_index)
        if not start_concept:
            return []
        
        # BFS to find all descendants
        descendants = []
        visited = set()
        queue = [start_concept]
        
        while queue:
            current_concept = queue.pop(0)
            if current_concept in visited:
                continue
            visited.add(current_concept)
            
            # Find inferences that use this concept
            dependents = self.find_dependents(inference_repo, current_concept)
            for dep_fi in dependents:
                if dep_fi not in visited and dep_fi != flow_index:
                    descendants.append(dep_fi)
                    # Get the concept for this inference and add to queue
                    dep_concept = flow_to_concept.get(dep_fi)
                    if dep_concept and dep_concept not in visited:
                        queue.append(dep_concept)
        
        return descendants
    
    def override_value(
        self,
        concept_repo: Any,
        inference_repo: Any,
        concept_name: str,
        new_value: Any,
    ) -> Dict[str, Any]:
        """
        Override a concept's reference value.
        
        Args:
            concept_repo: The concept repository
            inference_repo: The inference repository
            concept_name: The name of the concept to override
            new_value: The new value to set
            
        Returns:
            Dict with concept_name and list of stale_nodes
            
        Raises:
            ValueError: If concept not found
        """
        # Get concept from repo
        concept_entry = concept_repo.get_concept(concept_name)
        if concept_entry is None:
            raise ValueError(f"Concept '{concept_name}' not found in repository")
        
        concept = concept_entry.concept if hasattr(concept_entry, 'concept') else None
        if concept is None:
            raise ValueError(f"Could not access concept object for '{concept_name}'")
        
        # Get axis names from existing reference if present
        axis_names = None
        if hasattr(concept, 'reference') and concept.reference is not None:
            if hasattr(concept.reference, 'axes') and concept.reference.axes:
                axis_names = concept.reference.axes.copy() if isinstance(concept.reference.axes, list) else list(concept.reference.axes)
        
        # Use the concept_repo.add_reference() method which handles Reference creation properly
        concept_repo.add_reference(concept_name, new_value, axis_names=axis_names)
        
        # Find dependent inferences (nodes that use this concept as input)
        stale_nodes = self.find_dependents(inference_repo, concept_name)
        
        logger.info(f"Overridden value for '{concept_name}', {len(stale_nodes)} nodes marked stale")
        
        return {
            "concept_name": concept_name,
            "stale_nodes": stale_nodes,
        }


# Global value service instance
value_service = ValueService()


