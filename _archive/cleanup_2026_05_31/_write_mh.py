import ast, os, shutil

# Safety backup first
shutil.copy2('nepse_scanner.py', '_backups/nepse_scanner_pre_momentumhunter.py')
print('Backup created')

src = open('nepse_scanner.py', encoding='utf-8').read()

# Check if already added
if 'analyze_momentum_hunter' in src:
    print('analyze_momentum_hunter already exists in scanner')
    exit(0)

lns = src.splitlines()

# Find insertion point: end of analyze_broker_impact
start = next(i for i, l in enumerate(lns) if 'def analyze_broker_impact' in l)
end = len(lns)
for i in range(start+1, len(lns)):
    if lns[i].startswith('def ') and lns[i][4].isalpha():
        end = i
        break
print(f'Inserting at line {end}')

# Read the function from separate file
func_src = open('_mh_func.txt', encoding='utf-8').read()
func_lines = func_src.splitlines()

# Splice in
new_lns = lns[:end] + [''] + func_lines + [''] + lns[end:]
ns = '\n'.join(new_lns)

# Validate
try:
    ast.parse(ns)
    open('nepse_scanner.py', 'w', encoding='utf-8').write(ns)
    print('SUCCESS: analyze_momentum_hunter added and file validated')
except SyntaxError as e:
    print(f'SYNTAX ERROR - no changes written: {e}')
