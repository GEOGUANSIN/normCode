"""
Orchestration execution logic for NormCode Orchestrator Streamlit App.
"""

from .orchestration_runner import (
    create_orchestrator,
    inject_inputs_into_repo,
    verify_files_if_enabled
)

__all__ = [
    'create_orchestrator',
    'inject_inputs_into_repo',
    'verify_files_if_enabled'
]

