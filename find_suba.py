lines = open('nepse_scanner.py', encoding='utf-8', errors='replace').readlines()
idx = None
for i, l in enumerate(lines):
    if 'print_market_regime_analyzer' in l and 'def ' in l:
        idx = i
        break
if idx:
    for i in range(idx, min(idx+200, len(lines))):
        if any(x in lines[i] for x in ["sub ==", "sub ==" , "== 'a'", "== \"a\""]):
            print(i+1, repr(lines[i]))
