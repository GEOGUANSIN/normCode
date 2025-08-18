from infra._core import Inference, register_inference_sequence
from infra._states._imperative_states import States as ImperativeStates
import logging
from infra._core._reference import Reference
from typing import List

logger = logging.getLogger(__name__)

def log_states_progress(states: ImperativeStates, step_name: str, step_filter: str | None = None):
    logger = logging.getLogger(__name__)
    logger.info(f"\n--- States after {step_name} (Filtered by: {step_filter if step_filter else 'None'}) ---")
    logger.info(f"Current Step: {states.sequence_state.current_step}")
    
    def _log_record_list(label: str, record_list: List):
        logger.info(f"{label}:")
        filtered_records = [item for item in record_list if step_filter is None or item.step_name == step_filter]
        if not filtered_records:
            logger.info("  (Empty or no matching records for filter)")
            return
        for item in filtered_records:
            logger.info(f"  Step Name: {item.step_name}")
            if item.concept:
                logger.info(f"    Concept ID: {item.concept.id}, Name: {item.concept.name}, Type: {item.concept.type}, Context: {item.concept.context}, Axis: {item.concept.axis_name}")
            if item.reference and isinstance(item.reference, Reference):
                logger.info(f"    Reference Axes: {item.reference.axes}")
                logger.info(f"    Reference Shape: {item.reference.shape}")
                logger.info(f"    Reference Tensor: {item.reference.tensor}")
            if item.model:
                logger.info(f"    Model: {item.model}")

    _log_record_list("Function", states.function)
    _log_record_list("Values", states.values)
    _log_record_list("Context", states.context)
    _log_record_list("Inference", states.inference)

    logger.info("-----------------------------------")


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
        logger.info("---Step 1: Input Working Interpretation (IWI)---")
        states = self.IWI(self, states, body, working_interpretation)
        log_states_progress(states, "IWI", "IWI")
        logger.info("---Step 2: Input References (IR)---")
        states = self.IR(self, states)
        log_states_progress(states, "IR", "IR")
        logger.info("---Step 3: Model Function Perception (MFP)---")
        states = self.MFP(states)
        log_states_progress(states, "MFP", "MFP")
        logger.info("---Step 4: Memory Value Perception (MVP)---")
        states = self.MVP(states)
        log_states_progress(states, "MVP", "MVP")
        logger.info("---Step 5: Tool Value Actuation (TVA)---")
        states = self.TVA(states)
        log_states_progress(states, "TVA", "TVA")
        logger.info("---Step 6: Tool Inference Perception (TIP)---")
        states = self.TIP(states)
        log_states_progress(states, "TIP", "TIP")
        logger.info("---Step 7: Memory Inference Actuation (MIA)---")
        states = self.MIA(states)
        log_states_progress(states, "MIA", "MIA")
        logger.info("---Step 8: Output Reference (OR)---")
        states = self.OR(states)
        log_states_progress(states, "OR", "OR")
        logger.info("---Step 9: Output Working Interpretation (OWI)---")
        states = self.OWI(states)
        log_states_progress(states, "OWI", "OWI")
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
