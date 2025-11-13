import json

# Convert input strings to floats for generality
num1 = float(input_1)
num2 = float(input_2)

# Calculate mean and product
mean = (num1 + num2) / 2
product = num1 * num2

# Create JSON object
result_dict = {
    "mean": mean,
    "product": product
}

# Convert to JSON string
result = json.dumps(result_dict)