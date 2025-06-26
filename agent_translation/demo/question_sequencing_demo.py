#!/usr/bin/env python3
"""
Question Sequencing Agent Demo Script

A practical script for using the QuestionSequencingAgent to deconstruct natural language
instructions into structured question sequences using NormCode terminology.

Usage:
    python question_sequencing_demo.py "Create a user account with email and password"
    
    # Or run interactively
    python question_sequencing_demo.py
"""

import sys
import json
import logging
from pathlib import Path
from typing import Optional

# Add the agent_translation directory to the path
sys.path.append(str(Path(__file__).parent))

from LLMFactory import LLMFactory
from prompt_database import PromptManager
from phase_agent.question_sequencing_agent import QuestionSequencingAgent, QuestionDecomposition

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_normcode_terminology() -> str:
    """Load NormCode terminology from the documentation files"""
    try:
        # Load NormCode syntax reference
        syntax_ref_path = Path(__file__).parent.parent / "NormCode_terms" / "NormCode_Syntax_Reference.md"
        if syntax_ref_path.exists():
            with open(syntax_ref_path, 'r', encoding='utf-8') as f:
                syntax_ref = f.read()
        else:
            syntax_ref = "NormCode syntax reference not found"
        
        # Load terminology clarification
        terminology_path = Path(__file__).parent.parent / "NormCode_terms" / "normcode_terminology_clarification.md"
        if terminology_path.exists():
            with open(terminology_path, 'r', encoding='utf-8') as f:
                terminology = f.read()
        else:
            terminology = "NormCode terminology clarification not found"
        
        return f"""
NormCode Syntax Reference:
{syntax_ref}

NormCode Terminology Clarification:
{terminology}
"""
    except Exception as e:
        logger.warning(f"Could not load NormCode terminology: {e}")
        return """
NormCode Basic Syntax:
- $what?(target, condition): Asks what something is
- $how?(target, condition): Asks how to do something  
- $when?(target, condition): Asks when something happens
- Conditions: $= (equals), $. (contains), $:: (is-a), $% (percentage)
- Process markers: @by, @after, @before, @with
- Conditional markers: @if, @onlyIf, @while, @until
"""


def setup_llm_client(use_local: bool = False) -> Optional[LLMFactory]:
    """Setup LLM client based on configuration"""
    try:
        if use_local:
            # For local LLM endpoint (e.g., Ollama)
            return LLMFactory.create_for_local_endpoint(
                model_name="llama3.1:8b",
                base_url="http://localhost:11434/v1",
                api_key="dummy-key"
            )
        else:
            # For cloud endpoint - use the simple approach
            try:
                # Simple initialization - LLMFactory handles settings automatically
                llm = LLMFactory(model_name="deepseek-v3")
                
                # Test the connection with a simple ask
                test_response = llm.ask("Say 'Hello'", max_tokens=10)
                logger.info(f"LLM connection test successful: {test_response}")
                
                return llm
            except Exception as e:
                logger.warning(f"Could not initialize LLM client: {e}. Using mock mode.")
                return None
    except Exception as e:
        logger.warning(f"Could not setup LLM client: {e}. Using mock mode.")
        return None


def setup_prompt_manager() -> PromptManager:
    """Setup prompt manager with default prompts"""
    try:
        prompt_manager = PromptManager()
        prompt_manager.load_default_prompts()
        return prompt_manager
    except Exception as e:
        logger.warning(f"Could not setup prompt manager: {e}")
        return PromptManager()


def create_agent(llm_client: Optional[LLMFactory] = None, prompt_manager: Optional[PromptManager] = None) -> QuestionSequencingAgent:
    """Create and configure the QuestionSequencingAgent"""
    if llm_client is None:
        logger.info("No LLM client available. Agent will use mock responses.")
    
    if prompt_manager is None:
        prompt_manager = setup_prompt_manager()
    
    return QuestionSequencingAgent(
        llm_client=llm_client,
        prompt_manager=prompt_manager
    )


def format_decomposition_result(result: QuestionDecomposition) -> str:
    """Format the decomposition result for display"""
    output = []
    
    # Main question
    output.append("=" * 60)
    output.append("MAIN QUESTION")
    output.append("=" * 60)
    output.append(f"Type: {result.main_question.type}")
    output.append(f"Target: {result.main_question.target}")
    output.append(f"Condition: {result.main_question.condition}")
    output.append(f"Question: {result.main_question.question}")
    output.append()
    
    # Ensuing questions
    output.append("=" * 60)
    output.append("ENSuing QUESTIONS")
    output.append("=" * 60)
    for i, qa_pair in enumerate(result.ensuing_questions, 1):
        output.append(f"Chunk {i} (Index {qa_pair.chunk_index}):")
        output.append(f"  Question: {qa_pair.question}")
        output.append(f"  Answer: {qa_pair.answer}")
        output.append()
    
    # Metadata
    output.append("=" * 60)
    output.append("METADATA")
    output.append("=" * 60)
    for key, value in result.decomposition_metadata.items():
        output.append(f"{key}: {value}")
    
    return "\n".join(output)


def process_instruction(instruction: str, use_context: bool = True, use_local_llm: bool = False) -> QuestionDecomposition:
    """Process a natural language instruction through the QuestionSequencingAgent"""
    logger.info(f"Processing instruction: {instruction}")
    
    # Setup components
    llm_client = setup_llm_client(use_local_llm)
    prompt_manager = setup_prompt_manager()
    agent = create_agent(llm_client, prompt_manager)
    
    # Load context if requested
    prompt_context = None
    if use_context:
        prompt_context = load_normcode_terminology()
        logger.info("Loaded NormCode terminology context")
    
    # Process the instruction
    result = agent.deconstruct(
        norm_text=instruction,
        prompt_context=prompt_context
    )
    
    return result


def interactive_mode():
    """Run the script in interactive mode"""
    print("Question Sequencing Agent Demo")
    print("=" * 40)
    print("Enter natural language instructions to deconstruct into question sequences.")
    print("Type 'quit' to exit.")
    print()
    
    while True:
        try:
            instruction = input("Enter instruction: ").strip()
            
            if instruction.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not instruction:
                continue
            
            print("\nProcessing...")
            result = process_instruction(instruction)
            
            print("\n" + format_decomposition_result(result))
            print("\n" + "=" * 60 + "\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            logger.error(f"Error in interactive mode: {e}")


def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Command line mode
        instruction = " ".join(sys.argv[1:])
        print(f"Processing instruction: {instruction}")
        
        # Check for flags
        use_context = "--no-context" not in sys.argv
        use_local_llm = "--local" in sys.argv
        
        result = process_instruction(instruction, use_context, use_local_llm)
        print(format_decomposition_result(result))
        
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main() 