lines = open('nepse_scanner.py', encoding='utf-8').readlines()

# Find the main() function and all args handling
in_main = False
for i, l in enumerate(lines, 1):
    if l.startswith('def main('):
        in_main = True
    if in_main:
        print(f'{i}: {repr(l)}')
    if in_main and i > 100 and l.strip() == '':
        pass  # keep going
    if in_main and l.startswith('def ') and 'main' not in l:
        break
