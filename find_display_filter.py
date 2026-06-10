with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines[10730:10820], start=10731):
    if 'JulSc' in line or 'julsc' in line.lower() or '50' in line or 'READY' in line or 'HOT' in line:
        print(f'{i}: {line}', end='')
