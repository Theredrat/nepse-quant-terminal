lines = open('nepse_scanner.py', encoding='utf-8').readlines()

# Find _normalize_fs and get_full_floorsheet to see floorsheet structure
for func in ['def _normalize_fs(', 'def get_full_floorsheet(']:
    for i, l in enumerate(lines, 1):
        if func in l:
            print(f'\n=== {func} at line {i} ===')
            for j, ll in enumerate(lines[i-1:i+40], i):
                print(f'{j}: {repr(ll)}')
            break
