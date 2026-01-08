"""
NormCode parser for .ncd, .ncn, .ncdn, and .ncds formats.

This parser handles the NormCode family of file formats:
- .ncd: NormCode Draft (structure)
- .ncn: NormCode Natural language (human-readable annotations)
- .ncdn: NormCode Draft+Natural (combined format)
- .ncds: NormCode Draft Script (similar to ncdn)

The parser provides bidirectional conversion between these formats
and a structured JSON representation (nc.json) for programmatic access.
"""

import re
from typing import Dict, Any, List, Optional

from .base import BaseParser, ParseResult, SerializeResult


class NormCodeParser(BaseParser):
    """
    Parser for NormCode file formats.
    
    Handles parsing and serialization of .ncd, .ncn, .ncdn, and .ncds files.
    """
    
    @property
    def name(self) -> str:
        return "NormCode Parser"
    
    @property
    def supported_formats(self) -> List[str]:
        return ['ncd', 'ncn', 'ncdn', 'ncds', 'nci']
    
    @property
    def category(self) -> str:
        return "normcode"
    
    def parse(self, content: str, format: str, **kwargs) -> ParseResult:
        """
        Parse NormCode content into structured representation.
        
        Args:
            content: Raw file content
            format: One of 'ncd', 'ncn', 'ncdn', 'ncds', 'nci'
            ncn_content: Optional NCN content when parsing NCD
        """
        try:
            if format == 'nci':
                # Parse NCI JSON back to parsed format
                parsed = self._parse_nci(content)
            elif format in ('ncdn', 'ncds'):
                parsed = self._parse_ncdn(content)
            elif format == 'ncn':
                # NCN alone has the same structure
                parsed = self._parse_ncd_ncn(content, "")
            else:  # ncd
                ncn_content = kwargs.get('ncn_content', '')
                parsed = self._parse_ncd_ncn(content, ncn_content)
            
            return ParseResult(
                success=True,
                lines=parsed.get('lines', []),
                metadata={"format": format}
            )
        except Exception as e:
            return ParseResult(
                success=False,
                errors=[str(e)]
            )
    
    def serialize(self, parsed_data: Dict[str, Any], target_format: str, **kwargs) -> SerializeResult:
        """
        Serialize parsed data to target format.
        
        Args:
            parsed_data: Dict with 'lines' key
            target_format: One of 'ncd', 'ncn', 'ncdn', 'json', 'nci'
        """
        try:
            if target_format == 'ncdn':
                content = self._serialize_to_ncdn(parsed_data)
            elif target_format == 'ncds':
                content = self._serialize_to_ncdn(parsed_data)  # Same format
            elif target_format in ('ncd', 'ncn'):
                result = self._serialize_to_ncd_ncn(parsed_data)
                content = result.get(target_format, '')
            elif target_format == 'json':
                import json
                content = json.dumps(parsed_data, indent=2, ensure_ascii=False)
            elif target_format == 'nci':
                import json
                nci = self._to_nci(parsed_data)
                content = json.dumps(nci, indent=2, ensure_ascii=False)
            else:
                return SerializeResult(
                    success=False,
                    errors=[f"Unknown target format: {target_format}"]
                )
            
            return SerializeResult(success=True, content=content)
        except Exception as e:
            return SerializeResult(success=False, errors=[str(e)])
    
    # =========================================================================
    # Core Parsing Logic
    # =========================================================================
    
    def _detect_concept_type(self, content: str) -> Dict[str, Any]:
        """
        Detect the concept type from content.
        
        Returns:
            Dict with:
                - inference_marker: '<-', '<=', '<*', ':<:', ':>:' or None
                - concept_type: 'object', 'proposition', 'relation', 'subject', 
                               'imperative', 'judgement', 'operator', 'comment', 'informal'
                - operator_type: For operators - 'assigning', 'grouping', 'timing', 'looping'
                - warnings: List of potential issues
        """
        result = {
            'inference_marker': None,
            'concept_type': None,
            'operator_type': None,
            'concept_name': None,
            'warnings': []
        }
        
        content = content.strip()
        if not content:
            return result
        
        # Extract inference marker first
        inference_markers = [':<:', ':>:', '<=', '<-', '<*']
        remaining = content
        for marker in inference_markers:
            if content.startswith(marker):
                result['inference_marker'] = marker
                remaining = content[len(marker):].strip()
                break
        
        # --- Syntactic Operators ---
        if remaining.startswith('$='):
            result['concept_type'] = 'operator'
            result['operator_type'] = 'identity'
        elif remaining.startswith('$%'):
            result['concept_type'] = 'operator'
            result['operator_type'] = 'abstraction'
        elif remaining.startswith('$.'):
            result['concept_type'] = 'operator'
            result['operator_type'] = 'specification'
        elif remaining.startswith('$+'):
            result['concept_type'] = 'operator'
            result['operator_type'] = 'continuation'
        elif remaining.startswith('$-'):
            result['concept_type'] = 'operator'
            result['operator_type'] = 'selection'
        elif remaining.startswith('$::'):
            result['concept_type'] = 'operator'
            result['operator_type'] = 'nominalization'
        # Grouping
        elif remaining.startswith('&[{}]') or remaining.startswith('&[#]'):
            result['concept_type'] = 'operator'
            result['operator_type'] = 'grouping'
        # Timing
        elif remaining.startswith("@:'") or remaining.startswith('@:!'):
            result['concept_type'] = 'operator'
            result['operator_type'] = 'timing_conditional'
        elif remaining.startswith('@.'):
            result['concept_type'] = 'operator'
            result['operator_type'] = 'timing_completion'
        elif remaining.startswith('@::'):
            result['concept_type'] = 'operator'
            result['operator_type'] = 'timing_action'
        # Looping
        elif remaining.startswith('*.'):
            result['concept_type'] = 'operator'
            result['operator_type'] = 'looping'
        
        # --- Semantic Concepts ---
        elif remaining.startswith('::'):
            # Imperative or Judgement
            if re.search(r'::\([^)]*\)\s*<', remaining):
                result['concept_type'] = 'judgement'
                match = re.search(r'::\(([^)]*)\)', remaining)
                if match:
                    result['concept_name'] = match.group(1)
            else:
                result['concept_type'] = 'imperative'
                match = re.search(r'::\(([^)]*)\)', remaining)
                if match:
                    result['concept_name'] = match.group(1)
        
        # Subject: :Name:
        elif re.match(r'^:[A-Za-z_][A-Za-z0-9_]*:', remaining):
            result['concept_type'] = 'subject'
            match = re.match(r'^:([A-Za-z_][A-Za-z0-9_]*):', remaining)
            if match:
                result['concept_name'] = match.group(1)
        
        # Proposition: <name>
        elif remaining.startswith('<') and not remaining.startswith(('<$', '<:', '<=', '<-', '<*')):
            if '>' in remaining:
                result['concept_type'] = 'proposition'
                match = re.match(r'^<([^>]+)>', remaining)
                if match:
                    result['concept_name'] = match.group(1)
            else:
                result['concept_type'] = 'informal'
                result['warnings'].append('Unclosed proposition marker <')
        
        # Relation: [name]
        elif remaining.startswith('['):
            if ']' in remaining:
                result['concept_type'] = 'relation'
                match = re.match(r'^\[([^\]]+)\]', remaining)
                if match:
                    result['concept_name'] = match.group(1)
            else:
                result['concept_type'] = 'informal'
                result['warnings'].append('Unclosed relation marker [')
        
        # Object: {name}
        elif remaining.startswith('{'):
            if '}' in remaining:
                result['concept_type'] = 'object'
                match = re.match(r'^\{([^}]+)\}', remaining)
                if match:
                    result['concept_name'] = match.group(1)
            else:
                result['concept_type'] = 'informal'
                result['warnings'].append('Unclosed object marker {')
        
        # Comment markers
        elif remaining.startswith('/:') or remaining.startswith('?:') or remaining.startswith('...:'):
            result['concept_type'] = 'comment'
        elif remaining.startswith('%{') or remaining.startswith('?{'):
            result['concept_type'] = 'comment'
        
        # Inference marker but no recognized concept
        elif result['inference_marker'] and not result['concept_type']:
            result['concept_type'] = 'informal'
            result['warnings'].append(f"Unrecognized concept format after {result['inference_marker']}")
            if remaining:
                result['concept_name'] = remaining.split()[0] if remaining.split() else remaining[:30]
        
        # No inference marker
        elif not result['inference_marker']:
            if content.startswith('/') or content.startswith('?') or content.startswith('%'):
                result['concept_type'] = 'comment'
            else:
                result['concept_type'] = 'informal'
                if content and not content.startswith('|'):
                    result['warnings'].append('Line without inference marker or comment prefix')
        
        return result
    
    def _calculate_depth(self, line: str) -> int:
        """Calculate indentation depth (4 spaces = 1 level)."""
        stripped = line.lstrip()
        spaces = len(line) - len(stripped)
        return spaces // 4
    
    def _assign_flow_indices(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Parse lines and assign flow indices based on structure.
        """
        parsed_lines = []
        indices = []  # Stack of counters for each depth
        
        for raw_line in lines:
            if not raw_line.strip():
                continue
                
            depth = self._calculate_depth(raw_line)
            content = raw_line.strip()
            
            is_concept = False
            main_part = content
            inline_comment = None
            explicit_flow_index = None
            
            # Check for NCN annotation line
            is_ncn_annotation = content.startswith('|?{natural language}:') or content.startswith('|?{')
            
            # Split inline comments/metadata
            if '|' in content and not is_ncn_annotation:
                parts = content.split('|', 1)
                main_part = parts[0].strip()
                inline_comment = parts[1].strip()
                
                # Check for explicit flow_index
                if inline_comment:
                    flow_match = re.search(r'\?{flow_index}:\s*([\d.]+)', inline_comment)
                    if flow_match:
                        explicit_flow_index = flow_match.group(1)
            
            # Concept prefixes
            concept_prefixes = [':<:', ':>:', '<=', '<-', '<*', '$%', '$.', '*.',  '$+', '&[', '@:', '@:!', '::']
            for prefix in concept_prefixes:
                if main_part.startswith(prefix):
                    is_concept = True
                    break
            
            flow_index = None
            
            if is_concept:
                if explicit_flow_index:
                    flow_index = explicit_flow_index
                    parts = [int(p) for p in explicit_flow_index.split('.')]
                    indices = parts[:]
                else:
                    while len(indices) <= depth:
                        indices.append(0)
                    indices = indices[:depth+1]
                    indices[depth] += 1
                    flow_index = ".".join(map(str, indices))
            else:
                # Inherit flow index from preceding concept
                if parsed_lines:
                    for prev in reversed(parsed_lines):
                        if prev['type'] == 'main' and prev['flow_index']:
                            flow_index = prev['flow_index']
                            break
            
            # Detect concept type
            concept_info = self._detect_concept_type(main_part) if is_concept else {}
            
            # Handle pipe-only lines
            if not is_concept and not main_part and inline_comment:
                parsed_lines.append({
                    "raw_line": raw_line,
                    "content": f"| {inline_comment}",
                    "depth": depth,
                    "flow_index": flow_index,
                    "type": "comment"
                })
            else:
                if is_concept or main_part:
                    line_entry = {
                        "raw_line": raw_line,
                        "content": main_part,
                        "depth": depth,
                        "flow_index": flow_index,
                        "type": "main" if is_concept else "comment"
                    }
                    if is_concept and concept_info:
                        line_entry["inference_marker"] = concept_info.get("inference_marker")
                        line_entry["concept_type"] = concept_info.get("concept_type")
                        line_entry["operator_type"] = concept_info.get("operator_type")
                        line_entry["concept_name"] = concept_info.get("concept_name")
                        if concept_info.get("warnings"):
                            line_entry["warnings"] = concept_info["warnings"]
                    parsed_lines.append(line_entry)
                
                if inline_comment:
                    parsed_lines.append({
                        "raw_line": "",
                        "content": inline_comment,
                        "depth": depth,
                        "flow_index": flow_index,
                        "type": "inline_comment"
                    })
        
        return parsed_lines
    
    def _parse_ncd_ncn(self, ncd_content: str, ncn_content: str) -> Dict[str, Any]:
        """Parse .ncd and .ncn formats together."""
        ncd_lines = ncd_content.splitlines()
        ncn_lines = ncn_content.splitlines() if ncn_content else []
        
        parsed_ncd = self._assign_flow_indices(ncd_lines)
        parsed_ncn = self._assign_flow_indices(ncn_lines) if ncn_lines else []
        
        # Map NCN by flow_index
        ncn_map = {}
        for line in parsed_ncn:
            if line['type'] == 'main' and line['flow_index']:
                ncn_map[line['flow_index']] = line['content']
        
        merged_lines = []
        for line in parsed_ncd:
            merged_item = {
                "flow_index": line['flow_index'],
                "type": line['type'],
                "depth": line['depth']
            }
            
            if line['type'] == 'main':
                merged_item['nc_main'] = line['content']
                if line['flow_index'] in ncn_map:
                    merged_item['ncn_content'] = ncn_map[line['flow_index']]
                
                # Preserve concept type info
                for key in ['inference_marker', 'concept_type', 'operator_type', 'concept_name', 'warnings']:
                    if key in line:
                        merged_item[key] = line[key]
                        
            elif line['type'] == 'inline_comment':
                merged_item['nc_comment'] = line['content']
            elif line['type'] == 'comment':
                merged_item['nc_comment'] = line['content']
            
            merged_lines.append(merged_item)
        
        return {"lines": merged_lines}
    
    def _parse_ncdn(self, ncdn_content: str) -> Dict[str, Any]:
        """Parse .ncdn format."""
        lines = ncdn_content.splitlines()
        parsed_ncd = self._assign_flow_indices(lines)
        
        merged_lines = []
        i = 0
        
        while i < len(parsed_ncd):
            line = parsed_ncd[i]
            
            merged_item = {
                "flow_index": line['flow_index'],
                "type": line['type'],
                "depth": line['depth']
            }
            
            if line['type'] == 'main':
                merged_item['nc_main'] = line['content']
                
                # Preserve concept type info
                for key in ['inference_marker', 'concept_type', 'operator_type', 'concept_name', 'warnings']:
                    if key in line:
                        merged_item[key] = line[key]
                
                # Look ahead for NCN annotation
                lookahead = i + 1
                if lookahead < len(parsed_ncd) and parsed_ncd[lookahead]['type'] == 'inline_comment':
                    lookahead += 1
                
                if lookahead < len(parsed_ncd):
                    next_line = parsed_ncd[lookahead]
                    next_content = next_line['content']
                    
                    if next_content.startswith('|?{natural language}:') or next_content.startswith('|?{'):
                        if '|?{natural language}:' in next_content:
                            ncn_content = next_content.split('|?{natural language}:', 1)[1].strip()
                        else:
                            ncn_content = next_content.split(':', 1)[1].strip() if ':' in next_content else ''
                        merged_item['ncn_content'] = ncn_content
                        
            elif line['type'] == 'inline_comment':
                merged_item['nc_comment'] = line['content']
            elif line['type'] == 'comment':
                if line['content'].startswith('|?{natural language}:') or line['content'].startswith('|?{'):
                    i += 1
                    continue
                merged_item['nc_comment'] = line['content']
            
            merged_lines.append(merged_item)
            i += 1
        
        return {"lines": merged_lines}
    
    # =========================================================================
    # Serialization Logic
    # =========================================================================
    
    def _serialize_to_ncd_ncn(self, parsed_data: Dict[str, Any]) -> Dict[str, str]:
        """Convert parsed JSON to .ncd and .ncn strings."""
        ncd_lines = []
        ncn_lines = []
        
        for line in parsed_data.get('lines', []):
            depth = line.get('depth', 0)
            indent = "    " * depth
            
            if line['type'] == 'main':
                content = line.get('nc_main', '')
                ncd_lines.append(f"{indent}{content}")
                
                ncn_content = line.get('ncn_content', '')
                if ncn_content:
                    ncn_lines.append(f"{indent}{ncn_content}")
                    
            elif line['type'] == 'inline_comment':
                if ncd_lines:
                    ncd_lines[-1] = f"{ncd_lines[-1]} | {line.get('nc_comment', '')}"
            elif line['type'] == 'comment':
                content = line.get('nc_comment', '')
                ncd_lines.append(f"{indent}{content}")
        
        return {
            "ncd": "\n".join(ncd_lines) + "\n" if ncd_lines else "",
            "ncn": "\n".join(ncn_lines) + "\n" if ncn_lines else ""
        }
    
    def _serialize_to_ncdn(self, parsed_data: Dict[str, Any]) -> str:
        """Convert parsed JSON to .ncdn format."""
        ncdn_lines = []
        lines_list = parsed_data.get('lines', [])
        i = 0
        
        while i < len(lines_list):
            line = lines_list[i]
            depth = line.get('depth', 0)
            indent = "    " * depth
            
            if line['type'] == 'main':
                content = line.get('nc_main', '')
                current_line = f"{indent}{content}"
                
                # Check for inline_comment
                if i + 1 < len(lines_list) and lines_list[i + 1]['type'] == 'inline_comment':
                    inline_comment = lines_list[i + 1].get('nc_comment', '')
                    current_line = f"{current_line} | {inline_comment}"
                    i += 1
                
                ncdn_lines.append(current_line)
                
                # Add NCN annotation if present
                if 'ncn_content' in line and line['ncn_content']:
                    ncn_content = line['ncn_content']
                    ncdn_lines.append(f"{indent}    |?{{natural language}}: {ncn_content}")
                    
            elif line['type'] == 'comment':
                content = line.get('nc_comment', '')
                ncdn_lines.append(f"{indent}{content}")
            
            i += 1
        
        return "\n".join(ncdn_lines) + "\n" if ncdn_lines else ""
    
    # =========================================================================
    # NCI Format Conversion
    # =========================================================================
    
    def _to_nci(self, nc_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert nc.json structure to nci.json format.
        
        Identifies inference groups where a concept has children with '<=' markers.
        """
        lines = nc_json.get('lines', [])
        if not lines:
            return []
        
        # Group lines by flow_index
        concepts_by_index: Dict[str, Dict] = {}
        
        for line in lines:
            fi = line.get('flow_index')
            if not fi:
                continue
                
            if fi not in concepts_by_index:
                concepts_by_index[fi] = {"main": None, "comments": []}
                
            if line['type'] == 'main':
                concepts_by_index[fi]['main'] = line
            else:
                concepts_by_index[fi]['comments'].append(line)
        
        # Build parent-child relationships
        parent_stack = []
        children_map = {}
        
        for line in lines:
            if line['type'] != 'main':
                continue
                
            depth = line.get('depth', 0)
            fi = line.get('flow_index')
            if not fi:
                continue
            
            parent_fi = None
            while parent_stack:
                last_fi, last_depth = parent_stack[-1]
                if last_depth < depth:
                    parent_fi = last_fi
                    break
                else:
                    parent_stack.pop()
            
            if parent_fi:
                if parent_fi not in children_map:
                    children_map[parent_fi] = []
                children_map[parent_fi].append(fi)
            
            parent_stack.append((fi, depth))
        
        # Helper to get full concept object
        def get_concept_obj(fi):
            c = concepts_by_index.get(fi)
            if not c:
                return None
            obj = c['main'].copy() if c['main'] else {"flow_index": fi, "type": "virtual", "depth": -1}
            obj['attached_comments'] = c['comments']
            return obj
        
        # Build NCI groups
        nci_groups = []
        
        def index_sort_key(fi):
            try:
                return [int(x) for x in fi.split('.')]
            except:
                return []
        
        all_parents = sorted(children_map.keys(), key=index_sort_key)
        
        for parent_fi in all_parents:
            children_fis = children_map[parent_fi]
            
            function_child_fi = None
            value_child_fis = []
            other_child_fis = []
            
            has_function = False
            
            for child_fi in children_fis:
                child_main = concepts_by_index[child_fi]['main']
                if not child_main:
                    continue
                content = child_main.get('nc_main', '').strip()
                
                if content.startswith('<='):
                    if function_child_fi is None:
                        function_child_fi = child_fi
                        has_function = True
                    else:
                        other_child_fis.append(child_fi)
                elif content.startswith('<-'):
                    value_child_fis.append(child_fi)
                else:
                    other_child_fis.append(child_fi)
            
            if has_function:
                group = {
                    "concept_to_infer": get_concept_obj(parent_fi),
                    "function_concept": get_concept_obj(function_child_fi),
                    "value_concepts": [get_concept_obj(f) for f in value_child_fis],
                    "other_concepts": [get_concept_obj(f) for f in other_child_fis]
                }
                nci_groups.append(group)
        
        return nci_groups
    
    def _parse_nci(self, nci_content: str) -> Dict[str, Any]:
        """
        Parse NCI JSON content back to parsed format.
        
        This enables round-trip conversion: NCDS → NCI → NCDS
        
        Args:
            nci_content: NCI JSON string (list of inference groups)
            
        Returns:
            Dict with 'lines' key containing reconstructed parsed structure
        """
        import json
        nci_data = json.loads(nci_content)
        return self._from_nci(nci_data)
    
    def _from_nci(self, nci_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert nci.json structure back to nc.json format."""
        unique_concepts = {}
        
        def add_concept(c_obj, context_info=""):
            if not c_obj:
                return
            fi = c_obj.get('flow_index')
            if not fi:
                return
            
            main_line = c_obj.copy()
            comments = main_line.pop('attached_comments', [])
            
            if fi not in unique_concepts:
                unique_concepts[fi] = {"main": main_line, "comments": comments}
        
        for i, group in enumerate(nci_data):
            group_id = f"group_{i}"
            add_concept(group.get('concept_to_infer'), f"{group_id}.concept_to_infer")
            add_concept(group.get('function_concept'), f"{group_id}.function_concept")
            for j, c in enumerate(group.get('value_concepts', [])):
                add_concept(c, f"{group_id}.value_concepts[{j}]")
            for j, c in enumerate(group.get('other_concepts', [])):
                add_concept(c, f"{group_id}.other_concepts[{j}]")
        
        def index_sort_key(item):
            try:
                return [int(x) for x in item[0].split('.')]
            except:
                return []
        
        sorted_items = sorted(unique_concepts.items(), key=index_sort_key)
        
        reconstructed_lines = []
        for fi, data in sorted_items:
            reconstructed_lines.append(data['main'])
            reconstructed_lines.extend(data['comments'])
        
        return {"lines": reconstructed_lines}

