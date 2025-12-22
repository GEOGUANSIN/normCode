"""
Syntax Highlighter for NormCode Files

Provides syntax highlighting for .ncd, .nc, and .ncn file formats.
"""

import re
from typing import List, Tuple


class SyntaxHighlighter:
    """Syntax highlighter for NormCode formats."""
    
    # Color scheme
    COLORS = {
        'operator': '#ff79c6',  # Pink
        'concept': '#8be9fd',   # Cyan
        'keyword': '#bd93f9',   # Purple
        'string': '#f1fa8c',    # Yellow
        'comment': '#6272a4',   # Gray
        'annotation': '#50fa7b', # Green
        'flow_index': '#ffb86c', # Orange
        'sequence_type': '#ff5555' # Red
    }
    
    @classmethod
    def highlight_ncd(cls, content: str) -> str:
        """
        Generate syntax-highlighted HTML for .ncd format.
        
        Args:
            content: .ncd file content
            
        Returns:
            HTML string with syntax highlighting
        """
        lines = content.split('\n')
        highlighted_lines = []
        
        for line in lines:
            highlighted = cls._highlight_ncd_line(line)
            highlighted_lines.append(highlighted)
        
        html = '<pre style="background-color: #282a36; color: #f8f8f2; padding: 10px; border-radius: 5px; font-family: monospace;">'
        html += '\n'.join(highlighted_lines)
        html += '</pre>'
        
        return html
    
    @classmethod
    def _highlight_ncd_line(cls, line: str) -> str:
        """Highlight a single .ncd line."""
        if not line.strip():
            return line
        
        # Preserve leading whitespace
        leading_spaces = len(line) - len(line.lstrip())
        indent = line[:leading_spaces]
        content = line[leading_spaces:]
        
        # Check for annotations first
        if content.startswith('?:'):
            color = cls.COLORS['annotation']
            return f'{indent}<span style="color: {color}">?:</span>{cls._escape_html(content[2:])}'
        elif content.startswith('/:'):
            color = cls.COLORS['annotation']
            return f'{indent}<span style="color: {color}">/:< /span>{cls._escape_html(content[2:])}'
        elif content.startswith('...:'):
            color = cls.COLORS['annotation']
            return f'{indent}<span style="color: {color}">...:</span>{cls._escape_html(content[4:])}'
        
        # Highlight operators
        if content.startswith('<='):
            op_color = cls.COLORS['operator']
            rest = content[2:].strip()
            result = f'{indent}<span style="color: {op_color}">&lt;=</span> '
            result += cls._highlight_concept_content(rest)
            return result
        elif content.startswith('<-'):
            op_color = cls.COLORS['operator']
            rest = content[2:].strip()
            result = f'{indent}<span style="color: {op_color}">&lt;-</span> '
            result += cls._highlight_concept_content(rest)
            return result
        elif content.startswith(':<:'):
            op_color = cls.COLORS['operator']
            rest = content[3:]
            result = f'{indent}<span style="color: {op_color}">:&lt;:</span>'
            result += cls._highlight_concept_content(rest)
            return result
        
        # Default: highlight any concept syntax
        return indent + cls._highlight_concept_content(content)
    
    @classmethod
    def _highlight_concept_content(cls, content: str) -> str:
        """Highlight concept syntax within content."""
        # Split by | to separate metadata
        if '|' in content:
            parts = content.split('|', 1)
            concept_part = parts[0]
            metadata_part = parts[1] if len(parts) > 1 else ""
            
            highlighted = cls._highlight_concept_syntax(concept_part)
            
            if metadata_part:
                # Highlight flow index
                flow_match = re.match(r'^\s*([\d.]+)', metadata_part)
                if flow_match:
                    flow_idx = flow_match.group(1)
                    color = cls.COLORS['flow_index']
                    highlighted += f' <span style="color: {color}">| {flow_idx}</span>'
                    rest = metadata_part[flow_match.end():]
                    
                    # Highlight sequence type
                    seq_types = ['imperative', 'grouping', 'assigning', 'quantifying', 'timing', 'judgement', 'simple']
                    for seq in seq_types:
                        if seq in rest:
                            color = cls.COLORS['sequence_type']
                            rest = rest.replace(seq, f'<span style="color: {color}">{seq}</span>')
                            break
                    
                    highlighted += rest
                else:
                    highlighted += ' | ' + cls._escape_html(metadata_part)
            
            return highlighted
        else:
            return cls._highlight_concept_syntax(content)
    
    @classmethod
    def _highlight_concept_syntax(cls, content: str) -> str:
        """Highlight concept bracket syntax."""
        # Highlight {} [] <> :: etc.
        result = content
        
        # Concept brackets
        result = re.sub(r'(\{[^}]*\})', lambda m: f'<span style="color: {cls.COLORS["concept"]}">{cls._escape_html(m.group(1))}</span>', result)
        result = re.sub(r'(\[[^\]]*\])', lambda m: f'<span style="color: {cls.COLORS["concept"]}">{cls._escape_html(m.group(1))}</span>', result)
        result = re.sub(r'(&lt;[^&gt;]*&gt;)', lambda m: f'<span style="color: {cls.COLORS["concept"]}">{m.group(1)}</span>', result)
        
        # Operators
        result = re.sub(r'(::|\$=|\$\.|\$%|\$\+|@if|@if!|@after|@by|&in|&across|\*every)', 
                       lambda m: f'<span style="color: {cls.COLORS["keyword"]}">{cls._escape_html(m.group(1))}</span>', result)
        
        return result
    
    @classmethod
    def highlight_nc(cls, content: str) -> str:
        """
        Generate syntax-highlighted HTML for .nc format.
        
        Args:
            content: .nc file content
            
        Returns:
            HTML string with syntax highlighting
        """
        lines = content.split('\n')
        highlighted_lines = []
        
        for line in lines:
            if not line.strip():
                highlighted_lines.append(line)
                continue
            
            # Format: flow_index.type|content
            if '|' in line:
                parts = line.split('|', 1)
                metadata = parts[0]
                content_part = parts[1] if len(parts) > 1 else ""
                
                # Highlight flow index
                flow_color = cls.COLORS['flow_index']
                type_color = cls.COLORS['sequence_type']
                
                highlighted = f'<span style="color: {flow_color}">{cls._escape_html(metadata)}</span>'
                highlighted += '<span style="color: ' + cls.COLORS['operator'] + '">|</span>'
                highlighted += cls._highlight_concept_syntax(content_part)
                
                highlighted_lines.append(highlighted)
            else:
                highlighted_lines.append(cls._escape_html(line))
        
        html = '<pre style="background-color: #282a36; color: #f8f8f2; padding: 10px; border-radius: 5px; font-family: monospace;">'
        html += '\n'.join(highlighted_lines)
        html += '</pre>'
        
        return html
    
    @classmethod
    def highlight_ncn(cls, content: str) -> str:
        """
        Generate syntax-highlighted HTML for .ncn format.
        
        Args:
            content: .ncn file content
            
        Returns:
            HTML string with syntax highlighting
        """
        # .ncn is similar to .ncd but with natural language
        # Use simplified highlighting
        lines = content.split('\n')
        highlighted_lines = []
        
        for line in lines:
            if not line.strip():
                highlighted_lines.append(line)
                continue
            
            # Preserve leading whitespace
            leading_spaces = len(line) - len(line.lstrip())
            indent = line[:leading_spaces]
            content_part = line[leading_spaces:]
            
            # Highlight operators
            if content_part.startswith('<='):
                op_color = cls.COLORS['operator']
                rest = content_part[2:].strip()
                highlighted = f'{indent}<span style="color: {op_color}">&lt;=</span> {cls._escape_html(rest)}'
            elif content_part.startswith('<-'):
                op_color = cls.COLORS['operator']
                rest = content_part[2:].strip()
                highlighted = f'{indent}<span style="color: {op_color}">&lt;-</span> {cls._escape_html(rest)}'
            elif content_part.startswith(':<:'):
                op_color = cls.COLORS['operator']
                rest = content_part[3:]
                highlighted = f'{indent}<span style="color: {op_color}">:&lt;:</span>{cls._escape_html(rest)}'
            else:
                highlighted = indent + cls._escape_html(content_part)
            
            highlighted_lines.append(highlighted)
        
        html = '<pre style="background-color: #282a36; color: #f8f8f2; padding: 10px; border-radius: 5px; font-family: monospace;">'
        html += '\n'.join(highlighted_lines)
        html += '</pre>'
        
        return html
    
    @classmethod
    def _escape_html(cls, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    @classmethod
    def get_css(cls) -> str:
        """Get custom CSS for syntax highlighting."""
        return """
        <style>
        .normcode-editor {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
            background-color: #282a36;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .normcode-editor pre {
            margin: 0;
            padding: 0;
        }
        </style>
        """

