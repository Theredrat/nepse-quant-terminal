lines = open('nepse_scanner.py', encoding='utf-8', errors='replace').readlines()
for i in range(7820, 7960):
    print(i+1, lines[i].rstrip())
