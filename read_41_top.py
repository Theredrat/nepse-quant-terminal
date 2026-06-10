with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for line in lines[10688:10710]:
    print(line, end='')
