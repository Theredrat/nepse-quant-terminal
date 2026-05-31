import sys, types
src = open('nepse_scanner.py', encoding='utf-8').read()
mod = types.ModuleType('t')
exec(compile(src[:src.find('\nif __name__')], 'nepse_scanner.py', 'exec'), mod.__dict__)
data = mod._calc_relative_strength()
print(f'type={type(data)}, len={len(data) if data else 0}')
if data:
    print(f'First: {data[0]}')
