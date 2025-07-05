import re
from typing import List, Dict, Any, Tuple
from models.graph_models import Position, NodeData

class NormCodeTranslator:
    """Service for translating NormCode horizontal layout into graph data"""
    
    def __init__(self):
        # Node type to color mapping
        self.concept_type_colors = {
            'object': 'blue',           # Objects, entities, things
            'imperative': 'green',      # Actions, processes, commands
            'judgement': 'purple',      # Conditions, relationships, requirements
            'being': 'orange',          # Real-world referents
            'concept': 'teal',          # General concepts
            'assignment': 'yellow',     # Assignment operations ($=, $., $::, $%)
            'sequence': 'pink',         # Sequencing operations (@by, @after, @before, @with)
            'quantification': 'brown',  # Quantification operations (*every, *some, *count)
            'grouping': 'red',          # Grouping operations (&in, &across, &set, &pair)
            'abstraction': 'grey',      # Abstraction operations ($%)
            'default': 'grey'
        }
        
        # Edge style mapping
        self.edge_styles = {
            '<=': 'solid',
            '<-': 'dashed'
        }
    
    def parse_horizontal_layout(self, normcode_text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parse NormCode horizontal layout and convert to graph nodes and edges"""
        normcode_text = normcode_text.strip()
        parsed_elements = self._parse_elements(normcode_text)
        
        nodes = []
        edges = []
        
        for element in parsed_elements:
            node = self._create_node(element)
            nodes.append(node)
            
            if element.get('parent_index'):
                edge = self._create_edge(element)
                if edge:
                    edges.append(edge)
        
        return nodes, edges
    
    def _parse_elements(self, text: str) -> List[Dict[str, Any]]:
        """Parse NormCode horizontal layout into structured elements"""
        elements = []
        
        # Pattern to match |index|content up to the next |index|, |/index|, or end of string
        indexed_matches = re.findall(r'\|(\d+(?:\.\d+)*)\|([^|]+?)(?=\|\d+(?:\.\d+)*\||\|/\d+(?:\.\d+)*\||$)', text)
        
        if indexed_matches:
            for index, content in indexed_matches:
                element = self._parse_element_content(content, index)
                elements.append(element)
        else:
            # Parse simple format without indexes
            parts = text.split()
            current_index = 1
            for part in parts:
                if part in ['<=', '<-']:
                    continue
                elif part.startswith('_') and part.endswith('_'):
                    element = self._parse_element_content(part, str(current_index))
                    elements.append(element)
                    current_index += 1
        self._build_hierarchy(elements)
        return elements
    
    def _parse_element_content(self, content: str, index: str) -> Dict[str, Any]:
        """Parse individual element content"""
        operator = None
        concept = content.strip()
        
        if content.startswith('<='):
            operator = '<='
            concept = content[2:].strip()
        elif content.startswith('<-'):
            operator = '<-'
            concept = content[2:].strip()
        elif content.startswith('$='):
            operator = '$='
            concept = content[2:].strip()
        elif content.startswith('@'):
            # Extract @operator
            space_pos = content.find(' ')
            if space_pos > 0:
                operator = content[:space_pos]
                concept = content[space_pos:].strip()
            else:
                operator = content
                concept = ""
        elif content.startswith('&'):
            # Extract &operator
            space_pos = content.find(' ')
            if space_pos > 0:
                operator = content[:space_pos]
                concept = content[space_pos:].strip()
            else:
                operator = content
                concept = ""
        
        concept_type = self._determine_concept_type(concept, operator)
        
        return {
            'id': f"node_{index}",
            'index': index,
            'operator': operator,
            'concept': concept,
            'concept_type': concept_type,
            'parent_index': None,
            'level': len(index.split('.'))
        }
    
    def _determine_concept_type(self, concept: str, operator: str = None) -> str:
        """Determine the concept type based on content analysis and operators"""
        concept_lower = concept.lower().replace('_', ' ')
        
        # First check for operators that indicate specific types
        if operator:
            if operator in ['$=', '$.', '$::', '$%']:
                return 'assignment'
            elif operator in ['@by', '@after', '@before', '@with']:
                return 'sequence'
            elif operator in ['@If', '@OnlyIf', '@IfOnlyIf']:
                return 'judgement'
            elif operator in ['*every', '*some', '*count']:
                return 'quantification'
            elif operator in ['&in', '&across', '&set', '&pair']:
                return 'grouping'
        
        # Check for specific patterns in content
        if concept.startswith('::(') and concept.endswith(')'):
            return 'imperative'  # Compositional imperative
        elif concept.startswith('<') and concept.endswith('>'):
            return 'object'  # Referenced object
        elif concept.startswith('{') and concept.endswith('}'):
            return 'object'  # Template object
        elif '$' in concept and '%' in concept:
            return 'abstraction'  # Abstraction operation
        elif 'across(' in concept or '&across' in concept:
            return 'grouping'  # Grouping operation
        
        # Content-based indicators
        imperative_indicators = ['process', 'action', 'do', 'perform', 'execute', 'create', 'build', 'make', 'click', 'verify', 'submit']
        if any(indicator in concept_lower for indicator in imperative_indicators):
            return 'imperative'
        
        judgement_indicators = ['if', 'when', 'condition', 'relationship', 'depends', 'requires', 'must', 'should', 'need']
        if any(indicator in concept_lower for indicator in judgement_indicators):
            return 'judgement'
        
        object_indicators = ['entity', 'object', 'thing', 'item', 'element', 'component', 'email', 'password', 'account', 'form', 'link']
        if any(indicator in concept_lower for indicator in object_indicators):
            return 'object'
        
        being_indicators = ['person', 'user', 'system', 'world', 'reality']
        if any(indicator in concept_lower for indicator in being_indicators):
            return 'being'
        
        return 'concept'
    
    def _build_hierarchy(self, elements: List[Dict[str, Any]]) -> None:
        """Build parent-child relationships based on index hierarchy"""
        for element in elements:
            index_parts = element['index'].split('.')
            if len(index_parts) > 1:
                parent_index = '.'.join(index_parts[:-1])
                element['parent_index'] = parent_index
    
    def _create_node(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Create a node from parsed element"""
        color = self.concept_type_colors.get(element['concept_type'], self.concept_type_colors['default'])
        
        level = element['level']
        index_parts = element['index'].split('.')
        sibling_position = int(index_parts[-1]) - 1
        
        position = Position(
            x=level * 200,
            y=sibling_position * 100
        )
        
        label = element['concept']
        
        node_data = NodeData(label=label)
        
        return {
            'id': element['id'],
            'type': color,
            'data': node_data.model_dump(),
            'position': position.model_dump()
        }
    
    def _create_edge(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Create an edge from parsed element"""
        if not element.get('parent_index'):
            return None
        
        style_type = self.edge_styles.get(element['operator'], 'solid')
        edge_id = f"edge_{element['parent_index']}_{element['index']}"
        source_id = f"node_{element['parent_index']}"
        target_id = element['id']
        
        style = {"stroke": "#34495e", "strokeWidth": 1.5}
        if style_type == 'dashed':
            style["strokeDasharray"] = "5,5"
        
        return {
            'id': edge_id,
            'source': source_id,
            'target': target_id,
            'type': 'custom',
            'style': style,
            'markerEnd': 'url(#arrowhead)',
            'data': {'styleType': style_type}
        } 