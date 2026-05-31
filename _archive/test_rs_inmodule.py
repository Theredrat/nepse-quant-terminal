import sys, types

src = open('nepse_scanner.py', encoding='utf-8').read()
cutoff = src.find('\nif __name__')
partial = src[:cutoff]

mod = types.ModuleType('nepse_scanner_test')
mod.__file__ = 'nepse_scanner.py'
try:
    exec(compile(partial, 'nepse_scanner.py', 'exec'), mod.__dict__)
    print('Module loaded OK')
    data = mod._calc_relative_strength()
    print(f'type={type(data)}, len={len(data) if data else 0}')
    if data:
        print(f'First record: {data[0]}')
    else:
        print('RETURNED EMPTY - bug confirmed here')
except Exception as e:
    import traceback
    traceback.print_exc()
