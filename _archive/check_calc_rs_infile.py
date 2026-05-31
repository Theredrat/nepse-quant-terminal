lines = open('nepse_scanner.py', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'def _calc_relative_strength(' in l:
        print(f'Found at line {i}')
        for j, ll in enumerate(lines[i-1:i+60], i):
            print(f'{j}: {repr(ll)}')
        break
