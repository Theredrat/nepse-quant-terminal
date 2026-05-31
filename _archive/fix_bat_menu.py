import shutil

shutil.copy('launch_nepse.bat', 'launch_nepse_pre_holders.bat')
print('Backup created')

content = open('launch_nepse.bat', encoding='utf-8').read()

# Add option 34 to menu display
old1 = 'echo   17. Floorsheet - Any Stock'
new1 = 'echo   17. Floorsheet - Any Stock\necho   34. Top Broker Holders - Any Stock'
if old1 in content:
    content = content.replace(old1, new1)
    print('Added option 34 to menu display')
else:
    print('ERROR: menu display not found')

# Find where choice 17 is handled and add 34 before it
old2 = 'if "%choice%"=="17"'
new2 = '''if "%choice%"=="34" (
    set /p sym="  Enter stock symbol: "
    python nepse_scanner.py --broker-holders %sym%
    pause
    goto menu
)
if "%choice%"=="17"'''

if old2 in content:
    content = content.replace(old2, new2)
    print('Wired option 34 into menu handler')
else:
    print('ERROR: choice 17 handler not found')
    # Try alternate
    old2b = "if '%choice%'=='17'"
    if old2b in content:
        content = content.replace(old2b, f"if '%choice%'=='34' python nepse_scanner.py --broker-holders & pause & goto menu\nif '%choice%'=='17'")
        print('Wired option 34 (alternate pattern)')

open('launch_nepse.bat', 'w', encoding='utf-8').write(content)
print('launch_nepse.bat updated')

# Now add --broker-holders arg to scanner
import ast, re
shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_bat_wire.py')
src = open('nepse_scanner.py', encoding='utf-8').read()

# Find parse_args and add --broker-holders argument
old_arg = "parser.add_argument('--why'"
if old_arg in src:
    new_arg = """parser.add_argument('--broker-holders', metavar='SYMBOL', help='Show top 15 broker holders for a stock')
    parser.add_argument('--why'"""
    src = src.replace(old_arg, new_arg)
    print('Added --broker-holders argument to parser')

# Wire it in main
old_main = 'if args.why:'
if old_main in src:
    new_main = """if getattr(args, 'broker_holders', None):
        analyze_broker_holders(args.broker_holders)
    if args.why:"""
    src = src.replace(old_main, new_main, 1)
    print('Wired --broker-holders into main')

open('nepse_scanner.py', 'w', encoding='utf-8').write(src)

try:
    ast.parse(src)
    print('Syntax OK')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_bat_wire.py', 'nepse_scanner.py')
    print('Scanner backup restored')
