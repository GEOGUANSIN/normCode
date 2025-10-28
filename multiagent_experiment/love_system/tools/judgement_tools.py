from .llm_provider import llm


def _format_input_for_prompt(data: any) -> str:
    """Helper function to convert various inputs into a clean string for an LLM prompt."""
    if isinstance(data, list):
        # Filter out any None values and join the rest into a natural-sounding list.
        items = [str(item) for item in data if item is not None and str(item).strip()]
        if not items:
            return "nothing"
        return " and ".join(items)
    if data is None:
        return "an unspecified entity"
    return str(data)


def get_llm_judgement_from_existing(prompt: str) -> bool:
    """
    Sends a prompt to the pre-initialized LLM to get a boolean judgement.

    Args:
        prompt (str): The question to ask the LLM.

    Returns:
        bool: True if the LLM responds with 'true', False otherwise.
    """
    system_message = "You are a logical reasoner. Please answer the user's question with only the word 'True' or 'False'."
    try:
        response = llm.generate(prompt, system_message=system_message)
        content = response.strip().lower()
        print(f"LLM Judgement for '{prompt[:40]}...': {content}")
        return 'true' in content
    except Exception as e:
        print(f"An error occurred while calling the LLM: {e}")
        return False


def check_all_true(conditions: list) -> bool:
    """Evaluates if all conditions in a list are true."""
    return all(conditions)


def is_towards(feeling: object, target: object) -> bool:
    """Checks if a feeling is directed towards a target using an LLM."""
    feeling_str = _format_input_for_prompt(feeling)
    target_str = _format_input_for_prompt(target)
    prompt = f"Based on a common sense understanding, are feelings described as '{feeling_str}' typically directed towards '{target_str}'? Answer True or False."
    return get_llm_judgement_from_existing(prompt)


def shows_through(feeling: object, actions: list) -> bool:
    """Checks if a feeling is demonstrated through actions using an LLM."""
    feeling_str = _format_input_for_prompt(feeling)
    action_str = _format_input_for_prompt(actions)
    prompt = f"Does a feeling described as '{feeling_str}' typically manifest through actions like '{action_str}'? Answer True or False."
    return get_llm_judgement_from_existing(prompt)


def exists_between(feeling: object, entities: list) -> bool:
    """Checks if a feeling exists between entities using an LLM."""
    feeling_str = _format_input_for_prompt(feeling)
    # This prompt is intentionally generalized. It ignores the extracted 'entities'
    # to ask a general knowledge question about the *type* of feeling.
    prompt = f"Consider a feeling described as '{feeling_str}'. Is this general type of feeling something that can exist between various entities, such as partners, family, or friends? Answer True or False."
    return get_llm_judgement_from_existing(prompt)


def is_accepting_and_wants_happiness(someone: object, feeling: object) -> bool:
    """Judges a complex condition about acceptance using an LLM."""
    feeling_str = _format_input_for_prompt(feeling)
    someone_str = _format_input_for_prompt(someone)
    prompt = f"Does a feeling described as '{feeling_str}' towards '{someone_str}' imply a deep acceptance of them and a genuine desire for their happiness, even when it is difficult? Answer True or False."
    return get_llm_judgement_from_existing(prompt)


def has_dual_nature(feeling: object, emotion: object, decision: object) -> bool:
    """Checks for a dual nature in a concept using an LLM."""
    feeling_str = _format_input_for_prompt(feeling)
    emotion_str = _format_input_for_prompt(emotion)
    decision_str = _format_input_for_prompt(decision)
    prompt = f"Can a concept described as '{feeling_str}' be understood as having a dual nature, encompassing both an emotion like '{emotion_str}' and a decision like '{decision_str}'? Answer True or False."
    return get_llm_judgement_from_existing(prompt)


def is_wanting_wellbeing(emotion: object, someone: object) -> bool:
    """Checks if an emotion is characterized by wanting another's well-being using an LLM."""
    emotion_str = _format_input_for_prompt(emotion)
    someone_str = _format_input_for_prompt(someone)
    prompt = f"Is an emotion described as '{emotion_str}' fundamentally about wanting the wellbeing of '{someone_str}'? Answer True or False."
    return get_llm_judgement_from_existing(prompt)


def is_putting_wellbeing_first(decision: object, someone: object) -> bool:
    """Checks if a decision prioritizes another's well-being using an LLM."""
    decision_str = _format_input_for_prompt(decision)
    someone_str = _format_input_for_prompt(someone)
    prompt = f"Is a decision described as '{decision_str}' characterized by the act of putting the wellbeing of '{someone_str}' first? Answer True or False."
    return get_llm_judgement_from_existing(prompt)
