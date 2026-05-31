import ast, types, re, sys
from pathlib import Path

print("=" * 60)
print("NEPSE SCANNER — FULL HEALTH CHECK")
print("=" * 60)

# Read scanner
try:
    src = open('nepse_scanner.py', encoding='utf-8').read()
    print("\n✅ nepse_scanner.py — readable")
except Exception as e:
    print(f"\n❌ Cannot read nepse_scanner.py: {e}")
    sys.exit(1)

# Syntax check
try:
    ast.parse(src)
    print("✅ Syntax — OK")
except SyntaxError as e:
    print(f"❌ Syntax ERROR: {e}")
    sys.exit(1)

# Load all functions
try:
    mod = types.ModuleType('t')
    exec(compile(src[:src.rfind('\nif __name__')], 'nepse_scanner.py', 'exec'), mod.__dict__)
    fns = sorted([x for x in dir(mod) if callable(getattr(mod, x)) and not x.startswith('__')])
    print(f"✅ Functions loaded — {len(fns)} total")
except Exception as e:
    print(f"❌ Load ERROR: {e}")
    sys.exit(1)

# Check every expected feature
print("\n" + "=" * 60)
print("FEATURE CHECKLIST")
print("=" * 60)

features = [
    # Core scans
    ("Full scan / signals",        "run_signals"),
    ("Market movers",              "print_market_movers"),
    ("Watchlist",                  "analyze_watchlist"),
    ("Quick pick",                 "analyze_quick_pick"),
    ("Smart pick",                 "analyze_smart_pick"),
    # Smart money
    ("Power sell",                 "analyze_power_sell"),
    ("Sector rotation",            "analyze_sector_rotation"),
    ("Sector trend",               "analyze_sector_trend"),
    ("Sector heatmap",             "analyze_sector_heatmap"),
    ("Relative strength",          "analyze_relative_strength"),
    ("52-week analysis",           "analyze_week52"),
    ("Broker RS",                  "analyze_broker_rs"),
    # Whale / broker
    ("Whale tracker",              "analyze_whales"),
    ("Broker market",              "analyze_broker_market"),
    ("Broker tracker",             "analyze_broker_tracker"),
    # Why engine
    ("Why engine",                 "analyze_why"),
    ("Broker story",               "get_broker_story"),
    ("Broker logger",              "log_broker_activity"),
    ("Ensure broker table",        "_ensure_broker_activity_table"),
    # Broker history verdicts
    ("5d verdict",                 "five_day_verdict"),
    ("10d verdict",                "ten_day_verdict"),
    ("20d verdict",                "twenty_day_verdict"),
    ("REVERSAL detection",         "REVERSAL"),
    # Top holders
    ("Top broker holders func",    "get_top_broker_holders"),
    ("Broker holders analysis",    "analyze_broker_holders"),
    ("Broker date analysis",       "analyze_broker_date"),
    # Stock analysis
    ("Floorsheet symbol",          "analyze_floorsheet_symbol"),
    ("Support/resistance",         "analyze_support_resistance"),
    # Portfolio
    ("Portfolio",                  "analyze_portfolio"),
    ("Correlation",                "analyze_corr"),
    ("Position sizer",             "analyze_size"),
    # Fundamental
    ("Fundamental",                "analyze_fundamental"),
    ("Value screen",               "analyze_value"),
    ("Earnings",                   "analyze_earnings"),
    ("Float",                      "analyze_float"),
    ("Unlock",                     "analyze_unlock"),
    # Signals
    ("Signal momentum",            "signal_momentum"),
    ("Signal volume breakout",     "signal_volume_breakout"),
    ("Signal 52w high",            "signal_52week_high"),
    ("Signal 52w low bounce",      "signal_52week_low_bounce"),
    ("Signal mean reversion",      "signal_mean_reversion"),
    ("Signal range compression",   "signal_range_compression"),
    # Args
    ("--broker-holders arg",       "--broker-holders"),
    ("--broker-date arg",          "--broker-date"),
    ("--why arg",                  "--why"),
    ("--rs arg",                   "--rs"),
]

ok = 0
miss = 0
for name, key in features:
    found = key in src or key in fns
    status = "✅" if found else "❌ MISSING"
    print(f"  {status:<12} {name}")
    if found:
        ok += 1
    else:
        miss += 1

print(f"\n  {ok} OK  |  {miss} MISSING")

# Menu check
print("\n" + "=" * 60)
print("MENU (launch_nepse.bat)")
print("=" * 60)
try:
    bat = open('launch_nepse.bat', encoding='utf-8').read()
    menu_items = [
        ("Option 17b / broker-holders", "17b"),
        ("Option 17c / broker-date",    "17c"),
        ("Option 34",                   "34"),
        ("CUSTOM_HOLDERS label",        "CUSTOM_HOLDERS"),
        ("CUSTOM_BROKERDATE label",     "CUSTOM_BROKERDATE"),
    ]
    for name, key in menu_items:
        found = key in bat
        print(f"  {'✅' if found else '❌ MISSING':<12} {name}")
except Exception as e:
    print(f"  ❌ Cannot read bat file: {e}")

# File listing
print("\n" + "=" * 60)
print("ROOT FILES")
print("=" * 60)
for f in sorted(Path('.').iterdir()):
    if f.is_file():
        sz = f.stat().st_size
        print(f"  {f.name:<45} {sz:>10,} bytes")

print("\n" + "=" * 60)
print("ARCHIVE SUMMARY")
print("=" * 60)
for folder in ['_backups', '_data', '_archive']:
    p = Path(folder)
    if p.exists():
        n = len(list(p.iterdir()))
        print(f"  {folder}/  ({n} files)")

print("\n" + "=" * 60)
if miss == 0:
    print("ALL SYSTEMS GO ✅")
else:
    print(f"ACTION NEEDED — {miss} missing item(s) above")
print("=" * 60)
