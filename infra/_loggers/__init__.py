"""
Logging utilities for the NormCode infrastructure.

This module provides logging utilities for tracking states, concepts, and inference results
during the execution of NormCode sequences.
"""

import logging
from typing import List

from infra._core import Reference, cross_product
from infra._states import ReferenceRecordLite, BaseStates

# Import the utility functions from utils module
from .utils import (
    log_states_progress,
    _log_concept_details,
    _log_inference_result,
)

__all__ = [
    "log_states_progress",
    "_log_concept_details", 
    "_log_inference_result",
    "BaseStates",
]
