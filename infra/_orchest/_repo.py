import uuid
import logging
import hashlib
import json
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
    flow_indices: Optional[List[str]] = None  # Optional flow indices (e.g., ["1.6", "1.7.2", "1.8.2"]) - concept may appear multiple times in flow
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
    
    def get_signature(self) -> str:
        """
        Generates a deterministic hash signature for this concept's definition.
        Used to detect if the logic/definition has changed between checkpoint and new repo.
        """
        # Hash the definition fields that affect the concept's meaning
        signature_data = {
            "concept_name": self.concept_name,
            "type": self.type,
            "context": self.context,
            "axis_name": self.axis_name,
            "natural_name": self.natural_name,
            "is_ground_concept": self.is_ground_concept,
            "is_invariant": self.is_invariant,
            "flow_indices": self.flow_indices
        }
        # Serialize to JSON string for hashing (sorted keys for determinism)
        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.sha256(signature_str.encode('utf-8')).hexdigest()

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
    start_without_support_reference_only_once: bool = False
    inference: Optional['Inference'] = field(default=None, repr=False)
    working_interpretation: Optional[Dict[str, any]] = field(default=None, repr=False)
    
    def get_signature(self) -> str:
        """
        Generates a deterministic hash signature for this inference's definition.
        Used to detect if the logic/definition has changed between checkpoint and new repo.
        """
        # Hash the definition fields that affect the inference's behavior
        signature_data = {
            "inference_sequence": self.inference_sequence,
            "concept_to_infer": self.concept_to_infer.concept_name if self.concept_to_infer else None,
            "function_concept": self.function_concept.concept_name if self.function_concept else None,
            "value_concepts": sorted([vc.concept_name for vc in self.value_concepts]),
            "context_concepts": sorted([cc.concept_name for cc in self.context_concepts]),
            "flow_index": self.flow_info.get('flow_index') if self.flow_info else None,
            "working_interpretation": self.working_interpretation if self.working_interpretation else {}
        }
        # Serialize to JSON string for hashing (sorted keys for determinism)
        signature_str = json.dumps(signature_data, sort_keys=True, default=str)
        return hashlib.sha256(signature_str.encode('utf-8')).hexdigest()



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

    @classmethod
    def from_json_list(cls, json_list: List[Dict[str, Any]]) -> 'ConceptRepo':
        """Creates a ConceptRepo from a list of JSON objects."""
        concept_entries = []
        for item in json_list:
            # Create ConceptEntry from dictionary, ensuring all fields are handled
            entry = ConceptEntry(
                id=item.get('id', str(uuid.uuid4())),
                concept_name=item.get('concept_name'),
                type=item.get('type'),
                context=item.get('context', ''),
                axis_name=item.get('axis_name'),
                natural_name=item.get('natural_name'),
                description=item.get('description'),
                is_ground_concept=item.get('is_ground_concept', False),
                is_final_concept=item.get('is_final_concept', False),
                is_invariant=item.get('is_invariant', False),
                reference_data=item.get('reference_data'),
                reference_axis_names=item.get('reference_axis_names'),
                flow_indices=item.get('flow_indices')
            )
            concept_entries.append(entry)
        return cls(concept_entries)

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

    @classmethod
    def from_json_list(cls, json_list: List[Dict[str, Any]], concept_repo: ConceptRepo) -> 'InferenceRepo':
        """Creates an InferenceRepo from a list of JSON objects, linking to an existing ConceptRepo."""
        inference_entries = []
        for item in json_list:
            # Resolve concept names to ConceptEntry objects
            concept_to_infer = concept_repo.get_concept(item['concept_to_infer'])
            if not concept_to_infer:
                raise ValueError(f"Concept '{item['concept_to_infer']}' not found in ConceptRepo.")

            function_concept = concept_repo.get_concept(item['function_concept']) if item.get('function_concept') else None
            if item.get('function_concept') and not function_concept:
                raise ValueError(f"Function concept '{item['function_concept']}' not found in ConceptRepo.")

            value_concepts = []
            for name in item.get('value_concepts', []):
                concept = concept_repo.get_concept(name)
                if not concept:
                    raise ValueError(f"Value concept '{name}' not found in ConceptRepo.")
                value_concepts.append(concept)
            
            context_concepts = []
            for name in item.get('context_concepts', []):
                concept = concept_repo.get_concept(name)
                if not concept:
                    raise ValueError(f"Context concept '{name}' not found in ConceptRepo.")
                context_concepts.append(concept)

            # Create the InferenceEntry
            entry = InferenceEntry(
                id=str(uuid.uuid4()),
                inference_sequence=item['inference_sequence'],
                concept_to_infer=concept_to_infer,
                flow_info=item.get('flow_info', {}),
                function_concept=function_concept,
                value_concepts=value_concepts,
                context_concepts=context_concepts,
                start_without_value=item.get('start_without_value', False),
                start_without_value_only_once=item.get('start_without_value_only_once', False),
                start_without_function=item.get('start_without_function', False),
                start_without_function_only_once=item.get('start_without_function_only_once', False),
                start_with_support_reference_only=item.get('start_with_support_reference_only', False),
                start_without_support_reference_only_once=item.get('start_without_support_reference_only_once', False),
                working_interpretation=item.get('working_interpretation')
            )
            inference_entries.append(entry)
        return cls(inference_entries)


