lines = open('nepse_scanner.py', encoding='utf-8', errors='replace').readlines()
for i in range(7670, 7820):
    print(i+1, lines[i].rstrip())
