import json
from .llm_provider import llm


def extract_love_concepts(text_input: str) -> dict:
    """
    Extracts a predefined set of concepts about love from a single text block
    using an LLM.

    Args:
        text_input: A block of text describing a scenario or feelings.

    Returns:
        A dictionary with extracted concepts. If a concept is not found,
        the value will be None.
    """
    concepts_to_extract = [
        "care", "attachment", "target", "kind acts", "sacrifice",
        "caring about another person's happiness", "partners", "family",
        "friends", "spiritual connections", "emotion", "decision"
    ]

    prompt = f"""
        Read the following text carefully:
        ---
        {text_input}
        ---
        From the text above, extract information for the following concepts.
        Your response MUST be a single JSON object.
        The keys of the JSON should be the concepts from the list.
        The value for each key should be a string describing the concept as found in the text, or a reasonable inference from the text.
        If a concept is not mentioned or cannot be inferred, the value for that key MUST be null.

        Here are descriptions of the concepts to guide your extraction:
        - "target": The person, pet, or entity towards whom the feelings are directed. Infer this from context (e.g., pronouns like 'her', 'him', 'it', or descriptions) if not explicitly named.
        - "care": Specific actions or feelings showing concern for well-being.
        - "attachment": Descriptions of the bond or connection.
        - "kind acts": Concrete examples of kindness mentioned.
        - "emotion": The specific feelings or emotions described.
        - "decision": Any mention of the feeling being a choice or conscious decision.

        Full concept list: {', '.join(concepts_to_extract)}
    """

    try:
        system_message = "You are an expert at information extraction. Your output must be only a valid JSON object."
        response_str = llm.generate(prompt, system_message=system_message, response_format={"type": "json_object"})
        print(f"LLM Extraction Response: {response_str}")
        extracted_data = json.loads(response_str)

        # Ensure all keys are present, defaulting to None if missed by the LLM
        for concept in concepts_to_extract:
            if concept not in extracted_data:
                extracted_data[concept] = None
        return extracted_data

    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON from LLM response: {e}")
        return {concept: None for concept in concepts_to_extract}
    except Exception as e:
        print(f"An error occurred during concept extraction: {e}")
        return {concept: None for concept in concepts_to_extract}
