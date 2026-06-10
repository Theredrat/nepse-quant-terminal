with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines[320:460]:
    print(line, end='')
