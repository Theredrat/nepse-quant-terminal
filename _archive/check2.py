lines = open('nepse_scanner.py', encoding='utf-8').readlines()
for i, l in enumerate(lines[2320:2360], 2321):
    print(f'{i}: {repr(l)}')
