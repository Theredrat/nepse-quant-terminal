with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

sections = [
    ('analyze_best_rr', 6441, 6570),
    ('analyze_deployment_planner', 10689, 10820),
]

for name, start, end in sections:
    print('='*60)
    print(f'  {name} (lines {start}-{end})')
    print('='*60)
    for line in lines[start-1:end]:
        print(line, end='')
    print()
