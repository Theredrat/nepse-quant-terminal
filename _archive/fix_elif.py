lines = open('nepse_scanner.py', encoding='utf-8').readlines()

# Remove the orphaned duplicate 'elif args.rs:' at line 2307 (index 2306)
# Line 2306 (index 2306) is the empty duplicate elif args.rs:
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Remove empty elif args.rs: that has no body (next line is another elif)
    if line.strip() == 'elif args.rs:' or line.strip() == 'elif args.week52:':
        # Check if next non-empty line is also an elif/else (meaning this one is empty)
        next_i = i + 1
        while next_i < len(lines) and lines[next_i].strip() == '':
            next_i += 1
        if next_i < len(lines) and lines[next_i].strip().startswith('elif '):
            print(f'Removing empty elif at line {i+1}: {line.rstrip()}')
            i += 1
            continue
    new_lines.append(line)
    i += 1

open('nepse_scanner.py', 'w', encoding='utf-8').write(''.join(new_lines))
print('Done!')
