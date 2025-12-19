"""
Parser Service - NormCode file parsing and format conversion

Wraps the unified_parser from streamlit_app/editor_subapp
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add streamlit_app to path for importing unified_parser
streamlit_app_path = Path(__file__).parent.parent.parent.parent / "streamlit_app" / "editor_subapp"
sys.path.insert(0, str(streamlit_app_path))

try:
    from unified_parser import UnifiedParser
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False
    UnifiedParser = None


class ParserService:
    """Service for parsing and converting NormCode files."""
    
    def __init__(self):
        if PARSER_AVAILABLE:
            self.parser = UnifiedParser()
        else:
            self.parser = None
    
    @property
    def is_available(self) -> bool:
        """Check if the parser is available."""
        return PARSER_AVAILABLE and self.parser is not None
    
    def parse_ncd(self, ncd_content: str, ncn_content: str = "") -> Dict[str, Any]:
        """
        Parse NCD (and optionally NCN) content to structured JSON.
        
        Args:
            ncd_content: The NCD file content
            ncn_content: Optional NCN file content for merging
            
        Returns:
            Dict with 'lines' key containing parsed line structures
        """
        if not self.is_available:
            raise RuntimeError("Parser not available")
        
        return self.parser.parse(ncd_content, ncn_content)
    
    def parse_ncdn(self, ncdn_content: str) -> Dict[str, Any]:
        """
        Parse NCDN content to structured JSON.
        
        Args:
            ncdn_content: The NCDN file content
            
        Returns:
            Dict with 'lines' key containing parsed line structures
        """
        if not self.is_available:
            raise RuntimeError("Parser not available")
        
        return self.parser.parse_ncdn(ncdn_content)
    
    def serialize_to_ncd_ncn(self, parsed_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Convert parsed JSON to NCD and NCN formats.
        
        Args:
            parsed_data: The parsed JSON structure
            
        Returns:
            Dict with 'ncd' and 'ncn' keys
        """
        if not self.is_available:
            raise RuntimeError("Parser not available")
        
        return self.parser.serialize(parsed_data)
    
    def serialize_to_ncdn(self, parsed_data: Dict[str, Any]) -> str:
        """
        Convert parsed JSON to NCDN format.
        
        Args:
            parsed_data: The parsed JSON structure
            
        Returns:
            NCDN formatted string
        """
        if not self.is_available:
            raise RuntimeError("Parser not available")
        
        return self.parser.serialize_ncdn(parsed_data)
    
    def to_nci(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert parsed JSON to NCI (inference) format.
        
        Args:
            parsed_data: The parsed JSON structure
            
        Returns:
            List of inference groups
        """
        if not self.is_available:
            raise RuntimeError("Parser not available")
        
        return self.parser.to_nci(parsed_data)
    
    def get_flow_indices(self, content: str, file_format: str = "ncd") -> List[Dict[str, Any]]:
        """
        Parse content and return lines with flow indices.
        
        Args:
            content: File content
            file_format: Format type ('ncd', 'ncdn', etc.)
            
        Returns:
            List of line dicts with flow_index, content, type, depth
        """
        if not self.is_available:
            raise RuntimeError("Parser not available")
        
        if file_format == "ncdn":
            parsed = self.parser.parse_ncdn(content)
        else:
            parsed = self.parser.parse(content, "")
        
        return parsed.get('lines', [])
    
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
        if not self.is_available:
            raise RuntimeError("Parser not available")
        
        # Parse the source content
        if from_format == "ncdn":
            parsed = self.parser.parse_ncdn(content)
        elif from_format == "ncd":
            parsed = self.parser.parse(content, "")
        elif from_format == "ncn":
            # NCN alone doesn't have structure, just return as-is or empty
            parsed = {"lines": []}
        else:
            parsed = {"lines": []}
        
        # Convert to target format
        if to_format == "ncd":
            result = self.parser.serialize(parsed)
            return result.get('ncd', '')
        elif to_format == "ncn":
            result = self.parser.serialize(parsed)
            return result.get('ncn', '')
        elif to_format == "ncdn":
            return self.parser.serialize_ncdn(parsed)
        elif to_format == "json":
            import json
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        elif to_format == "nci":
            import json
            nci = self.parser.to_nci(parsed)
            return json.dumps(nci, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unknown target format: {to_format}")


# Singleton instance
_parser_service: Optional[ParserService] = None


def get_parser_service() -> ParserService:
    """Get the singleton parser service instance."""
    global _parser_service
    if _parser_service is None:
        _parser_service = ParserService()
    return _parser_service
