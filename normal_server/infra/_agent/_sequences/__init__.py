"""
Sequence modules for different inference patterns.

This module provides five main sequence types:
- simple: Basic inference sequence (IWI-IR-OR-OWI)
- grouping: Grouping-based inference sequence (IWI-IR-GR-OR-OWI)  
- quantifying: Quantification-based inference sequence (IWI-IR-GR-QR-OR-OWI)
- imperative: Complex imperative inference sequence (IWI-IR-MFP-MVP-TVA-TIP-MIA-OR-OWI)
- assigning: Assignment-based inference sequence (IWI-IR-AR-OR-OWI)
"""

# Import setup functions from each sequence module
from .simple import set_up_simple_demo, configure_simple_demo
from .grouping import set_up_grouping_demo, configure_grouping_demo
from .quantifying import set_up_quantifying_demo, configure_quantifying_demo
from .judgement import set_up_judgement_demo, configure_judgement_demo
from .imperative import set_up_imperative_demo, configure_imperative_demo
from .assigning import set_up_assigning_demo, configure_assigning_demo
from .timing import set_up_timing_demo, configure_timing_demo
from .imperative_direct import set_up_imperative_direct_demo, configure_imperative_direct_demo
from .imperative_input import set_up_imperative_input_demo, configure_imperative_input_demo
from .judgement_in_composition import set_up_judgement_in_composition_demo, configure_judgement_in_composition_demo
from .imperative_in_composition import set_up_imperative_in_composition_demo,  configure_imperative_in_composition_demo
from .looping import set_up_looping_demo, configure_looping_demo
from .judgement_direct import set_up_judgement_direct_demo, configure_judgement_direct_demo
from .imperative_python import set_up_imperative_python_demo, configure_imperative_python_demo
from .judgement_python import set_up_judgement_python_demo, configure_judgement_python_demo
from .imperative_python_indirect import set_up_imperative_python_indirect_demo, configure_imperative_python_indirect_demo
from .judgement_python_indirect import set_up_judgement_python_indirect_demo, configure_judgement_python_indirect_demo


# Export all setup and configuration functions
__all__ = [
    # Simple sequence
    "set_up_simple_demo",
    "configure_simple_demo",
    
    # Grouping sequence
    "set_up_grouping_demo", 
    "configure_grouping_demo",
    
    # Quantifying sequence
    "set_up_quantifying_demo",
    "configure_quantifying_demo",
    
    # Imperative sequence
    "set_up_imperative_demo",
    "configure_imperative_demo",

    # Judgement sequence 
    "set_up_judgement_demo",
    "configure_judgement_demo",
    
    # Assigning sequence
    "set_up_assigning_demo",
    "configure_assigning_demo",
    
    # Timing sequence
    "set_up_timing_demo",
    "configure_timing_demo",
    
    # Imperative direct sequence
    "set_up_imperative_direct_demo",
    "configure_imperative_direct_demo",
    
    # Imperative input sequence
    "set_up_imperative_input_demo",
    "configure_imperative_input_demo",

    # Judgement in composition sequence
    "set_up_judgement_in_composition_demo",
    "configure_judgement_in_composition_demo",

    # Imperative in composition sequence
    "set_up_imperative_in_composition_demo",
    "configure_imperative_in_composition_demo",

    # Looping sequence
    "set_up_looping_demo",
    "configure_looping_demo",

    # Judgement direct sequence
    "set_up_judgement_direct_demo",
    "configure_judgement_direct_demo",

    # Imperative python sequence
    "set_up_imperative_python_demo",
    "configure_imperative_python_demo",

    # Judgement python sequence
    "set_up_judgement_python_demo",
    "configure_judgement_python_demo",
]
