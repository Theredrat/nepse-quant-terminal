with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

keywords = ['quickpick', 'quick_pick', 'smartpick', 'smart_pick', 'momentum_hunter', 
            'momentum hunter', 'deploy_ready', 'deploy ready', 'broker_rs', 'broker_accumulation']

for i, line in enumerate(lines):
    ll = line.lower()
    for kw in keywords:
        if kw in ll and 'def ' in ll:
            print(f'Line {i+1}: {line.rstrip()}')
            break
