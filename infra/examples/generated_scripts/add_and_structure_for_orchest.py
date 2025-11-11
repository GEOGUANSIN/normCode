import json

input_1 = float(input_1)
input_2 = float(input_2)
result_sum = input_1 + input_2

result = json.dumps({
    "input_1": input_1,
    "input_2": input_2,
    "sum": result_sum
})
