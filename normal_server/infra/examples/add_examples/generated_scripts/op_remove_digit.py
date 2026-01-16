num_str = input_1

num = int(num_str)

def remove_digit():
    digit_to_remove = num // 10
    return str(digit_to_remove)

if num < 10:
    result = "0"
else:
    result = remove_digit()