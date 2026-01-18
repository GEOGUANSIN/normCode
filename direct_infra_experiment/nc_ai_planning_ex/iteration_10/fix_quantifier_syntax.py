"""
Script to fix quantifier syntax in repos files.
Changes <{ALL True}> to <ALL True> (removes curly braces from quantifiers).
"""

import json
import re
from pathlib import Path


def fix_quantifier_syntax(text: str) -> str:
    """
    Replace <{QUANTIFIER CONDITION}> with <QUANTIFIER CONDITION>.
    
    Examples:
        <{ALL True}> -> <ALL True>
        <{ANY True}> -> <ANY True>
        <{ALL False}> -> <ALL False>
    """
    # Pattern matches <{...}> and captures the content
    pattern = r'<\{(\w+\s+(?:True|False))\}>'
    replacement = r'<\1>'
    return re.sub(pattern, replacement, text)


def process_json_file(file_path: Path) -> int:
    """Process a JSON file and fix quantifier syntax in all string values."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count matches before replacement
    matches = re.findall(r'<\{(\w+\s+(?:True|False))\}>', content)
    count = len(matches)
    
    if count == 0:
        print(f"  No quantifier patterns found in {file_path.name}")
        return 0
    
    # Apply fix
    fixed_content = fix_quantifier_syntax(content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"  Fixed {count} quantifier patterns in {file_path.name}")
    for match in matches[:5]:  # Show first 5 examples
        print(f"    <{{{match}}}> -> <{match}>")
    if len(matches) > 5:
        print(f"    ... and {len(matches) - 5} more")
    
    return count


def main():
    repos_dir = Path("direct_infra_experiment/nc_ai_planning_ex/iteration_10/repos")
    
    if not repos_dir.exists():
        print(f"Error: Directory not found: {repos_dir}")
        return
    
    total_fixed = 0
    
    for json_file in repos_dir.glob("*.json"):
        print(f"\nProcessing {json_file.name}...")
        total_fixed += process_json_file(json_file)
    
    print(f"\n{'='*50}")
    print(f"Total: Fixed {total_fixed} quantifier patterns across all files.")


if __name__ == "__main__":
    main()

