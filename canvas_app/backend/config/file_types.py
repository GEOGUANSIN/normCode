"""
File type configuration for canvas_app.

This module defines all supported file types, their categories, and capabilities.
Adding new file type support is as simple as adding an entry to FILE_TYPES.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class FileTypeCategory(Enum):
    """Categories of file types."""
    NORMCODE = "normcode"      # NormCode family (.ncd, .ncn, .ncdn, etc.)
    CODE = "code"              # Programming languages (.py, .js, etc.)
    DATA = "data"              # Data files (.json, .yaml, .toml)
    DOCUMENTATION = "doc"      # Documentation (.md, .txt, .rst)
    CONFIG = "config"          # Configuration files
    OTHER = "other"            # Uncategorized


@dataclass
class FileTypeConfig:
    """Configuration for a file type."""
    
    # File identification
    extension: str                  # e.g., ".ncd"
    format_name: str                # e.g., "ncd" (used as format identifier)
    display_name: str               # e.g., "NormCode Draft"
    category: FileTypeCategory
    
    # Capabilities
    supports_parsing: bool = False  # Can be parsed into structured format
    supports_preview: bool = False  # Can generate previews in other formats
    supports_line_edit: bool = False  # Supports line-by-line editing
    supports_validation: bool = False  # Has validation rules
    
    # Parser info
    parser_key: Optional[str] = None  # Key to look up parser in registry
    
    # Display info
    icon_name: str = "file"         # Icon identifier for frontend
    icon_color: str = "gray"        # Color for icon
    
    # MIME type
    mime_type: str = "text/plain"
    
    # Additional metadata
    metadata: Dict = field(default_factory=dict)


# =============================================================================
# File Type Registry
# =============================================================================

FILE_TYPES: Dict[str, FileTypeConfig] = {
    # NormCode family
    ".ncd": FileTypeConfig(
        extension=".ncd",
        format_name="ncd",
        display_name="NormCode Draft",
        category=FileTypeCategory.NORMCODE,
        supports_parsing=True,
        supports_preview=True,
        supports_line_edit=True,
        supports_validation=True,
        parser_key="ncd",
        icon_name="file-code",
        icon_color="blue",
    ),
    ".ncn": FileTypeConfig(
        extension=".ncn",
        format_name="ncn",
        display_name="NormCode Natural",
        category=FileTypeCategory.NORMCODE,
        supports_parsing=True,
        supports_preview=True,
        supports_line_edit=True,
        parser_key="ncn",
        icon_name="file-text",
        icon_color="green",
    ),
    ".ncdn": FileTypeConfig(
        extension=".ncdn",
        format_name="ncdn",
        display_name="NormCode Draft+Natural",
        category=FileTypeCategory.NORMCODE,
        supports_parsing=True,
        supports_preview=True,
        supports_line_edit=True,
        supports_validation=True,
        parser_key="ncdn",
        icon_name="code",
        icon_color="purple",
    ),
    ".ncds": FileTypeConfig(
        extension=".ncds",
        format_name="ncds",
        display_name="NormCode Draft Script",
        category=FileTypeCategory.NORMCODE,
        supports_parsing=True,
        supports_preview=True,
        supports_line_edit=True,
        parser_key="ncds",
        icon_name="code",
        icon_color="indigo",
    ),
    ".nc.json": FileTypeConfig(
        extension=".nc.json",
        format_name="nc-json",
        display_name="NormCode JSON",
        category=FileTypeCategory.NORMCODE,
        supports_parsing=True,
        icon_name="file-json",
        icon_color="orange",
        mime_type="application/json",
    ),
    ".nci.json": FileTypeConfig(
        extension=".nci.json",
        format_name="nci",
        display_name="NormCode Inference",
        category=FileTypeCategory.NORMCODE,
        supports_parsing=True,
        icon_name="file-json",
        icon_color="red",
        mime_type="application/json",
    ),
    ".concept.json": FileTypeConfig(
        extension=".concept.json",
        format_name="concept",
        display_name="Concept Definition",
        category=FileTypeCategory.NORMCODE,
        supports_parsing=True,
        icon_name="database",
        icon_color="cyan",
        mime_type="application/json",
    ),
    ".inference.json": FileTypeConfig(
        extension=".inference.json",
        format_name="inference",
        display_name="Inference Definition",
        category=FileTypeCategory.NORMCODE,
        supports_parsing=True,
        icon_name="hash",
        icon_color="pink",
        mime_type="application/json",
    ),
    
    # Paradigm files (composition patterns)
    # Note: We detect paradigm files by their naming pattern h_*-c_*-o_*.json or v_*-c_*-o_*.json
    # and by checking for metadata/env_spec/sequence_spec structure
    
    # Programming languages
    ".py": FileTypeConfig(
        extension=".py",
        format_name="python",
        display_name="Python",
        category=FileTypeCategory.CODE,
        icon_name="file-type",
        icon_color="blue",
        mime_type="text/x-python",
    ),
    ".js": FileTypeConfig(
        extension=".js",
        format_name="javascript",
        display_name="JavaScript",
        category=FileTypeCategory.CODE,
        icon_name="file-type",
        icon_color="yellow",
        mime_type="text/javascript",
    ),
    ".ts": FileTypeConfig(
        extension=".ts",
        format_name="typescript",
        display_name="TypeScript",
        category=FileTypeCategory.CODE,
        icon_name="file-type",
        icon_color="blue",
        mime_type="text/typescript",
    ),
    
    # Data formats
    ".json": FileTypeConfig(
        extension=".json",
        format_name="json",
        display_name="JSON",
        category=FileTypeCategory.DATA,
        supports_parsing=True,
        supports_validation=True,
        parser_key="json",
        icon_name="file-json",
        icon_color="yellow",
        mime_type="application/json",
    ),
    ".yaml": FileTypeConfig(
        extension=".yaml",
        format_name="yaml",
        display_name="YAML",
        category=FileTypeCategory.DATA,
        supports_parsing=True,
        parser_key="yaml",
        icon_name="file",
        icon_color="amber",
        mime_type="text/yaml",
    ),
    ".yml": FileTypeConfig(
        extension=".yml",
        format_name="yaml",
        display_name="YAML",
        category=FileTypeCategory.DATA,
        supports_parsing=True,
        parser_key="yaml",
        icon_name="file",
        icon_color="amber",
        mime_type="text/yaml",
    ),
    ".toml": FileTypeConfig(
        extension=".toml",
        format_name="toml",
        display_name="TOML",
        category=FileTypeCategory.DATA,
        supports_parsing=True,
        parser_key="toml",
        icon_name="file",
        icon_color="orange",
        mime_type="text/x-toml",
    ),
    
    # Documentation
    ".md": FileTypeConfig(
        extension=".md",
        format_name="markdown",
        display_name="Markdown",
        category=FileTypeCategory.DOCUMENTATION,
        supports_preview=True,
        icon_name="file-text",
        icon_color="gray",
        mime_type="text/markdown",
    ),
    ".txt": FileTypeConfig(
        extension=".txt",
        format_name="text",
        display_name="Plain Text",
        category=FileTypeCategory.DOCUMENTATION,
        icon_name="file-text",
        icon_color="gray",
    ),
    ".rst": FileTypeConfig(
        extension=".rst",
        format_name="rst",
        display_name="reStructuredText",
        category=FileTypeCategory.DOCUMENTATION,
        icon_name="file-text",
        icon_color="gray",
    ),
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_supported_extensions() -> List[str]:
    """Get list of all supported file extensions."""
    return list(FILE_TYPES.keys())


def get_extensions_by_category(category: FileTypeCategory) -> List[str]:
    """Get all extensions in a specific category."""
    return [
        ext for ext, config in FILE_TYPES.items()
        if config.category == category
    ]


def get_file_type_config(extension: str) -> Optional[FileTypeConfig]:
    """
    Get configuration for a file extension.
    
    Handles compound extensions like .nc.json, .concept.json.
    """
    # Check exact match first
    if extension in FILE_TYPES:
        return FILE_TYPES[extension]
    
    # Check compound extensions
    for ext in sorted(FILE_TYPES.keys(), key=len, reverse=True):
        if extension.endswith(ext):
            return FILE_TYPES[ext]
    
    return None


def get_format_from_path(path: str) -> str:
    """
    Determine the format name from a file path.
    
    Handles compound extensions like .nc.json, .concept.json.
    """
    path_lower = path.lower()
    
    # Check compound extensions first (longer ones)
    for ext in sorted(FILE_TYPES.keys(), key=len, reverse=True):
        if path_lower.endswith(ext):
            return FILE_TYPES[ext].format_name
    
    # Fallback to simple extension
    import os
    _, ext = os.path.splitext(path_lower)
    if ext in FILE_TYPES:
        return FILE_TYPES[ext].format_name
    
    return "text"


def is_parseable_format(format_name: str) -> bool:
    """Check if a format supports parsing."""
    for config in FILE_TYPES.values():
        if config.format_name == format_name:
            return config.supports_parsing
    return False


def is_normcode_format(format_name: str) -> bool:
    """Check if a format is in the NormCode family."""
    for config in FILE_TYPES.values():
        if config.format_name == format_name:
            return config.category == FileTypeCategory.NORMCODE
    return False


def get_normcode_extensions() -> List[str]:
    """Get all NormCode family extensions."""
    return get_extensions_by_category(FileTypeCategory.NORMCODE)

