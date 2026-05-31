lines = open('nepse_scanner.py', encoding='utf-8').readlines()

# Remove the first incomplete block (lines 2299-2304, indices 2298-2303)
# Keep the second complete block (lines 2332-2340) which has console.print()
# We need to remove lines 2299-2304 (the ones WITHOUT console.print())

new_lines = []
i = 0
while i < len(len_lines := lines):
    pass

# Simpler: just remove specific line ranges
# Lines to remove: 2299,2300,2301,2302,2303,2304 (0-indexed: 2298-2303)
remove_indices = set(range(2298, 2304))
new_lines = [l for i, l in enumerate(lines) if i not in remove_indices]

open('nepse_scanner.py', 'w', encoding='utf-8').write(''.join(new_lines))
print('Done - removed duplicate call block')

# Verify
content = open('nepse_scanner.py', encoding='utf-8').read()
for func in ['analyze_sector_trend()', 'analyze_sector_heatmap()', 'analyze_relative_strength()']:
    print(f'{func} call count: {content.count(func)}')
