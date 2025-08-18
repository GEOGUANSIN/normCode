from infra._core import Inference, register_inference_sequence
from infra._states._imperative_states import States as ImperativeStates
import logging

logger = logging.getLogger(__name__)

def _null_step(**fkwargs):return None

def set_up_imperative_demo(agent_frame):
    logger.debug("Setting up imperative demo sequence")
    working_interpretation = agent_frame.working_interpretation #suppose that all syntatical parsing is done here.
    body = agent_frame.body

    @register_inference_sequence("imperative")
    def imperative(self: Inference):
        """`(IWI-IR-MFP-MVP-TVA-TIP-MIA-OR-OWI)`"""
        logger.info("=====EXECUTING IMPERATIVE SEQUENCE=====")
        states = ImperativeStates()
        logger.info("---Step 1: Input Working Interpretation (IWI)---"); states = self.IWI(self, states, body, working_interpretation)
        logger.info("---Step 2: Input References (IR)---"); states = self.IR(self, states)
        logger.info("---Step 3: Model Function Perception (MFP)---"); states = self.MFP(states)
        logger.info("---Step 4: Memory Value Perception (MVP)---"); states = self.MVP(states)
        logger.info("---Step 5: Tool Value Actuation (TVA)---"); states = self.TVA(states)
        logger.info("---Step 6: Tool Inference Perception (TIP)---"); states = self.TIP(states)
        logger.info("---Step 7: Memory Inference Actuation (MIA)---"); states = self.MIA(states)
        logger.info("---Step 8: Output Reference (OR)---"); states = self.OR(states)
        logger.info("---Step 9: Output Working Interpretation (OWI)---"); states = self.OWI(states)
        logger.info("=====IMPERATIVE SEQUENCE COMPLETED=====")
        return states

def configure_imperative_demo(agent_frame, inference_instance: Inference, **methods):
    logger.debug("Configuring imperative demo steps")
    @inference_instance.register_step("IWI")
    def IWI(**fkwargs): return methods.get("input_working_interpretation", _null_step)(**fkwargs) 
    
    @inference_instance.register_step("IR")
    def IR(**fkwargs): return methods.get("input_references", _null_step)(**fkwargs)
    
    @inference_instance.register_step("MFP")
    def MFP(**fkwargs): return methods.get("model_function_perception", _null_step)(**fkwargs)
    
    @inference_instance.register_step("MVP")
    def MVP(**fkwargs): return methods.get("memory_value_perception", _null_step)(**fkwargs)
    
    @inference_instance.register_step("TVA")
    def TVA(**fkwargs): return methods.get("tool_value_actuation", _null_step)(**fkwargs)
    
    @inference_instance.register_step("TIP")
    def TIP(**fkwargs): return methods.get("tool_inference_perception", _null_step)(**fkwargs)
    
    @inference_instance.register_step("MIA")
    def MIA(**fkwargs): return methods.get("memory_inference_actuation", _null_step)(**fkwargs)
    
    @inference_instance.register_step("OR")
    def OR(**fkwargs): return methods.get("output_reference", _null_step)(**fkwargs)
    
    @inference_instance.register_step("OWI")
    def OWI(**fkwargs): return methods.get("output_working_interpretation", _null_step)(**fkwargs)
