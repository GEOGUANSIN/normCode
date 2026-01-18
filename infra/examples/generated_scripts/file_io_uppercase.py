with open(input_path, 'r', encoding='utf-8') as f:
    content = f.read()

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(content.upper())