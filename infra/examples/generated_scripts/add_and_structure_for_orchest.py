import json

# Convert input strings to floats
num1 = float(input_1)
num2 = float(input_2)

# Calculate the sum
summation = num1 + num2

# Create the JSON object
result_dict = {
    "input_1": num1,
    "input_2": num2,
    "sum": summation
}

# Serialize to JSON string
result = json.dumps(result_dict)