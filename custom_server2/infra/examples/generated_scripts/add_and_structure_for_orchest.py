import json

input_1_num = float(input_1)
input_2_num = float(input_2)
sum_result = input_1_num + input_2_num

result = json.dumps({
    "input_1": input_1_num,
    "input_2": input_2_num,
    "sum": sum_result
})