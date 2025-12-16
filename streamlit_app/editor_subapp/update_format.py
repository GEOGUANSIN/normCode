"""
NormCode Format Update and Migration Script

This script provides utilities to:
1. Convert between different NormCode formats (.ncd, .ncn, .ncdn, .nc.json, .nci.json)
2. Validate format consistency
3. Batch process multiple files
4. Fix common format issues
5. Generate missing companion files

Usage:
    python update_format.py convert input.ncd --to ncdn
    python update_format.py validate example.ncd example.ncn
    python update_format.py batch-convert ./files --from ncd --to ncdn
    python update_format.py generate-companion input.ncd --ncn --json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from unified_parser import UnifiedParser, load_file


class FormatUpdater:
    """Handles format conversion, validation, and updates."""
    
    def __init__(self):
        self.parser = UnifiedParser()
        
    def convert_file(self, input_path: str, output_format: str, output_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Convert a file to a different NormCode format.
        
        Args:
            input_path: Path to input file
            output_format: Target format (ncd, ncn, ncdn, nc.json, nci.json)
            output_path: Optional output path (auto-generated if None)
            
        Returns:
            Tuple of (success, message/error)
        """
        try:
            # Determine input format
            input_ext = Path(input_path).suffix.lower()
            
            # Load and parse input
            parsed_data = self._load_any_format(input_path)
            
            if parsed_data is None:
                return False, f"Could not parse {input_path}"
            
            # Generate output path if not provided
            if output_path is None:
                output_path = self._generate_output_path(input_path, output_format)
            
            # Convert to target format
            success = self._write_format(parsed_data, output_path, output_format)
            
            if success:
                return True, f"Converted {input_path} -> {output_path}"
            else:
                return False, f"Failed to write {output_path}"
                
        except Exception as e:
            return False, f"Error converting {input_path}: {e}"
    
    def _load_any_format(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load a file in any supported format and return parsed JSON structure."""
        ext = Path(file_path).suffix.lower()
        
        try:
            if ext == '.json':
                # Check if it's .nc.json or .nci.json
                if file_path.endswith('.nci.json'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        nci_data = json.load(f)
                    return self.parser.from_nci(nci_data)
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                        
            elif ext == '.ncdn':
                content = load_file(file_path)
                return self.parser.parse_ncdn(content)
                
            elif ext == '.ncd':
                # Look for companion .ncn file
                ncd_content = load_file(file_path)
                ncn_path = file_path[:-4] + '.ncn'
                ncn_content = load_file(ncn_path) if os.path.exists(ncn_path) else ""
                return self.parser.parse(ncd_content, ncn_content)
                
            elif ext == '.ncn':
                # Load as NCN only (will create minimal structure)
                ncn_content = load_file(file_path)
                # Try to find companion .ncd
                ncd_path = file_path[:-4] + '.ncd'
                ncd_content = load_file(ncd_path) if os.path.exists(ncd_path) else ""
                return self.parser.parse(ncd_content, ncn_content)
                
            else:
                print(f"Unknown file extension: {ext}")
                return None
                
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None
    
    def _write_format(self, parsed_data: Dict[str, Any], output_path: str, format_type: str) -> bool:
        """Write parsed data to specified format."""
        try:
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            
            if format_type == 'ncd':
                serialized = self.parser.serialize(parsed_data)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(serialized['ncd'])
                    
            elif format_type == 'ncn':
                serialized = self.parser.serialize(parsed_data)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(serialized['ncn'])
                    
            elif format_type == 'ncdn':
                ncdn_content = self.parser.serialize_ncdn(parsed_data)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(ncdn_content)
                    
            elif format_type == 'nc.json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(parsed_data, f, indent=2, ensure_ascii=False)
                    
            elif format_type == 'nci.json':
                nci_data = self.parser.to_nci(parsed_data)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(nci_data, f, indent=2, ensure_ascii=False)
                    
            else:
                print(f"Unknown output format: {format_type}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Error writing {output_path}: {e}")
            return False
    
    def _generate_output_path(self, input_path: str, format_type: str) -> str:
        """Generate output path based on input path and target format."""
        base = Path(input_path).stem
        
        # Remove format-specific suffixes
        if base.endswith('.nc'):
            base = base[:-3]
        elif base.endswith('.nci'):
            base = base[:-4]
        
        parent = Path(input_path).parent
        
        if format_type == 'ncd':
            return str(parent / f"{base}.ncd")
        elif format_type == 'ncn':
            return str(parent / f"{base}.ncn")
        elif format_type == 'ncdn':
            return str(parent / f"{base}.ncdn")
        elif format_type == 'nc.json':
            return str(parent / f"{base}.nc.json")
        elif format_type == 'nci.json':
            return str(parent / f"{base}.nci.json")
        else:
            return str(parent / f"{base}_converted.txt")
    
    def validate_files(self, ncd_path: str, ncn_path: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Validate NormCode files for consistency.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        try:
            # Load files
            if not os.path.exists(ncd_path):
                return False, [f"File not found: {ncd_path}"]
            
            ncd_content = load_file(ncd_path)
            ncn_content = ""
            
            if ncn_path:
                if os.path.exists(ncn_path):
                    ncn_content = load_file(ncn_path)
                else:
                    issues.append(f"Companion file not found: {ncn_path}")
            
            # Parse
            parsed = self.parser.parse(ncd_content, ncn_content)
            
            if not parsed or 'lines' not in parsed:
                return False, ["Failed to parse files"]
            
            lines = parsed['lines']
            
            # Validation checks
            flow_indices = set()
            prev_depth = -1
            
            for idx, line in enumerate(lines):
                # Check required fields
                if 'type' not in line:
                    issues.append(f"Line {idx}: Missing 'type' field")
                
                if 'depth' not in line:
                    issues.append(f"Line {idx}: Missing 'depth' field")
                else:
                    depth = line['depth']
                    
                    # Check depth consistency (shouldn't jump more than 1 level)
                    if prev_depth >= 0 and depth > prev_depth + 1:
                        issues.append(f"Line {idx}: Depth jump from {prev_depth} to {depth}")
                    
                    if line['type'] == 'main':
                        prev_depth = depth
                
                # Check flow indices
                flow_idx = line.get('flow_index')
                if flow_idx:
                    if flow_idx in flow_indices and line['type'] == 'main':
                        issues.append(f"Line {idx}: Duplicate flow index {flow_idx}")
                    flow_indices.add(flow_idx)
                
                # Check content fields
                if line['type'] == 'main':
                    if 'nc_main' not in line:
                        issues.append(f"Line {idx}: Main line missing 'nc_main' field")
                elif line['type'] in ['comment', 'inline_comment']:
                    if 'nc_comment' not in line:
                        issues.append(f"Line {idx}: Comment line missing 'nc_comment' field")
            
            # Test round-trip
            try:
                serialized = self.parser.serialize(parsed)
                reparsed = self.parser.parse(serialized['ncd'], serialized['ncn'])
                
                if len(reparsed['lines']) != len(parsed['lines']):
                    issues.append(f"Round-trip test failed: Line count mismatch ({len(parsed['lines'])} vs {len(reparsed['lines'])})")
            except Exception as e:
                issues.append(f"Round-trip test failed: {e}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            return False, [f"Validation error: {e}"]
    
    def batch_convert(self, directory: str, from_format: str, to_format: str, recursive: bool = False) -> Dict[str, Any]:
        """
        Batch convert files in a directory.
        
        Returns:
            Dict with conversion statistics
        """
        stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'files': []
        }
        
        # Map format names to extensions
        ext_map = {
            'ncd': '.ncd',
            'ncn': '.ncn',
            'ncdn': '.ncdn',
            'json': '.nc.json',
            'nci': '.nci.json'
        }
        
        search_ext = ext_map.get(from_format)
        if not search_ext:
            print(f"Unknown format: {from_format}")
            return stats
        
        # Find files
        pattern = f"**/*{search_ext}" if recursive else f"*{search_ext}"
        files = list(Path(directory).glob(pattern))
        
        stats['total'] = len(files)
        
        for file_path in files:
            success, message = self.convert_file(str(file_path), to_format)
            
            if success:
                stats['success'] += 1
                stats['files'].append({'file': str(file_path), 'status': 'success', 'message': message})
            else:
                stats['failed'] += 1
                stats['files'].append({'file': str(file_path), 'status': 'failed', 'message': message})
        
        return stats
    
    def generate_companions(self, input_path: str, generate_ncn: bool = False, 
                          generate_json: bool = False, generate_ncdn: bool = False,
                          generate_nci: bool = False) -> List[str]:
        """
        Generate companion files for an existing NormCode file.
        
        Returns:
            List of generated file paths
        """
        generated = []
        
        try:
            # Load input
            parsed_data = self._load_any_format(input_path)
            
            if parsed_data is None:
                print(f"Could not load {input_path}")
                return generated
            
            base_path = Path(input_path).stem
            if base_path.endswith('.nc'):
                base_path = base_path[:-3]
            elif base_path.endswith('.nci'):
                base_path = base_path[:-4]
            
            parent = Path(input_path).parent
            
            # Generate requested formats
            if generate_ncn:
                output_path = str(parent / f"{base_path}.ncn")
                if self._write_format(parsed_data, output_path, 'ncn'):
                    generated.append(output_path)
            
            if generate_json:
                output_path = str(parent / f"{base_path}.nc.json")
                if self._write_format(parsed_data, output_path, 'nc.json'):
                    generated.append(output_path)
            
            if generate_ncdn:
                output_path = str(parent / f"{base_path}.ncdn")
                if self._write_format(parsed_data, output_path, 'ncdn'):
                    generated.append(output_path)
            
            if generate_nci:
                output_path = str(parent / f"{base_path}.nci.json")
                if self._write_format(parsed_data, output_path, 'nci.json'):
                    generated.append(output_path)
            
            return generated
            
        except Exception as e:
            print(f"Error generating companions: {e}")
            return generated


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="NormCode Format Update and Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single file
  python update_format.py convert example.ncd --to ncdn
  
  # Validate files
  python update_format.py validate example.ncd example.ncn
  
  # Batch convert directory
  python update_format.py batch-convert ./files --from ncd --to ncdn --recursive
  
  # Generate companion files
  python update_format.py generate example.ncd --ncn --json --ncdn
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert a file to another format')
    convert_parser.add_argument('input', help='Input file path')
    convert_parser.add_argument('--to', dest='format', required=True, 
                               choices=['ncd', 'ncn', 'ncdn', 'nc.json', 'nci.json'],
                               help='Target format')
    convert_parser.add_argument('--output', '-o', help='Output file path (optional)')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate NormCode files')
    validate_parser.add_argument('ncd', help='NCD file path')
    validate_parser.add_argument('ncn', nargs='?', help='NCN file path (optional)')
    
    # Batch convert command
    batch_parser = subparsers.add_parser('batch-convert', help='Batch convert files in directory')
    batch_parser.add_argument('directory', help='Directory to process')
    batch_parser.add_argument('--from', dest='from_format', required=True,
                             choices=['ncd', 'ncn', 'ncdn', 'json', 'nci'],
                             help='Source format')
    batch_parser.add_argument('--to', dest='to_format', required=True,
                             choices=['ncd', 'ncn', 'ncdn', 'nc.json', 'nci.json'],
                             help='Target format')
    batch_parser.add_argument('--recursive', '-r', action='store_true',
                             help='Process subdirectories recursively')
    
    # Generate companions command
    gen_parser = subparsers.add_parser('generate', help='Generate companion files')
    gen_parser.add_argument('input', help='Input file path')
    gen_parser.add_argument('--ncn', action='store_true', help='Generate .ncn file')
    gen_parser.add_argument('--json', action='store_true', help='Generate .nc.json file')
    gen_parser.add_argument('--ncdn', action='store_true', help='Generate .ncdn file')
    gen_parser.add_argument('--nci', action='store_true', help='Generate .nci.json file')
    gen_parser.add_argument('--all', action='store_true', help='Generate all companion formats')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    updater = FormatUpdater()
    
    # Execute command
    if args.command == 'convert':
        success, message = updater.convert_file(args.input, args.format, args.output)
        print(message)
        sys.exit(0 if success else 1)
        
    elif args.command == 'validate':
        is_valid, issues = updater.validate_files(args.ncd, args.ncn)
        
        if is_valid:
            print(f"✅ Validation passed for {args.ncd}")
        else:
            print(f"❌ Validation failed for {args.ncd}")
            print("\nIssues found:")
            for issue in issues:
                print(f"  - {issue}")
        
        sys.exit(0 if is_valid else 1)
        
    elif args.command == 'batch-convert':
        print(f"Batch converting {args.from_format} -> {args.to_format} in {args.directory}")
        stats = updater.batch_convert(args.directory, args.from_format, args.to_format, args.recursive)
        
        print(f"\nResults:")
        print(f"  Total files: {stats['total']}")
        print(f"  Success: {stats['success']}")
        print(f"  Failed: {stats['failed']}")
        
        if stats['failed'] > 0:
            print("\nFailed files:")
            for file_info in stats['files']:
                if file_info['status'] == 'failed':
                    print(f"  - {file_info['file']}: {file_info['message']}")
        
        sys.exit(0 if stats['failed'] == 0 else 1)
        
    elif args.command == 'generate':
        gen_ncn = args.ncn or args.all
        gen_json = args.json or args.all
        gen_ncdn = args.ncdn or args.all
        gen_nci = args.nci or args.all
        
        generated = updater.generate_companions(args.input, gen_ncn, gen_json, gen_ncdn, gen_nci)
        
        if generated:
            print(f"✅ Generated {len(generated)} companion file(s):")
            for path in generated:
                print(f"  - {path}")
        else:
            print("❌ No files generated")
        
        sys.exit(0 if generated else 1)


if __name__ == "__main__":
    main()




