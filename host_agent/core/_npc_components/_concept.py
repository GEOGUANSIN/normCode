from ._reference import Reference
from typing import Optional

# Concept type constants
CONCEPT_TYPE_CLASSIFICATION = "?"
CONCEPT_TYPE_JUDGEMENT = "<>"
CONCEPT_TYPE_RELATION = "[]"
CONCEPT_TYPE_OBJECT = "{}"
CONCEPT_TYPE_SENTENCE = "^"
CONCEPT_TYPE_ASSIGNMENT = "@"
CONCEPT_TYPE_INPUT = ":>:"
CONCEPT_TYPE_OUTPUT = ":<:"

CONCEPT_TYPES = {
    CONCEPT_TYPE_CLASSIFICATION: "classification",
    CONCEPT_TYPE_JUDGEMENT: "judgement",
    CONCEPT_TYPE_RELATION: "relation",
    CONCEPT_TYPE_OBJECT: "object",
    CONCEPT_TYPE_SENTENCE: "sentence",
    CONCEPT_TYPE_ASSIGNMENT: "assignment",
    CONCEPT_TYPE_INPUT: "input",
    CONCEPT_TYPE_OUTPUT: "output"
}

class Concept:
    def __init__(self, name, context="", reference=None, type=CONCEPT_TYPE_OBJECT):
        if type is not None and type not in CONCEPT_TYPES:
            raise ValueError(f"Invalid concept type. Must be one of: {list(CONCEPT_TYPES.keys())}")
            
        # Comprehension attribute (required)
        self.comprehension = {
            "name": name,
            "context": context,
            "type": type,
            "type_description": CONCEPT_TYPES.get(type, None)
        }

        # Reference attribute (optional)
        self.reference: Reference = reference



