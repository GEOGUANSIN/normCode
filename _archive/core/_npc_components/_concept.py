# from ._reference import Reference
from typing import Optional

class Reference:
    def __init__(self, name, type, context):
        self.name = name
        self.type = type
        self.context = context


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
    def __init__(self, name, context="", reference=None, type="{}"):
        if type not in CONCEPT_TYPES:
            raise ValueError(f"Invalid concept type. Must be one of: {list(CONCEPT_TYPES.keys())}")
            
        self._name = name      # Private storage for the name
        self._type = type      # Private storage for the type
        self._context = context # Private storage for the context
        self.reference: Reference = reference
    
    # Name properties
    @property
    def contribute_name(self):
        """Get the contribute name (always same as comprehension name)"""
        return self._name
    
    @contribute_name.setter
    def contribute_name(self, value):
        """Set the contribute name (updates both contribute_name and comprehension name)"""
        self._name = value
    
    @property
    def comprehension_name(self):
        """Get the name from comprehension (always same as contribute_name)"""
        return self._name
    
    @comprehension_name.setter
    def comprehension_name(self, value):
        """Set the name in comprehension (updates both contribute_name and comprehension name)"""
        self._name = value
    
    # Type properties
    @property
    def contribute_type(self):
        """Get the contribute type (always same as comprehension type)"""
        return self._type
    
    @contribute_type.setter
    def contribute_type(self, value):
        """Set the contribute type (updates both contribute_type and comprehension type)"""
        if value not in CONCEPT_TYPES:
            raise ValueError(f"Invalid concept type. Must be one of: {list(CONCEPT_TYPES.keys())}")
        self._type = value
    
    @property
    def comprehension_type(self):
        """Get the type from comprehension (always same as contribute_type)"""
        return self._type
    
    @comprehension_type.setter
    def comprehension_type(self, value):
        """Set the type in comprehension (updates both contribute_type and comprehension type)"""
        if value not in CONCEPT_TYPES:
            raise ValueError(f"Invalid concept type. Must be one of: {list(CONCEPT_TYPES.keys())}")
        self._type = value
    
    # Context properties
    @property
    def contribute_context(self):
        """Get the contribute context (always same as comprehension context)"""
        return self._context
    
    @contribute_context.setter
    def contribute_context(self, value):
        """Set the contribute context (updates both contribute_context and comprehension context)"""
        self._context = value
    
    @property
    def comprehension_context(self):
        """Get the context from comprehension (always same as contribute_context)"""
        return self._context
    
    @comprehension_context.setter
    def comprehension_context(self, value):
        """Set the context in comprehension (updates both contribute_context and comprehension context)"""
        self._context = value
    
    def is_syntactical(self) -> bool:
        return CONCEPT_TYPES[self._type]["type_class"] == TYPE_CLASS_SYNTACTICAL
    
    def is_semantical(self) -> bool:
        return CONCEPT_TYPES[self._type]["type_class"] == TYPE_CLASS_SEMANTICAL
    
    def get_type_class(self) -> str:
        return CONCEPT_TYPES[self._type]["type_class"]
    
    def comprehension(self) -> dict:
        """Return all concept attributes in a dictionary format"""
        return {
            "name": self._name,
            "type": self._type,
            "context": self._context,
            "type_description": CONCEPT_TYPES[self._type]["description"],
            "type_class": CONCEPT_TYPES[self._type]["type_class"],
        }
    
    # For backward compatibility - accessing comprehension directly
    def __getitem__(self, key):
        if key == "name":
            return self._name
        elif key == "type":
            return self._type
        elif key == "context":
            return self._context
        elif key == "type_description":
            return CONCEPT_TYPES[self._type]["description"]
        elif key == "type_class":
            return CONCEPT_TYPES[self._type]["type_class"]
        else:
            raise KeyError(f"Key '{key}' not found")
    
    def __setitem__(self, key, value):
        if key == "name":
            self._name = value
        elif key == "type":
            if value not in CONCEPT_TYPES:
                raise ValueError(f"Invalid concept type. Must be one of: {list(CONCEPT_TYPES.keys())}")
            self._type = value
        elif key == "context":
            self._context = value
        else:
            raise KeyError(f"Key '{key}' not found")

