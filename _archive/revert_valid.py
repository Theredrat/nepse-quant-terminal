import shutil
shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_validfix.py')

content = open('nepse_scanner.py', encoding='utf-8').read()

# Revert the bad fix - restore valid.sum() < 2
old = '            if valid.sum() < 1:'
new = '            if valid.sum() < 2:'
if old in content:
    content = content.replace(old, new)
    print('Reverted valid.sum fix')

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)
print('Done.')
