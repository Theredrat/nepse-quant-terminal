lines = open('nepse_scanner.py', encoding='utf-8', errors='replace').readlines()
for i in range(8063, 8085):
    print(i+1, repr(lines[i]))
