with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines[10800:10950], start=10801):
    print(f'{i}: {line}', end='')
