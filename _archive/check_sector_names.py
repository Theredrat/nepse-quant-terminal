lines = open('nepse_scanner.py', encoding='utf-8').readlines()
for i, l in enumerate(lines[455:530], 456):
    print(f'{i}: {repr(l)}')
