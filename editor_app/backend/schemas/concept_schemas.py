from pydantic import BaseModel, Field
from typing import Any, List, Literal, Optional
import uuid

# Concept type literals from infra._core._concept
ConceptTypeLiterals = Literal[
    "<=", "<-", "$what?", "$how?", "$when?", "$=", "$::", "$.", "$%", "$+",
    "@by", "@if", "@if!", "@onlyIf", "@ifOnlyIf", "@after", "@before", "@with",
    "@while", "@until", "@afterstep", "&in", "&across", "&set", "&pair",
    "*every", "*some", "*count", "{}", "::", "<>", "<{}>", "::({})", "[]",
    ":S:", ":>:", ":<:", "{}?", "<:_>"
]


class ConceptEntrySchema(BaseModel):
    """Pydantic schema for ConceptEntry."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    concept_name: str
    type: ConceptTypeLiterals
    context: Optional[str] = None
    axis_name: Optional[str] = None
    natural_name: Optional[str] = None
    description: Optional[str] = None
    is_ground_concept: bool = False
    is_final_concept: bool = False
    is_invariant: bool = False
    reference_data: Optional[Any] = None  # Can be a list, dict, or scalar
    reference_axis_names: Optional[List[str]] = None


class ConceptFileSchema(BaseModel):
    concepts: List[ConceptEntrySchema]
