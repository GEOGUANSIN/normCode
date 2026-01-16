from infra._core import Inference, register_inference_sequence
from infra._states._looping_states import States as LoopingStates
import logging
from typing import Callable
from infra._loggers import log_states_progress

logger = logging.getLogger(__name__)

def _null_step(**fkwargs):return None

def set_up_looping_demo(agent_frame):
    logger.debug("Setting up looping demo sequence")
    working_interpretation = agent_frame.working_interpretation #suppose that all syntatical parsing is done here.
    body = agent_frame.body

    @register_inference_sequence("looping")
    def looping(self: Inference):
        """`(IWI-IR-GR-LR-OR-OWI)`"""
        logger.info("=====EXECUTING LOOPING SEQUENCE=====")
        states = LoopingStates()
        logger.info("---Step 1: Input Working Interpretation (IWI)---"); states = self.IWI(inference=self, states=states, body=body, working_interpretation=working_interpretation); log_states_progress(states, "IWI", "IWI")
        logger.info("---Step 2: Input References (IR)---"); states = self.IR(inference=self, states=states); log_states_progress(states, "IR", "IR")
        logger.info("---Step 3: Grouping References (GR)---"); states = self.GR(states=states); log_states_progress(states, "GR", "GR")
        logger.info("---Step 4: Looping References (LR)---"); states = self.LR(states=states); log_states_progress(states, "LR", "LR")
        logger.info("---Step 5: Output Reference (OR)---"); states = self.OR(states=states); log_states_progress(states, "OR", "OR")
        logger.info("---Step 6: Output Working Interpretation (OWI)---"); states = self.OWI(states=states); log_states_progress(states, "OWI", "OWI")
        logger.info("=====LOOPING SEQUENCE COMPLETED=====")
        return states

def configure_looping_demo(agent_frame, inference_instance: Inference, methods: dict[str, Callable]):
    logger.debug("Configuring looping demo steps")
    @inference_instance.register_step("IWI")
    def IWI(**fkwargs): return methods.get("input_working_interpretation", _null_step)(**fkwargs) 
    
    @inference_instance.register_step("IR")
    def IR(**fkwargs): return methods.get("input_references", _null_step)(**fkwargs)
    
    @inference_instance.register_step("GR")
    def GR(**fkwargs): return methods.get("grouping_references", _null_step)(**fkwargs)
    
    @inference_instance.register_step("LR")
    def LR(**fkwargs): return methods.get("looping_references", _null_step)(**fkwargs)
    
    @inference_instance.register_step("OR")
    def OR(**fkwargs): return methods.get("output_reference", _null_step)(**fkwargs)
    
    @inference_instance.register_step("OWI")
    def OWI(**fkwargs): return methods.get("output_working_interpretation", _null_step)(**fkwargs)

