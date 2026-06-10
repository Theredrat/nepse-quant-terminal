with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Total lines: {len(lines)}')

for i, line in enumerate(lines):
    if 'auto_update_watchlist' in line and 'def ' in line:
        print(f'Line {i+1}: {line.rstrip()}')
