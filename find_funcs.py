import re
# Find the quick_pick, smart_pick, momentum_hunter, deploy_ready functions
with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find function definitions
functions = ['quick_pick', 'smart_pick', 'momentum_hunter', 'auto_update_watchlist', 'deploy']
for func in functions:
    matches = [m.start() for m in re.finditer(f'def {func}', content, re.IGNORECASE)]
    for pos in matches:
        print(f'=== def found: {func} at char {pos} ===')
        print(content[pos:pos+200])
        print()
