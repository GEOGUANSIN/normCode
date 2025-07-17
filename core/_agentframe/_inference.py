"""
Abstract Sequence Configuration - Demonstrates the core logic pattern
"""

from typing import Dict, Any, Callable
import inspect


# Sequence class for executing registered steps
class Inference:
    def __init__(self, sequence_name: str, concepts_to_infer: list[str], value_concepts: list[str], function_concept: str):
        self.concepts_to_infer = concepts_to_infer
        self.value_concepts = value_concepts
        self.function_concept = function_concept
        self.sequence_name = sequence_name
        self._sequences = self._discover_sequences()
        # Instance-specific step registry
        self._step_registry = {}
        self._initialize_steps()

    @classmethod
    def register_inference_sequence(cls, sequence_name: str):
        """Class method decorator to register a function as a sequence method of the Inference class"""
        def decorator(func: Callable) -> Callable:
            # Add the function as a method to the Inference class
            method_name = f"{sequence_name}"
            setattr(cls, method_name, func)
            return func
        return decorator

    def register_step(self, step_name: str, **metadata):
        """Instance method to register a step for this specific instance"""
        def decorator(func: Callable) -> Callable:
            self._step_registry[step_name] = {
                "function": func,
                "metadata": metadata
            }
            return func
        return decorator

    @property
    def steps(self):
        """Return steps for this specific instance"""
        # Use object.__getattribute__ to avoid triggering __getattr__
        return object.__getattribute__(self, '_step_registry')

    def _initialize_steps(self):
        """Initialize step and check functions from instance registry"""
        # Replace step functions
        for step_name, step_data in self._step_registry.items():
            # Remove 'step_' prefix if present for cleaner method names
            method_name = step_name.replace('step_', '') if step_name.startswith('step_') else step_name
            setattr(self, method_name, step_data["function"])
    
    def __getattr__(self, name):
        """Handle missing methods gracefully"""
        # Use object.__getattribute__ to avoid recursion
        step_registry = object.__getattribute__(self, '_step_registry')
        if name in step_registry:
            return step_registry[name]["function"]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def _discover_sequences(self) -> Dict[str, Callable]:
        """Discover sequence methods dynamically"""
        return {
            name: method for name, method in inspect.getmembers(self, inspect.ismethod)
            if name in [self.sequence_name]  # Only include the specific sequence method
        }

    def execute(self, input_data, sequence_method: str | None = None):
        """Execute the selected sequence method (default: the one matching sequence_name)"""
        method_name = sequence_method or self.sequence_name
        if method_name not in self._sequences:
            raise ValueError(f"Sequence '{method_name}' not found. Available: {list(self._sequences.keys())}")
        return self._sequences[method_name](input_data)



    
class AgentFrame():
    def __init__(self, AgentFrameModel: str):
        self.AgentFrameModel = AgentFrameModel
        self._norm_code_setup()
        self.configuration_memory = {}
        pass

    def _norm_code_setup(self):
        if self.AgentFrameModel == "demo":
            # Judgement
            self._set_up_judgement_demo()   

    def configure(self, inference_instance: Inference, inference_sequence: str):
        if inference_sequence == "judgement" and self.AgentFrameModel == "demo":
            self._configure_judgement_demo(inference_instance)

    def _set_up_judgement_demo(self):
            @Inference.register_inference_sequence("judgement")
            def judgement(self: Inference, input_data: dict):
                """`(IWC-[(MVP-CP)-[(PA)]-MA)]-RR-OWC)`"""
                
                # 1. Input Working Configuration
                working_configuration = self.IWC()
                # 2. Memorized Values Perception
                perception_references = self.MVP(working_configuration, self.value_concepts)
                # 3. Cross Perception
                crossed_perception_reference = self.CP(perception_references)
                # 4. On-Perception Actuation
                actuated_reference = self.PA(working_configuration, crossed_perception_reference, self.function_concept)
                # 5. Memory Actuation
                self.MA(actuated_reference)
                # 6. Return Reference
                self.RR(actuated_reference, self.concepts_to_infer)
                # 7. Output Working Configuration
                self.OWC(self.concepts_to_infer)


    def _configure_judgement_demo(self, inference_instance: Inference):
        # Register steps for THIS SPECIFIC INSTANCE
        @inference_instance.register_step("IWC")
        def input_working_configurations():
            """Validate that input contains two numbers"""
            pass

        @inference_instance.register_step("OWC")
        def output_working_configurations(concepts_to_infer):
            """Perform the output working configurations"""
            pass

        @inference_instance.register_step("RR")
        def return_reference(actuated_reference, concepts_to_infer):
            """Perform the return reference"""
            pass
        
        @inference_instance.register_step("MVP")
        def memorized_values_perception(working_configuration, value_concepts):
            """Perform the memorized values perception"""
            pass

        @inference_instance.register_step("CP")
        def cross_perception(perception_references):
            """Perform the cross perception"""
            pass
        
        @inference_instance.register_step("PA")
        def on_perception_actuation(working_configuration, crossed_perception_reference, function_concept):
            """Perform the on-perception actuation"""
            pass
        
        
        @inference_instance.register_step("MA")
        def memory_actuation(actuated_reference):
            """Perform the memory actuation"""
            pass
        

# Abstract usage pattern
if __name__ == "__main__":

    
    agent = AgentFrame("demo")

    # Create inference instance for arithmetic calculator
    judgement_instance = Inference(
        concepts_to_infer = [],
        value_concepts = [],
        function_concept = "",
        sequence_name="judgement"
    )

    agent.configure(judgement_instance, "judgement")
    judgement_instance.execute(input_data={})


