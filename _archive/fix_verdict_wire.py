import shutil, ast

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_wire.py')
print('Backup created')

content = open('nepse_scanner.py', encoding='utf-8').read()

old = "hist_note += \" \u2190 FIRST BUY after distribution (reversal alert)\"\n\n            broad = ''"

new = """hist_note += " \u2190 FIRST BUY after distribution (reversal alert)"
            if bstory.get('five_day_verdict'):
                hist_note += "\\n      \U0001f4ca 5D:  " + bstory['five_day_verdict']
            if bstory.get('ten_day_verdict'):
                hist_note += "\\n      \u2b50 10D: " + bstory['ten_day_verdict']
            if bstory.get('twenty_day_verdict'):
                hist_note += "\\n      \U0001f3c6 20D: " + bstory['twenty_day_verdict']

            broad = ''"""

if old in content:
    content = content.replace(old, new)
    print('Wired 5d/10d/20d verdicts into _print_why')
else:
    print('ERROR: wire point still not found')
    exit()

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

try:
    ast.parse(content)
    print('Syntax OK — all verdicts now display correctly')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_wire.py', 'nepse_scanner.py')
    print('Backup restored')
