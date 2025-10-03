from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import uuid
from enum import Enum


class InferenceSequenceEnum(str, Enum):
    SIMPLE = "simple"
    IMPERATIVE = "imperative"
    JUDGEMENT = "judgement"
    GROUPING = "grouping"
    ASSIGNING = "assigning"
    QUANTIFYING = "quantifying"
    TIMING = "timing"


class InferenceEntrySchema(BaseModel):
    """Pydantic schema for InferenceEntry."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    inference_sequence: InferenceSequenceEnum
    concept_to_infer: str
    function_concept: str
    value_concepts: List[str]
    context_concepts: Optional[List[str]] = None
    flow_info: Optional[Dict[str, Any]] = None
    working_interpretation: Optional[Dict[str, Any]] = None
    start_without_value: bool = False
    start_without_value_only_once: bool = False
    start_without_function: bool = False
    start_without_function_only_once: bool = False
    start_with_support_reference_only: bool = False


class InferenceFileSchema(BaseModel):
    inferences: List[InferenceEntrySchema]
