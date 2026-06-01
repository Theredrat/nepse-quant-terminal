src = open("nepse_scanner.py", encoding="utf-8").read()

old = '        for table in ["daily_prices", "prices", "market_data"]:'
new = '        for table in ["stock_prices", "daily_prices", "prices", "market_data"]:'

if old in src:
    src = src.replace(old, new)
    print("Fixed: stock_prices added as first table")
else:
    print("ERROR: line not found")

open("nepse_scanner.py", "w", encoding="utf-8").write(src)
