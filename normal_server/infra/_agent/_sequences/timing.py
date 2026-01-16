from infra._core import Inference, register_inference_sequence
from infra._states._timing_states import States as TimingStates
import logging
from typing import Callable
from infra._loggers import log_states_progress

logger = logging.getLogger(__name__)

def _null_step(**fkwargs):return None

def set_up_timing_demo(agent_frame):
    logger.debug("Setting up timing demo sequence")
    working_interpretation = agent_frame.working_interpretation #suppose that all syntatical parsing is done here.
    body = agent_frame.body

    @register_inference_sequence("timing")
    def timing(self: Inference):
        """`(IWI-T-OWI)`"""
        logger.info("=====EXECUTING TIMING SEQUENCE=====")
        states = TimingStates()
        logger.info("---Step 1: Input Working Interpretation (IWI)---"); states = self.IWI(inference=self, states=states, body=body, working_interpretation=working_interpretation); log_states_progress(states, "IWI", "IWI")
        logger.info("---Step 2: Timing (T)---"); states = self.T(states=states); log_states_progress(states, "T", "T")
        logger.info("---Step 3: Output Working Interpretation (OWI)---"); states = self.OWI(states=states); log_states_progress(states, "OWI", "OWI")
        logger.info("=====TIMING SEQUENCE COMPLETED=====")
        return states

def configure_timing_demo(agent_frame, inference_instance: Inference, methods: dict[str, Callable]):
    logger.debug("Configuring timing demo steps")
    @inference_instance.register_step("IWI")
    def IWI(**fkwargs): return methods.get("input_working_interpretation", _null_step)(**fkwargs) 
    
    @inference_instance.register_step("T")
    def T(**fkwargs): return methods.get("timing", _null_step)(**fkwargs)
    
    @inference_instance.register_step("OWI")
    def OWI(**fkwargs): return methods.get("output_working_interpretation", _null_step)(**fkwargs) 