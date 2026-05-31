lines = open('nepse_scanner.py', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'def _calc_relative_strength(' in l:
        # Print lines i through i+100
        for j, ll in enumerate(lines[i-1:i+100], i):
            print(f'{j}: {repr(ll)}')
        break
