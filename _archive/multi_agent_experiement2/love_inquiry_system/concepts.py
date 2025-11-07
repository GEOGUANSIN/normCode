from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional

@dataclass
class NormCodeConcept:
    """
    Represents a single concept (a line and its children) in a NormCode plan.
    This dataclass holds the parsed information and the execution state.
    """
    name: str
    concept_type: str  # e.g., 'Object', 'Statement', 'Input', 'Imperative'
    raw_line: str
    indentation: int
    
    # Annotations
    source_text: str = ""  # from ...:
    question: str = ""     # from ?:
    description: str = ""  # from /:
    
    # Functional and Value parts
    operator: Optional[str] = None # The syntactical operator, e.g., '$.', '@if'
    operator_args: List[str] = field(default_factory=list)
    is_functional_concept: bool = False # Is this a '<=' line?
    is_value_concept: bool = False # Is this a '<-' line?

    # Execution State
    value: Any = None      # The actual data/result after execution
    
    # Tree Structure
    children: List[NormCodeConcept] = field(default_factory=list)
    parent: Optional[NormCodeConcept] = field(default=None, repr=False)

    # Reference from the guide for multi-dimensional data
    reference_data: Any = None
    reference_axis_names: List[str] = field(default_factory=list)

    def __str__(self):
        return f"{' ' * self.indentation}{self.raw_line}"

    def display(self, level=0):
        """Prints a representation of the concept tree."""
        indent = "    " * level
        print(f"{indent}- {self.name} ({self.concept_type}) | Value: {self.value}")
        for child in self.children:
            child.display(level + 1)
