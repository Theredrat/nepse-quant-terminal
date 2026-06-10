with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the rename block with contractRate
for i, line in enumerate(lines):
    if 'contractRate' in line:
        print(f'Line {i+1}: {line.rstrip()}')

print()

# Find where analyze_support_resistance is called
for i, line in enumerate(lines):
    if 'analyze_support_resistance' in line:
        print(f'Line {i+1}: {line.rstrip()}')
