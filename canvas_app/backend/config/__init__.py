"""
Configuration module for canvas_app backend.
"""

from .file_types import (
    FileTypeCategory,
    FileTypeConfig,
    FILE_TYPES,
    get_supported_extensions,
    get_extensions_by_category,
    get_file_type_config,
    is_parseable_format,
)

__all__ = [
    'FileTypeCategory',
    'FileTypeConfig',
    'FILE_TYPES',
    'get_supported_extensions',
    'get_extensions_by_category',
    'get_file_type_config',
    'is_parseable_format',
]

