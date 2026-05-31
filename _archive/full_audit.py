lines = open('nepse_scanner.py', encoding='utf-8').readlines()

print('=== FUNCTIONS THAT USE _load_sector_prices ===')
for i, l in enumerate(lines, 1):
    if '_load_sector_prices' in l:
        print(f'  line {i}: {l.rstrip()}')

print()
print('=== FUNCTIONS THAT USE _sector_returns ===')
for i, l in enumerate(lines, 1):
    if '_sector_returns' in l:
        print(f'  line {i}: {l.rstrip()}')

print()
print('=== FUNCTIONS THAT USE _calc_relative_strength ===')
for i, l in enumerate(lines, 1):
    if '_calc_relative_strength' in l:
        print(f'  line {i}: {l.rstrip()}')

print()
print('=== _load_sector_prices FULL BODY ===')
in_func = False
for i, l in enumerate(lines, 1):
    if 'def _load_sector_prices(' in l:
        in_func = True
    if in_func:
        print(f'  {i}: {repr(l)}')
    if in_func and i > 357 and l.strip() == '' and i > 370:
        pass
    if in_func and l.startswith('def ') and '_load_sector_prices' not in l:
        break
