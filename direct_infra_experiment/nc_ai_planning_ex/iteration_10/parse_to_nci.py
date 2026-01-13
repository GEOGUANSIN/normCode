"""
Minimal NormCode Parser: .pf.ncd → .nci.json

A self-contained parser that converts Post-Formalized NormCode (.pf.ncd)
to NormCode Inference format (.nci.json) for activation.

Usage:
    python parse_to_nci.py formalization.pf.ncd
    # Outputs: formalization.pf.nci.json

Based on: canvas_app/backend/services/parsers/normcode.py
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# Core Parsing Functions
# =============================================================================

def calculate_depth(line: str) -> int:
    """Calculate indentation depth (4 spaces = 1 level)."""
    stripped = line.lstrip()
    spaces = len(line) - len(stripped)
    return spaces // 4


def detect_concept_type(content: str) -> Dict[str, Any]:
    """
    Detect the concept type from content.
    
    Returns:
        Dict with:
            - inference_marker: '<-', '<=', '<*', ':<:', ':>:' or None
            - concept_type: 'object', 'proposition', 'relation', 'subject', 
                           'imperative', 'judgement', 'operator', 'comment', 'informal'
            - operator_type: For operators - 'assigning', 'grouping', 'timing', 'looping'
            - concept_name: Extracted name if applicable
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
        if re.search(r'::\([^)]*\)\s*<', remaining) or '::<{' in remaining:
            result['concept_type'] = 'judgement'
            match = re.search(r'::\(([^)]*)\)', remaining)
            if not match:
                match = re.search(r'::<\{([^}]+)\}>', remaining)
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


def assign_flow_indices(lines: List[str]) -> List[Dict[str, Any]]:
    """
    Parse lines and assign flow indices based on structure.
    """
    parsed_lines = []
    indices = []  # Stack of counters for each depth
    
    for raw_line in lines:
        if not raw_line.strip():
            continue
            
        depth = calculate_depth(raw_line)
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
        concept_info = detect_concept_type(main_part) if is_concept else {}
        
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


def parse_ncdn(ncdn_content: str) -> Dict[str, Any]:
    """Parse .ncdn/.pf.ncd format to structured JSON."""
    lines = ncdn_content.splitlines()
    parsed_ncd = assign_flow_indices(lines)
    
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


# =============================================================================
# NCI Conversion Functions
# =============================================================================

def to_nci(nc_json: Dict[str, Any]) -> List[Dict[str, Any]]:
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


# =============================================================================
# Main Entry Point
# =============================================================================

def parse_pf_ncd_to_nci(pf_ncd_path: str) -> str:
    """
    Parse a .pf.ncd file and convert to NCI JSON.
    
    Args:
        pf_ncd_path: Path to the .pf.ncd file
        
    Returns:
        Path to the output .nci.json file
    """
    pf_ncd_path = Path(pf_ncd_path)
    
    if not pf_ncd_path.exists():
        raise FileNotFoundError(f"File not found: {pf_ncd_path}")
    
    # Read input
    content = pf_ncd_path.read_text(encoding='utf-8')
    
    # Parse to structured format
    parsed = parse_ncdn(content)
    
    # Convert to NCI
    nci_data = to_nci(parsed)
    
    # Determine output path
    if pf_ncd_path.name.endswith('.pf.ncd'):
        output_path = pf_ncd_path.with_suffix('.nci.json')
        # Handle double suffix
        output_path = pf_ncd_path.parent / (pf_ncd_path.stem.replace('.pf', '.pf.nci') + '.json')
    else:
        output_path = pf_ncd_path.with_suffix('.nci.json')
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(nci_data, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Parsed {len(parsed['lines'])} lines")
    print(f"[OK] Generated {len(nci_data)} inference groups")
    print(f"[OK] Output: {output_path}")
    
    return str(output_path)


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python parse_to_nci.py <path/to/file.pf.ncd>")
        print("\nThis script parses a Post-Formalized NormCode file and outputs")
        print("a NormCode Inference JSON file for activation.")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    try:
        output_path = parse_pf_ncd_to_nci(input_path)
        print(f"\n[SUCCESS] NCI file created: {output_path}")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

