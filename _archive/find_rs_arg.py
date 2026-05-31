content = open('nepse_scanner.py', encoding='utf-8').read()

# Find parse_args and show lines around --rs argument
lines = content.split('\n')
for i, l in enumerate(lines, 1):
    if '--rs' in l and 'add_argument' in l:
        print(f'Found at line {i}: {repr(l)}')
