lines = open('nepse_scanner.py', encoding='utf-8').readlines()
for i, l in enumerate(lines[3700:3750], 3701):
    print(f'{i}: {repr(l)}')
