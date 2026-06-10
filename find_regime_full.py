lines = open('nepse_scanner.py', encoding='utf-8', errors='replace').readlines()
# Find print_market_regime_analyzer
for i, l in enumerate(lines):
    if 'print_market_regime_analyzer' in l and 'def ' in l:
        print(f"FUNC DEF at line {i+1}")
        for j in range(i, min(i+400, len(lines))):
            print(j+1, lines[j].rstrip())
        break
