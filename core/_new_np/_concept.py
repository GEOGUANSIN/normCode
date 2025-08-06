from _reference import Reference
from typing import Optional
import uuid

# Type classification
TYPE_CLASS_SYNTACTICAL = "syntactical"
TYPE_CLASS_SEMANTICAL = "semantical"
TYPE_CLASS_INFERENTIAL = "inferential"

# Concept type constants with type classification
CONCEPT_TYPES = {
    # Core inference operators (INFERENTIAL)
    "<=": {"description": "functional", "type_class": TYPE_CLASS_INFERENTIAL},
    "<-": {"description": "value", "type_class": TYPE_CLASS_INFERENTIAL},
    
    # Question markers (SYNTACTICAL)
    "$what?": {"description": "what", "type_class": TYPE_CLASS_SYNTACTICAL},
    "$how?": {"description": "how", "type_class": TYPE_CLASS_SYNTACTICAL},
    "$when?": {"description": "when", "type_class": TYPE_CLASS_SYNTACTICAL},
    
    # Assignment operators (SYNTACTICAL)
    "$=": {"description": "assignment", "type_class": TYPE_CLASS_SYNTACTICAL},
    "$::": {"description": "nominalization", "type_class": TYPE_CLASS_SYNTACTICAL},
    "$.": {"description": "specification", "type_class": TYPE_CLASS_SYNTACTICAL},
    "$%": {"description": "abstraction", "type_class": TYPE_CLASS_SYNTACTICAL},
    
    # Sequencing operators (SYNTACTICAL)
    "@by": {"description": "by", "type_class": TYPE_CLASS_SYNTACTICAL},
    "@if": {"description": "if", "type_class": TYPE_CLASS_SYNTACTICAL},
    "@onlyIf": {"description": "onlyIf", "type_class": TYPE_CLASS_SYNTACTICAL},
    "@ifOnlyIf": {"description": "ifOnlyIf", "type_class": TYPE_CLASS_SYNTACTICAL},
    "@after": {"description": "after", "type_class": TYPE_CLASS_SYNTACTICAL},
    "@before": {"description": "before", "type_class": TYPE_CLASS_SYNTACTICAL},
    "@with": {"description": "with", "type_class": TYPE_CLASS_SYNTACTICAL},
    "@while": {"description": "while", "type_class": TYPE_CLASS_SYNTACTICAL},
    "@until": {"description": "until", "type_class": TYPE_CLASS_SYNTACTICAL},
    "@afterstep": {"description": "afterstep", "type_class": TYPE_CLASS_SYNTACTICAL},
    
    # Grouping operators (SYNTACTICAL)
    "&in": {"description": "in", "type_class": TYPE_CLASS_SYNTACTICAL},
    "&across": {"description": "across", "type_class": TYPE_CLASS_SYNTACTICAL},
    "&set": {"description": "set", "type_class": TYPE_CLASS_SYNTACTICAL},
    "&pair": {"description": "pair", "type_class": TYPE_CLASS_SYNTACTICAL},
    
    # Quantification operators (SYNTACTICAL)
    "*every": {"description": "every", "type_class": TYPE_CLASS_SYNTACTICAL},
    "*some": {"description": "some", "type_class": TYPE_CLASS_SYNTACTICAL},
    "*count": {"description": "count", "type_class": TYPE_CLASS_SYNTACTICAL},
    
    # Object and concept types (SEMANTICAL)
    "{}": {"description": "object", "type_class": TYPE_CLASS_SEMANTICAL},
    "::": {"description": "imperative", "type_class": TYPE_CLASS_SEMANTICAL},
    "<>": {"description": "judgement", "type_class": TYPE_CLASS_SEMANTICAL},
    "<{}>": {"description": "functional_judgement", "type_class": TYPE_CLASS_SEMANTICAL},
    "::({})": {"description": "functional_imperative", "type_class": TYPE_CLASS_SEMANTICAL},
    "[]": {"description": "relation", "type_class": TYPE_CLASS_SEMANTICAL},
    ":S:": {"description": "subject", "type_class": TYPE_CLASS_SEMANTICAL},
    
    # Input/Output concepts (SYNTACTICAL)
    ":>:": {"description": "input", "type_class": TYPE_CLASS_SYNTACTICAL},
    ":<:": {"description": "output", "type_class": TYPE_CLASS_SYNTACTICAL},
    
    # Template and placeholder types (SYNTACTICAL)
    "{}?": {"description": "object_placeholder", "type_class": TYPE_CLASS_SYNTACTICAL},
    "<:_>": {"description": "position_reference", "type_class": TYPE_CLASS_SYNTACTICAL},
}


