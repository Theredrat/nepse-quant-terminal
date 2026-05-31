lines = open('nepse_scanner.py', encoding='utf-8').readlines()

# Backup first
import shutil
shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_sector_fix.py')
print('Backup saved: nepse_scanner_pre_sector_fix.py')

# Fix only line 362: add c.sector to the SELECT
old = '        SELECT sp.symbol, sp.date, sp.close\n'
new = '        SELECT sp.symbol, c.sector, sp.date, sp.close\n'

fixed = 0
out = []
for i, l in enumerate(lines, 1):
    if l == old and fixed == 0:
        out.append(new)
        fixed += 1
        print(f'  Fixed line {i}: added c.sector to SELECT')
    else:
        out.append(l)

if fixed == 0:
    print('ERROR: target line not found - no changes made')
else:
    open('nepse_scanner.py', 'w', encoding='utf-8').write(''.join(out))
    print('Done. Only 1 line changed.')
