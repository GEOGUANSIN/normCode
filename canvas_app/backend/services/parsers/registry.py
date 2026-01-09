"""
Parser registry for managing available parsers.

The registry provides a central place to register and retrieve parsers
by format name, enabling a plugin-style architecture.
"""

from typing import Dict, Optional, List, Type
from .base import BaseParser


class ParserRegistry:
    """
    Central registry for parser plugins.
    
    Parsers register themselves with the registry and can be retrieved
    by format name. This enables easy extension with new file type support.
    """
    
    _parsers: Dict[str, BaseParser] = {}
    _parser_instances: List[BaseParser] = []
    
    @classmethod
    def register(cls, parser: BaseParser) -> None:
        """
        Register a parser for its supported formats.
        
        Args:
            parser: Parser instance to register
        """
        cls._parser_instances.append(parser)
        for format_name in parser.supported_formats:
            format_key = format_name.lower()
            if format_key in cls._parsers:
                existing = cls._parsers[format_key]
                print(f"Warning: Overwriting parser for '{format_key}' "
                      f"(was: {existing.name}, now: {parser.name})")
            cls._parsers[format_key] = parser
    
    @classmethod
    def unregister(cls, format_name: str) -> bool:
        """
        Unregister a parser for a specific format.
        
        Args:
            format_name: Format to unregister
            
        Returns:
            True if a parser was unregistered
        """
        format_key = format_name.lower()
        if format_key in cls._parsers:
            del cls._parsers[format_key]
            return True
        return False
    
    @classmethod
    def get(cls, format_name: str) -> Optional[BaseParser]:
        """
        Get the parser for a specific format.
        
        Args:
            format_name: Format identifier (e.g., 'ncd', 'json')
            
        Returns:
            Parser instance or None if not found
        """
        return cls._parsers.get(format_name.lower())
    
    @classmethod
    def is_supported(cls, format_name: str) -> bool:
        """Check if a format is supported."""
        return format_name.lower() in cls._parsers
    
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """Get list of all supported format names."""
        return list(cls._parsers.keys())
    
    @classmethod
    def get_all_parsers(cls) -> List[BaseParser]:
        """Get list of all registered parser instances."""
        return cls._parser_instances.copy()
    
    @classmethod
    def get_formats_by_category(cls, category: str) -> List[str]:
        """Get all formats in a specific category."""
        formats = []
        for format_name, parser in cls._parsers.items():
            if parser.category == category:
                formats.append(format_name)
        return formats
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered parsers (mainly for testing)."""
        cls._parsers.clear()
        cls._parser_instances.clear()


# Convenience functions
def get_parser(format_name: str) -> Optional[BaseParser]:
    """Get the parser for a specific format."""
    return ParserRegistry.get(format_name)


def is_format_supported(format_name: str) -> bool:
    """Check if a format is supported by any registered parser."""
    return ParserRegistry.is_supported(format_name)

