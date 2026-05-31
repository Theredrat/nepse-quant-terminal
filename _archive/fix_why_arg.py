content = open('nepse_scanner.py', encoding='utf-8').read()

old = "    p.add_argument('--rs',           action='store_true', help='Relative strength vs sector')"
new = "    p.add_argument('--rs',           action='store_true', help='Relative strength vs sector')\n    p.add_argument('--why',          action='store_true', help='Show Why block — broker+RS+52W+unlock reasoning')"

if old in content:
    content = content.replace(old, new)
    open('nepse_scanner.py', 'w', encoding='utf-8').write(content)
    print('Fixed: --why argument added')
else:
    print('ERROR: line not found')
