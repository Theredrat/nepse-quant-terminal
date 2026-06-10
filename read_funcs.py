with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

sections = [
    ('analyze_quick_pick', 1797, 1900),
    ('analyze_smart_pick', 2097, 2200),
    ('analyze_broker_rs', 8454, 8550),
    ('analyze_momentum_hunter', 10565, 10670),
]

for name, start, end in sections:
    print(f'{"="*60}')
    print(f'  {name} (lines {start}-{end})')
    print(f'{"="*60}')
    for line in lines[start-1:end]:
        print(line, end='')
    print()
