import shutil

shutil.copy('launch_nepse.bat', 'launch_nepse_pre_17c2.bat')
print('Backup created')

content = open('launch_nepse.bat', encoding='utf-8').read()

# Fix CUSTOM_DATE label — only pass symbol, let scanner ask for date
old = ':CUSTOM_DATE\nset /p dt_sym=  Enter stock symbol (e.g. CHCL):\nset /p dt_date=  Enter date (YYYY-MM-DD):\npython nepse_scanner.py --broker-date %dt_sym% %dt_date%\ngoto AGAIN'
new = ':CUSTOM_DATE\nset /p dt_sym=  Enter stock symbol (e.g. CHCL):\npython nepse_scanner.py --broker-date %dt_sym% prompt\ngoto AGAIN'

if old in content:
    content = content.replace(old, new)
    print('Fixed CUSTOM_DATE — date now asked by scanner')
else:
    print('ERROR: label not found')
    exit()

open('launch_nepse.bat', 'w', encoding='utf-8').write(content)
print('Done')

# Also patch scanner to treat 'prompt' as no date
import ast
src = open('nepse_scanner.py', encoding='utf-8').read()
old2 = "    if getattr(args, 'broker_date', None):\n        analyze_broker_date(args.broker_date[0], args.broker_date[1])"
new2 = "    if getattr(args, 'broker_date', None):\n        _bd = args.broker_date\n        _date = None if (len(_bd) < 2 or _bd[1].lower() == 'prompt') else _bd[1]\n        analyze_broker_date(_bd[0], _date)"
if old2 in src:
    src = src.replace(old2, new2)
    open('nepse_scanner.py', 'w', encoding='utf-8').write(src)
    try:
        ast.parse(src)
        print('Scanner updated — prompt handled correctly')
    except SyntaxError as e:
        print(f'ERROR: {e}')
else:
    print('WARNING: scanner wire not found')
