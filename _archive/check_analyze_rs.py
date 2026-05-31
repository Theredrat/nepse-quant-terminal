lines = open('nepse_scanner.py', encoding='utf-8').readlines()

print('=== analyze_relative_strength FULL BODY ===')
for i, l in enumerate(lines, 1):
    if 'def analyze_relative_strength(' in l:
        for j, ll in enumerate(lines[i-1:i+80], i):
            print(f'{j}: {repr(ll)}')
        break
