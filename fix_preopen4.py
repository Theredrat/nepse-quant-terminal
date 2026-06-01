src = open("nepse_scanner.py", encoding="utf-8").read()

old = '''def cmd_preopen(symbols=None):
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
                pass'''

new = '''def cmd_preopen(symbols=None):
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
        for table in ["stock_prices", "daily_prices", "prices", "market_data"]:
            try:
                c.execute(f"SELECT close, date FROM {table} WHERE symbol=? ORDER BY date DESC LIMIT 1", (symbol,))
                row = c.fetchone()
                if row:
                    break
            except:
                pass'''

if old in src:
    src = src.replace(old, new)
    print("Fixed: table order updated")
else:
    print("ERROR: could not find old block")

open("nepse_scanner.py", "w", encoding="utf-8").write(src)
