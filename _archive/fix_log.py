with open('signal_tracker.py', encoding='utf-8') as f:
    src = f.read()

old = '        if not sym or not ltp:\n            continue'
new = '        if not sym:\n            continue'

if old in src:
    src = src.replace(old, new)
    open('signal_tracker.py', 'w', encoding='utf-8').write(src)
    print('Fixed!')
else:
    print('Not found')
