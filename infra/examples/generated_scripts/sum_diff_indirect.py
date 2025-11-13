import json

# Convert input strings to floats
num1 = float(input_1)
num2 = float(input_2)

# Calculate sum and difference
sum_result = num1 + num2
difference_result = num1 - num2

# Create JSON object
json_object = {
    "sum": sum_result,
    "difference": difference_result
}

# Serialize to JSON string and assign to result
result = json.dumps(json_object)