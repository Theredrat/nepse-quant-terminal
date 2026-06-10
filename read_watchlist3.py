with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines[460:530]:
    print(line, end='')
