import json
from pathlib import Path
from typing import Any, Dict, List

from infra._states import (
    ModelEnvSpecLite,
    ModelSequenceSpecLite,
    ModelStepSpecLite,
    ToolSpecLite,
    AffordanceSpecLite,
    MetaValue,
)

# --- Constants ---
PARADIGMS_DIR = Path(__file__).parent

# --- Custom Deserialization Hook ---

def _paradigm_object_hook(d: Dict[str, Any]) -> Any:
    """
    A custom object hook for json.load to reconstruct specific object types
    like MetaValue from a dictionary representation.
    """
    if "__type__" in d:
        if d["__type__"] == "MetaValue":
            return MetaValue(key=d["key"])
    return d

# --- Helper Functions for Reconstruction ---

def _build_affordance_spec(data: Dict[str, Any]) -> AffordanceSpecLite:
    return AffordanceSpecLite(affordance_name=data['affordance_name'], call_code=data['call_code'])

def _build_tool_spec(data: Dict[str, Any]) -> ToolSpecLite:
    return ToolSpecLite(
        tool_name=data['tool_name'],
        affordances=[_build_affordance_spec(aff) for aff in data['affordances']]
    )

def _build_env_spec(data: Dict[str, Any]) -> ModelEnvSpecLite:
    return ModelEnvSpecLite(
        tools=[_build_tool_spec(tool) for tool in data['tools']]
    )

def _build_step_spec(data: Dict[str, Any]) -> ModelStepSpecLite:
    return ModelStepSpecLite(
        step_index=data['step_index'],
        affordance=data['affordance'],
        params=data['params'],
        result_key=data['result_key']
    )

def _build_sequence_spec(data: Dict[str, Any], env_spec: ModelEnvSpecLite) -> ModelSequenceSpecLite:
    return ModelSequenceSpecLite(
        env=env_spec,
        steps=[_build_step_spec(step) for step in data['steps']]
    )

# --- Main Paradigm Class ---

class Paradigm:
    """
    Loads and reconstructs a full composition paradigm (environment and sequence specs)
    from a JSON file.
    """
    def __init__(self, env_spec: ModelEnvSpecLite, sequence_spec: ModelSequenceSpecLite, metadata: Dict[str, Any] | None = None):
        self.env_spec = env_spec
        self.sequence_spec = sequence_spec
        self.metadata = metadata or {}

    @classmethod
    def load(cls, paradigm_name: str) -> 'Paradigm':
        """
        Loads a paradigm by its name from the corresponding JSON file in this directory.

        Args:
            paradigm_name (str): The name of the paradigm (e.g., 'json_output').

        Returns:
            Paradigm: An instance containing the reconstructed env and sequence specs.
        """
        paradigm_file = PARADIGMS_DIR / f"{paradigm_name}.json"
        if not paradigm_file.exists():
            raise FileNotFoundError(f"Paradigm '{paradigm_name}' not found at {paradigm_file}")

        with open(paradigm_file, 'r', encoding='utf-8') as f:
            raw_spec = json.load(f, object_hook=_paradigm_object_hook)

        env_spec_data = raw_spec['env_spec']
        sequence_spec_data = raw_spec['sequence_spec']
        metadata_data = raw_spec.get('metadata', {})

        # Reconstruct the spec objects from the loaded data
        env_spec = _build_env_spec(env_spec_data)
        sequence_spec = _build_sequence_spec(sequence_spec_data, env_spec)
        
        return cls(env_spec, sequence_spec, metadata_data)
