src = open('nepse_scanner.py', encoding='utf-8').read()
lines = src.splitlines()
for i, l in enumerate(lines):
    if 'broker_activity' in l.lower() or 'net_qty' in l.lower() or 'accumul' in l.lower():
        print(i, l)
