lines = open('nepse_scanner.py', encoding='utf-8').readlines()

# Fix empty if/elif blocks by adding proper calls
fixes = {
    '    if args.sector_trend:\n': '    if args.sector_trend:\n        analyze_sector_trend()\n        console.print()\n',
    '    if args.heatmap:\n': '    if args.heatmap:\n        analyze_sector_heatmap()\n        console.print()\n',
    '    elif args.rs:\n': '    elif args.rs:\n        analyze_relative_strength()\n        console.print()\n',
}

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Check if this is an empty block (next non-empty line is if/elif/else at same indent)
    if line in fixes:
        next_i = i + 1
        if next_i < len(lines) and (lines[next_i].strip().startswith('if ') or lines[next_i].strip().startswith('elif ')):
            print(f'Fixing empty block at line {i+1}: {line.rstrip()}')
            new_lines.append(fixes[line])
            i += 1
            continue
    new_lines.append(line)
    i += 1

open('nepse_scanner.py', 'w', encoding='utf-8').write(''.join(new_lines))
print('Done!')
