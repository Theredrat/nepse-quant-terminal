src = open("nepse_scanner.py", encoding="utf-8").read()

old = "    return p.parse_args()"
new = "    p.add_argument('--preopen', nargs='*', metavar='SYMBOL', help='Pre-open band calculator')\n    return p.parse_args()"

if old in src:
    src = src.replace(old, new, 1)
    print("Fixed: --preopen added to parser")
else:
    print("ERROR: could not find return p.parse_args()")

open("nepse_scanner.py", "w", encoding="utf-8").write(src)
