from multiagent_experiment.nc_compiler.agents.blueprint_agent import BlueprintAgent
from multiagent_experiment.nc_compiler.agents.compilation_agent import CompilationAgent
from multiagent_experiment.nc_compiler.agents.verification_agent import VerificationAgent

class MasterControllerAgent:
    def __init__(self):
        self.blueprint_agent = BlueprintAgent()
        self.compilation_agent = CompilationAgent()
        self.verification_agent = VerificationAgent()
        # In a real system, an ExecutionState object would be initialized here.

    def run(self, initial_normtext_path: str):
        """
        Orchestrates the entire NormCode compilation workflow from start to finish.
        """
        print("MasterControllerAgent: Starting NormCode compilation workflow...")
        
        # Phase 1: Blueprinting
        with open(initial_normtext_path, 'r') as f:
            normtext = f.read()
        
        normcode_plan_path = self.blueprint_agent.run(normtext)
        
        # We now use the dynamically generated plan for the next phase
        # In a real system, we would log the result to ExecutionState here.

        # Phase 2: Compilation
        system_source_code_path = self.compilation_agent.run(normcode_plan_path)
        # Log result to ExecutionState...
        
        # Phase 3: Verification
        # Define some dummy input data for the target system
        input_data = {"example_input": "data"}
        
        final_trace = self.verification_agent.run(system_source_code_path, input_data)
        # Log final trace to ExecutionState...

        print("\nMasterControllerAgent: Workflow completed!")
        print("=========================================")
        print("Final Verifiable Execution Trace:")
        print(final_trace)
        print("=========================================")

        return final_trace
