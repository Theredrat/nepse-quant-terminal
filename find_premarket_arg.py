with open('nepse_scanner.py', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'premarket' in l.lower() and 'add_argument' in l:
        print(i, l.rstrip())
