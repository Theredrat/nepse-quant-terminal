import re

with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find exact function boundaries
start = content.index('def detect_phase(')
rest = content[start:]
next_def = re.search(r'\ndef [a-zA-Z]', rest[20:])
end = start + 20 + next_def.start() + 1

print("Old function:")
print(repr(content[start:end]))
