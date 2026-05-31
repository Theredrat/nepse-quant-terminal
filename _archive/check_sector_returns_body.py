lines = open('nepse_scanner.py', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'def _sector_returns(' in l:
        for j, ll in enumerate(lines[i-1:i+70], i):
            print(f'{j}: {repr(ll)}')
        break
