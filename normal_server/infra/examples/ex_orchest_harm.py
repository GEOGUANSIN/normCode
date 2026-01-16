import uuid
import logging
import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# --- Infra Imports ---
try:
    # Adjust these imports based on the actual structure of your 'infra' module
    from infra._core._concept import Concept
    from infra._core._inference import Inference
    from infra._orchest._repo import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo
    from infra._orchest._orchestrator import Orchestrator
    from infra._loggers.utils import setup_orchestrator_logging
except ImportError:
    # If running as a script, this helps Python find the 'infra' module
    import pathlib
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent))
    from infra._core._concept import Concept
    from infra._core._inference import Inference
    from infra._orchest._repo import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo
    from infra._orchest._orchestrator import Orchestrator
    from infra._loggers.utils import setup_orchestrator_logging


# Harm Principle: Feinberg's setback-to-interests account
harm_principle_natural_language = """
To harm a person 
is to set back that person's interests.
Interests are the things a person has a genuine stake in. 
In particular, interests include welfare interests and ulterior interests.
Welfare interests are preconditions of any worthwhile life—bodily integrity, health, minimal resources, freedom of movement, reputation, basic opportunities.
Ulterior interests are one's particular aims and life projects.
A setback is a negative effect on the protection or realization of an interest. 
This includes thwarting, damaging, or depriving the interest. 
"""


breakdown_of_harm_principle = """
<harmful action to a person is present>
    <= @$+[{1};{2}]
    <- Bool.<True><:{1}>
        <= $.
            <= @if({harmful action})
                <= @after({harmful action})
    <- Bool.<False><:{2}>
        <= $.
            <= @if({harmful action}!)
                <= @after({harmful action}!)
    <- {harmful action to a person}
        <= $=({setbacks}:{harmful action to a person})
        <- {setbacks}
            <= ::(identify are setbacks of {interest} to this {person} in the {story})
                <= @$+[{1}]
                    <= @after()
                <- ::(identify the {negative effect} on the protection or realization of an interest)<:{1}>
                    <= $.
                    <- {negative effect}? |?. such as tharting, damaging or depriving the interest.
    <- {persons}
        <= ::(identify the {persons}? involved in the {story})
        <- {persons}? |?. interest-bearers.
        <- {story} 
    <- {interests}
        <= ::(identify the {interests} of the {persons} invovled in the {story})
            <= @$+[{1};{2}]
                <= @after({persons})
            <- ::(identify {welfare interests} of the {persons} in the {story})
                <= $.
                <- {welfare interests}? |?. one's particular aims and life project.
                <- {person}
                <- {story} 
            <- ::(identify {ulterior interests} of the persons)
                <- $.
                <- {ulterior interests}? |?. preconditions of any worthwhile life, such as bodily integrity, health, minimal resources, freedom of movement, reputation, basic opportunities.
                <- {person}
                <- {story}
        <- {persons}
        <- {interests}
        <- {story}
    <- [persons and interests]
        <- &in([persons] and [interests])
    <- {story} |input.
"""