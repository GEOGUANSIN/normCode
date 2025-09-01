import uuid
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from infra._core import Concept, Reference, Inference

# --- Data Classes ---
@dataclass
class ConceptEntry:
    id: str
    concept_name: str
    type: str
    description: Optional[str] = None
    is_ground_concept: bool = False
    is_final_concept: bool = False
    concept: Optional[Concept] = field(default=None, repr=False)

@dataclass
class InferenceEntry:
    id: str
    inference_sequence: str
    concept_to_infer: ConceptEntry
    flow_info: Dict[str, any]
    function_concept: Optional[ConceptEntry] = None
    value_concepts: List[ConceptEntry] = field(default_factory=list)
    context_concepts: List[ConceptEntry] = field(default_factory=list)
    start_without_value: bool = False
    start_without_value_only_once: bool = False
    start_without_function: bool = False
    start_without_function_only_once: bool = False
    inference: Optional['Inference'] = field(default=None, repr=False)
    working_interpretation: Optional[Dict[str, any]] = field(default=None, repr=False)



# --- Repositories (Data Access) ---

class ConceptRepo:
    def __init__(self, concepts: List[ConceptEntry]):
        self._concept_map = {c.concept_name: c for c in concepts}
        # Import Concept here to ensure it's available
        try:
            from infra import Concept
            for entry in concepts:
                entry.concept = Concept(entry.concept_name)
        except ImportError:
            logging.warning("Concept class not available during initialization")
            for entry in concepts:
                entry.concept = None
            
    def add_reference(self, concept_name: str, data: Any, axis_names: Optional[List[str]] = None):
        """Adds a Reference object to a concept."""
        try:
            from infra import Reference
        except ImportError:
            logging.error("Reference class not available")
            return
            
        concept_entry = self.get_concept(concept_name)
        if concept_entry and concept_entry.concept:
            # from_data expects a list.
            if not isinstance(data, list):
                data = [data]
            concept_entry.concept.reference = Reference.from_data(data, axis_names=axis_names)
            logging.info(f"Added reference to concept '{concept_name}'.")
        else:
            logging.warning(f"Could not find concept '{concept_name}' to add reference.")

    def get_concept(self, name: str) -> Optional[ConceptEntry]:
        return self._concept_map.get(name)

    def get_all_concepts(self) -> List[ConceptEntry]:
        return list(self._concept_map.values())

class InferenceRepo:
    def __init__(self, inferences: List[InferenceEntry]):
        self.inferences = inferences
        self._map_by_flow = {inf.flow_info['flow_index']: inf for inf in inferences}
        
        # Initialize Inference objects for each entry
        try:
            from infra import Inference
            for entry in inferences:
                if entry.inference is None:
                    entry.inference = Inference(
                        entry.inference_sequence,
                        entry.concept_to_infer.concept,
                        entry.function_concept.concept if entry.function_concept else None,
                        [vc.concept for vc in entry.value_concepts],
                        context_concepts=[cc.concept for cc in entry.context_concepts]
                    )
        except ImportError:
            logging.warning("Inference class not available during initialization")
            for entry in inferences:
                entry.inference = None
    
    def get_all_inferences(self) -> List[InferenceEntry]:
        return self.inferences
    
    def get_inference_by_flow_index(self, idx: str) -> Optional[InferenceEntry]:
        return self._map_by_flow.get(idx)


