lines = open('nepse_scanner.py', encoding='utf-8', errors='replace').readlines()
for i, l in enumerate(lines):
    if '43' in l and ('def ' in l or 'regime' in l.lower()):
        print(i+1, l.rstrip())
