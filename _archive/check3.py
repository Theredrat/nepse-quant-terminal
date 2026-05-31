lines = open('nepse_scanner.py', encoding='utf-8').readlines()

# Find lines around 2290-2350 to see full structure
for i, l in enumerate(lines[2280:2360], 2281):
    print(f'{i}: {repr(l)}')
