with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Read auto_update_watchlist function
for line in lines[13008:13150]:
    print(line, end='')
