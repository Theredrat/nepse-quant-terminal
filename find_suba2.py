lines = open('nepse_scanner.py', encoding='utf-8', errors='replace').readlines()
for i, l in enumerate(lines):
    if "sub ==" in l and ("'a'" in l or '"a"' in l):
        print(i+1, repr(l))
