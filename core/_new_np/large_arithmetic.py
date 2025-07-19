from _language_models import LanguageModel
import json

llm = LanguageModel("qwen-turbo-latest")







if __name__ == "__main__":

    number_1_list = [124525342123, 84765234, 12345678901234567890, 934132345678901234567890]
    number_2_list = [12345678901234567890, 934132345678901234567890, 124525342123, 84765234]
    operation = "add"

    for number_1, number_2 in zip(number_1_list, number_2_list):
        answer = llm.generate(
            prompt=f"""
            Think step by step, and then answer the question.
            Instruction:{number_1} {operation} {number_2}
            Output in JSON format:
            {{
                "reasoning": "The reasoning to the answer",
                "answer": "the number of the answer in string format",
            }}
            """,
            response_format= {
                "type": "json_object",
            }
        )

        answer_dict = json.loads(answer)
        correct_answer = number_1 + number_2
        print(f"The answer is: {answer_dict['answer']} for {number_1} {operation} {number_2}")
        print(f"The correct answer is: {correct_answer}")
        print("================================================")
        print(f"The answer is correct: {answer_dict['answer'] == correct_answer}")
        print("================================================")
        print(f"The reasoning is: {answer_dict['reasoning']}")
        print("================================================")




