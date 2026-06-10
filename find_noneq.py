with open('nepse_scanner.py', encoding='utf-8') as f:
    lines = f.readlines()

# Find the NON_EQUITY list variable name
for i, l in enumerate(lines[140:160], start=140):
    print(i, l.rstrip())
