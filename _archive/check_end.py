lines = open('nepse_scanner.py', encoding='utf-8').readlines()
print(f'Total lines: {len(lines)}')
for i, l in enumerate(lines[3900:], 3901):
    print(f'{i}: {repr(l)}')
