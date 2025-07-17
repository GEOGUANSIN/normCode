from typing import Dict, Any, Callable
import inspect
import logging
import sys
from _concept import Concept
from _reference import Reference
from _inference import Inference, register_inference_sequence



# Configure logging
def setup_logging(level=logging.INFO, log_file=None):
    """Setup logging configuration for the inference module"""
    # Create formatter
    # formatter = logging.Formatter(
    #     '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    # )
    formatter = logging.Formatter(
        '[%(levelname)s] %(message)s - %(asctime)s - %(name)s'
    )

    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



class AgentFrame():
    def __init__(self, AgentFrameModel: str):
        logger.info(f"Initializing AgentFrame with model: {AgentFrameModel}")
        self.AgentFrameModel = AgentFrameModel
        self._norm_code_setup()
        self.working_configuration = {}
        self.body = {}
        logger.info("AgentFrame initialized successfully")

    def _norm_code_setup(self):
        logger.debug(f"Setting up norm code for model: {self.AgentFrameModel}")
        if self.AgentFrameModel == "demo":
            logger.info("Setting up demo configuration")
            # Judgement
            self._set_up_judgement_demo()   
            # Imperative
            self._set_up_imperative_demo()
        else:
            logger.warning(f"Unknown AgentFrameModel: {self.AgentFrameModel}")

    def configure(self, inference_instance: Inference, inference_sequence: str):
        logger.info(f"Configuring inference instance with sequence: {inference_sequence}")
        if self.AgentFrameModel == "demo":
            if inference_sequence == "judgement":
                logger.debug("Configuring judgement demo")
                self._configure_judgement_demo(inference_instance)
            elif inference_sequence == "imperative":
                logger.debug("Configuring imperative demo")
                self._configure_imperative_demo(inference_instance)
            else:
                logger.warning(f"Unknown inference sequence: {inference_sequence}")
        else:
            logger.warning(f"Configuration not supported for model: {self.AgentFrameModel}")

    def _set_up_judgement_demo(self):
        logger.debug("Setting up judgement demo sequence")
        # Define the judgement sequence function
        @register_inference_sequence("judgement")
        def judgement(self: Inference, input_data: dict):
            """`(IWC-[(MVP-CP)-[(PA)]-MA)]-RR-OWC)`"""
            logger.info("Executing judgement sequence")
            # 1. Input Working Configuration
            logger.debug("Step 1: Input Working Configuration (IWC)")
            working_configuration = self.IWC()
            # 2. Memorized Values Perception
            logger.debug("Step 2: Memorized Values Perception (MVP)")
            perception_references = self.MVP(working_configuration, self.value_concepts)
            # 3. Cross Perception
            logger.debug("Step 3: Cross Perception (CP)")
            crossed_perception_reference = self.CP(perception_references)
            # 4. On-Perception Actuation
            logger.debug("Step 4: On-Perception Actuation (PA)")
            actuated_reference = self.PA(working_configuration, crossed_perception_reference, self.function_concept)
            # 5. Memory Actuation
            logger.debug("Step 5: Memory Actuation (MA)")
            self.MA(actuated_reference)
            # 6. Return Reference
            logger.debug("Step 6: Return Reference (RR)")
            self.RR(actuated_reference, self.concept_to_infer)
            # 7. Output Working Configuration
            logger.debug("Step 7: Output Working Configuration (OWC)")
            self.OWC(self.concept_to_infer)
            logger.info("Judgement sequence completed")


    def _set_up_imperative_demo(self):
        logger.debug("Setting up imperative demo sequence")
        # Define the imperative sequence function
        @register_inference_sequence("imperative")
        def imperative(self: Inference, input_data: dict):
            """`(IWC-[(MVP-CP)-[PTA-ASP]-MA)]-RR-OWC)`"""
            logger.info("Executing imperative sequence")
            # 1. Input Working Configuration
            logger.debug("Step 1: Input Working Configuration (IWC)")
            working_configuration = self.IWC()
            # 2. Memorized Values Perception
            logger.debug("Step 2: Memorized Values Perception (MVP)")
            perception_references = self.MVP(working_configuration, self.value_concepts)
            # 3. Cross Perception
            logger.debug("Step 3: Cross Perception (CP)")
            crossed_perception_reference = self.CP(perception_references)
            # 4. On-Perception Tool Actuation
            logger.debug("Step 4: On-Perception Tool Actuation (PTA)")
            actuated_reference = self.PTA(working_configuration, crossed_perception_reference, self.function_concept)
            # 5. Action Specification Perception
            logger.debug("Step 5: Action Specification Perception (ASP)")
            action_specification_perception = self.ASP(actuated_reference, self.function_concept)
            # 6. Memory Actuation
            logger.debug("Step 6: Memory Actuation (MA)")
            self.MA(action_specification_perception)
            # 7. Return Reference
            logger.debug("Step 7: Return Reference (RR)")
            self.RR(actuated_reference, self.concept_to_infer)
            # 8. Output Working Configuration
            logger.debug("Step 8: Output Working Configuration (OWC)")
            self.OWC(self.concept_to_infer)
            logger.info("Imperative sequence completed")


    def _configure_judgement_demo(self, inference_instance: Inference):
        logger.debug("Configuring judgement demo steps")
        # Register steps for THIS SPECIFIC INSTANCE
        @inference_instance.register_step("IWC")
        def input_working_configurations():
            """Validate that input contains two numbers"""
            logger.debug("Executing IWC step")
            pass

        @inference_instance.register_step("OWC")
        def output_working_configurations(concepts_to_infer):
            """Perform the output working configurations"""
            logger.debug(f"Executing OWC step with concepts: {concepts_to_infer}")
            pass

        @inference_instance.register_step("RR")
        def return_reference(actuated_reference, concepts_to_infer):
            """Perform the return reference"""
            logger.debug(f"Executing RR step with concepts: {concepts_to_infer}")
            pass
        
        @inference_instance.register_step("MVP")
        def memorized_values_perception(working_configuration, value_concepts):
            """Perform the memorized values perception"""
            logger.debug(f"Executing MVP step with value concepts: {value_concepts}")
            pass

        @inference_instance.register_step("CP")
        def cross_perception(perception_references):
            """Perform the cross perception"""
            logger.debug("Executing CP step")
            pass
        
        @inference_instance.register_step("PA")
        def on_perception_actuation(working_configuration, crossed_perception_reference, function_concept):
            """Perform the on-perception actuation"""
            logger.debug(f"Executing PA step with function concept: {function_concept}")
            pass
        
        
        @inference_instance.register_step("MA")
        def memory_actuation(actuated_reference):
            """Perform the memory actuation"""
            logger.debug("Executing MA step")
            pass

    def _configure_imperative_demo(self, inference_instance: Inference):
        logger.debug("Configuring imperative demo steps")
        @inference_instance.register_step("IWC")
        def input_working_configurations():
            """Validate that input contains two numbers"""
            logger.debug("Executing IWC step")
            pass
        
        @inference_instance.register_step("OWC")
        def output_working_configurations(concepts_to_infer):
            """Perform the output working configurations"""
            logger.debug(f"Executing OWC step with concepts: {concepts_to_infer}")
            pass
        
        @inference_instance.register_step("RR")
        def return_reference(actuated_reference, concepts_to_infer):
            """Perform the return reference"""
            logger.debug(f"Executing RR step with concepts: {concepts_to_infer}")
            pass    
        
        @inference_instance.register_step("MVP")
        def memorized_values_perception(working_configuration, value_concepts):
            """Perform the memorized values perception"""
            logger.debug(f"Executing MVP step with value concepts: {value_concepts}")
            pass
        
        @inference_instance.register_step("CP")
        def cross_perception(perception_references):
            """Perform the cross perception"""
            logger.debug("Executing CP step")
            pass
        
        @inference_instance.register_step("PTA")
        def on_perception_tool_actuation(working_configuration, crossed_perception_reference, function_concept):
            """Perform the on-perception tool actuation"""
            logger.debug(f"Executing PTA step with function concept: {function_concept}")
            pass
        
        @inference_instance.register_step("ASP")
        def action_specification_perception(actuated_reference, function_concept):
            """Perform the action specification perception"""
            logger.debug(f"Executing ASP step with function concept: {function_concept}")
            pass
        
        @inference_instance.register_step("MA") 
        def memory_actuation(actuated_reference):
            """Perform the memory actuation"""
            logger.debug("Executing MA step")
            pass

# Abstract usage pattern
if __name__ == "__main__":

    # Create inference instance for arithmetic calculator
    judgement_instance = Inference(
        "judgement",
        Concept("concept_to_infer", "Concept to infer", Reference(axes=["concept_to_infer"], shape=(1,), initial_value=None)),
        [Concept("value_concept", "Value concept", Reference(axes=["value_concept"], shape=(1,), initial_value=None))],
        Concept("function_concept", "Function concept", Reference(axes=["function_concept"], shape=(1,), initial_value=None))
    )

    agent = AgentFrame("demo")

    agent.configure(judgement_instance, "judgement")
    
    judgement_instance.execute(input_data={})