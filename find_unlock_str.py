import re
with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    content = f.read()
idx = content.find('unlock_str')
while idx >= 0:
    print(repr(content[idx:idx+150]))
    print()
    idx = content.find('unlock_str', idx+1)
