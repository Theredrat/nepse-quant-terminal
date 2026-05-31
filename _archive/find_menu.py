import os
backups = ['nepse_scanner_backup_clean.py', 'nepse_scanner_pre_momentum.py', 'nepse_scanner_pre_rs.py']
for f in backups:
    if os.path.exists(f):
        lines = open(f, encoding='utf-8').readlines()
        print(f'{f}: {len(lines)} lines')
        for i, l in enumerate(lines, 1):
            if 'Pick a number' in l or 'input(' in l or '== "1"' in l or "== '1'" in l:
                print(f'  line {i}: {repr(l)}')
    else:
        print(f'{f} NOT FOUND')
