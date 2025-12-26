"""
Parser system for canvas_app.

This module provides a plugin-based parser architecture for handling
different file formats. Parsers register themselves with the registry
and can be retrieved by format name.

Usage:
    from services.parsers import get_parser, ParserRegistry
    
    # Get a parser for a specific format
    parser = get_parser('ncd')
    if parser:
        result = parser.parse(content)
        
    # Register a new parser
    ParserRegistry.register(MyCustomParser())
"""

from .base import BaseParser, ParseResult, SerializeResult
from .registry import ParserRegistry, get_parser, is_format_supported
from .normcode import NormCodeParser
from .paradigm import ParadigmParser

# Auto-register built-in parsers
ParserRegistry.register(NormCodeParser())
ParserRegistry.register(ParadigmParser())

__all__ = [
    'BaseParser',
    'ParseResult', 
    'SerializeResult',
    'ParserRegistry',
    'get_parser',
    'is_format_supported',
    'NormCodeParser',
    'ParadigmParser',
]

