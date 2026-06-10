with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines[1130:1170], start=1131):
    print(f'{i}: {line}', end='')
