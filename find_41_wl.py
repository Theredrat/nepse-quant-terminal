with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find where Option 41 loads watchlist symbols
for i, line in enumerate(lines[10688:10730], start=10689):
    print(f'{i}: {line}', end='')
