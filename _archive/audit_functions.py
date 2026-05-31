lines = open('nepse_scanner.py', encoding='utf-8').readlines()

# Find ALL function definitions
print('=== ALL FUNCTIONS ===')
for i, l in enumerate(lines, 1):
    if l.startswith('def ') or (l.startswith('    def ') and 'class' not in l):
        print(f'{i}: {l.rstrip()}')
