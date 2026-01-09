"""
Paradigm Parser - Parse and serialize paradigm JSON files.

Paradigms are JSON files that define reusable composition patterns for agent sequences.
They have a specific structure with metadata, env_spec, and sequence_spec sections.

This parser provides:
- Parsing paradigm JSON to a structured, editor-friendly format
- Validation of paradigm structure
- Serialization back to paradigm JSON
"""

import json
from typing import Dict, Any, List, Optional
from .base import BaseParser, ParseResult, SerializeResult


class ParadigmParser(BaseParser):
    """
    Parser for paradigm JSON files.
    
    Paradigm files define reusable composition patterns with:
    - metadata: Description, inputs (vertical/horizontal), outputs
    - env_spec: Tools and their affordances
    - sequence_spec: Steps for setup and execution
    """
    
    @property
    def name(self) -> str:
        return "Paradigm Parser"
    
    @property
    def supported_formats(self) -> List[str]:
        return ['paradigm']
    
    @property
    def category(self) -> str:
        return "paradigm"
    
    def parse(self, content: str, format: str, **kwargs) -> ParseResult:
        """
        Parse paradigm JSON content into structured representation.
        
        Args:
            content: Raw JSON content
            format: Format identifier ('paradigm')
            
        Returns:
            ParseResult with parsed lines representing paradigm structure
        """
        errors: List[str] = []
        warnings: List[str] = []
        lines: List[Dict[str, Any]] = []
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
            return ParseResult(success=False, errors=errors)
        
        # Validate required top-level keys
        required_keys = ['metadata', 'env_spec', 'sequence_spec']
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")
        
        if errors:
            return ParseResult(success=False, errors=errors)
        
        # Parse metadata
        metadata = data.get('metadata', {})
        metadata_parsed = self._parse_metadata(metadata, warnings)
        
        # Parse env_spec (tools)
        env_spec = data.get('env_spec', {})
        tools_parsed, all_affordances = self._parse_env_spec(env_spec, warnings)
        
        # Parse sequence_spec (steps)
        sequence_spec = data.get('sequence_spec', {})
        steps_parsed, composition_step_index = self._parse_sequence_spec(
            sequence_spec, all_affordances, warnings
        )
        
        # Build the parsed representation as lines
        # Each "line" represents a logical unit for the editor
        
        # Metadata section
        lines.append({
            'type': 'section',
            'section': 'metadata',
            'data': metadata_parsed
        })
        
        # Inputs
        for inp in metadata_parsed.get('inputs', []):
            lines.append({
                'type': 'input',
                'section': 'metadata',
                'data': inp
            })
        
        # Output
        lines.append({
            'type': 'output',
            'section': 'metadata',
            'data': {
                'type': metadata_parsed.get('output_type', ''),
                'description': metadata_parsed.get('output_description', '')
            }
        })
        
        # Tools section
        for tool in tools_parsed:
            lines.append({
                'type': 'tool',
                'section': 'tools',
                'data': tool
            })
            
            # Affordances under this tool
            for aff in tool.get('affordances', []):
                lines.append({
                    'type': 'affordance',
                    'section': 'tools',
                    'parent_tool': tool.get('tool_name', ''),
                    'data': aff
                })
        
        # Steps section (vertical)
        for step in steps_parsed:
            lines.append({
                'type': 'step',
                'section': 'steps',
                'data': step
            })
            
            # If step has a composition plan, add those as sub-lines
            for comp_step in step.get('composition_steps', []):
                lines.append({
                    'type': 'composition_step',
                    'section': 'composition',
                    'parent_step_index': step.get('step_index'),
                    'data': comp_step
                })
        
        # Create metadata for the parsed result
        result_metadata = {
            'description': metadata_parsed.get('description', ''),
            'inputs': metadata_parsed.get('inputs', []),
            'output_type': metadata_parsed.get('output_type', ''),
            'output_description': metadata_parsed.get('output_description', ''),
            'tools': tools_parsed,
            'all_affordances': all_affordances,
            'steps': steps_parsed,
            'composition_step_index': composition_step_index,
            'raw': data  # Keep original for reference
        }
        
        return ParseResult(
            success=True,
            lines=lines,
            warnings=warnings,
            metadata=result_metadata
        )
    
    def _parse_metadata(self, metadata: Dict[str, Any], warnings: List[str]) -> Dict[str, Any]:
        """Parse the metadata section."""
        result = {
            'description': metadata.get('description', ''),
            'inputs': [],
            'output_type': '',
            'output_description': ''
        }
        
        # Parse inputs
        inputs_data = metadata.get('inputs', {})
        
        # Vertical inputs (composition-time)
        vertical = inputs_data.get('vertical', {})
        for name, desc in vertical.items():
            result['inputs'].append({
                'name': name,
                'description': desc,
                'type': 'vertical'
            })
        
        # Horizontal inputs (runtime)
        horizontal = inputs_data.get('horizontal', {})
        for name, desc in horizontal.items():
            result['inputs'].append({
                'name': name,
                'description': desc,
                'type': 'horizontal'
            })
        
        # Parse outputs
        outputs = metadata.get('outputs', {})
        result['output_type'] = outputs.get('type', '')
        result['output_description'] = outputs.get('description', '')
        
        return result
    
    def _parse_env_spec(
        self, 
        env_spec: Dict[str, Any], 
        warnings: List[str]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parse the env_spec section."""
        tools_parsed = []
        all_affordances = []
        
        tools = env_spec.get('tools', [])
        
        for tool_idx, tool in enumerate(tools):
            tool_name = tool.get('tool_name', f'tool_{tool_idx}')
            tool_data = {
                'index': tool_idx,
                'tool_name': tool_name,
                'affordances': []
            }
            
            affordances = tool.get('affordances', [])
            for aff_idx, aff in enumerate(affordances):
                aff_name = aff.get('affordance_name', f'affordance_{aff_idx}')
                full_id = f"{tool_name}.{aff_name}"
                
                aff_data = {
                    'index': aff_idx,
                    'tool_name': tool_name,
                    'affordance_name': aff_name,
                    'call_code': aff.get('call_code', ''),
                    'full_id': full_id
                }
                
                tool_data['affordances'].append(aff_data)
                all_affordances.append(aff_data)
            
            tools_parsed.append(tool_data)
        
        return tools_parsed, all_affordances
    
    def _parse_sequence_spec(
        self, 
        sequence_spec: Dict[str, Any], 
        all_affordances: List[Dict[str, Any]],
        warnings: List[str]
    ) -> tuple[List[Dict[str, Any]], Optional[int]]:
        """Parse the sequence_spec section."""
        steps_parsed = []
        composition_step_index = None
        
        # Create affordance lookup
        affordance_lookup = {aff['full_id']: aff for aff in all_affordances}
        
        steps = sequence_spec.get('steps', [])
        
        for idx, step in enumerate(steps):
            step_index = step.get('step_index', idx + 1)
            affordance = step.get('affordance', '')
            
            # Parse affordance reference
            parts = affordance.split('.')
            tool_name = parts[0] if parts else ''
            aff_name = parts[1] if len(parts) > 1 else ''
            
            # Check if affordance exists
            if affordance and affordance not in affordance_lookup:
                warnings.append(f"Step {step_index}: Unknown affordance '{affordance}'")
            
            # Check for composition plan
            params = step.get('params', {})
            has_composition = 'plan' in params
            composition_steps = []
            
            if has_composition:
                composition_step_index = step_index
                plan = params.get('plan', [])
                composition_steps = self._parse_composition_plan(plan, warnings)
            
            step_data = {
                'index': idx,
                'step_index': step_index,
                'affordance': affordance,
                'tool_name': tool_name,
                'affordance_name': aff_name,
                'params': params,
                'result_key': step.get('result_key', ''),
                'has_composition_plan': has_composition,
                'composition_steps': composition_steps
            }
            
            steps_parsed.append(step_data)
        
        return steps_parsed, composition_step_index
    
    def _parse_composition_plan(
        self, 
        plan: List[Dict[str, Any]], 
        warnings: List[str]
    ) -> List[Dict[str, Any]]:
        """Parse a composition plan (horizontal data flow)."""
        parsed_steps = []
        
        for idx, step in enumerate(plan):
            output_key = step.get('output_key', '')
            
            # Parse function reference
            function_data = step.get('function', {})
            function_ref = ''
            if isinstance(function_data, dict) and function_data.get('__type__') == 'MetaValue':
                function_ref = function_data.get('key', '')
            
            # Parse params (dynamic references)
            params = []
            for name, value in step.get('params', {}).items():
                params.append({
                    'name': name,
                    'value': value,
                    'is_literal': False
                })
            
            # Parse literal_params (static values)
            for name, value in step.get('literal_params', {}).items():
                params.append({
                    'name': name,
                    'value': str(value),
                    'is_literal': True
                })
            
            parsed_steps.append({
                'index': idx,
                'output_key': output_key,
                'function_ref': function_ref,
                'params': params
            })
        
        return parsed_steps
    
    def serialize(self, parsed_data: Dict[str, Any], target_format: str, **kwargs) -> SerializeResult:
        """
        Serialize parsed paradigm data back to JSON.
        
        Args:
            parsed_data: Dictionary with parsed paradigm structure
            target_format: Target format ('paradigm' or 'json')
            
        Returns:
            SerializeResult with JSON content
        """
        errors: List[str] = []
        
        try:
            # Check if we have raw data to start from
            metadata = parsed_data.get('metadata', {})
            raw = metadata.get('raw')
            
            if raw:
                # We have the original, reconstruct from parsed changes
                output = self._reconstruct_from_parsed(parsed_data, errors)
            else:
                # Build from scratch using the lines
                output = self._build_from_lines(parsed_data, errors)
            
            if errors:
                return SerializeResult(success=False, errors=errors)
            
            # Pretty print JSON
            content = json.dumps(output, indent=2)
            return SerializeResult(success=True, content=content)
            
        except Exception as e:
            errors.append(f"Serialization error: {e}")
            return SerializeResult(success=False, errors=errors)
    
    def _reconstruct_from_parsed(
        self, 
        parsed_data: Dict[str, Any], 
        errors: List[str]
    ) -> Dict[str, Any]:
        """Reconstruct paradigm from parsed metadata."""
        metadata = parsed_data.get('metadata', {})
        
        # Start with a copy of raw
        raw = metadata.get('raw', {})
        output = json.loads(json.dumps(raw))  # Deep copy
        
        # Update metadata section
        inputs_list = metadata.get('inputs', [])
        vertical = {}
        horizontal = {}
        
        for inp in inputs_list:
            if inp.get('type') == 'vertical':
                vertical[inp['name']] = inp.get('description', '')
            else:
                horizontal[inp['name']] = inp.get('description', '')
        
        output['metadata'] = {
            'description': metadata.get('description', ''),
            'inputs': {
                'vertical': vertical,
                'horizontal': horizontal
            },
            'outputs': {
                'type': metadata.get('output_type', ''),
                'description': metadata.get('output_description', '')
            }
        }
        
        # Update tools from parsed
        tools_parsed = metadata.get('tools', [])
        if tools_parsed:
            output['env_spec'] = {
                'tools': [
                    {
                        'tool_name': tool['tool_name'],
                        'affordances': [
                            {
                                'affordance_name': aff['affordance_name'],
                                'call_code': aff['call_code']
                            }
                            for aff in tool.get('affordances', [])
                        ]
                    }
                    for tool in tools_parsed
                ]
            }
        
        # Update steps from parsed
        steps_parsed = metadata.get('steps', [])
        if steps_parsed:
            output['sequence_spec'] = {
                'steps': [
                    self._serialize_step(step)
                    for step in steps_parsed
                ]
            }
        
        return output
    
    def _serialize_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize a single step back to paradigm format."""
        result = {
            'step_index': step.get('step_index', 0),
            'affordance': step.get('affordance', ''),
            'params': {},
            'result_key': step.get('result_key', '')
        }
        
        # Handle params
        params = step.get('params', {})
        
        if step.get('has_composition_plan'):
            # Rebuild the composition plan
            comp_steps = step.get('composition_steps', [])
            plan = self._serialize_composition_plan(comp_steps)
            result['params'] = {
                'plan': plan,
                'return_key': params.get('return_key', 'result')
            }
        else:
            # Copy non-plan params
            for key, value in params.items():
                if key != 'plan':
                    result['params'][key] = value
        
        return result
    
    def _serialize_composition_plan(self, comp_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Serialize composition steps back to plan format."""
        plan = []
        
        for step in comp_steps:
            plan_step: Dict[str, Any] = {
                'output_key': step.get('output_key', ''),
                'function': {
                    '__type__': 'MetaValue',
                    'key': step.get('function_ref', '')
                },
                'params': {},
            }
            
            # Separate params and literal_params
            literal_params = {}
            
            for param in step.get('params', []):
                name = param.get('name', '')
                value = param.get('value', '')
                is_literal = param.get('is_literal', False)
                
                if is_literal:
                    # Try to parse as JSON for non-string literals
                    try:
                        literal_params[name] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        literal_params[name] = value
                else:
                    plan_step['params'][name] = value
            
            if literal_params:
                plan_step['literal_params'] = literal_params
            
            plan.append(plan_step)
        
        return plan
    
    def _build_from_lines(self, parsed_data: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
        """Build paradigm structure from lines (when no raw data available)."""
        lines = parsed_data.get('lines', [])
        
        # Initialize structure
        metadata_inputs = {'vertical': {}, 'horizontal': {}}
        metadata_outputs = {'type': '', 'description': ''}
        description = ''
        tools = []
        current_tool = None
        steps = []
        current_step = None
        
        for line in lines:
            line_type = line.get('type', '')
            data = line.get('data', {})
            
            if line_type == 'section' and line.get('section') == 'metadata':
                description = data.get('description', '')
            
            elif line_type == 'input':
                inp_type = data.get('type', 'horizontal')
                name = data.get('name', '')
                desc = data.get('description', '')
                if inp_type == 'vertical':
                    metadata_inputs['vertical'][name] = desc
                else:
                    metadata_inputs['horizontal'][name] = desc
            
            elif line_type == 'output':
                metadata_outputs['type'] = data.get('type', '')
                metadata_outputs['description'] = data.get('description', '')
            
            elif line_type == 'tool':
                current_tool = {
                    'tool_name': data.get('tool_name', ''),
                    'affordances': []
                }
                tools.append(current_tool)
            
            elif line_type == 'affordance' and current_tool:
                current_tool['affordances'].append({
                    'affordance_name': data.get('affordance_name', ''),
                    'call_code': data.get('call_code', '')
                })
            
            elif line_type == 'step':
                current_step = self._serialize_step(data)
                steps.append(current_step)
        
        return {
            'metadata': {
                'description': description,
                'inputs': metadata_inputs,
                'outputs': metadata_outputs
            },
            'env_spec': {
                'tools': tools
            },
            'sequence_spec': {
                'steps': steps
            }
        }
    
    def validate(self, content: str, format: str) -> Dict[str, Any]:
        """
        Validate paradigm content.
        
        Checks:
        - Valid JSON
        - Required structure (metadata, env_spec, sequence_spec)
        - All affordance references exist
        - Composition plan references are valid
        """
        result = self.parse(content, format)
        
        validation_errors = list(result.errors)
        validation_warnings = list(result.warnings)
        
        if result.success and result.metadata:
            # Additional validation
            steps = result.metadata.get('steps', [])
            all_result_keys = {step['result_key'] for step in steps}
            
            # Check composition plan references
            for step in steps:
                for comp_step in step.get('composition_steps', []):
                    func_ref = comp_step.get('function_ref', '')
                    if func_ref and func_ref not in all_result_keys:
                        if func_ref not in ['__initial_input__']:
                            validation_warnings.append(
                                f"Composition step '{comp_step.get('output_key')}' "
                                f"references unknown result key: '{func_ref}'"
                            )
        
        return {
            'valid': result.success and len(validation_errors) == 0,
            'errors': validation_errors,
            'warnings': validation_warnings,
            'format': format
        }


# Create and register the parser
paradigm_parser = ParadigmParser()

