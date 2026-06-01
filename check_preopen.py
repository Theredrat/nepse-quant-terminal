src = open("nepse_scanner.py", encoding="utf-8").read()
print("def cmd_preopen:", "def cmd_preopen" in src)
print("add_argument preopen:", "preopen" in src)
print("args.preopen:", "args.preopen" in src)

# Find parse_args return line
lines = src.splitlines()
for i, l in enumerate(lines):
    if "return parser.parse_args" in l:
        print(f"\nparse_args return at line {i}:")
        for j in range(max(0,i-5), i+2):
            print(f"  {j}: {lines[j]}")
