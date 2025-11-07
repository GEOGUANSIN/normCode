from infra._core import Inference, register_inference_sequence
from infra._states._judgement_states import States as JudgementStates
import logging
from infra._core._reference import Reference
from typing import List, Callable
from infra._loggers import log_states_progress



logger = logging.getLogger(__name__)


def _null_step(**fkwargs):return None

def set_up_judgement_demo(agent_frame):
    logger.debug("Setting up judgement demo sequence")
    working_interpretation = agent_frame.working_interpretation #suppose that all syntatical parsing is done here.
    body = agent_frame.body

    @register_inference_sequence("judgement")
    def judgement(self: Inference):
        """`(IWI-IR-MFP-MVP-TVA-TIP-MIA-OR-OWI)`"""
        logger.info("=====EXECUTING JUDGEMENT SEQUENCE=====")
        states = JudgementStates()
        logger.info("---Step 1: Input Working Interpretation (IWI)---")
        states = self.IWI(inference=self, states=states, body=body, working_interpretation=working_interpretation)
        log_states_progress(states, "IWI", "IWI")
        logger.info("---Step 2: Input References (IR)---")
        states = self.IR(inference=self, states=states)
        log_states_progress(states, "IR", "IR")
        logger.info("---Step 3: Model Function Perception (MFP)---")
        states = self.MFP(states=states)
        log_states_progress(states, "MFP", "MFP")
        logger.info("---Step 4: Memory Value Perception (MVP)---")
        states = self.MVP(states=states)
        log_states_progress(states, "MVP", "MVP")
        logger.info("---Step 5: Tool Value Actuation (TVA)---")
        states = self.TVA(states=states)
        log_states_progress(states, "TVA", "TVA")
        logger.info("---Step 6: Tool Inference Perception (TIP)---")
        states = self.TIP(states=states)
        log_states_progress(states, "TIP", "TIP")
        logger.info("---Step 7: Memory Inference Actuation (MIA)---")
        states = self.MIA(states=states)
        log_states_progress(states, "MIA", "MIA")
        logger.info("---Step 8: Output Reference (OR)---")
        states = self.OR(states=states)
        log_states_progress(states, "OR", "OR")
        logger.info("---Step 9: Output Working Interpretation (OWI)---")
        states = self.OWI(states=states)
        log_states_progress(states, "OWI", "OWI")
        logger.info("=====JUDGEMENT SEQUENCE COMPLETED=====")
        return states

def configure_judgement_demo(agent_frame, inference_instance: Inference, methods: dict[str, Callable]):
    logger.debug("Configuring judgement demo steps")
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
