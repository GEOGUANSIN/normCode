from infra._core import Inference, register_inference_sequence
from infra._states._simple_states import States as SimpleStates
import logging

logger = logging.getLogger(__name__)

def _null_step(**fkwargs):return None

def set_up_simple_demo(agent_frame):
    logger.debug("Setting up simple demo sequence")
    working_interpretation = agent_frame.working_interpretation #suppose that all syntatical parsing is done here.
    body = agent_frame.body

    @register_inference_sequence("simple")
    def simple(self: Inference):
        """`(IWI-IR-MFP-MVP-TVA-TIP-MIA-OR-OWI)`"""
        logger.info("=====EXECUTING SIMPLE SEQUENCE=====")
        states = SimpleStates()
        logger.info("---Step 1: Input Working Interpretation (IWI)---"); states = self.IWI(self, states, body, working_interpretation)
        logger.info("---Step 2: Input References (IR)---"); states = self.IR(self, states)
        logger.info("---Step 3: Output Reference (OR)---"); states = self.OR(states)
        logger.info("---Step 4: Output Working Interpretation (OWI)---"); states = self.OWI(states)
        logger.info("=====SIMPLE SEQUENCE COMPLETED=====")
        return states

def configure_simple_demo(agent_frame, inference_instance: Inference, **methods):
    logger.debug("Configuring simple demo steps")
    @inference_instance.register_step("IWI")
    def IWI(**fkwargs): return methods.get("input_working_interpretation", _null_step)(**fkwargs) 
    
    @inference_instance.register_step("IR")
    def IR(**fkwargs): return methods.get("input_references", _null_step)(**fkwargs)
        
    @inference_instance.register_step("OR")
    def OR(**fkwargs): return methods.get("output_reference", _null_step)(**fkwargs)
    
    @inference_instance.register_step("OWI")
    def OWI(**fkwargs): return methods.get("output_working_interpretation", _null_step)(**fkwargs)
