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
    context: str = ""  # Context from Concept class
    axis_name: Optional[str] = None  # Axis name from Concept class
    natural_name: Optional[str] = None  # Natural name from Concept class
    description: Optional[str] = None
    is_ground_concept: bool = False
    is_final_concept: bool = False
    is_invariant: bool = False  # New attribute: prevents reference reset during quantifying loops
    reference_data: Optional[Any] = None
    reference_axis_names: Optional[List[str]] = None
    concept: Optional[Concept] = field(default=None, repr=False)
    
    def to_concept(self) -> 'Concept':
        """Convert this ConceptEntry to a Concept object with all attributes."""
        from infra import Concept
        return Concept(
            name=self.concept_name,
            context=self.context,
            axis_name=self.axis_name,
            natural_name=self.natural_name,
            type=self.type
        )
    
    def update_from_concept(self, concept: 'Concept'):
        """Update this ConceptEntry with attributes from a Concept object."""
        self.concept_name = concept.name
        self.type = concept.type
        self.context = concept.context
        self.axis_name = concept.axis_name
        self.natural_name = concept.natural_name
        if concept.reference:
            self.reference_data = concept.reference.data if hasattr(concept.reference, 'data') else None

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
    start_with_support_reference_only: bool = False
    inference: Optional['Inference'] = field(default=None, repr=False)
    working_interpretation: Optional[Dict[str, any]] = field(default=None, repr=False)



# --- Repositories (Data Access) ---

class ConceptRepo:
    def __init__(self, concepts: List[ConceptEntry]):
        self._concept_map = {c.concept_name: c for c in concepts}
        # Import Concept here to ensure it's available
        try:
            from infra import Concept, Reference
            for entry in concepts:
                # Initialize Concept with all available attributes from ConceptEntry
                entry.concept = Concept(
                    name=entry.concept_name,
                    context=entry.context,
                    axis_name=entry.axis_name,
                    natural_name=entry.natural_name,
                    type=entry.type
                )
                if entry.reference_data is not None:
                    data = entry.reference_data
                    if not isinstance(data, list):
                        data = [data]
                    entry.concept.reference = Reference.from_data(data, axis_names=entry.reference_axis_names)
                    logging.info(f"Added initial reference to concept '{entry.concept_name}'.")
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
            # Update the ConceptEntry with the new reference data
            concept_entry.reference_data = data
            concept_entry.reference_axis_names = axis_names
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


