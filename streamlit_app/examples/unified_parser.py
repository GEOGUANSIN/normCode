import os
import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

# Skeleton for parsing .ncd and .ncn files to produce .nc.json

def load_file(path: str) -> str:
    """Helper to read file content."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

class UnifiedParser:
    def __init__(self):
        pass

    def _calculate_depth(self, line: str) -> int:
        """Calculate indentation depth (4 spaces = 1 level)."""
        stripped = line.lstrip()
        spaces = len(line) - len(stripped)
        return spaces // 4

    def assign_flow_indices(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Parse lines and assign flow indices based on structure.
        Returns a list of dicts with line info and flow_index.
        """
        parsed_lines = []
        indices = []  # Stack of counters for each depth
        
        for raw_line in lines:
            if not raw_line.strip():
                continue
                
            depth = self._calculate_depth(raw_line)
            content = raw_line.strip()
            
            # Check if it's a concept line (starts with :<:, <=, <-)
            is_concept = False
            main_part = content
            inline_comment = None
            
            # Check if this is an NCN annotation line (starts with |?{natural language}:)
            # These should NOT be split on | - keep the full content
            is_ncn_annotation = content.startswith('|?{natural language}:') or content.startswith('|?{')
            
            # Split inline comments/metadata, but NOT for NCN annotation lines
            if '|' in content and not is_ncn_annotation:
                parts = content.split('|', 1)
                main_part = parts[0].strip()
                inline_comment = parts[1].strip()
            
            for prefix in [':<:', '<=', '<-']:
                if main_part.startswith(prefix):
                    is_concept = True
                    break
            
            flow_index = None
            
            if is_concept:
                # Ensure indices list is long enough for current depth
                while len(indices) <= depth:
                    indices.append(0)
                
                # Remove deeper indices if we moved up or stayed same
                indices = indices[:depth+1]
                
                # Increment counter at current depth
                indices[depth] += 1
                
                # Generate flow index string (e.g., "1.2.1")
                flow_index = ".".join(map(str, indices))
            else:
                # For comments/annotations, inherit the flow index of the preceding concept
                # Find the last concept line's flow index
                if parsed_lines:
                    for prev in reversed(parsed_lines):
                        if prev['type'] == 'main' and prev['flow_index']:
                            flow_index = prev['flow_index']
                            break
            
            # Handle case where line starts with pipe (empty main part but has comment)
            # Treat as a single comment line preserving the pipe
            if not is_concept and not main_part and inline_comment:
                parsed_lines.append({
                    "raw_line": raw_line,
                    "content": f"| {inline_comment}",
                    "depth": depth,
                    "flow_index": flow_index,
                    "type": "comment"
                })
            else:
                # Add the main concept line
                if is_concept or main_part:
                    parsed_lines.append({
                        "raw_line": raw_line,
                        "content": main_part,
                        "depth": depth,
                        "flow_index": flow_index,
                        "type": "main" if is_concept else "comment"
                    })
                
                # Add separate line for inline comment if present
                if inline_comment:
                    parsed_lines.append({
                        "raw_line": "",  # Synthetic line
                        "content": inline_comment,
                        "depth": depth,  # Keep same depth as parent
                        "flow_index": flow_index,
                        "type": "inline_comment"
                    })
            
        return parsed_lines

    def parse(self, ncd_content: str, ncn_content: str) -> Dict[str, Any]:
        """
        Parse .ncd and .ncn formats together and produce a JSON structure.
        
        Args:
            ncd_content: Draft format (structure source)
            ncn_content: Natural language format
            
        Returns:
            Dict representing the .nc.json structure
        """
        print("Parsing started...")
        
        ncd_lines = ncd_content.splitlines()
        ncn_lines = ncn_content.splitlines()
        
        parsed_ncd = self.assign_flow_indices(ncd_lines)
        parsed_ncn = self.assign_flow_indices(ncn_lines)
        
        # Create a map of ncn lines by flow_index for easy lookup
        # Only map 'main' types since comments might not match or exist in ncn
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
            
            # Map content based on type
            if line['type'] == 'main':
                merged_item['nc_main'] = line['content']
                # Try to find matching ncn content
                if line['flow_index'] in ncn_map:
                    merged_item['ncn_content'] = ncn_map[line['flow_index']]
            elif line['type'] == 'inline_comment':
                merged_item['nc_comment'] = line['content']
            elif line['type'] == 'comment':
                merged_item['nc_comment'] = line['content']
            
            merged_lines.append(merged_item)
        
        result = {
            "lines": merged_lines
        }
        
        print("Parsing finished (Skeleton).")
        return result

    def serialize(self, parsed_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Convert parsed JSON structure back to .ncd and .ncn strings.
        
        Args:
            parsed_data: The JSON structure (dict with 'lines' key)
            
        Returns:
            Dict with keys 'ncd' and 'ncn' containing the generated file contents
        """
        ncd_lines = []
        ncn_lines = []
        
        for line in parsed_data['lines']:
            depth = line['depth']
            indent = "    " * depth
            
            # --- Reconstruct .ncd ---
            if line['type'] == 'main':
                content = line.get('nc_main', '')
                ncd_line = f"{indent}{content}"
                ncd_lines.append(ncd_line)
            elif line['type'] == 'inline_comment':
                # Append to the previous line with a pipe
                if ncd_lines:
                    ncd_lines[-1] = f"{ncd_lines[-1]} | {line.get('nc_comment', '')}"
            elif line['type'] == 'comment':
                content = line.get('nc_comment', '')
                ncd_line = f"{indent}{content}"
                ncd_lines.append(ncd_line)
                
            # --- Reconstruct .ncn ---
            if line['type'] == 'main':
                content = line.get('ncn_content', '')
                if content:
                    ncn_line = f"{indent}{content}"
                    ncn_lines.append(ncn_line)
            
        return {
            "ncd": "\n".join(ncd_lines) + "\n",
            "ncn": "\n".join(ncn_lines) + "\n"
        }
    
    def serialize_ncdn(self, parsed_data: Dict[str, Any]) -> str:
        """
        Convert parsed JSON structure to .ncdn format.
        .ncdn shows NCD with inline NCN annotations.
        
        Format:
        <NCD line> | <inline_comment>
            |?{natural language}: <NCN content>
        
        Args:
            parsed_data: The JSON structure (dict with 'lines' key)
            
        Returns:
            String in .ncdn format
        """
        ncdn_lines = []
        i = 0
        lines_list = parsed_data['lines']
        
        while i < len(lines_list):
            line = lines_list[i]
            depth = line['depth']
            indent = "    " * depth
            
            # Add main NCD content
            if line['type'] == 'main':
                content = line.get('nc_main', '')
                current_line = f"{indent}{content}"
                
                # Check if next line is an inline_comment for this main line
                if i + 1 < len(lines_list) and lines_list[i + 1]['type'] == 'inline_comment':
                    inline_comment = lines_list[i + 1].get('nc_comment', '')
                    current_line = f"{current_line} | {inline_comment}"
                    i += 1  # Skip the inline_comment line in next iteration
                
                ncdn_lines.append(current_line)
                
                # Add NCN annotation if present
                if 'ncn_content' in line and line['ncn_content']:
                    ncn_content = line['ncn_content']
                    ncdn_lines.append(f"{indent}    |?{{natural language}}: {ncn_content}")
                    
            elif line['type'] == 'comment':
                content = line.get('nc_comment', '')
                ncdn_lines.append(f"{indent}{content}")
            
            i += 1
        
        return "\n".join(ncdn_lines) + "\n"
    
    def parse_ncdn(self, ncdn_content: str) -> Dict[str, Any]:
        """
        Parse .ncdn format into JSON structure.
        
        Format:
        <NCD line> | <inline_comment>
            |?{natural language}: <NCN content>
        
        Args:
            ncdn_content: Content of .ncdn file
            
        Returns:
            Dict representing the .nc.json structure
        """
        lines = ncdn_content.splitlines()
        parsed_ncd = self.assign_flow_indices(lines)
        
        merged_lines = []
        i = 0
        
        while i < len(parsed_ncd):
            line = parsed_ncd[i]
            
            merged_item = {
                "flow_index": line['flow_index'],
                "type": line['type'],
                "depth": line['depth']
            }
            
            # Map content based on type
            if line['type'] == 'main':
                merged_item['nc_main'] = line['content']
                
                # Look ahead for inline_comment and NCN annotation
                # The order after a main line could be:
                # 1. inline_comment (optional)
                # 2. NCN annotation (optional, starts with |?{natural language}:)
                lookahead = i + 1
                
                # Check for inline_comment first
                if lookahead < len(parsed_ncd) and parsed_ncd[lookahead]['type'] == 'inline_comment':
                    # The inline_comment will be handled in its own iteration
                    lookahead += 1
                
                # Now check for NCN annotation
                if lookahead < len(parsed_ncd):
                    next_line = parsed_ncd[lookahead]
                    next_content = next_line['content']
                    
                    if next_content.startswith('|?{natural language}:') or next_content.startswith('|?{'):
                        # Extract NCN content
                        if '|?{natural language}:' in next_content:
                            ncn_content = next_content.split('|?{natural language}:', 1)[1].strip()
                        else:
                            # Handle shorter format |?{...}: 
                            ncn_content = next_content.split(':', 1)[1].strip() if ':' in next_content else ''
                        merged_item['ncn_content'] = ncn_content
                        # Mark this NCN line to be skipped (we'll handle it by checking in the loop)
                        
            elif line['type'] == 'inline_comment':
                merged_item['nc_comment'] = line['content']
            elif line['type'] == 'comment':
                # Skip NCN annotation lines - they were already processed with their main line
                if line['content'].startswith('|?{natural language}:') or line['content'].startswith('|?{'):
                    i += 1
                    continue
                merged_item['nc_comment'] = line['content']
            
            merged_lines.append(merged_item)
            i += 1
        
        return {
            "lines": merged_lines
        }

if __name__ == "__main__":
    # Paths to example files
    base_path = os.path.dirname(os.path.abspath(__file__))
    ncd_path = os.path.join(base_path, "example.ncd")
    ncn_path = os.path.join(base_path, "example.ncn")
    output_path = os.path.join(base_path, "example.nc.json")

    # Load contents
    try:
        ncd_content = load_file(ncd_path)
        ncn_content = load_file(ncn_path)
        
        print(f"Loaded files from {base_path}")
        
        parser = UnifiedParser()
        json_output = parser.parse(ncd_content, ncn_content)
        
        # Save to .nc.json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, indent=2)
            
        print(f"\nSuccessfully saved parsed output to {output_path}")
        
        # Test reverse serialization
        serialized = parser.serialize(json_output)
        
        print("\n" + "="*30)
        print("RECONSTRUCTED .NCD:")
        print("="*30)
        print(serialized['ncd'])
        
        print("\n" + "="*30)
        print("RECONSTRUCTED .NCN:")
        print("="*30)
        print(serialized['ncn'])
        
        # Test .ncdn format
        print("\n" + "="*30)
        print("NCDN FORMAT (NCD + NCN Annotations):")
        print("="*30)
        ncdn_output = parser.serialize_ncdn(json_output)
        print(ncdn_output)
        
        # Save .ncdn file
        ncdn_path = os.path.join(base_path, "example.ncdn")
        with open(ncdn_path, 'w', encoding='utf-8') as f:
            f.write(ncdn_output)
        print(f"Saved to {ncdn_path}")
        
        # Test round-trip: .ncdn -> JSON -> .ncd/.ncn
        print("\n" + "="*30)
        print("NCDN ROUND-TRIP TEST:")
        print("="*30)
        reparsed_json = parser.parse_ncdn(ncdn_output)
        re_serialized = parser.serialize(reparsed_json)
        
        def normalize(text):
            return "\n".join([l.rstrip() for l in text.strip().splitlines()])
        
        ncdn_ncd_match = normalize(serialized['ncd']) == normalize(re_serialized['ncd'])
        ncdn_ncn_match = normalize(serialized['ncn']) == normalize(re_serialized['ncn'])
        
        print(f".ncdn -> .ncd consistency: {ncdn_ncd_match}")
        print(f".ncdn -> .ncn consistency: {ncdn_ncn_match}")
        
        # Verify original consistency
        print("\n" + "="*30)
        print("ORIGINAL CONSISTENCY CHECK:")
        print("="*30)
            
        ncd_match = normalize(ncd_content) == normalize(serialized['ncd'])
        ncn_match = normalize(ncn_content) == normalize(serialized['ncn'])
        
        print(f".ncd matches original: {ncd_match}")
        if not ncd_match:
            print("Original ncd length:", len(normalize(ncd_content)))
            print("Reconstructed ncd length:", len(normalize(serialized['ncd'])))
            
        print(f".ncn matches original: {ncn_match}")
        if not ncn_match:
            print("Original ncn length:", len(normalize(ncn_content)))
            print("Reconstructed ncn length:", len(normalize(serialized['ncn'])))
            
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
