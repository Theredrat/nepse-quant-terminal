import shutil

shutil.copy('launch_nepse.bat', 'launch_nepse_pre_17b3.bat')
print('Backup created')

content = open('launch_nepse.bat', encoding='utf-8').read()

# Fix the CUSTOM_HOLDERS label to match exact pattern of CUSTOM_FLOOR
old = ':CUSTOM_HOLDERS\nset /p bh_sym="  Enter stock symbol: "\npython nepse_scanner.py --broker-holders %bh_sym%\npause\ngoto menu\n\n'
new = ':CUSTOM_HOLDERS\nset /p symbol=  Enter stock symbol (e.g. BUNGAL):\npython nepse_scanner.py --broker-holders %symbol%\ngoto AGAIN\n\n'

if old in content:
    content = content.replace(old, new)
    print('Fixed CUSTOM_HOLDERS label')
else:
    print('ERROR: label not found — trying alternate')
    # Try without the trailing newlines
    idx = content.find(':CUSTOM_HOLDERS')
    if idx != -1:
        end = content.find('\n\n', idx) + 2
        old_block = content[idx:end]
        print('Found block:', repr(old_block))
        new_block = ':CUSTOM_HOLDERS\nset /p symbol=  Enter stock symbol (e.g. BUNGAL):\npython nepse_scanner.py --broker-holders %symbol%\ngoto AGAIN\n\n'
        content = content[:idx] + new_block + content[end:]
        print('Fixed using index replacement')

open('launch_nepse.bat', 'w', encoding='utf-8').write(content)
print('Done')
