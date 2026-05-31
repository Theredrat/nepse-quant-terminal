lines = open('nepse_scanner.py', encoding='utf-8').readlines()
for i, l in enumerate(lines[2300:2320], 2301):
    print(f'{i}: {repr(l)}')
