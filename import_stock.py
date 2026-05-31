import sys
from import_holdings import parse_and_import, show_summary

if len(sys.argv) < 2:
    print("Usage: python import_stock.py SYMBOL")
    print("Example: python import_stock.py AKJCL")
    print("Make sure sharehub_data/SYMBOL_raw.txt exists first")
    sys.exit(1)

symbol = sys.argv[1].upper()
raw_file = f"sharehub_data/{symbol}_raw.txt"

try:
    raw = open(raw_file, encoding="utf-8").read()
    print(f"Reading {raw_file}...")
    count = parse_and_import(symbol, raw)
    if count > 0:
        show_summary()
except FileNotFoundError:
    print(f"File not found: {raw_file}")
    print(f"Steps:")
    print(f"  1. Go to ShareHub -> AKJCL -> Floorsheet Zero Sum -> 1Y")
    print(f"  2. Select all table data -> Ctrl+C")
    print(f"  3. Open Notepad -> Ctrl+V -> Save as sharehub_data/{symbol}_raw.txt")
    print(f"  4. Run: python import_stock.py {symbol}")
