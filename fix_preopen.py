src = open("nepse_scanner.py", encoding="utf-8").read()

# Check current state
print("cmd_preopen in file:", "def cmd_preopen" in src)
print("--preopen in parse_args:", "preopen" in src)
print("args.preopen in main:", "args.preopen" in src)

# Fix 1: Add to parse_args if missing
if "add_argument('--preopen'" not in src and 'add_argument("--preopen"' not in src:
    src = src.replace(
        "    return parser.parse_args()",
        "    parser.add_argument('--preopen', nargs='*', metavar='SYMBOL', help='Pre-open band calculator')\n    return parser.parse_args()"
    )
    print("Fixed: --preopen added to parse_args()")

# Fix 2: Add cmd_preopen function if missing
if "def cmd_preopen" not in src:
    preopen_func = '''
def cmd_preopen(symbols=None):
    import sqlite3
    from datetime import datetime
    db = "nepse_market_data.db"
    if not symbols:
        raw = input("  Enter symbol(s) separated by space: ").strip().upper()
        symbols = [s.strip().replace(",","") for s in raw.split() if s.strip()]
    if not symbols:
        print("  No symbols entered.")
        return
    conn = sqlite3.connect(db)
    c = conn.cursor()
    results = []
    not_found = []
    for symbol in symbols:
        symbol = symbol.upper()
        row = None
        for table in ["daily_prices", "prices", "market_data"]:
            try:
                c.execute(f"SELECT close, date FROM {table} WHERE symbol=? ORDER BY date DESC LIMIT 1", (symbol,))
                row = c.fetchone()
                if row:
                    break
            except:
                pass
        if row:
            close = float(row[0])
            mn = round(close * 0.95, 2)
            mx = round(close * 1.05, 2)
            results.append((symbol, close, mn, mx, row[1]))
        else:
            not_found.append(symbol)
    conn.close()
    print()
    print("  " + "=" * 58)
    print(f"  PRE-OPEN BAND  --  {datetime.now().strftime('%Y-%m-%d')}")
    print("  Valid order range  (10:30 - 10:45 AM)")
    print("  " + "=" * 58)
    print(f"  {'Symbol':<10} {'Last Close':>12} {'Min (-5%)':>12} {'Max (+5%)':>12}")
    print("  " + "-" * 58)
    for sym, close, mn, mx, date in results:
        print(f"  {sym:<10} {close:>12,.2f} {mn:>12,.2f} {mx:>12,.2f}")
    print("  " + "=" * 58)
    if not_found:
        print(f"  Not found in DB: {', '.join(not_found)}")
    print()

'''
    src = src.replace("def main():", preopen_func + "def main():")
    print("Fixed: cmd_preopen function added")

# Fix 3: Add handler in main() if missing
if "args.preopen" not in src:
    src = src.replace(
        "    if args.legend:",
        "    if getattr(args, 'preopen', None) is not None:\n        cmd_preopen([s.upper() for s in args.preopen] if args.preopen else None)\n        return\n    if args.legend:"
    )
    print("Fixed: handler added in main()")

open("nepse_scanner.py", "w", encoding="utf-8").write(src)
print("All done")
