src = open("nepse_scanner.py", encoding="utf-8").read()

# Find the exact return line in parse_args
if "add_argument('--preopen'" not in src and 'add_argument("--preopen"' not in src:
    # Add before return parser.parse_args()
    old = "    return parser.parse_args()"
    new = "    parser.add_argument('--preopen', nargs='*', metavar='SYMBOL', help='Pre-open band calculator')\n    return parser.parse_args()"
    if old in src:
        src = src.replace(old, new, 1)  # replace only first occurrence
        print("Fixed: --preopen added to parser")
    else:
        print("ERROR: could not find return parser.parse_args()")
else:
    print("Already present")

open("nepse_scanner.py", "w", encoding="utf-8").write(src)

# Verify
src2 = open("nepse_scanner.py", encoding="utf-8").read()
lines = src2.splitlines()
for i, l in enumerate(lines):
    if "preopen" in l.lower():
        print(f"{i}: {l}")
