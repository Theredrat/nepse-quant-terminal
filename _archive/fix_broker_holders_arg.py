import shutil, ast

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_holders_arg.py')
print('Backup created')

content = open('nepse_scanner.py', encoding='utf-8').read()

# Wire into parser — insert before return p.parse_args()
old1 = "    return p.parse_args()"
new1 = "    p.add_argument('--broker-holders', metavar='SYMBOL', default=None, help='Top 15 broker holders for a stock')\n    return p.parse_args()"

if old1 in content:
    content = content.replace(old1, new1)
    print('Added --broker-holders to parser')
else:
    print('ERROR: parser return not found')
    exit()

# Wire into main — find args.rs or args.week52 as anchor
old2 = "    if args.rs:"
if old2 in content:
    new2 = """    if getattr(args, 'broker_holders', None):
        analyze_broker_holders(args.broker_holders)
        return
    if args.rs:"""
    content = content.replace(old2, new2, 1)
    print('Wired --broker-holders into main')
else:
    print('WARNING: args.rs not found — trying args.why')
    old2b = "    if args.why:"
    if old2b in content:
        new2b = """    if getattr(args, 'broker_holders', None):
        analyze_broker_holders(args.broker_holders)
        return
    if args.why:"""
        content = content.replace(old2b, new2b, 1)
        print('Wired --broker-holders into main (via why)')

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

try:
    ast.parse(content)
    print('Syntax OK')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_holders_arg.py', 'nepse_scanner.py')
    print('Backup restored')
