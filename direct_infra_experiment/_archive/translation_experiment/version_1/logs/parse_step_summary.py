#!/usr/bin/env python3
"""
Parse orchestrator log files to extract MFP step names, MVP values, and OR outputs
for judgement and imperative related sequences.
"""

import re
import json
import ast
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field


@dataclass
class StepInfo:
    """Information extracted from a step."""
    sequence_type: str
    sequence_number: int
    timestamp: str
    mfp_name: Optional[str] = None
    mvp_values: Optional[str] = None
    or_output: Optional[str] = None


@dataclass
class SequenceContext:
    """Context tracking for current sequence."""
    sequence_type: Optional[str] = None
    sequence_number: int = 0
    timestamp: Optional[str] = None
    is_judgement_or_imperative: bool = False
    
    # Step data
    in_ir: bool = False
    in_mfp: bool = False
    in_mvp: bool = False
    in_or: bool = False
    
    # Collected data
    mfp_name: Optional[str] = None
    ir_function_concept_name: Optional[str] = None  # Fallback for MFP name
    mvp_values: Optional[str] = None
    or_output: Optional[str] = None
    
    # Parsing state
    current_section: Optional[str] = None
    collecting_tensor: bool = False
    tensor_lines: List[str] = field(default_factory=list)


def is_judgement_or_imperative_sequence(sequence_name: str) -> bool:
    """Check if sequence is judgement or imperative related."""
    judgement_patterns = ['judgement', 'judgment']
    imperative_patterns = ['imperative']
    
    seq_lower = sequence_name.lower()
    return any(pattern in seq_lower for pattern in judgement_patterns) or \
           any(pattern in seq_lower for pattern in imperative_patterns)


def extract_timestamp(line: str) -> Optional[str]:
    """Extract timestamp from log line."""
    match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
    return match.group(1) if match else None


def extract_sequence_name(line: str) -> Optional[str]:
    """Extract sequence name from EXECUTING line."""
    match = re.search(r'=====EXECUTING (\w+(?:\s+\w+)*) SEQUENCE=====', line)
    if match:
        return match.group(1).strip()
    return None


# Note: extract_mfp_step_name function removed - we now extract directly from Concept Name field


