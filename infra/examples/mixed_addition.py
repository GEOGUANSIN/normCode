import os
import sys
import logging
from typing import Any, Dict, List, Optional, Callable, Tuple
from types import SimpleNamespace
from dataclasses import dataclass, field
from string import Template
from copy import copy

# Configure logging to show DEBUG messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

# Ensure this directory is importable regardless of where the script is run from
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Import core components
try:
	from infra import Inference, Concept, Reference, AgentFrame, BaseStates, Body
except Exception:
	import sys, pathlib
	here = pathlib.Path(__file__).parent
	sys.path.insert(0, str(here.parent.parent))  # Add workspace root to path
	from infra import Inference, Concept, Reference, AgentFrame, BaseStates, Body

	

# Inference Plan in NormCode in the long term, but for now:
full_plan = """
{two numbers' sum}
    <= *every({position})%:({position})^({carryover in position}<*1>)
        <= $.({remainder in position}*)
        <- {carryover in position}* 
            <= ::(find {carryover in position} from {sum in position})
            <- {sum in position}           
        <- {remainder in position}*
            <= ::(find {remainder in position} from {sum in position})
            <- {sum in position}
        <- {sum in position}
            <- {number 1's digit in position}
                <= ::(find {digit in position}? of {position}* from {number 1's position breakdown})
                <- {position}*
            <- {number 2's digit in position}
                <= ::(find {digit in position}? of {position}* from {number 2's position breakdown})
                <- {position}"
            <- {carryover in position}*
    <- {position}


{number 1's position breakdown}
    <= $.([{number 1}'s {digit in position} and {position}]: {number 1's position breakdown}) 
    <- [number 1's {digit in position} and {position}]
        <= ::({number 1}'s {digit in position}? and {position}?)
        <- {number 1}
        <- {digit in position}?
        <- {position}?



{number 2's position breakdown}
    <= $.([{number 2}'s {digit in position} and {position}]: {number 2's position breakdown}) 
    <- [{number 2}'s {digit in position} and {position}]
        <= ::({number 2}'s {digit in position}? and {position}?)
        <- {number 2}
        <- {digit in position}?
        <- {position}?
"""

# Inference Plan in NormCode for now:
# {digit in position}? and {position}? will have explanatory reference because of the ?, that is a short definition of the concept i.e. {digit in position}? is a short definition of {digit in position} and {position}? is a short definition of {position}.
now_plan = """
[number 1's {digit in position} and {position}]
        <= ::(find all {1}?<$({number 1})%_>'s {2}?<$({digit in position})%_> and {3}?<$({position})%_> from the rightmost digit to the leftmost digit)
        <- {number 1}<:{1}>
        <- {digit in position}?<:{2}>
        <- {position}?<:{3}>
"""



def _build_mixed_addition_concepts() -> tuple[Concept, List[Concept], Concept]:

    pass

def run_mixed_addition() -> BaseStates:





	concept_to_infer, value_concepts, function_concept = _build_mixed_addition_concepts()



	# Create inference instance configured for the simple sequence
	inference = Inference(
		"imperative",
		concept_to_infer,
		value_concepts,
		function_concept,
	)

	agent = AgentFrame("demo")

	agent.configure(inference, "imperative")

	inference.execute()
