import json

# Convert input strings to numbers
num1 = float(input_1)
num2 = float(input_2)

# Calculate sum and difference
sum_result = num1 + num2
difference_result = num1 - num2

# Create JSON object
result_dict = {
    "sum": sum_result,
    "difference": difference_result
}

# Convert to JSON string and assign to result
result = json.dumps(result_dict)