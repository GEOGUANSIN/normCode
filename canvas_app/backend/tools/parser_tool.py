"""
Parser Tool - NormCode parsing capabilities for agents.

This tool wraps the ParserService and provides parsing/serialization
capabilities that can be injected into a Body instance.

The tool enables agents to:
1. Parse NormCode files (ncd, ncn, ncdn, ncds) into structured JSON
2. Serialize structured JSON back to NormCode formats
3. Convert between formats
4. Extract flow indices and concept information
5. Convert to NCI (inference) format for execution
"""

import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class CanvasParserTool:
    """
    A tool for parsing and serializing NormCode content.
    
    This tool provides the Body with access to the editor's parser,
    enabling agents to programmatically work with NormCode files.
    
    Usage patterns:
    1. Parse NCDS content to get structured lines with flow indices
    2. Convert between formats (ncd ↔ ncdn ↔ ncds ↔ json ↔ nci)
    3. Extract concept type information from lines
    4. Generate NCI for execution pipelines
    """
    
    def __init__(self):
        """Initialize the parser tool with the singleton ParserService."""
        self._parser = None  # Lazy initialization
    
    def _get_parser(self):
        """Get the parser service (lazy load to avoid import issues)."""
        if self._parser is None:
            try:
                from services.parser_service import get_parser_service
                self._parser = get_parser_service()
            except ImportError as e:
                logger.error(f"Failed to import parser service: {e}")
                raise RuntimeError("Parser service not available")
        return self._parser
    
    @property
    def is_available(self) -> bool:
        """Check if the parser is available."""
        try:
            return self._get_parser().is_available
        except Exception:
            return False
    
    @property
    def supported_formats(self) -> List[str]:
        """Get list of supported formats."""
        try:
            return self._get_parser().get_supported_formats()
        except Exception:
            return []
    
    # =========================================================================
    # Parse Methods - Convert text to structured data
    # =========================================================================
    
    def parse_ncd(self, ncd_content: str, ncn_content: str = "") -> Dict[str, Any]:
        """
        Parse NCD (and optionally NCN) content to structured JSON.
        
        Args:
            ncd_content: The NCD file content (NormCode Draft)
            ncn_content: Optional NCN file content for merging
            
        Returns:
            Dict with 'lines' key containing parsed line structures.
            Each line has: flow_index, type, depth, nc_main, ncn_content,
                          inference_marker, concept_type, concept_name, etc.
        """
        return self._get_parser().parse_ncd(ncd_content, ncn_content)
    
    def parse_ncdn(self, ncdn_content: str) -> Dict[str, Any]:
        """
        Parse NCDN/NCDS content to structured JSON.
        
        NCDN (NormCode Draft+Natural) combines structure with annotations.
        NCDS (NormCode Draft Script) uses the same format.
        
        Args:
            ncdn_content: The NCDN/NCDS file content
            
        Returns:
            Dict with 'lines' key containing parsed line structures
        """
        return self._get_parser().parse_ncdn(ncdn_content)
    
    def parse(self, content: str, format: str, **kwargs) -> Dict[str, Any]:
        """
        Parse content of any supported format.
        
        Args:
            content: File content
            format: Format identifier ('ncd', 'ncn', 'ncdn', 'ncds', etc.)
            **kwargs: Format-specific options (e.g., ncn_content for ncd)
            
        Returns:
            Dict with 'lines', 'warnings', 'metadata' keys
        """
        return self._get_parser().parse(content, format, **kwargs)
    
    # =========================================================================
    # Serialize Methods - Convert structured data to text
    # =========================================================================
    
    def serialize_to_ncd_ncn(self, parsed_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Convert parsed JSON to NCD and NCN formats.
        
        Args:
            parsed_data: The parsed JSON structure with 'lines' key
            
        Returns:
            Dict with 'ncd' and 'ncn' keys containing serialized content
        """
        return self._get_parser().serialize_to_ncd_ncn(parsed_data)
    
    def serialize_to_ncdn(self, parsed_data: Dict[str, Any]) -> str:
        """
        Convert parsed JSON to NCDN format.
        
        Args:
            parsed_data: The parsed JSON structure with 'lines' key
            
        Returns:
            NCDN formatted string
        """
        return self._get_parser().serialize_to_ncdn(parsed_data)
    
    def serialize(self, parsed_data: Dict[str, Any], source_format: str, target_format: str) -> str:
        """
        Serialize parsed data to a target format.
        
        Args:
            parsed_data: Parsed data structure with 'lines' key
            source_format: Original format (to find the right parser)
            target_format: Target format
            
        Returns:
            Serialized content string
        """
        return self._get_parser().serialize(parsed_data, source_format, target_format)
    
    # =========================================================================
    # Conversion Methods
    # =========================================================================
    
    def convert_format(self, content: str, from_format: str, to_format: str) -> str:
        """
        Convert content from one format to another.
        
        Supported conversions:
        - ncd ↔ ncdn ↔ ncds
        - Any format → json
        - Any format → nci
        
        Args:
            content: Source content
            from_format: Source format ('ncd', 'ncn', 'ncdn', 'ncds')
            to_format: Target format ('ncd', 'ncn', 'ncdn', 'ncds', 'json', 'nci')
            
        Returns:
            Converted content string
        """
        return self._get_parser().convert_format(content, from_format, to_format)
    
    def to_nci(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert parsed JSON to NCI (inference) format.
        
        NCI format identifies inference groups where a concept has children
        with '<=' (function) and '<-' (value) markers.
        
        Args:
            parsed_data: The parsed JSON structure with 'lines' key
            
        Returns:
            List of inference groups, each with:
            - concept_to_infer: The parent concept
            - function_concept: The child with '<=' marker
            - value_concepts: Children with '<-' markers
            - other_concepts: Other children
        """
        return self._get_parser().to_nci(parsed_data)
    
    def from_nci(self, nci_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert NCI (inference) format back to parsed JSON.
        
        This enables round-trip conversion: NCDS → NCI → NCDS
        
        Args:
            nci_data: List of inference groups (or JSON string)
            
        Returns:
            Dict with 'lines' key containing parsed line structures
        """
        return self._get_parser().from_nci(nci_data)
    
    def parse_nci(self, nci_content: str) -> Dict[str, Any]:
        """
        Parse NCI JSON string to structured JSON.
        
        Args:
            nci_content: The NCI JSON content (as string)
            
        Returns:
            Dict with 'lines' key containing parsed line structures
        """
        return self._get_parser().parse_nci(nci_content)
    
    # =========================================================================
    # Activation Methods - Generate execution-ready repos
    # =========================================================================
    
    def activate(self, nci_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Activate NCI data into concept_repo and inference_repo.
        
        This is the final phase of NormCode compilation:
        NCI → concept_repo.json + inference_repo.json
        
        Args:
            nci_data: List of inference groups from NCI format
            
        Returns:
            Dict with:
            - concept_repo: List of concept entries (ready for ConceptRepo)
            - inference_repo: List of inference entries (ready for InferenceRepo)
            - summary: Statistics about the activation
        """
        return self._get_parser().activate(nci_data)
    
    def activate_ncds(self, ncds_content: str) -> Dict[str, Any]:
        """
        Full pipeline: NCDS → repos.
        
        Convenience method that chains parse → to_nci → activate.
        
        Args:
            ncds_content: NCDS file content
            
        Returns:
            Dict with concept_repo, inference_repo, and summary
        """
        return self._get_parser().activate_ncds(ncds_content)
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_flow_indices(self, content: str, file_format: str = "ncd") -> List[Dict[str, Any]]:
        """
        Parse content and return lines with flow indices.
        
        This is useful for getting a quick overview of the document structure.
        
        Args:
            content: File content
            file_format: Format type ('ncd', 'ncdn', 'ncds')
            
        Returns:
            List of line dicts with flow_index, content, type, depth
        """
        return self._get_parser().get_flow_indices(content, file_format)
    
    def validate(self, content: str, format: str) -> Dict[str, Any]:
        """
        Validate content against format rules.
        
        Args:
            content: File content
            format: Format identifier
            
        Returns:
            Dict with 'valid', 'errors', 'warnings', 'format' keys
        """
        return self._get_parser().validate(content, format)
    
    # =========================================================================
    # Paradigm Affordances - Functions for composition (MFP → TVA pattern)
    # These return callables that the paradigm's composition_tool uses
    # =========================================================================
    
    @property
    def parse_content(self) -> Callable:
        """
        Affordance: Return a function that parses NormCode content.
        
        Used by paradigm: c_Parser-o_ParsedContent
        
        The returned function:
        - Takes content and format as arguments
        - Returns parsed structure with lines
        """
        def _parse_fn(content: str = "", format: str = "ncds", **kwargs) -> Dict[str, Any]:
            fmt = format or kwargs.get("format", "ncds")
            if fmt in ('ncdn', 'ncds'):
                return self.parse_ncdn(content)
            else:
                ncn = kwargs.get("ncn_content", "")
                return self.parse_ncd(content, ncn)
        
        return _parse_fn
    
    @property
    def serialize_content(self) -> Callable:
        """
        Affordance: Return a function that serializes parsed data.
        
        Used by paradigm: c_Parser-o_SerializedContent
        
        The returned function:
        - Takes parsed_data and target_format as arguments
        - Returns serialized string
        """
        def _serialize_fn(
            parsed_data: Dict[str, Any] = None,
            target_format: str = "ncds",
            **kwargs
        ) -> str:
            data = parsed_data or kwargs.get("data", {"lines": []})
            fmt = target_format or kwargs.get("format", "ncds")
            
            if fmt in ('ncdn', 'ncds'):
                return self.serialize_to_ncdn(data)
            elif fmt == 'ncd':
                result = self.serialize_to_ncd_ncn(data)
                return result.get('ncd', '')
            elif fmt == 'ncn':
                result = self.serialize_to_ncd_ncn(data)
                return result.get('ncn', '')
            else:
                return self.serialize(data, 'ncd', fmt)
        
        return _serialize_fn
    
    @property
    def convert(self) -> Callable:
        """
        Affordance: Return a function that converts between formats.
        
        Used by paradigm: c_Parser-o_ConvertedContent
        
        The returned function:
        - Takes content, from_format, and to_format as arguments
        - Returns converted string
        """
        def _convert_fn(
            content: str = "",
            from_format: str = "ncds",
            to_format: str = "json",
            **kwargs
        ) -> str:
            src = from_format or kwargs.get("source_format", "ncds")
            dst = to_format or kwargs.get("target_format", "json")
            return self.convert_format(content, src, dst)
        
        return _convert_fn
    
    @property
    def extract_flow_indices(self) -> Callable:
        """
        Affordance: Return a function that extracts flow indices.
        
        Used by paradigm: c_Parser-o_FlowIndices
        
        The returned function:
        - Takes content and optional format
        - Returns list of flow index entries
        """
        def _extract_fn(content: str = "", format: str = "ncds", **kwargs) -> List[Dict[str, Any]]:
            fmt = format or kwargs.get("format", "ncds")
            return self.get_flow_indices(content, fmt)
        
        return _extract_fn
    
    @property
    def to_inference_format(self) -> Callable:
        """
        Affordance: Return a function that converts to NCI format.
        
        Used by paradigm: c_Parser-o_InferenceStructure
        
        The returned function:
        - Takes parsed_data (or parses content if string provided)
        - Returns list of inference groups
        """
        def _to_nci_fn(data: Any = None, **kwargs) -> List[Dict[str, Any]]:
            if isinstance(data, str):
                # Parse first if string content provided
                parsed = self.parse_ncdn(data)
                return self.to_nci(parsed)
            elif isinstance(data, dict) and 'lines' in data:
                return self.to_nci(data)
            else:
                # Try to get from kwargs
                content = kwargs.get("content", "")
                if content:
                    parsed = self.parse_ncdn(content)
                    return self.to_nci(parsed)
                return []
        
        return _to_nci_fn
    
    @property
    def from_inference_format(self) -> Callable:
        """
        Affordance: Return a function that converts from NCI format.
        
        Used by paradigm: c_Parser-o_FromInferenceStructure
        
        The returned function:
        - Takes nci_data (list or JSON string)
        - Returns parsed data structure with 'lines' key
        """
        def _from_nci_fn(data: Any = None, **kwargs) -> Dict[str, Any]:
            if isinstance(data, str):
                # Parse NCI JSON string
                return self.parse_nci(data)
            elif isinstance(data, list):
                # Convert NCI list directly
                return self.from_nci(data)
            else:
                # Try to get from kwargs
                nci_data = kwargs.get("nci_data") or kwargs.get("data", [])
                if isinstance(nci_data, str):
                    return self.parse_nci(nci_data)
                elif isinstance(nci_data, list):
                    return self.from_nci(nci_data)
                return {"lines": []}
        
        return _from_nci_fn
    
    # =========================================================================
    # Factory Methods for NormCode Integration
    # =========================================================================
    
    def create_parse_function(self, default_format: str = "ncds") -> Callable:
        """
        Create a function for parsing NormCode content.
        
        Args:
            default_format: Default format to use if not specified
            
        Returns:
            A callable that takes (content: str, **kwargs) and returns parsed data
        """
        def parse_fn(content: str = "", **kwargs) -> Dict[str, Any]:
            fmt = kwargs.get("format", default_format)
            if fmt in ('ncdn', 'ncds'):
                return self.parse_ncdn(content)
            else:
                ncn = kwargs.get("ncn_content", "")
                return self.parse_ncd(content, ncn)
        
        return parse_fn
    
    def create_serialize_function(self, default_format: str = "ncds") -> Callable:
        """
        Create a function for serializing parsed data.
        
        Args:
            default_format: Default format to serialize to
            
        Returns:
            A callable that takes (parsed_data: dict, **kwargs) and returns string
        """
        def serialize_fn(parsed_data: Dict[str, Any] = None, **kwargs) -> str:
            data = parsed_data or {"lines": []}
            fmt = kwargs.get("format", default_format)
            if fmt in ('ncdn', 'ncds'):
                return self.serialize_to_ncdn(data)
            elif fmt in ('ncd', 'ncn'):
                result = self.serialize_to_ncd_ncn(data)
                return result.get(fmt, '')
            else:
                return self.serialize(data, 'ncd', fmt)
        
        return serialize_fn

