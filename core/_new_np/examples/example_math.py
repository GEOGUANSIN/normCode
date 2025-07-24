from _concept import Concept
from _reference import Reference, cross_product
from _inference import Inference
from _agentframe import AgentFrame
from _language_models import LanguageModel


def init_concept_with_references():
    """Demonstrate Concept class with actual Reference objects"""
    
    print("=== Concept with References Examples ===\n")

    # Example 1: Mathematical operations with functional concepts
    print("1. Numbers:")
    number1_axes = ["number_1"]
    number1_shape = (2,)  # 2 numbers
    number1_ref = Reference(number1_axes, number1_shape)
    
    # Set mathematical operations
    number1_ref.set("%(1)", number_1=0) 
    number1_ref.set("%(2)", number_1=1) 

    number2_axes = ["number_2"]
    number2_shape = (2,)  # 2 numbers
    number2_ref = Reference(number2_axes, number2_shape)

    # Set mathematical operations
    number2_ref.set("%(3)", number_2=0)   
    number2_ref.set("%(4)", number_2=1) 

    number_1 = Concept("number_1", "Numbers", number1_ref, "{}")
    number_2 = Concept("number_2", "Numbers", number2_ref, "{}")

    print(f"   Concept: {number_1.name}")
    print(f"   Type: {number_1.type} ({number_1.get_type_class()})")
    print(f"   All numbers: {number1_ref.get(number_1=slice(None))}")
    print()

    print(f"   Concept: {number_2.name}")
    print(f"   Type: {number_2.type} ({number_2.get_type_class()})")
    print(f"   All numbers: {number2_ref.get(number_2=slice(None))}")
    print()

    # Example 2: Mathematical operations with functional concepts
    print("2. Mathematical Operation Concept:")
    operation_axes = ["operation"]
    operation_shape = (2,)  # 4 operations
    operation_ref = Reference(operation_axes, operation_shape)
    
    # Set mathematical operations
    operation_ref.set("%(::({1}<$({number})%_> add {2}<$({number})%_>))", operation=0)
    operation_ref.set("%(::({1}<$({number})%_> subtract {2}<$({number})%_>))", operation=1)
    # operation_ref.set("%(::({1}<$({number})%_> multiply {2}<$({number})%_>))", operation=2)
    # operation_ref.set("%(::({1}<$({number})%_> divide {2}<$({number})%_>))", operation=3)
    
    operation_concept = Concept("::({1}<$({number})%_> operate on {2}<$({number})%_>)", "Basic mathematical operations", operation_ref, "::({})")
    print(f"   Concept: {operation_concept.name}")
    print(f"   Type: {operation_concept.type} ({operation_concept.get_type_class()})")
    print(f"   All operations: {operation_ref.get(operation=slice(None))}")
    print()


    # Answer concept
    answer_axes = ["number_answer"]
    answer_shape = (1,)
    # answer_ref = Reference(answer_axes, answer_shape)
    # answer_ref.set("%(1)", answer=0)
    answer_concept = Concept("number_answer", "Answer", None, "{}")
    print(f"   Concept: {answer_concept.name}")

    return operation_concept, number_1, number_2, answer_concept
 
def init_working_configuration():
    working_configuration = {
    "number_1": {
        "perception": {
            "mvp": {
                "mode": "formal"
            },
        },
        "actuation": {
        },
        "cognition": {
        }
    },
    "number_2": {
        "perception": {
            "mvp": {
                "mode": "formal"
            },
        },
        "actuation": {
        },
        "cognition": {
        }
    },
    "::({1}<$({number})%_> operate on {2}<$({number})%_>)": {
        "perception": {
            "asp": {
                "mode": "in-cognition"
            },
            "ap": {
                "mode": "llm_formal",
                "product": "translated_templated_function",
                "value_order": {
                    "number_1": 0,
                    "number_2": 1
                }
            }
        },
        "actuation": {
            "pta": {
                "mode": "in-cognition",
                "value_order": {
                    "number_1": 0,
                    "number_2": 1
                }
            },
            "ma": {
                "mode": "formal",
            },
        },  
        "cognition": {
            "rr": {
                "mode": "identity"
            },
        }
    },
    "number_answer": {
        "perception": {
            "mvp": {
                "mode": "formal"
            },
        },
        },
    }
    return working_configuration



if __name__ == "__main__":

    # Initialize concepts and inference
    operation_concept, number_1, number_2, answer_concept = init_concept_with_references()   
    operation_inference = Inference(
        "imperative", 
        answer_concept,
        [number_1, number_2],
        operation_concept
    )

    # Initialize agent
    llm = LanguageModel("deepseek-r1-distill-qwen-1.5b")
    agent = AgentFrame("demo", init_working_configuration(), llm=llm)
    agent.configure(
        inference_instance=operation_inference, 
        inference_sequence="imperative",
    )

    # Execute inference
    answer_concept = operation_inference.execute(input_data={})

    # Print answer
    if answer_concept.reference:
        print(f"Answer concept reference: {answer_concept.reference.tensor}")
        print(f"Answer concept reference without skip values: {answer_concept.reference.get_tensor(ignore_skip=True)}")
        print(f"Answer concept axes: {answer_concept.reference.axes}")
        all_info_reference = cross_product([number_1.reference, number_2.reference, operation_concept.reference, answer_concept.reference])
        print(f"All info reference: {all_info_reference.tensor}")
        print(f"All info reference without skip values: {all_info_reference.get_tensor(ignore_skip=True)}")
        print(f"All info axes: {all_info_reference.axes}")
    else:
        print("Answer concept reference is None")