if __name__ == "__main__":
    def test_concept_synchronization():
        print("=== Testing Concept Synchronization ===\n")
        
        # Test 1: Basic initialization
        print("1. Basic initialization:")
        concept = Concept("test_concept", "test context", type="{}")
        print(f"   contribute_name: {concept.contribute_name}")
        print(f"   comprehension_name: {concept.comprehension_name}")
        print(f"   contribute_type: {concept.contribute_type}")
        print(f"   comprehension_type: {concept.comprehension_type}")
        print(f"   contribute_context: {concept.contribute_context}")
        print(f"   comprehension_context: {concept.comprehension_context}")
        print()
        
        # Test 2: Name synchronization
        print("2. Name synchronization:")
        concept.contribute_name = "new_name"
        print(f"   After setting contribute_name='new_name':")
        print(f"   contribute_name: {concept.contribute_name}")
        print(f"   comprehension_name: {concept.comprehension_name}")
        print(f"   Dictionary access: {concept['name']}")
        print()
        
        concept.comprehension_name = "another_name"
        print(f"   After setting comprehension_name='another_name':")
        print(f"   contribute_name: {concept.contribute_name}")
        print(f"   comprehension_name: {concept.comprehension_name}")
        print(f"   Dictionary access: {concept['name']}")
        print()
        
        # Test 3: Type synchronization
        print("3. Type synchronization:")
        concept.contribute_type = "::"
        print(f"   After setting contribute_type='::':")
        print(f"   contribute_type: {concept.contribute_type}")
        print(f"   comprehension_type: {concept.comprehension_type}")
        print(f"   Dictionary access: {concept['type']}")
        print(f"   type_description: {concept['type_description']}")
        print(f"   type_class: {concept['type_class']}")
        print()
        
        concept.comprehension_type = "[]"
        print(f"   After setting comprehension_type='[]':")
        print(f"   contribute_type: {concept.contribute_type}")
        print(f"   comprehension_type: {concept.comprehension_type}")
        print(f"   Dictionary access: {concept['type']}")
        print(f"   type_description: {concept['type_description']}")
        print(f"   type_class: {concept['type_class']}")
        print()
        
        # Test 4: Context synchronization
        print("4. Context synchronization:")
        concept.contribute_context = "new context"
        print(f"   After setting contribute_context='new context':")
        print(f"   contribute_context: {concept.contribute_context}")
        print(f"   comprehension_context: {concept.comprehension_context}")
        print(f"   Dictionary access: {concept['context']}")
        print()
        
        concept.comprehension_context = "another context"
        print(f"   After setting comprehension_context='another context':")
        print(f"   contribute_context: {concept.contribute_context}")
        print(f"   comprehension_context: {concept.comprehension_context}")
        print(f"   Dictionary access: {concept['context']}")
        print()
        
        # Test 5: Dictionary access
        print("5. Dictionary access:")
        concept["name"] = "dict_name"
        concept["type"] = "<>"
        concept["context"] = "dict_context"
        print(f"   After setting via dictionary:")
        print(f"   contribute_name: {concept.contribute_name}")
        print(f"   contribute_type: {concept.contribute_type}")
        print(f"   contribute_context: {concept.contribute_context}")
        print()
        
        # Test 6: Type validation
        print("6. Type validation:")
        try:
            concept.contribute_type = "invalid_type"
            print("   ERROR: Should have raised ValueError")
        except ValueError as e:
            print(f"   ✓ Correctly raised ValueError: {e}")
        print()
        
        # Test 7: Type class methods
        print("7. Type class methods:")
        concept.contribute_type = "{}"  # semantical
        print(f"   Type '{concept.contribute_type}':")
        print(f"   is_syntactical: {concept.is_syntactical()}")
        print(f"   is_semantical: {concept.is_semantical()}")
        print(f"   get_type_class: {concept.get_type_class()}")
        print()
        
        concept.contribute_type = "<="  # syntactical
        print(f"   Type '{concept.contribute_type}':")
        print(f"   is_syntactical: {concept.is_syntactical()}")
        print(f"   is_semantical: {concept.is_semantical()}")
        print(f"   get_type_class: {concept.get_type_class()}")
        print()
        
        # Test 8: All concept types
        print("8. All concept types:")
        for concept_type, info in CONCEPT_TYPES.items():
            test_concept = Concept("test", type=concept_type)
            print(f"   {concept_type}: {info['description']} ({info['type_class']})")
        print()
        
        # Test 9: Comprehension method
        print("9. Comprehension method:")
        test_ref = Reference("ref_name", "ref_type", "ref_context")
        concept_with_ref = Concept("test_concept", "test context", test_ref, "::")
        comprehension_dict = concept_with_ref.comprehension()
        print(f"   Comprehension dictionary:")
        for key, value in comprehension_dict.items():
            print(f"     {key}: {value}")
        print()

    test_concept_synchronization()



