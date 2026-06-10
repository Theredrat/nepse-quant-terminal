with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    content = f.read()
for line in content.split('\n'):
    if line.strip().startswith('def ') and ('46' in line or 'ipo' in line.lower() or 'season' in line.lower()):
        print(line.strip())
