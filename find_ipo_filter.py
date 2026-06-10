with open('nepse_scanner.py', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'debenture' in l.lower() or 'equity_ipos' in l or 'PNP' in l or 'D8' in l:
        print(i, l.rstrip())
