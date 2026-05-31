lines = open('nepse_scanner.py', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'analyze_relative_strength()' in l:
        print(f'{i}: {repr(l)}')
