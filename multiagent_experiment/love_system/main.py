from multiagent_experiment.love_system.agents.controller_agent import ControllerAgent


def main():
    """Initializes and runs the multi-agent system with a single text input."""
    print("--- Initializing Love Definition System ---")

    # The single text input that will be processed.
    text_input = """
A quiet hum, a constant warmth. It’s the certainty of a wiggling welcome at the door, a joy that needs no words. It’s a wet nose nudging her hand, a heavy head on her foot, a shared language of simple things. A protective flare when he startles; a deep softness watching him dream. Her world has shrunk to the size of his walks, yet expanded to notice the light on the grass as he does. There are no negotiations, only a quiet vow. It’s checking the sidewalk heat with her hand, knowing the spot behind his ear that makes his leg thump. He is her simplest, furry piece of home."""

    controller = ControllerAgent()
    final_result = controller.run(text_input)
    print("\n--- System Execution Complete ---")
    print(f"Final Result: {final_result}")


if __name__ == "__main__":
    main()