class Concept:
    def __init__(self, name, context="", axis_name: Optional[str] = None, reference: Optional[Reference] = None, type="{}"):
        if type not in CONCEPT_TYPES:
            raise ValueError(f"Invalid concept type. Must be one of: {list(CONCEPT_TYPES.keys())}")
            
        self.name = name
        self.type = type
        self.context = context
        self.axis_name = axis_name if axis_name else name
        self.reference: Optional[Reference] = reference
        self.id = str(uuid.uuid4())  # Generate unique identification number
    
    def is_syntactical(self) -> bool:
        return CONCEPT_TYPES[self.type]["type_class"] == TYPE_CLASS_SYNTACTICAL
    
    def is_semantical(self) -> bool:
        return CONCEPT_TYPES[self.type]["type_class"] == TYPE_CLASS_SEMANTICAL
    
    def get_type_class(self) -> str:
        return CONCEPT_TYPES[self.type]["type_class"]
    
    def comprehension(self) -> dict:
        """Return all concept attributes in a dictionary format"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "context": self.context,
            "axis_name": self.axis_name,
            "type_description": CONCEPT_TYPES[self.type]["description"],
            "type_class": CONCEPT_TYPES[self.type]["type_class"],
        }
    
    # Dictionary-like access for backward compatibility
    def __getitem__(self, key):
        if key == "id":
            return self.id
        elif key == "name":
            return self.name
        elif key == "type":
            return self.type
        elif key == "context":
            return self.context
        elif key == "axis_name":
            return self.axis_name
        elif key == "type_description":
            return CONCEPT_TYPES[self.type]["description"]
        elif key == "type_class":
            return CONCEPT_TYPES[self.type]["type_class"]
        else:
            raise KeyError(f"Key '{key}' not found")
    
    def __setitem__(self, key, value):
        if key == "id":
            self.id = value
        elif key == "name":
            self.name = value
        elif key == "type":
            if value not in CONCEPT_TYPES:
                raise ValueError(f"Invalid concept type. Must be one of: {list(CONCEPT_TYPES.keys())}")
            self.type = value
        elif key == "context":
            self.context = value
        elif key == "axis_name":
            self.axis_name = value
        else:
            raise KeyError(f"Key '{key}' not found")


if __name__ == "__main__":
    def test_concept_simplified():
        print("=== Testing Simplified Concept ===\n")
        
        # Test 1: Basic initialization
        print("1. Basic initialization:")
        concept = Concept("test_concept", "test context", type="{}")
        print(f"   id: {concept.id}")
        print(f"   name: {concept.name}")
        print(f"   type: {concept.type}")
        print(f"   context: {concept.context}")
        print()
        
        # Test 2: Direct attribute access
        print("2. Direct attribute access:")
        concept.name = "new_name"
        concept.type = "::"
        concept.context = "new context"
        print(f"   id: {concept.id}")
        print(f"   name: {concept.name}")
        print(f"   type: {concept.type}")
        print(f"   context: {concept.context}")
        print()
        
        # Test 3: Dictionary access
        print("3. Dictionary access:")
        concept["name"] = "dict_name"
        concept["type"] = "<>"
        concept["context"] = "dict_context"
        print(f"   id: {concept['id']}")
        print(f"   name: {concept.name}")
        print(f"   type: {concept.type}")
        print(f"   context: {concept.context}")
        print()
        
        # Test 4: Type validation
        print("4. Type validation:")
        try:
            concept.type = "invalid_type"
            print("   ERROR: Should have raised ValueError")
        except ValueError as e:
            print(f"   ✓ Correctly raised ValueError: {e}")
        print()
        
        # Test 5: Type class methods
        print("5. Type class methods:")
        concept.type = "{}"  # semantical
        print(f"   Type '{concept.type}':")
        print(f"   is_syntactical: {concept.is_syntactical()}")
        print(f"   is_semantical: {concept.is_semantical()}")
        print(f"   get_type_class: {concept.get_type_class()}")
        print()
        
        concept.type = "<="  # inferential
        print(f"   Type '{concept.type}':")
        print(f"   is_syntactical: {concept.is_syntactical()}")
        print(f"   is_semantical: {concept.is_semantical()}")
        print(f"   get_type_class: {concept.get_type_class()}")
        print()
        
        # Test 6: Comprehension method
        print("6. Comprehension method:")
        comp = concept.comprehension()
        print(f"   comprehension(): {comp}")
        print()
        
        # Test 7: Unique ID generation
        print("7. Unique ID generation:")
        concept1 = Concept("concept1", type="{}")
        concept2 = Concept("concept2", type="::")
        concept3 = Concept("concept3", type="<>")
        print(f"   concept1 id: {concept1.id}")
        print(f"   concept2 id: {concept2.id}")
        print(f"   concept3 id: {concept3.id}")
        print(f"   IDs are unique: {concept1.id != concept2.id != concept3.id}")
        print()

    test_concept_simplified()


