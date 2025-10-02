from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional, Union
import uuid


class ConceptEntrySchema(BaseModel):
    """Pydantic schema for ConceptEntry."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    concept_name: str
    concept_type: Literal["ground", "intermediate", "function", "final"]
    description: Optional[str] = None
    reference_data: Optional[Any] = None  # Can be a list, dict, or scalar
    reference_axis_names: Optional[List[str]] = None
    is_final_concept: bool = False


class InferenceEntrySchema(BaseModel):
    """Pydantic schema for InferenceEntry."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    concept_to_infer: str
    function_concept: str
    value_concepts: List[str]
    context_concepts: Optional[List[str]] = None
    flow_info: Optional[Dict[str, Any]] = None
    working_interpretation: Optional[Dict[str, Any]] = None
    inference_type: Literal["default", "conditional"] = "default"
    condition: Optional[str] = None


class RepositorySetSchema(BaseModel):
    """Pydantic schema for a collection of ConceptEntry and InferenceEntry objects."""
    name: str
    concepts: List[str]  # List of concept IDs
    inferences: List[str]  # List of inference IDs


class RepositorySetData(BaseModel):
    """Pydantic schema for a collection of ConceptEntry and InferenceEntry objects."""
    name: str
    concepts: List[ConceptEntrySchema]
    inferences: List[InferenceEntrySchema]


class ConceptFileSchema(BaseModel):
    concepts: List[ConceptEntrySchema]


class InferenceFileSchema(BaseModel):
    inferences: List[InferenceEntrySchema]


class RepositorySetListResponse(BaseModel):
    """Schema for listing available repository sets."""
    repository_set_names: List[str]


class RepositorySetResponse(BaseModel):
    """Schema for retrieving a single repository set."""
    repository_set: RepositorySetSchema


class RepositorySetSaveResponse(BaseModel):
    """Schema for a response after saving a repository set."""
    status: str = "success"
    name: str


class RunRepositorySetRequest(BaseModel):
    """Schema for requesting to run a repository set."""
    repository_set_name: str


class RunResponse(BaseModel):
    """Schema for a run response, including log file name."""
    status: str
    log_file: str


class LogContentResponse(BaseModel):
    """Schema for log content response."""
    content: str


class ErrorResponse(BaseModel):
    """Generic error response schema."""
    detail: str
