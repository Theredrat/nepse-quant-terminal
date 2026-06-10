with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

sections = [
    ('best_rr', 36),
    ('deployment_planner', 41),
]

keywords = ['analyze_best_rr', 'best_rr', 'deployment_planner', 'analyze_deployment']
for i, line in enumerate(lines):
    ll = line.lower()
    for kw in keywords:
        if kw in ll and 'def ' in ll:
            print(f'Line {i+1}: {line.rstrip()}')
