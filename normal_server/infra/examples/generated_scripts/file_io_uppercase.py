with open(input_path, 'r') as f:
    content = f.read()

with open(output_path, 'w') as f:
    f.write(content.upper())