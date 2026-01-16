import re

numbers1 = re.findall(r'\d+', str(input_1))
sum_value = sum(int(n) for n in numbers1)

sum_value += int(input_2)
result = str(sum_value)