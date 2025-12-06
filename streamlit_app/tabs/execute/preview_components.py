"""
Preview components for Execute tab.
Handles rendering of concepts, inferences, and inputs file previews.
Enhanced with visual categorization and graph visualization (hybrid approach).

NOTE: This module has been refactored into the `preview` package.
This file now serves as a compatibility layer, importing from the new structure.

Module structure:
- preview/
  - __init__.py       - Main entry point (render_file_previews)
  - utils.py          - Utility functions (categorization, formatting, tensor utils)
  - tensor_display.py - Tensor rendering and editing components
  - card_view.py      - Card-based preview components
  - graph_view.py     - Graph visualization with Viz.js
"""

# Import the main function from the refactored module
from .preview import render_file_previews

# Re-export for backward compatibility
__all__ = ['render_file_previews']
