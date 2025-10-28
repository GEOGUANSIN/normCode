import sys
import os

# Add project root to path to allow direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from multi_agent_experiement2.love_inquiry_system.parser import NormCodeParser
from multi_agent_experiement2.love_inquiry_system.agents.orchestrator_agent import OrchestratorAgent

def main():
    """
    Main entry point for the NormCode execution system.
    """
    # Path is now relative to the project root
    file_path = "multi_agent_experiement2/love_decomposition.md"
    
    print(f"Parsing NormCode file: {file_path}")
    
    try:
        parser = NormCodeParser()
        root_concept = parser.parse_file(file_path)
        
        print("\n--- Parsed Concept Tree ---")
        # root_concept.display() # Commenting out for cleaner logs during agent development
        print("\nParsing complete.")
        
        orchestrator = OrchestratorAgent(root_concept)
        orchestrator.execute()

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
