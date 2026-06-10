lines = open('patch_dynamic_regime.py', encoding='utf-8').readlines()
for i, l in enumerate(lines[:30]):
    print(i+1, repr(l))
