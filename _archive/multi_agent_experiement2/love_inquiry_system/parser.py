import re
from multi_agent_experiement2.love_inquiry_system.concepts import NormCodeConcept

class NormCodeParser:
    """
    Parses a NormCode file (.md) into a tree of NormCodeConcept objects.
    """
    def parse_file(self, file_path: str) -> NormCodeConcept:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Filter out ```normcode blocks
        normcode_lines = []
        in_normcode_block = False
        for line in lines:
            if line.strip() == '```normcode':
                in_normcode_block = True
                continue
            if line.strip() == '```':
                in_normcode_block = False
                continue
            if in_normcode_block:
                normcode_lines.append(line)

        return self.parse_lines(normcode_lines)

    def parse_lines(self, lines: list[str]) -> NormCodeConcept:
        """
        Parses a list of NormCode lines into a tree of concepts.
        """
        root_concept = None
        parent_stack = [] # Stack of (indentation, concept)
        
        # Temporary holders for annotations that appear before their concept
        current_annotations = {
            "source_text": [],
            "question": [],
            "description": []
        }

        for line in lines:
            if not line.strip():
                continue

            indentation = len(line) - len(line.lstrip(' '))
            clean_line = line.strip()

            # Handle annotation lines
            if clean_line.startswith('...:'):
                current_annotations["source_text"].append(clean_line[4:].strip())
                continue
            elif clean_line.startswith('?:'):
                current_annotations["question"].append(clean_line[3:].strip())
                continue
            elif clean_line.startswith('/:'):
                current_annotations["description"].append(clean_line[2:].strip())
                continue

            # This is a concept line, so we process it
            concept = self._parse_line_to_concept(clean_line, indentation)
            
            # Apply collected annotations to this new concept
            concept.source_text = "\n".join(current_annotations["source_text"])
            concept.question = "\n".join(current_annotations["question"])
            concept.description = "\n".join(current_annotations["description"])
            
            # Reset annotations for the next concept
            current_annotations = {
                "source_text": [], "question": [], "description": []
            }

            if root_concept is None:
                root_concept = concept
                parent_stack.append((indentation, root_concept))
            else:
                # Go up the stack to find the correct parent
                while parent_stack and parent_stack[-1][0] >= indentation:
                    parent_stack.pop()
                
                if parent_stack:
                    parent = parent_stack[-1][1]
                    parent.children.append(concept)
                    concept.parent = parent

                parent_stack.append((indentation, concept))
        
        if root_concept is None:
            raise ValueError("Could not parse any concepts from the provided lines.")
            
        return root_concept

    def _parse_line_to_concept(self, line: str, indentation: int) -> NormCodeConcept:
        """
        Parses a single line of NormCode into a NormCodeConcept object.
        """
        is_functional = '<=' in line
        is_value = '<-' in line
        
        # Default concept type if not specified by syntax
        concept_type_str = "Object" 
        
        # Enhanced regex to find the primary concept name first
        name_match = re.search(r'(\{.*?\}|\<.*?\>|\[.*?\])', line)
        if name_match:
            name = name_match.group(0)
        else:
            # Fallback for lines where the primary concept is an operator itself
            name = line

        # Determine concept type more accurately
        if '::<_texts_>' in name:
            concept_type_str = 'Judgement'
        elif name.startswith('{'): 
            concept_type_str = 'Object'
        elif name.startswith('<'): 
            concept_type_str = 'Statement'
        elif name.startswith('['): 
            concept_type_str = 'Relation'
        elif '::(' in line: 
            concept_type_str = 'Imperative'
        
        # Special check for Judgement type based on operator
        if is_functional and '::<' in line:
             concept_type_str = 'Judgement'


        concept = NormCodeConcept(
            name=name,
            concept_type=concept_type_str,
            raw_line=line,
            indentation=indentation,
            is_functional_concept=is_functional,
            is_value_concept=is_value,
        )

        # More sophisticated parsing for operators
        if is_functional:
            parts = line.split("<=", 1)
            op_part = parts[1].strip()
            
            # Extract operator without arguments
            op_match = re.match(r'([@$&\*]?[a-zA-Z!]+|[:$]\S+)', op_part)
            if op_match:
                concept.operator = op_match.group(0)
            else:
                concept.operator = op_part.split("(")[0] if '(' in op_part else op_part

        return concept
