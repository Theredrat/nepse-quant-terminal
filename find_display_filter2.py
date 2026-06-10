with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines[10800:10950], start=10801):
    if 'JulSc' in line or '>=50' in line or '>= 50' in line or 'READY' in line or 'HOT' in line:
        print(f'{i}: {line}', end='')
