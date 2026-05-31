import shutil, ast

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_duparg.py')
print('Backup created')

content = open('nepse_scanner.py', encoding='utf-8').read()

# Remove duplicate -- keep only one
dup_line = "    p.add_argument('--broker-holders', metavar='SYMBOL', default=None, help='Top 15 broker holders for a stock')\n"
count = content.count(dup_line)
print(f'Found {count} occurrences of --broker-holders')

if count > 1:
    # Remove all then add back once
    content = content.replace(dup_line, '', count)
    # Add back once before return p.parse_args()
    content = content.replace(
        "    return p.parse_args()",
        "    p.add_argument('--broker-holders', metavar='SYMBOL', default=None, help='Top 15 broker holders for a stock')\n    return p.parse_args()",
        1
    )
    print('Fixed — kept only one occurrence')
elif count == 0:
    print('Not found — adding once')
    content = content.replace(
        "    return p.parse_args()",
        "    p.add_argument('--broker-holders', metavar='SYMBOL', default=None, help='Top 15 broker holders for a stock')\n    return p.parse_args()",
        1
    )

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

try:
    ast.parse(content)
    print('Syntax OK')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_duparg.py', 'nepse_scanner.py')
    print('Backup restored')
