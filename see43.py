lines = open('nepse_scanner.py', encoding='utf-8', errors='replace').readlines()
for i in range(7520, 7670):
    print(i+1, lines[i].rstrip())
