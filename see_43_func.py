lines = open('nepse_scanner.py', encoding='utf-8', errors='replace').readlines()
for i in range(7532, min(7650, len(lines))):
    print(i+1, lines[i].rstrip())
