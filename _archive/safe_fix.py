import re

lines = open('nepse_scanner.py', encoding='utf-8').readlines()

# --- Step 1: Remove duplicate function blocks ---
# Keep FIRST occurrence of each, remove second
targets = [
    '_load_sector_prices',
    '_sector_returns', 
    '_momentum_label',
    '_calc_relative_strength',
]

seen = set()
out = []
i = 0
while i < len(lines):
    line = lines[i]
    matched = None
    for fn in targets:
        if line.strip().startswith(f'def {fn}('):
            matched = fn
            break
    
    if matched:
        if matched in seen:
            # Skip this duplicate def and its entire body
            i += 1
            while i < len(lines):
                l = lines[i]
                # Body ends when we hit a new top-level def/class or EOF
                if l and not l[0].isspace() and l.strip() and not l.strip().startswith('#'):
                    break
                i += 1
            print(f'  Removed duplicate: {matched}')
            continue
        else:
            seen.add(matched)
    
    out.append(line)
    i += 1

# --- Step 2: Fix elif args.rs -> if args.rs (so --rs works independently of --heatmap) ---
fixed = []
for line in out:
    if line.rstrip() == '    elif args.rs:':
        fixed.append('    if args.rs:\n')
        print('  Fixed: elif args.rs -> if args.rs')
    else:
        fixed.append(line)

open('nepse_scanner.py', 'w', encoding='utf-8').write(''.join(fixed))
print('Done.')
