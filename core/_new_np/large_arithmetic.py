from _language_models import LanguageModel
import json

llm = LanguageModel("qwen-turbo-latest")


def add_in_base(num1: str, num2: str, base: int) -> str:
    if base < 2 or base > 36:
        raise ValueError("Base must be between 2 and 36")
    
    rev1 = list(num1.upper())[::-1]
    rev2 = list(num2.upper())[::-1]
    carry = 0
    result_digits = []
    n = max(len(rev1), len(rev2))
    valid_digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    for i in range(n):
        d1 = rev1[i] if i < len(rev1) else '0'
        d2 = rev2[i] if i < len(rev2) else '0'
        
        if '0' <= d1 <= '9':
            n1 = ord(d1) - ord('0')
        else:
            n1 = 10 + ord(d1) - ord('A')
            
        if '0' <= d2 <= '9':
            n2 = ord(d2) - ord('0')
        else:
            n2 = 10 + ord(d2) - ord('A')
            
        total = n1 + n2 + carry
        carry = total // base
        digit = total % base
        result_digits.append(valid_digits[digit])
    
    if carry:
        result_digits.append(valid_digits[carry])
    
    res_string = ''.join(result_digits)[::-1]
    res_string = res_string.lstrip('0')
    return res_string if res_string != '' else '0'




if __name__ == "__main__":

    number_1 = "2374839283767523943"
    number_2 = "424390824342"
    answer_base_10 = "23743839708158348285"
    answer_base_10_2 = "2375263674591865868285"
    answer_base_16 = "1234567890ABCDEF"
    answer_base_30 = "23748396A7AF7D47C85"
    answer_base_30_2 = "23748396A7AF7D66D65"


    print(add_in_base(number_1, number_2, 10))
    print(f"The answer is correct in base 10: {add_in_base(number_1, number_2, 10) == answer_base_10}")
    print(add_in_base(number_1, number_2, 16))
    print(f"The answer is correct in base 16: {add_in_base(number_1, number_2, 16) == answer_base_16}")
    print(add_in_base(number_1, number_2, 30))
    print(f"The answer is correct in base 30: {add_in_base(number_1, number_2, 30) == answer_base_30}")


    # number_1_list = [124525342123, 84765234, 12345678901234567890, 934132345678901234567890]
    # number_2_list = [12345678901234567890, 934132345678901234567890, 124525342123, 84765234]
    # operation = "add"

    # for number_1, number_2 in zip(number_1_list, number_2_list):
    #     answer = llm.generate(
    #         prompt=f"""
    #         Think step by step, and then answer the question.
    #         Instruction:{number_1} {operation} {number_2}
    #         Output in JSON format:
    #         {{
    #             "reasoning": "The reasoning to the answer",
    #             "answer": "the number of the answer in string format",
    #         }}
    #         """,
    #         response_format= {
    #             "type": "json_object",
    #         }
    #     )

    #     answer_dict = json.loads(answer)
    #     correct_answer = number_1 + number_2
    #     print(f"The answer is: {answer_dict['answer']} for {number_1} {operation} {number_2}")
    #     print(f"The correct answer is: {correct_answer}")
    #     print("================================================")
    #     print(f"The answer is correct: {answer_dict['answer'] == correct_answer}")
    #     print("================================================")
    #     print(f"The reasoning is: {answer_dict['reasoning']}")
    #     print("================================================")




