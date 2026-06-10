with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines[10950:11020], start=10951):
    print(f'{i}: {line}', end='')
