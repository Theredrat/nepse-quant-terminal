import re

content = open('nepse_scanner.py', encoding='utf-8').read()
lines = content.split('\n')

# Step 1: Remove duplicate function definitions (keep first occurrence)
seen_defs = set()
funcs_to_dedup = ['analyze_sector_trend', 'analyze_sector_heatmap', 'analyze_relative_strength']
out = []
i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    is_dup_def = False
    for fn in funcs_to_dedup:
        if stripped.startswith('def ' + fn + '('):
            if fn in seen_defs:
                # skip this duplicate def and its entire body
                i += 1
                while i < len(lines):
                    l = lines[i]
                    if l and not l[0].isspace() and l.strip() != '':
                        break
                    i += 1
                is_dup_def = True
                print(f'Removed duplicate def: {fn}')
                break
            else:
                seen_defs.add(fn)
    if not is_dup_def:
        out.append(line)
        i += 1

content = '\n'.join(out)
lines = content.split('\n')

# Step 2: Remove duplicate calls in main() - keep only first occurrence of each call
call_counts = {}
out2 = []
for line in lines:
    stripped = line.strip()
    is_dup_call = False
    for fn in funcs_to_dedup:
        call = fn + '()'
        if stripped == call or stripped.startswith(call):
            call_counts[fn] = call_counts.get(fn, 0) + 1
            if call_counts[fn] > 1:
                is_dup_call = True
                print(f'Removed duplicate call: {fn}()')
                break
    if not is_dup_call:
        out2.append(line)

content = '\n'.join(out2)
open('nepse_scanner.py', 'w', encoding='utf-8').write(content)
print('Done!')
