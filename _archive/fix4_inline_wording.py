"""
Fix 4: Correct "STOCK-SPECIFIC weakness" wording for stocks that are inline with sector
The variable is named b2, not sec_context. Patch that specific line.
"""
import shutil, ast

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_fix4.py')
content = open('nepse_scanner.py', encoding='utf-8').read()

# Find the exact line
search = 'STOCK-SPECIFIC weakness, not sector'
idx = content.find(search)
if idx == -1:
    print('ERROR: target line not found')
    exit()

# Get the full line
line_start = content.rfind('\n', 0, idx) + 1
line_end   = content.find('\n', idx)
old_line   = content[line_start:line_end]
print(f'Found line: {repr(old_line)}')

# Determine indentation
indent = len(old_line) - len(old_line.lstrip())
pad    = ' ' * indent

# The variable name (b2 or sec_context)
varname = old_line.lstrip().split('=')[0].strip()   # e.g. "b2"
print(f'Variable name: {varname}')

# We need to find the matching positive branch (rs5 >= 0) just before this
# Look backward for the if/elif that sets the same variable
pos_search = f'{varname} = f"Sector'
back_idx = content.rfind(pos_search, 0, idx)
if back_idx == -1:
    print('ERROR: could not find the positive branch')
    exit()

pos_line_start = content.rfind('\n', 0, back_idx) + 1
pos_line_end   = content.find('\n', back_idx)
old_pos_line   = content[pos_line_start:pos_line_end]
print(f'Positive branch line: {repr(old_pos_line)}')

# Build the new three-branch block replacing just the negative line
# We keep the positive branch as-is and replace the negative line with a two-branch check
new_neg_block = (
    f"{pad}if rs5 >= -2:\n"
    f"{pad}    {varname} = f\"Sector ({{sector}}) up +{{sec5:.1f}}% 5D — stock inline with sector ({{rs5:+.1f}}% RS)\"\n"
    f"{pad}else:\n"
    f"{pad}    {varname} = f\"Sector ({{sector}}) up +{{sec5:.1f}}% but stock {{ret5:+.1f}}% — STOCK-SPECIFIC weakness, not sector\""
)

# Replace only the old negative line
content = content[:line_start] + new_neg_block + content[line_end:]

# Save
open('nepse_scanner.py', 'w', encoding='utf-8').write(content)
print('Fix 4 applied.')

# Syntax check
try:
    ast.parse(content)
    print('Syntax OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    shutil.copy('nepse_scanner_pre_fix4.py', 'nepse_scanner.py')
    print('Backup restored.')