def parse_log_file(log_path: Path) -> List[StepInfo]:
    """Parse log file and extract step information."""
    results: List[StepInfo] = []
    context = SequenceContext()
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()
            
            # Check for sequence start
            if '=====EXECUTING' in line and 'SEQUENCE=====' in line:
                # Save previous sequence if it was judgement/imperative
                if context.is_judgement_or_imperative and context.sequence_type:
                    if context.mfp_name or context.mvp_values or context.or_output:
                        results.append(StepInfo(
                            sequence_type=context.sequence_type,
                            sequence_number=context.sequence_number,
                            timestamp=context.timestamp or '',
                            mfp_name=context.mfp_name,
                            mvp_values=context.mvp_values,
                            or_output=context.or_output
                        ))
                
                # Start new sequence
                seq_name = extract_sequence_name(line)
                timestamp = extract_timestamp(line)
                if seq_name:
                    context = SequenceContext()
                    context.sequence_type = seq_name
                    context.timestamp = timestamp
                    context.is_judgement_or_imperative = is_judgement_or_imperative_sequence(seq_name)
                    context.sequence_number = len([r for r in results if r.sequence_type == seq_name]) + 1
                    continue
            
            # Skip if not in a relevant sequence
            if not context.is_judgement_or_imperative:
                continue
            
            # Extract timestamp if available
            if not context.timestamp:
                timestamp = extract_timestamp(line)
                if timestamp:
                    context.timestamp = timestamp
            
            # Detect IR section (to capture function concept name as fallback for MFP)
            if '--- States after IR' in line:
                context.in_ir = True
                context.in_mfp = False
                context.in_mvp = False
                context.in_or = False
                context.current_section = None
                context.collecting_tensor = False
                context.tensor_lines = []
                context.ir_function_concept_name = None  # Reset
                continue
            
            # Extract function concept name from IR section (for MFP fallback)
            if context.in_ir and context.current_section == 'Function':
                match = re.search(r'Concept ID:[^,]+,\s*Name:\s*([^,]+?)(?:,\s*Type:|$)', line)
                if match:
                    context.ir_function_concept_name = match.group(1).strip()
            
            # Detect MFP section (States after MFP)
            if '--- States after MFP' in line:
                # Keep in_mfp flag if already set (from step start)
                if not context.in_mfp:
                    context.in_mfp = True
                context.in_ir = False
                context.in_mvp = False
                context.in_or = False
                context.current_section = None
                context.collecting_tensor = False
                context.tensor_lines = []
                continue
            
            # Detect MVP section
            if '--- States after MVP' in line:
                context.in_mvp = True
                context.in_mfp = False
                context.in_or = False
                context.current_section = None
                context.collecting_tensor = False
                context.tensor_lines = []
                continue
            
            # Detect OR section
            if '--- States after OR' in line:
                context.in_or = True
                context.in_mfp = False
                context.in_mvp = False
                context.current_section = None
                context.collecting_tensor = False
                context.tensor_lines = []
                continue
            
            # Detect section end
            if '---' in line and ('Step' in line or 'States after' in line):
                # End of current step section
                if context.collecting_tensor:
                    tensor_content = '\n'.join(context.tensor_lines).strip()
                    if tensor_content:
                        if context.in_mfp and context.current_section == 'Function':
                            # Extract function name from tensor
                            if not context.mfp_name:
                                # Try to extract from tensor content
                                match = re.search(r'<function\s+([^>]+)>', tensor_content)
                                if match:
                                    context.mfp_name = match.group(1).strip()
                                elif 'function' in tensor_content.lower():
                                    context.mfp_name = tensor_content[:200]  # Truncate if too long
                        
                        elif context.in_mvp and context.current_section == 'Values':
                            context.mvp_values = tensor_content
                        
                        elif context.in_or and context.current_section == 'Inference':
                            context.or_output = tensor_content
                    
                    context.collecting_tensor = False
                    context.tensor_lines = []
                    context.current_section = None
                continue
            
            # Detect MFP step start (before States after MFP)
            if '---Step' in line and 'Model Function Perception (MFP)' in line:
                context.in_mfp = True
                context.mfp_name = None  # Reset for new MFP step
                # Continue processing to capture step name from following lines
                continue
            
            # Extract MFP step name from Concept Name in Function section (after States after MFP)
            # This is the PRIMARY source - extract from "Name: ..." in the Concept ID line
            if context.in_mfp and context.current_section == 'Function':
                # Look for "Concept ID: ... Name: ..." pattern
                match = re.search(r'Concept ID:[^,]+,\s*Name:\s*([^,]+?)(?:,\s*Type:|$)', line)
                if match:
                    mfp_name = match.group(1).strip()
                    context.mfp_name = mfp_name
                # If no Concept Name found in MFP Function section, use IR's function concept name as fallback
                elif not context.mfp_name and context.ir_function_concept_name:
                    context.mfp_name = context.ir_function_concept_name
            
            # Detect section type (Function, Values, Context, Inference)
            if context.in_ir or context.in_mfp or context.in_mvp or context.in_or:
                if 'Function:' in line:
                    context.current_section = 'Function'
                    context.collecting_tensor = False
                    context.tensor_lines = []
                elif 'Values:' in line:
                    context.current_section = 'Values'
                    context.collecting_tensor = False
                    context.tensor_lines = []
                elif 'Context:' in line:
                    context.current_section = 'Context'
                    context.collecting_tensor = False
                    context.tensor_lines = []
                elif 'Inference:' in line:
                    context.current_section = 'Inference'
                    context.collecting_tensor = False
                    context.tensor_lines = []
            
            # Collect Reference Tensor lines
            if (context.in_mfp or context.in_mvp or context.in_or) and context.current_section:
                if 'Reference Tensor:' in line:
                    context.collecting_tensor = True
                    # Extract tensor content from same line if present
                    tensor_match = re.search(r'Reference Tensor:\s*(.+)', line)
                    if tensor_match:
                        tensor_content = tensor_match.group(1).strip()
                        context.tensor_lines.append(tensor_content)
                        
                        # Process immediately if it's a single-line tensor
                        if tensor_content and not tensor_content.endswith('\\'):
                            tensor_content = '\n'.join(context.tensor_lines).strip()
                            if tensor_content:
                                if context.in_mfp and context.current_section == 'Function':
                                    if not context.mfp_name:
                                        match = re.search(r'<function\s+([^>]+)>', tensor_content)
                                        if match:
                                            context.mfp_name = match.group(1).strip()
                                elif context.in_mvp and context.current_section == 'Values':
                                    context.mvp_values = tensor_content
                                elif context.in_or and context.current_section == 'Inference':
                                    context.or_output = tensor_content
                            context.collecting_tensor = False
                            context.tensor_lines = []
                elif context.collecting_tensor:
                    # Continue collecting tensor lines (multi-line tensors)
                    if line.strip() and not line.strip().startswith('---'):
                        # Check if this is a new section indicator
                        if any(keyword in line for keyword in ['Function:', 'Values:', 'Context:', 'Inference:', 'Step Name:', 'Current Step:']):
                            # End tensor collection
                            tensor_content = '\n'.join(context.tensor_lines).strip()
                            if tensor_content:
                                if context.in_mfp and context.current_section == 'Function':
                                    if not context.mfp_name:
                                        match = re.search(r'<function\s+([^>]+)>', tensor_content)
                                        if match:
                                            context.mfp_name = match.group(1).strip()
                                elif context.in_mvp and context.current_section == 'Values':
                                    context.mvp_values = tensor_content
                                elif context.in_or and context.current_section == 'Inference':
                                    context.or_output = tensor_content
                            context.collecting_tensor = False
                            context.tensor_lines = []
                        else:
                            # Remove timestamp prefix if present
                            clean_line = re.sub(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - [A-Z]+ - ', '', line)
                            if clean_line.strip():
                                context.tensor_lines.append(clean_line.strip())
        
        # Save last sequence if applicable
        if context.is_judgement_or_imperative and context.sequence_type:
            if context.mfp_name or context.mvp_values or context.or_output:
                results.append(StepInfo(
                    sequence_type=context.sequence_type,
                    sequence_number=context.sequence_number,
                    timestamp=context.timestamp or '',
                    mfp_name=context.mfp_name,
                    mvp_values=context.mvp_values,
                    or_output=context.or_output
                ))
    
    return results


def process_mvp_values(mvp_string: str, max_length: int = 2000) -> str:
    """
    Process MVP values string:
    1. Parse as Python literal (list/dict)
    2. Truncate only 'prompt_template' field if it exists
    3. Convert \n to actual newlines for display
    """
    if not mvp_string:
        return mvp_string
    
    try:
        # Try to parse as Python literal (handles lists, dicts, etc.)
        parsed = ast.literal_eval(mvp_string)
        
        def truncate_prompt_template(obj: Union[dict, list]) -> Union[dict, list]:
            """Recursively truncate prompt_template fields."""
            if isinstance(obj, dict):
                result = {}
                for key, value in obj.items():
                    if key == 'prompt_template' and isinstance(value, str):
                        if len(value) > max_length:
                            result[key] = value[:max_length] + "\n... (truncated)"
                        else:
                            result[key] = value
                    elif isinstance(value, (dict, list)):
                        result[key] = truncate_prompt_template(value)
                    else:
                        result[key] = value
                return result
            elif isinstance(obj, list):
                return [truncate_prompt_template(item) for item in obj]
            else:
                return obj
        
        # Truncate prompt_template if present
        processed = truncate_prompt_template(parsed)
        
        # Convert back to string representation with proper formatting and actual newlines
        def to_formatted_string(obj: Union[dict, list], indent: int = 0) -> str:
            """Convert object to formatted string with actual newlines for display."""
            indent_str = '  ' * indent
            if isinstance(obj, dict):
                lines = ['{']
                items = []
                for key, value in obj.items():
                    if isinstance(value, str):
                        # String values are already parsed (ast.literal_eval converted \n to actual newlines)
                        # Format as Python dict with actual newlines preserved
                        # Use triple quotes for multi-line strings to preserve newlines
                        if '\n' in value:
                            # Multi-line string - use triple quotes
                            escaped_value = value.replace('\\', '\\\\').replace('"""', '\\"\\"\\"')
                            items.append(f'{indent_str}  {repr(key)}: """{escaped_value}"""')
                        else:
                            # Single-line string - use regular quotes
                            items.append(f'{indent_str}  {repr(key)}: {repr(value)}')
                    elif isinstance(value, (dict, list)):
                        items.append(f'{indent_str}  {repr(key)}: {to_formatted_string(value, indent + 1)}')
                    else:
                        items.append(f'{indent_str}  {repr(key)}: {repr(value)}')
                lines.append(',\n'.join(items))
                lines.append(f'{indent_str}}}')
                return '\n'.join(lines)
            elif isinstance(obj, list):
                if not obj:
                    return '[]'
                lines = ['[']
                items = [to_formatted_string(item, indent + 1) for item in obj]
                lines.append(',\n'.join(f'{indent_str}  {item}' for item in items))
                lines.append(f'{indent_str}]')
                return '\n'.join(lines)
            else:
                return repr(obj)
        
        formatted = to_formatted_string(processed)
        # Replace escaped newlines that might still be in the representation with actual newlines
        # This handles cases where the original string had literal \n sequences
        formatted = formatted.replace('\\n', '\n').replace('\\t', '\t')
        return formatted
        
    except (ValueError, SyntaxError):
        # If parsing fails, just truncate the whole string and convert newlines
        if len(mvp_string) > max_length:
            truncated = mvp_string[:max_length] + "\n... (truncated)"
        else:
            truncated = mvp_string
        # Convert escaped newlines to actual newlines
        return truncated.replace('\\n', '\n').replace('\\t', '\t')


def generate_statistics(results: List[StepInfo]) -> Dict:
    """Generate statistics about the extracted sequences."""
    from collections import Counter
    from datetime import datetime
    
    stats = {
        'total_sequences': len(results),
        'by_type': Counter(r.sequence_type for r in results),
        'has_mfp': sum(1 for r in results if r.mfp_name),
        'has_mvp': sum(1 for r in results if r.mvp_values),
        'has_or': sum(1 for r in results if r.or_output),
        'complete': sum(1 for r in results if r.mfp_name and r.or_output),
        'timestamps': []
    }
    
    # Parse timestamps for duration calculation
    if results:
        try:
            first_ts = datetime.strptime(results[0].timestamp, '%Y-%m-%d %H:%M:%S,%f')
            last_ts = datetime.strptime(results[-1].timestamp, '%Y-%m-%d %H:%M:%S,%f')
            stats['duration_seconds'] = (last_ts - first_ts).total_seconds()
            stats['first_timestamp'] = results[0].timestamp
            stats['last_timestamp'] = results[-1].timestamp
        except (ValueError, IndexError):
            stats['duration_seconds'] = None
    
    # Calculate coverage percentages
    if stats['total_sequences'] > 0:
        stats['mfp_coverage'] = (stats['has_mfp'] / stats['total_sequences']) * 100
        stats['mvp_coverage'] = (stats['has_mvp'] / stats['total_sequences']) * 100
        stats['or_coverage'] = (stats['has_or'] / stats['total_sequences']) * 100
        stats['complete_coverage'] = (stats['complete'] / stats['total_sequences']) * 100
    else:
        stats['mfp_coverage'] = 0
        stats['mvp_coverage'] = 0
        stats['or_coverage'] = 0
        stats['complete_coverage'] = 0
    
    return stats


def format_output(results: List[StepInfo], output_format: str = 'markdown', include_stats: bool = True) -> str:
    """Format results as markdown or JSON."""
    if output_format == 'json':
        json_data = [{
            'sequence_type': r.sequence_type,
            'sequence_number': r.sequence_number,
            'timestamp': r.timestamp,
            'mfp_name': r.mfp_name,
            'mvp_values': r.mvp_values,
            'or_output': r.or_output
        } for r in results]
        if include_stats:
            json_data = {
                'statistics': generate_statistics(results),
                'sequences': json_data
            }
        return json.dumps(json_data, indent=2)
    
    # Markdown format
    stats = generate_statistics(results) if include_stats else None
    
    lines = [
        "# Step Summary: MFP Names, MVP Values, and OR Outputs",
        "",
        "**Extracted from orchestrator log for judgement and imperative sequences**",
        "",
        f"**Total Sequences Found**: {len(results)}",
        ""
    ]
    
    # Add statistics section
    if stats:
        lines.extend([
            "## Statistics",
            "",
            f"- **Total Sequences**: {stats['total_sequences']}",
            f"- **Sequence Types**: {dict(stats['by_type'])}",
            "",
            "### Data Coverage",
            f"- **MFP Names**: {stats['has_mfp']}/{stats['total_sequences']} ({stats['mfp_coverage']:.1f}%)",
            f"- **MVP Values**: {stats['has_mvp']}/{stats['total_sequences']} ({stats['mvp_coverage']:.1f}%)",
            f"- **OR Outputs**: {stats['has_or']}/{stats['total_sequences']} ({stats['or_coverage']:.1f}%)",
            f"- **Complete** (MFP + OR): {stats['complete']}/{stats['total_sequences']} ({stats['complete_coverage']:.1f}%)",
            ""
        ])
        
        if stats.get('duration_seconds') is not None:
            lines.extend([
                "### Timeline",
                f"- **First Sequence**: {stats['first_timestamp']}",
                f"- **Last Sequence**: {stats['last_timestamp']}",
                f"- **Total Duration**: {stats['duration_seconds']:.2f} seconds",
                ""
            ])
        
        lines.append("---")
        lines.append("")
    else:
        lines.append("---")
        lines.append("")
    
    for i, result in enumerate(results, 1):
        lines.append(f"## Sequence {i}: {result.sequence_type} (#{result.sequence_number})")
        lines.append(f"**Timestamp**: {result.timestamp}")
        lines.append("")
        
        if result.mfp_name:
            lines.append("### MFP Step Name")
            lines.append("```")
            lines.append(result.mfp_name)
            lines.append("```")
            lines.append("")
        
        if result.mvp_values:
            lines.append("### MVP Values")
            lines.append("```")
            # Process MVP values: truncate only prompt_template, convert \n to actual newlines
            mvp_display = process_mvp_values(result.mvp_values, max_length=2000)
            lines.append(mvp_display)
            lines.append("```")
            lines.append("")
        
        if result.or_output:
            lines.append("### OR Output")
            lines.append("```")
            # Convert escaped newlines to actual newlines for OR output too
            or_display = result.or_output
            # Replace escaped newlines with actual newlines
            or_display = or_display.replace('\\n', '\n').replace('\\t', '\t')
            # Truncate if very long
            if len(or_display) > 2000:
                or_display = or_display[:2000] + "\n... (truncated)"
            lines.append(or_display)
            lines.append("```")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return '\n'.join(lines)


def find_newest_log_file(search_directories: List[Path] = None) -> Optional[Path]:
    """Find the newest orchestrator log file in the given directories."""
    if search_directories is None:
        # Default: check current directory, script directory, and script directory's parent
        script_dir = Path(__file__).parent
        search_directories = [Path.cwd(), script_dir, script_dir.parent]
    
    # Look for orchestrator log files in all directories
    log_pattern = 'orchestrator_log_*.txt'
    all_log_files = []
    
    for directory in search_directories:
        if directory.exists() and directory.is_dir():
            log_files = list(directory.glob(log_pattern))
            all_log_files.extend(log_files)
    
    if not all_log_files:
        return None
    
    # Remove duplicates and sort by modification time (newest first)
    unique_files = list(set(all_log_files))
    unique_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return unique_files[0]


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Parse orchestrator log to extract MFP names, MVP values, and OR outputs'
    )
    parser.add_argument('log_file', type=Path, nargs='?', default=None,
                       help='Path to orchestrator log file (default: newest orchestrator_log_*.txt in current directory)')
    parser.add_argument('-o', '--output', type=Path, help='Output file path (default: <log_file>_summary.md)')
    parser.add_argument('-f', '--format', choices=['markdown', 'json'], default='markdown',
                       help='Output format (default: markdown)')
    parser.add_argument('--no-stats', action='store_true',
                       help='Skip statistics section in output')
    
    args = parser.parse_args()
    
    # If no log file specified, find the newest one
    if args.log_file is None:
        log_file = find_newest_log_file()
        if log_file is None:
            print("Error: No log file specified and no orchestrator_log_*.txt files found")
            print(f"Searched in:")
            script_dir = Path(__file__).parent
            print(f"  - Current directory: {Path.cwd()}")
            print(f"  - Script directory: {script_dir}")
            print(f"  - Parent directory: {script_dir.parent}")
            return 1
        args.log_file = log_file
        print(f"Using newest log file: {args.log_file}")
    
    if not args.log_file.exists():
        print(f"Error: Log file not found: {args.log_file}")
        return 1
    
    print(f"Parsing log file: {args.log_file}")
    results = parse_log_file(args.log_file)
    
    print(f"Found {len(results)} relevant sequences")
    
    # Determine output file
    if args.output:
        output_path = args.output
    else:
        output_path = args.log_file.parent / f"{args.log_file.stem}_summary.{'json' if args.format == 'json' else 'md'}"
    
    # Format and write output
    output_content = format_output(results, args.format, include_stats=not args.no_stats)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_content)
    
    print(f"Summary written to: {output_path}")
    
    # Print summary statistics to console
    if not args.no_stats:
        stats = generate_statistics(results)
        print(f"\nStatistics:")
        print(f"  Total sequences: {stats['total_sequences']}")
        print(f"  Sequence types: {dict(stats['by_type'])}")
        print(f"  Coverage - MFP: {stats['mfp_coverage']:.1f}%, MVP: {stats['mvp_coverage']:.1f}%, OR: {stats['or_coverage']:.1f}%")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

