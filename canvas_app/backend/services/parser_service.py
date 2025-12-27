"""
Parser Service - File parsing and format conversion.

This service provides a unified interface for parsing various file formats.
It uses the parser registry to support multiple file types in a plugin-like manner.

The service maintains backwards compatibility with the original API while
delegating to the new parser infrastructure.
"""

from typing import Dict, Any, List, Optional

from .parsers import ParserRegistry, get_parser, BaseParser
from config.file_types import is_normcode_format, get_file_type_config


class ParserService:
    """
    Service for parsing and converting files.
    
    Provides a unified interface for parsing different file formats.
    Uses the parser registry to support extensible file type handling.
    """
    
    def __init__(self):
        """Initialize the parser service."""
        # Parser registry is auto-initialized when parsers module is imported
        pass
    
    @property
    def is_available(self) -> bool:
        """Check if any parser is available."""
        return len(ParserRegistry.get_supported_formats()) > 0
    
    def get_supported_formats(self) -> List[str]:
        """Get list of all supported format names."""
        return ParserRegistry.get_supported_formats()
    
    def supports_format(self, format_name: str) -> bool:
        """Check if a format is supported."""
        return ParserRegistry.is_supported(format_name)
    
    # =========================================================================
    # NormCode-specific Methods (Backwards Compatible)
    # =========================================================================
    
    def parse_ncd(self, ncd_content: str, ncn_content: str = "") -> Dict[str, Any]:
        """
        Parse NCD (and optionally NCN) content to structured JSON.
        
        Args:
            ncd_content: The NCD file content
            ncn_content: Optional NCN file content for merging
            
        Returns:
            Dict with 'lines' key containing parsed line structures
        """
        parser = get_parser('ncd')
        if not parser:
            raise RuntimeError("NormCode parser not available")
        
        result = parser.parse(ncd_content, 'ncd', ncn_content=ncn_content)
        if not result.success:
            raise RuntimeError(f"Parse error: {', '.join(result.errors)}")
        
        return {"lines": result.lines}
    
    def parse_ncdn(self, ncdn_content: str) -> Dict[str, Any]:
        """
        Parse NCDN content to structured JSON.
        
        Args:
            ncdn_content: The NCDN file content
            
        Returns:
            Dict with 'lines' key containing parsed line structures
        """
        parser = get_parser('ncdn')
        if not parser:
            raise RuntimeError("NormCode parser not available")
        
        result = parser.parse(ncdn_content, 'ncdn')
        if not result.success:
            raise RuntimeError(f"Parse error: {', '.join(result.errors)}")
        
        return {"lines": result.lines}
    
    def serialize_to_ncd_ncn(self, parsed_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Convert parsed JSON to NCD and NCN formats.
        
        Args:
            parsed_data: The parsed JSON structure
            
        Returns:
            Dict with 'ncd' and 'ncn' keys
        """
        parser = get_parser('ncd')
        if not parser:
            raise RuntimeError("NormCode parser not available")
        
        ncd_result = parser.serialize(parsed_data, 'ncd')
        ncn_result = parser.serialize(parsed_data, 'ncn')
        
        return {
            "ncd": ncd_result.content if ncd_result.success else "",
            "ncn": ncn_result.content if ncn_result.success else ""
        }
    
    def serialize_to_ncdn(self, parsed_data: Dict[str, Any]) -> str:
        """
        Convert parsed JSON to NCDN format.
        
        Args:
            parsed_data: The parsed JSON structure
            
        Returns:
            NCDN formatted string
        """
        parser = get_parser('ncdn')
        if not parser:
            raise RuntimeError("NormCode parser not available")
        
        result = parser.serialize(parsed_data, 'ncdn')
        if not result.success:
            raise RuntimeError(f"Serialize error: {', '.join(result.errors)}")
        
        return result.content
    
    def to_nci(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert parsed JSON to NCI (inference) format.
        
        Args:
            parsed_data: The parsed JSON structure
            
        Returns:
            List of inference groups
        """
        parser = get_parser('ncd')
        if not parser:
            raise RuntimeError("NormCode parser not available")
        
        result = parser.serialize(parsed_data, 'nci')
        if not result.success:
            raise RuntimeError(f"Serialize error: {', '.join(result.errors)}")
        
        # NCI is JSON, need to parse it
        import json
        return json.loads(result.content)
    
    # =========================================================================
    # Generic Methods
    # =========================================================================
    
    def parse(self, content: str, format: str, **kwargs) -> Dict[str, Any]:
        """
        Parse content of any supported format.
        
        Args:
            content: File content
            format: Format identifier (e.g., 'ncd', 'json', 'yaml')
            **kwargs: Format-specific options
            
        Returns:
            Dict with 'lines' key and format-specific data
        """
        parser = get_parser(format)
        if not parser:
            raise RuntimeError(f"No parser available for format: {format}")
        
        result = parser.parse(content, format, **kwargs)
        if not result.success:
            raise RuntimeError(f"Parse error: {', '.join(result.errors)}")
        
        return {
            "lines": result.lines,
            "warnings": result.warnings,
            "metadata": result.metadata
        }
    
    def serialize(self, parsed_data: Dict[str, Any], source_format: str, target_format: str) -> str:
        """
        Serialize parsed data to a target format.
        
        Args:
            parsed_data: Parsed data structure
            source_format: Original format (to find the right parser)
            target_format: Target format
            
        Returns:
            Serialized content string
        """
        parser = get_parser(source_format)
        if not parser:
            raise RuntimeError(f"No parser available for format: {source_format}")
        
        result = parser.serialize(parsed_data, target_format)
        if not result.success:
            raise RuntimeError(f"Serialize error: {', '.join(result.errors)}")
        
        return result.content
    
    def get_flow_indices(self, content: str, file_format: str = "ncd") -> List[Dict[str, Any]]:
        """
        Parse content and return lines with flow indices.
        
        Args:
            content: File content
            file_format: Format type ('ncd', 'ncdn', etc.)
            
        Returns:
            List of line dicts with flow_index, content, type, depth
        """
        parser = get_parser(file_format)
        if not parser:
            raise RuntimeError(f"No parser available for format: {file_format}")
        
        result = parser.parse(content, file_format)
        return result.lines if result.success else []
    
    def convert_format(self, content: str, from_format: str, to_format: str) -> str:
        """
        Convert content from one format to another.
        
        Args:
            content: Source content
            from_format: Source format ('ncd', 'ncn', 'ncdn')
            to_format: Target format ('ncd', 'ncn', 'ncdn', 'json', 'nci')
            
        Returns:
            Converted content string
        """
        parser = get_parser(from_format)
        if not parser:
            raise RuntimeError(f"No parser available for format: {from_format}")
        
        # Parse the source content
        parse_result = parser.parse(content, from_format)
        if not parse_result.success:
            raise RuntimeError(f"Parse error: {', '.join(parse_result.errors)}")
        
        parsed_data = {"lines": parse_result.lines}
        
        # Serialize to target format
        serialize_result = parser.serialize(parsed_data, to_format)
        if not serialize_result.success:
            raise RuntimeError(f"Serialize error: {', '.join(serialize_result.errors)}")
        
        return serialize_result.content
    
    def validate(self, content: str, format: str) -> Dict[str, Any]:
        """
        Validate content against format rules.
        
        Args:
            content: File content
            format: Format identifier
            
        Returns:
            Dict with 'valid', 'errors', 'warnings' keys
        """
        parser = get_parser(format)
        if not parser:
            return {
                "valid": False,
                "errors": [f"No parser available for format: {format}"],
                "warnings": [],
                "format": format
            }
        
        return parser.validate(content, format)


# =============================================================================
# Singleton Instance
# =============================================================================

_parser_service: Optional[ParserService] = None


def get_parser_service() -> ParserService:
    """Get the singleton parser service instance."""
    global _parser_service
    if _parser_service is None:
        _parser_service = ParserService()
    return _parser_service
