src = open("nepse_scanner.py", encoding="utf-8").read()

# Step 1 - Add preopen function before main()
preopen_func = '''
def cmd_preopen(symbols=None):
    import sqlite3
    from datetime import datetime
    db = "nepse_market_data.db"

    if not symbols:
        raw = input("  Enter symbol(s) separated by space (e.g. AKJCL GUFL HPPL): ").strip().upper()
        symbols = [s.strip().replace(",","") for s in raw.split() if s.strip()]

    if not symbols:
        print("  No symbols entered.")
        return

    conn = sqlite3.connect(db)
    c = conn.cursor()

    results = []
    not_found = []

    for symbol in symbols:
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
            date  = row[1]
            mn    = round(close * 0.95, 2)
            mx    = round(close * 1.05, 2)
            results.append((symbol, close, mn, mx, date))
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

# Insert function just before def main()
if "def cmd_preopen" not in src:
    src = src.replace("def main():", preopen_func + "def main():")
    print("Step 1: preopen function added")
else:
    print("Step 1: function already exists - skipping")

# Step 2 - Add --preopen to parse_args()
if "preopen" not in src:
    # Find parse_args and add argument
    old_parse = "def parse_args():"
    if old_parse in src:
        # Find the return parser.parse_args() line and add before it
        src = src.replace(
            "    return parser.parse_args()",
            "    parser.add_argument('--preopen', nargs='*', metavar='SYMBOL', help='Pre-open band calculator')\n    return parser.parse_args()"
        )
        print("Step 2: argument added to parse_args()")
    else:
        print("Step 2: ERROR - parse_args() not found")
else:
    print("Step 2: argument already exists - skipping")

# Step 3 - Handle --preopen in main() before live market fetch
if "cmd_preopen" not in src or "args.preopen" not in src:
    old_handler = "    if args.legend:"
    new_handler = """    if getattr(args, 'preopen', None) is not None:
        cmd_preopen(args.preopen if args.preopen else None)
        return
    if args.legend:"""
    src = src.replace(old_handler, new_handler)
    print("Step 3: handler added in main()")
else:
    print("Step 3: handler already exists - skipping")

open("nepse_scanner.py", "w", encoding="utf-8").write(src)
print("Done - now running test...")
