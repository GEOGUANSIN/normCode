"""
Test script for In-Question Analysis Agent
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from phase_agent.in_question_analysis_agent import InQuestionAnalysisAgent


def test_in_question_analysis():
    """Test the in-question analysis agent with various examples"""
    
    print("=== In-Question Analysis Agent Test ===\n")
    
    try:
        # Create agent with verbose mode
        agent = InQuestionAnalysisAgent(verbose=True, llm_model="qwen-turbo-latest")
        print("✓ Agent created successfully")
        
        # Get NormCode context
        normcode_context = agent.prompt_manager.get_prompt("general", "context")
        if normcode_context:
            print(f"✓ NormCode context retrieved ({len(normcode_context)} characters)")
        else:
            print("⚠ No NormCode context found")
        
        # Test cases from the algorithm document
        test_cases = [
            {
                "name": "Single Clause (Imperative)",
                "question": "$what?({step_2}, $::)",
                "answer": "Mix the ingredients together"
            },
            {
                "name": "Coordinate Clauses (Declarative)",
                "question": "$what?({step_2}, $::)",
                "answer": "The bread is heated and the pan is greased"
            },
            {
                "name": "Conditional Clauses (Imperative)",
                "question": "$what?({step_2}, $::)",
                "answer": "If the dough is sticky, add more flour"
            },
            {
                "name": "Sequential Clauses (Imperative)",
                "question": "$what?({step_2}, $::)",
                "answer": "First mix the ingredients, then pour into pan, finally bake"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {test_case['name']} ---")
            print(f"Question: {test_case['question']}")
            print(f"Answer: {test_case['answer']}")
            
            try:
                result = agent.analyze(
                    question=test_case['question'],
                    answer=test_case['answer'],
                    prompt_context=normcode_context,
                    save_result=True
                )
                
                print(f"✓ Analysis completed successfully")
                print(f"  Question Structure: {result.question_structure.question}")
                print(f"  Clause Analysis: {result.clause_analysis.structure_type} with {result.clause_analysis.clause_count} clauses")
                print(f"  Template Mappings: {len(result.template_mappings)}")
                
                print(f"\n  Phase 1 Draft:")
                print(f"    {result.phase1_draft.content}")
                
                print(f"\n  Phase 2 Draft:")
                print(f"    {result.phase2_draft.content}")
                
                print(f"\n  Phase 3 Draft:")
                print(f"    {result.phase3_draft.content}")
                
                if result.template_mappings:
                    print(f"\n  Template Mappings:")
                    for mapping in result.template_mappings:
                        print(f"    {mapping.concrete_term} -> {mapping.abstract_placeholder} ({mapping.placeholder_type})")
                
            except Exception as e:
                print(f"❌ Error in test case {i}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n=== Test Complete ===")
        print(f"All test cases processed")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_in_question_analysis() 