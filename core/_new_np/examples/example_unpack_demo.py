from _reference import Reference
from _concept import Concept
from example_and import _log_concept_details, init_working_configuration, _log_inference_result, WriteAgent, init_concept_with_references
from _concept import Concept
from _reference import Reference, cross_product, element_action
from _inference import Inference, register_inference_sequence
from _agentframe import AgentFrame, logger
from _language_models import LanguageModel
from _methods._demo import strip_element_wrapper, wrap_element_wrapper
from _methods._workspace_demo import all_workspace_demo_methods
from _methods._grouping_demo import all_grouping_demo_methods

# Example: answer concept reference 1 (from log)
# Axes: ['technical_concepts_classification', 'technical_concepts_1']
answer_concept_reference_1_tensor = [[['%(cloud architecture)', '%(latency)', '%(edge caching)', '%(parallel processing)', '%(AI models)', '%(response times)']]]

# Example: answer concept reference 2 (from log)
# Axes: ['relatable_ideas_operation', 'technical_concepts_classification', 'technical_concepts_1', '{technical_concepts}', 'relatable_ideas', '{relatable_ideas}']
answer_concept_reference_2_tensor = [[[[[['%(Cloud architecture is like a virtual LEGO set for computers — just like how you can snap together LEGO pieces to build different structures, cloud architecture lets you combine virtual servers, storage, and networks to create IT solutions without needing physical hardware.)']], [['%(Latency is like a traffic jam on the information highway — the more congested it is, the longer it takes for data to reach its destination.)']], [['%(Edge caching is like a local grocery store keeping your favorite snacks in stock so you don’t have to drive to the warehouse every time you want one.)']], [['%(Parallel processing is like a team of chefs in a kitchen, each cooking a different part of the meal at the same time to finish faster.)']], [['%(A neural network is like a team of chefs in a kitchen, each specializing in a different ingredient, working together to create a perfect dish — each layer processes information and passes it on, refining the result step by step.)']], [['%(How quickly a waiter brings your food after you order — the shorter the wait, the better the service (low response time).)']]]]]]

# Example tensor for unpacking demo: a relation concept as a list of records
# Axes: ['technical_concepts_classification', 'technical_concepts_1']
relation_tensor_raw = [[
    {
        '{technical_concepts}': 'cloud architecture',
        '{relatable_ideas}': [[['Cloud architecture is like a virtual LEGO set for computers — just like how you can snap together LEGO pieces to build different structures, cloud architecture lets you combine virtual servers, storage, and networks to create IT solutions without needing physical hardware.']]]
    },
    {
        '{technical_concepts}': 'latency',
        '{relatable_ideas}': [[['Latency is like a traffic jam on the information highway — the more congested it is, the longer it takes for data to reach its destination.']]]
    },
    # {
    #     '{technical_concepts}': 'edge caching',
    #     '{relatable_ideas}': [[['Edge caching is like a local grocery store keeping your favorite snacks in stock so you don’t have to drive to the warehouse every time you want one.']]]
    # },
    # {
    #     '{technical_concepts}': 'parallel processing',
    #     '{relatable_ideas}': [[['Parallel processing is like a team of chefs in a kitchen, each cooking a different part of the meal at the same time to finish faster.']]]
    # },
    # {
    #     '{technical_concepts}': 'AI models',
    #     '{relatable_ideas}': [[['A neural network is like a team of chefs in a kitchen, each specializing in a different ingredient, working together to create a perfect dish — each layer processes information and passes it on, refining the result step by step.']]]
    # },
    # {
    #     '{technical_concepts}': 'response times',
    #     '{relatable_ideas}': [[['How quickly a waiter brings your food after you order — the shorter the wait, the better the service (low response time).']]]
    # },
]]
relation_tensor = [[f"%({str(relation_tensor_raw[0])})"]]
relation_reference = Reference.from_data(relation_tensor, axis_names=["technical_concepts_classification", "technical_concepts_1"])

if __name__ == "__main__":
    # Initialize concepts and inference
    (technical_concepts_1, 
    technical_concepts_classification_concept, 
    technical_concepts_2, 
    relatable_ideas_operation_concept, 
    relatable_ideas_concept,
    relatable_ideas_concept_2,
    write_content_concept,
    content_concept,
    technical_and_relatable_ideas_concept,
    grouping_technical_and_relatable_ideas_concept) = init_concept_with_references()   

    technical_and_relatable_ideas_concept.reference = relation_reference
   # Initialize agent
    llm = LanguageModel("qwen-plus")
    workspace = {
        "content": "The new cloud architecture reduces latency by 35% through optimized edge caching and parallel processing. Enterprise customers can now deploy AI models with sub-100ms response times."
        # "content": "The mitochondrial oxidative phosphorylation cascade exhibits remarkable efficiency in ATP synthesis through the electron transport chain, utilizing cytochrome c oxidase as the terminal electron acceptor. This process is facilitated by the proton gradient established across the inner mitochondrial membrane, enabling chemiosmotic coupling between electron transfer and ATP synthase activity. The Krebs cycle intermediates serve as substrates for various biosynthetic pathways, while the pentose phosphate pathway generates NADPH for reductive biosynthesis and ribose-5-phosphate for nucleotide synthesis."
    } 

    configuration = init_working_configuration()
    configuration[":S_write_content:(transform {1}<$({technical_concepts})%_> into {2}?<$({relatable_ideas})%_>)"][":S_write_content:(transform {1}<$({technical_concepts})%_> into {2}?<$({relatable_ideas})%_>)"]=\
    {
        "perception": {
            "ap": {
                "mode": "llm_workspace",
                "product": "translated_templated_function_for_workspace",
                "value_order": {
                    "[{technical_concepts} and {relatable_ideas} in all {technical_concepts}]": 0,
                    "[{technical_concepts} and {relatable_ideas} in all {technical_concepts}]": 1,
                },
                "relation_extraction":{
                    0: "{technical_concepts}",
                    1: "{relatable_ideas}",
                },
                "filter_constraints": [[0, 1]],
                "workspace_object_name_list": ["content"]
            },
            "asp": {
                "mode": "in-cognition",
                "workspace_object_name_list": ["content"]
            }
        },
        "actuation": {
            "pta": {
                "mode": "in-workspace",
                "value_order": {
                    "[{technical_concepts} and {relatable_ideas} in all {technical_concepts}]": 0,
                    "[{technical_concepts} and {relatable_ideas} in all {technical_concepts}]": 1,
                },
                "relation_extraction":{
                        0: "{technical_concepts}",
                        1: "{relatable_ideas}", 
                },
                "filter_constraints": [[0, 1]],
                "workspace_object_name_list": ["content"]
            },
            "ma": {
                "mode": "formal"
            }
        },
        "cognition": {
            "rr": {
                "mode": "identity",
            }
        },
    }
    

    fourth_inference = Inference(
        sequence_name="imperative", 
        concept_to_infer=content_concept,
        value_concepts=[technical_and_relatable_ideas_concept],
        function_concept=write_content_concept,
    )


    # Initialize content agent
    content_agent = WriteAgent(
        "workspace_demo",
        configuration,
        llm=llm,
        workspace=workspace)

    # Configure content agent and update value concepts
    content_agent.configure(
        inference_instance=fourth_inference, 
        inference_sequence="imperative",
    )
    technical_concepts_2 = fourth_inference.execute()




