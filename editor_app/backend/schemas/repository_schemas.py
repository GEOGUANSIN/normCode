from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from .concept_schemas import ConceptEntrySchema
from .inference_schemas import InferenceEntrySchema


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


class AddConceptFromGlobalRequest(BaseModel):
    """Schema for adding a concept from global to a repository."""
    global_concept_id: str
    reference_data: Optional[Any] = None
    reference_axis_names: Optional[List[str]] = None
    is_ground_concept: bool = False
    is_final_concept: bool = False
    is_invariant: bool = False


class AddInferenceFromGlobalRequest(BaseModel):
    """Schema for adding an inference from global to a repository."""
    global_inference_id: str
    flow_info: Optional[Dict[str, Any]] = None
    working_interpretation: Optional[Dict[str, Any]] = None
    start_without_value: bool = False
    start_without_value_only_once: bool = False
    start_without_function: bool = False
    start_without_function_only_once: bool = False
    start_with_support_reference_only: bool = False


# Flow-related schemas
class FlowNodeSchema(BaseModel):
    """Schema for a flow node."""
    id: str
    type: str  # 'inference' or 'concept'
    position: Dict[str, float]
    data: Dict[str, Any]


class FlowEdgeSchema(BaseModel):
    """Schema for a flow edge."""
    id: str
    source: str
    target: str
    label: Optional[str] = None
    type: Optional[str] = None


class FlowDataSchema(BaseModel):
    """Schema for flow data."""
    nodes: List[FlowNodeSchema]
    edges: List[FlowEdgeSchema]