lines = open('nepse_scanner.py', encoding='utf-8').readlines()

# Remove lines 2299-2304 (0-indexed: 2298-2303) - the duplicate block without console.print()
remove_indices = set(range(2298, 2304))
new_lines = [l for i, l in enumerate(lines) if i not in remove_indices]

open('nepse_scanner.py', 'w', encoding='utf-8').write(''.join(new_lines))
print('Done - removed duplicate call block')

content = open('nepse_scanner.py', encoding='utf-8').read()
for func in ['analyze_sector_trend()', 'analyze_sector_heatmap()', 'analyze_relative_strength()']:
    print(f'{func} call count: {content.count(func)}')
