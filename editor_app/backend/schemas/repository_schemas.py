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