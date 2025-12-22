"""
Format Converter for NormCode Files

Provides bidirectional conversion between .ncd, .nc, and .ncn formats
using the common IR (Intermediate Representation).
"""

from typing import List, Tuple
from ..parsers import NCDParser, NCParser, NCNParser, NormCodeNode


class FormatConverter:
    """Bidirectional converter between NormCode formats."""
    
    @classmethod
    def ncd_to_nc(cls, ncd_content: str) -> Tuple[str, List[str]]:
        """
        Convert .ncd to .nc format.
        
        Args:
            ncd_content: Content of .ncd file
            
        Returns:
            Tuple of (converted content, list of warnings)
        """
        warnings = []
        
        # Parse .ncd to IR
        nodes = NCDParser.parse(ncd_content)
        
        # Check for lossy conversions
        warnings.extend(cls._check_ncd_to_nc_warnings(nodes))
        
        # Ensure flow indices are present
        nodes = cls._ensure_flow_indices(nodes)
        
        # Serialize to .nc
        nc_content = NCParser.serialize(nodes)
        
        return nc_content, warnings
    
    @classmethod
    def nc_to_ncd(cls, nc_content: str) -> Tuple[str, List[str]]:
        """
        Convert .nc to .ncd format.
        
        Args:
            nc_content: Content of .nc file
            
        Returns:
            Tuple of (converted content, list of warnings)
        """
        warnings = []
        
        # Parse .nc to IR
        nodes = NCParser.parse(nc_content)
        
        # Serialize to .ncd
        ncd_content = NCDParser.serialize(nodes)
        
        warnings.append("Note: .nc to .ncd conversion may lose type details")
        
        return ncd_content, warnings
    
    @classmethod
    def ncd_to_ncn(cls, ncd_content: str) -> Tuple[str, List[str]]:
        """
        Convert .ncd to .ncn format.
        
        Args:
            ncd_content: Content of .ncd file
            
        Returns:
            Tuple of (converted content, list of warnings)
        """
        warnings = []
        
        # Parse .ncd to IR
        nodes = NCDParser.parse(ncd_content)
        
        # Convert annotations to natural language descriptions
        nodes = cls._convert_to_natural_language(nodes)
        
        # Serialize to .ncn
        ncn_content = NCNParser.serialize(nodes)
        
        warnings.append("Converted to natural language format")
        
        return ncn_content, warnings
    
    @classmethod
    def ncn_to_ncd(cls, ncn_content: str) -> Tuple[str, List[str]]:
        """
        Convert .ncn to .ncd format.
        
        Args:
            ncn_content: Content of .ncn file
            
        Returns:
            Tuple of (converted content, list of warnings)
        """
        warnings = []
        
        # Parse .ncn to IR
        nodes = NCNParser.parse(ncn_content)
        
        # Serialize to .ncd
        ncd_content = NCDParser.serialize(nodes)
        
        warnings.append("Warning: .ncn to .ncd may lose formal syntax details")
        
        return ncd_content, warnings
    
    @classmethod
    def nc_to_ncn(cls, nc_content: str) -> Tuple[str, List[str]]:
        """
        Convert .nc to .ncn format.
        
        Args:
            nc_content: Content of .nc file
            
        Returns:
            Tuple of (converted content, list of warnings)
        """
        warnings = []
        
        # Parse .nc to IR
        nodes = NCParser.parse(nc_content)
        
        # Convert to natural language
        nodes = cls._convert_to_natural_language(nodes)
        
        # Serialize to .ncn
        ncn_content = NCNParser.serialize(nodes)
        
        warnings.append("Converted to natural language format")
        
        return ncn_content, warnings
    
    @classmethod
    def ncn_to_nc(cls, ncn_content: str) -> Tuple[str, List[str]]:
        """
        Convert .ncn to .nc format.
        
        Args:
            ncn_content: Content of .ncn file
            
        Returns:
            Tuple of (converted content, list of warnings)
        """
        warnings = []
        
        # Parse .ncn to IR
        nodes = NCNParser.parse(ncn_content)
        
        # Ensure flow indices
        nodes = cls._ensure_flow_indices(nodes)
        
        # Serialize to .nc
        nc_content = NCParser.serialize(nodes)
        
        warnings.append("Warning: .ncn to .nc may lose natural language nuances")
        
        return nc_content, warnings
    
    # Helper methods
    
    @classmethod
    def _check_ncd_to_nc_warnings(cls, nodes: List[NormCodeNode]) -> List[str]:
        """Check for potential lossy conversions from .ncd to .nc."""
        warnings = []
        
        def check_node(node: NormCodeNode):
            # Check for annotations that might be lost
            if node.annotations:
                if 'question' in node.annotations:
                    warnings.append(f"Question annotation will be lost: {node.annotations['question'][:50]}...")
                if 'source_text' in node.annotations:
                    warnings.append(f"Source text annotation will be lost: {node.annotations['source_text'][:50]}...")
            
            # Check children
            for child in node.children:
                check_node(child)
        
        for node in nodes:
            check_node(node)
        
        return list(set(warnings))[:5]  # Limit to 5 unique warnings
    
    @classmethod
    def _ensure_flow_indices(cls, nodes: List[NormCodeNode], parent_index: str = "") -> List[NormCodeNode]:
        """
        Ensure all nodes have flow indices.
        
        Generates indices like 1, 1.1, 1.2, 1.2.1, etc.
        """
        for i, node in enumerate(nodes, 1):
            if parent_index:
                node.flow_index = f"{parent_index}.{i}"
            else:
                node.flow_index = str(i)
            
            # Recursively ensure indices for children
            if node.children:
                cls._ensure_flow_indices(node.children, node.flow_index)
        
        return nodes
    
    @classmethod
    def _convert_to_natural_language(cls, nodes: List[NormCodeNode]) -> List[NormCodeNode]:
        """
        Convert formal syntax to natural language descriptions.
        
        This is a simplified conversion that uses available annotations
        or content to create readable descriptions.
        """
        def convert_node(node: NormCodeNode):
            # Use description annotation if available
            if 'description' in node.annotations:
                node.content = node.annotations['description']
            
            # Convert children
            for child in node.children:
                convert_node(child)
        
        for node in nodes:
            convert_node(node)
        
        return nodes

