src = open("nepse_alerts.py", encoding="utf-8").read()

alerts = [
    ("Morning Briefing",  "morning" in src.lower()),
    ("Breakout Alert",    "breakout" in src.lower()),
    ("Volume Spike",      "volspike" in src.lower()),
    ("RS Reversal",       "reversal" in src.lower()),
    ("Power Sell",        "powersell" in src.lower()),
    ("Whale Alert",       "whale" in src.lower()),
    ("Watchlist Alert",   "watchlist" in src.lower()),
    ("EOD Summary",       "summary" in src.lower()),
]

print("=== TELEGRAM ALERTS CHECK ===")
all_ok = True
for name, found in alerts:
    status = "OK" if found else "MISSING"
    if not found: all_ok = False
    print(f"  {status}  {name}")

print()
print("ALL ALERTS PRESENT" if all_ok else "WARNING - SOME ALERTS MISSING")
