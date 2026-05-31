lines = open('nepse_scanner.py', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'Pick a number' in l or 'pick a number' in l or 'input(' in l or 'choice' in l.lower():
        print(f'{i}: {repr(l)}')
