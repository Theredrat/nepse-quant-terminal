lines = open('nepse_scanner.py', encoding='utf-8', errors='replace').readlines()
for i, l in enumerate(lines):
    if 'regime' in l.lower() and ('choice' in l.lower() or 'sub' in l.lower() or "'a'" in l or '"a"' in l):
        print(i+1, repr(l))
