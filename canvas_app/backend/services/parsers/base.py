"""
Base parser interface for the parser plugin system.

All parsers should inherit from BaseParser and implement the required methods.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ParseResult:
    """Result of parsing content."""
    success: bool
    lines: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "lines": self.lines,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


@dataclass
class SerializeResult:
    """Result of serializing parsed data."""
    success: bool
    content: str = ""
    errors: List[str] = field(default_factory=list)


class BaseParser(ABC):
    """
    Abstract base class for file parsers.
    
    Parsers handle the conversion between raw text content and structured
    representations (typically a list of line dictionaries with metadata).
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the parser."""
        pass
    
    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """
        List of format identifiers this parser handles.
        
        Examples: ['ncd', 'ncn', 'ncdn'] for NormCode parser
        """
        pass
    
    @property
    def category(self) -> str:
        """
        Category of files this parser handles.
        
        Examples: 'normcode', 'code', 'data', 'text'
        """
        return "generic"
    
    @abstractmethod
    def parse(self, content: str, format: str, **kwargs) -> ParseResult:
        """
        Parse raw content into structured representation.
        
        Args:
            content: Raw file content as string
            format: Format identifier (e.g., 'ncd', 'json')
            **kwargs: Format-specific options
            
        Returns:
            ParseResult with parsed lines and any errors/warnings
        """
        pass
    
    @abstractmethod
    def serialize(self, parsed_data: Dict[str, Any], target_format: str, **kwargs) -> SerializeResult:
        """
        Serialize parsed data back to text format.
        
        Args:
            parsed_data: Dictionary with 'lines' key containing parsed structure
            target_format: Target format to serialize to
            **kwargs: Format-specific options
            
        Returns:
            SerializeResult with serialized content
        """
        pass
    
    def validate(self, content: str, format: str) -> Dict[str, Any]:
        """
        Validate content without full parsing.
        
        Args:
            content: Raw file content
            format: Format identifier
            
        Returns:
            Dict with 'valid', 'errors', 'warnings' keys
        """
        # Default implementation - just try to parse
        result = self.parse(content, format)
        return {
            "valid": result.success and len(result.errors) == 0,
            "errors": result.errors,
            "warnings": result.warnings,
            "format": format,
        }
    
    def get_line_at_index(self, parsed_data: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Get a specific line by index."""
        lines = parsed_data.get('lines', [])
        if 0 <= index < len(lines):
            return lines[index]
        return None
    
    def supports_format(self, format: str) -> bool:
        """Check if this parser supports the given format."""
        return format.lower() in [f.lower() for f in self.supported_formats]

