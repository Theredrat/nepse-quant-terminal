import sys, os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import os
#!/usr/bin/env python3
"""
NEPSE Personal Scanner — Full Edition
======================================
Signals + Floorsheet + Broker Analysis + Power Sell + Sector Rotation
+ Whale Tracker + Support/Resistance + Watchlist + Daily Report

Requirements:
    pip install pandas rich
    pip install "nepse @ git+https://github.com/basic-bgnr/NepseUnofficialApi.git@2f09fbfdcbaf23545d5755b6f11b367324d5b8a4"

Usage:
    python nepse_scanner.py                   # Full scan + signals
    python nepse_scanner.py --powersell       # Power sell alert
    python nepse_scanner.py --sector          # Sector rotation
    python nepse_scanner.py --whale           # Whale tracker
    python nepse_scanner.py --sr NABIL        # Support/resistance
    python nepse_scanner.py --watchlist       # Your watchlist
    python nepse_scanner.py --report          # Save daily report
    python nepse_scanner.py --floor NABIL     # Floorsheet
    python nepse_scanner.py --brokers         # Broker leaderboard
    python nepse_scanner.py --legend          # Help
"""

import argparse, sys, time, os
from datetime import datetime
from typing import Optional

try:
    import pandas as pd
    from nepse import Nepse
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    from rich import box
    from rich.rule import Rule
    from rich.text import Text
except ImportError as e:
    print(f"\nMissing dependency: {e}")
    print("  pip install pandas rich")
    sys.exit(1)

console = Console()

# ── YOUR WATCHLIST — edit these ───────────────────────────────────────────────
WATCHLIST = [
    "NABIL", "ADBL", "NICA", "SBI", "EBL",
    "NIFRA", "UPPER", "NHPC", "RIDI", "AKJCL",
    "NLIC", "LICN", "NTC", "CHCL", "HIDCL",
]

# ── SECTOR MAP (auto-generated from nepse_market_data.db) ───────────────────
SECTOR_MAP = {
    "Commercial Banks": [
        "ADBL", "CZBIL", "EBL", "GBIME", "HBL", "KBL", "LSL", "MBL",
        "NABIL", "NBL", "NICA", "NIMB", "NMB", "PCBL", "PRVU", "SANIMA",
        "SBI", "SBL", "SCB",
    ],
    "Development Banks": [
        "CORBL", "EDBL", "GBBL", "GRDBL", "JBBL", "KSBBL", "LBBL", "MDB",
        "MLBL", "MNBBL", "NABBC", "SABBL", "SADBL", "SAPDBL", "SHINE", "SINDU",
    ],
    "Finance": [
        "BFC", "CFCL", "GFCL", "GMFIL", "GUFL", "ICFC", "JFL", "MFIL",
        "MPFL", "NFS", "PFL", "PROFL", "RLFL", "SFCL", "SIFC",
    ],
    "Hydropower": [
        "AHL", "AHPC", "AKJCL", "AKPL", "API", "BARUN", "BEDC", "BGWT",
        "BHCL", "BHDC", "BHL", "BHPL", "BJHL", "BNHC", "BPCL", "BUNGAL",
        "CHCL", "CHL", "CKHL", "DHEL", "DHPL", "DOLTI", "DORDI", "EHPL",
        "GHL", "GLH", "GVL", "HDHPC", "HHL", "HIMSTAR", "HPPL", "HURJA",
        "IHL", "JOSHI", "KBSH", "KHPL", "KKHC", "KPCL", "LEC", "MABEL",
        "MAKAR", "MANDU", "MBJC", "MCHL", "MEHL", "MEL", "MEN", "MHCL",
        "MHL", "MHNL", "MKHC", "MKHL", "MKJC", "MMKJL", "MSHL", "NGPL",
        "NHDL", "NHPC", "NYADI", "PHCL", "PMHPL", "PPCL", "PPL", "RADHI",
        "RAWA", "RFPL", "RHGCL", "RHPL", "RIDI", "RLEL", "RURU", "SAHAS",
        "SANVI", "SGHC", "SHEL", "SHPC", "SIKLES", "SIPD", "SJCL", "SKHEL",
        "SKHL", "SMH", "SMHL", "SMJC", "SOHL", "SPC", "SPDL", "SPHL",
        "SPL", "SSHL", "TAMOR", "TPC", "TSHL", "TVCL", "UHEWA", "ULHC",
        "UMHL", "UMRH", "UNHPL", "UPCL", "UPPER", "USHEC", "USHL", "VLUCL",
    ],
    "Life Insurance": [
        "ALICL", "CLI", "CREST", "GMLI", "HLI", "ILI", "LICN", "NLIC",
        "NLICL", "PMLI", "RNLI", "SJLIC", "SNLI", "SRLI",
    ],
    "Non-Life Insurance": [
        "HEI", "IGI", "NICL", "NIL", "NLG", "NMIC", "PRIN", "RBCL",
        "SALICO", "SGIC", "SICL", "SPIL", "UAIL",
    ],
    "Microfinance": [
        "ACLBSL", "ALBSL", "ANLB", "AVYAN", "CBBL", "CYCL", "DDBL", "DLBS",
        "FMDBL", "FOWAD", "GBLBS", "GILB", "GLBSL", "GMFBS", "HLBSL", "ILBS",
        "JBLB", "JSLBB", "KMCDB", "LLBS", "MATRI", "MERO", "MLBBL", "MLBS",
        "MLBSL", "MSLB", "NADEP", "NESDO", "NICLBSL", "NMBMF", "NMFBS", "NMLBBL",
        "NUBL", "RSDC", "SHLB", "SKBBL", "SLBBL", "SLBSL", "SMATA", "SMB",
        "SMFBS", "SMPDA", "SWASTIK", "SWBBL", "SWMF", "ULBSL", "UNLB", "USLB",
        "VLBS", "WNLB",
    ],
    "Manufacturing": [
        "BNL", "BNT", "GCIL", "HDL", "NLO", "OMPL", "PCIL", "RSML",
        "SAGAR", "SAIL", "SARBTM", "SHIVM", "SONA", "SYPNL", "UNL",
    ],
    "Hotels": [
        "BANDIPUR", "CGH", "CITY", "HFIN", "KDL", "OHL", "SHL", "TRH",
    ],
    "Investment": [
        "CHDC", "CIT", "ENL", "HATHY", "HIDCL", "NIFRA", "NRN",
    ],
    "Trading": [
        "BBC", "STC",
    ],
    "Others": [
        "HRL", "JHAPA", "MKCL", "NRIC", "NRM", "NTC", "NWCL", "PURE",
        "TTL",
    ],
}

# Total listed equity stocks per sector
SECTOR_LISTED = {
    "Commercial Banks": 19,
    "Development Banks": 16,
    "Finance": 15,
    "Hydropower": 104,
    "Life Insurance": 14,
    "Non-Life Insurance": 13,
    "Microfinance": 50,
    "Manufacturing": 15,
    "Hotels": 8,
    "Investment": 7,
    "Trading": 2,
    "Others": 9,
}

# Non-equity symbols to exclude from sector rotation
NON_EQUITY_SYMBOLS = {
    "ADBLD83", "C30MF", "CBLD88", "CCBD88", "CMF2", "CSY",
    "EBLD85", "EBLD86", "EBLD91", "GBBD85", "GBILD86/87", "GBIMESY2",
    "GIBF1", "GSY", "H8020", "HBLD83", "HEIP", "HIDCLP",
    "HLICF", "ICFCD88", "ICFCD89", "KBLD90", "KDBY", "KEF",
    "KSBBLD87", "KSBBLP", "KSY", "LUK", "LVF2", "MBLD2085",
    "MBLEF", "MMF1", "MND84/85", "MNMF1", "NBF2", "NBF3",
    "NBLD82", "NBLD85", "NBLD87", "NIBD84", "NIBLGF", "NIBLSTF",
    "NIBSF2", "NICAD2091", "NICBF", "NICD88", "NICFC", "NICGF2",
    "NICSF", "NIFRAGED", "NIMBD90", "NIMBPO", "NMB50", "NMBD87/88",
    "NMBHF2", "NSIF2", "NSY", "PBD84", "PBD85", "PBD88",
    "PBLD84", "PRSF", "PSF", "RBBD2088", "RBBF40", "RBCLPO",
    "RMF1", "RMF2", "RSY", "SAGF", "SAND2085", "SBCF",
    "SBID83", "SBLD2091", "SEF", "SFEF", "SFMF", "SIGS2",
    "SIGS3", "SLCF",
}

def get_sector(symbol):
    """Return sector for a symbol, or None if non-equity."""
    import re as _re
    sym = symbol.upper()
    if sym in NON_EQUITY_SYMBOLS:
        return None
    # Debenture/bond pattern: ends in 2-digit year (e.g. LBLD88, SBD87, NCCD86)
    if _re.search(r'(LD|BD|CD|BLD|CBD|NBD|NILD|BILD)\d{2}$', sym):
        return None
    # Mutual fund pattern
    if _re.search(r'(MF|SF|GF)\d+$', sym):
        return None
    for sector, symbols in SECTOR_MAP.items():
        if sym in symbols:
            return sector
    return "Others"



# ── NEPSE CLIENT ──────────────────────────────────────────────────────────────

def init_nepse():
    n = Nepse()
    n.setTLSVerification(False)
    return n

def fetch_with_retry(fn, label="data", retries=3, delay=2):
    for i in range(retries):
        try:
            return fn()
        except Exception as e:
            if i < retries - 1:
                console.print(f"  [yellow]Retrying {label}... ({i+2}/{retries})[/yellow]")
                time.sleep(delay)
            else:
                console.print(f"  [red]Failed to fetch {label}: {e}[/red]")
                return None

# ── DATA FETCHERS ─────────────────────────────────────────────────────────────

def get_live_market(n):
    data = fetch_with_retry(n.getLiveMarket, "live market")
    if not data:
        return None
    df = pd.DataFrame(data)
    col_map = {
        'symbol': 'symbol', 'lastTradedPrice': 'ltp', 'percentageChange': 'change_pct',
        'openPrice': 'open', 'highPrice': 'high', 'lowPrice': 'low',
        'previousClose': 'prev_close', 'totalTradeQuantity': 'volume',
        'totalTradeValue': 'turnover', 'fiftyTwoWeekHigh': 'week52_high',
        'fiftyTwoWeekLow': 'week52_low',
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    sector_fix = {
        'Hotels And Tourism': 'Hotel & Tourism',
        'Hotels and Tourism': 'Hotel & Tourism',
    }
    if 'sector' in df.columns:
        df['sector'] = df['sector'].replace(sector_fix)
    for c in ['ltp','change_pct','open','high','low','prev_close','volume','turnover','week52_high','week52_low']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def get_summary(n):   return fetch_with_retry(n.getSummary, "summary")
def get_top_gainers(n): return fetch_with_retry(n.getTopGainers, "gainers")
def get_top_losers(n):  return fetch_with_retry(n.getTopLosers, "losers")
def get_top_turnover(n): return fetch_with_retry(n.getTopTenTurnoverScrips, "turnover")

def _normalize_fs(data):
    if not data:
        return None
    df = pd.DataFrame(data)
    col_map = {
        'stockSymbol': 'symbol', 'buyerMemberId': 'buyer_broker',
        'sellerMemberId': 'seller_broker', 'contractQuantity': 'quantity',
        'contractRate': 'rate', 'contractAmount': 'amount',
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    sector_fix = {
        'Hotels And Tourism': 'Hotel & Tourism',
        'Hotels and Tourism': 'Hotel & Tourism',
    }
    if 'sector' in df.columns:
        df['sector'] = df['sector'].replace(sector_fix)
    for c in ['quantity','rate','amount']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def get_full_floorsheet(n):
    console.print("  [yellow]Fetching full floorsheet — 30-60 seconds...[/yellow]")
    data = fetch_with_retry(lambda: n.getFloorSheet(show_progress=False), "floorsheet", retries=2, delay=3)
    return _normalize_fs(data)

def get_floorsheet_of_symbol(full_df, symbol):
    if full_df is None or full_df.empty or 'symbol' not in full_df.columns:
        return None
    f = full_df[full_df['symbol'].str.upper() == symbol.upper()].copy()
    return f if not f.empty else None

# ── FORMAT HELPERS ────────────────────────────────────────────────────────────

def color_change(val):
    try:
        v = float(val)
        if v > 0:   return f"[green]+{v:.2f}%[/green]"
        elif v < 0: return f"[red]{v:.2f}%[/red]"
        return f"[white]{v:.2f}%[/white]"
    except: return str(val)

def fmt_vol(val):
    try:
        v = float(val)
        if v >= 1_000_000: return f"{v/1_000_000:.1f}M"
        if v >= 1_000:     return f"{v/1_000:.0f}K"
        return str(int(v))
    except: return str(val)

def fmt_rs(val):
    try:
        v = float(val)
        if v >= 1_000_000_000: return f"Rs {v/1_000_000_000:.2f}B"
        if v >= 1_000_000:     return f"Rs {v/1_000_000:.1f}M"
        if v >= 1_000:         return f"Rs {v/1_000:.0f}K"
        return f"Rs {v:.0f}"
    except: return str(val)

# ── POWER SELL ────────────────────────────────────────────────────────────────

def auto_update_watchlist(rs_data, full_fs, db_path, top_n=15, silent=False):
    import sqlite3, json
    from pathlib import Path
    from collections import defaultdict

    try:
        conn = sqlite3.connect(db_path)
    except Exception as e:
        if not silent: print('Watchlist: DB error', e)
        return

    # RS scores
    if not rs_data:
        try: rs_data = _calc_relative_strength(db_path)
        except: rs_data = []
    rs_map = {r['symbol']: r for r in (rs_data or [])}

    # Fundamentals
    fund_map = {}
    try:
        for row in conn.execute('SELECT symbol, pe_ratio, pb_ratio, roe FROM fundamentals').fetchall():
            fund_map[row[0]] = {'pe': row[1] or 0, 'pb': row[2] or 0, 'roe': row[3] or 0}
    except: pass

    # EPS growth QoQ
    eps_growth_map = {}
    try:
        fy = conn.execute('SELECT MAX(fiscal_year) FROM quarterly_earnings').fetchone()[0]
        if fy:
            rows = conn.execute(
                'SELECT symbol, quarter, eps FROM quarterly_earnings WHERE fiscal_year=? ORDER BY symbol, quarter',
                (fy,)
            ).fetchall()
            eq = defaultdict(list)
            for sym, q, eps in rows:
                eq[sym].append(eps or 0)
            for sym, eps_list in eq.items():
                if len(eps_list) >= 2 and eps_list[-2] != 0:
                    eps_growth_map[sym] = (eps_list[-1] - eps_list[-2]) / abs(eps_list[-2]) * 100
    except: pass

    # Broker net activity
    broker_map = {}
    try:
        latest = conn.execute('SELECT MAX(date) FROM broker_activity').fetchone()[0]
        if latest:
            rows = conn.execute(
                'SELECT symbol, SUM(net_qty), SUM(net_val) FROM broker_activity WHERE date=? GROUP BY symbol',
                (latest,)
            ).fetchall()
            all_vals = sorted([abs(r[2] or 0) for r in rows], reverse=True)
            threshold = all_vals[int(len(all_vals) * 0.2)] if len(all_vals) > 5 else 0
            for sym, net_qty, net_val in rows:
                nq = net_qty or 0
                nv = net_val or 0
                broker_map[sym] = {'net_qty': nq, 'net_val': nv, 'top20': abs(nv) >= threshold and nv > 0}
    except: pass

    # Volume spike vs 20d avg
    vol_map = {}
    try:
        latest_price = conn.execute('SELECT MAX(date) FROM stock_prices').fetchone()[0]
        if latest_price:
            cur_vol = {r[0]: r[1] for r in conn.execute(
                'SELECT symbol, volume FROM stock_prices WHERE date=?', (latest_price,)
            ).fetchall()}
            avg_vol = {r[0]: r[1] for r in conn.execute(
                'SELECT symbol, AVG(volume) FROM stock_prices WHERE date >= date(?, "-20 days") GROUP BY symbol',
                (latest_price,)
            ).fetchall()}
            for sym, avg in avg_vol.items():
                vol = cur_vol.get(sym) or 0
                vol_map[sym] = {'spike': vol > avg * 1.5 if avg > 0 else False, 'avg': avg}
    except: pass

    conn.close()

    # Score every symbol
    all_syms = set(list(rs_map.keys()) + list(fund_map.keys()) + list(broker_map.keys()))
    scores = {}
    for sym in all_syms:
        sc = 0
        rs = rs_map.get(sym, {})
        rs5  = rs.get('rs5',  0) or 0
        rs10 = rs.get('rs10', 0) or 0
        rs20 = rs.get('rs20', 0) or 0
        if rs5  > 5:  sc += 20
        elif rs5 > 2: sc += 10
        if rs10 > 3:  sc += 10
        elif rs10 > 1: sc += 5
        if rs20 > 2:  sc += 5

        bk = broker_map.get(sym, {})
        if bk.get('net_qty', 0) > 0: sc += 10
        if bk.get('top20', False):   sc += 5

        if vol_map.get(sym, {}).get('spike', False): sc += 10

        fn = fund_map.get(sym, {})
        roe = fn.get('roe', 0) or 0
        pe  = fn.get('pe',  0) or 0
        pb  = fn.get('pb',  0) or 0
        if roe > 15:  sc += 10
        elif roe > 8: sc += 5
        if 0 < pe < 15:   sc += 8
        elif 0 < pe < 30: sc += 4
        if 0 < pb < 3:    sc += 5

        eg = eps_growth_map.get(sym)
        if eg is not None:
            if eg > 20:   sc += 12
            elif eg > 10: sc += 7
            elif eg > 0:  sc += 3

        if sc > 0:
            scores[sym] = sc

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top = [sym for sym, sc in ranked if vol_map.get(sym, {}).get('avg', 0) >= 2000 and rs_map.get(sym, {}).get('rs5', 0) > -2][:top_n]

    if not top:
        if not silent: print('Watchlist: no candidates found')
        return

    WL_PATH = Path('data/runtime/accounts/account_1/watchlist.json')
    watchlist = [
        {'kind': 'stock', 'key': 'stock:' + sym, 'label': sym, 'symbol': sym, 'score': scores.get(sym, 0)}
        for sym in top
    ]
    WL_PATH.parent.mkdir(parents=True, exist_ok=True)
    json.dump(watchlist, open(str(WL_PATH), 'w', encoding='utf-8'), indent=2)
    if not silent:
        print('Watchlist auto-updated ? top ' + str(len(top)) + ' by RS+Broker+Vol+ROE+EPS')
        if top: print('  Top: ' + ', '.join(top[:5]) + ('...' if len(top) > 5 else ''))

def analyze_power_sell(full_df, live_df):
    console.print()
    console.print(Rule("[bold red]Power Sell Scanner[/bold red]", style="red"))
    console.print("[dim]Stocks where big brokers are actively dumping today[/dim]\n")

    if full_df is None or full_df.empty:
        console.print("[red]No floorsheet data.[/red]")
        return []

    results = []
    for sym, grp in full_df.groupby('symbol'):
        total_qty = grp['quantity'].sum()
        if total_qty < 500:
            continue
        buy_qty  = grp.groupby('buyer_broker')['quantity'].sum()
        sell_qty = grp.groupby('seller_broker')['quantity'].sum()
        total_buy  = buy_qty.sum()
        total_sell = sell_qty.sum()
        sell_ratio = total_sell / max(total_buy + total_sell, 1) * 100

        all_b = set(buy_qty.index) | set(sell_qty.index)
        net   = {b: buy_qty.get(b,0) - sell_qty.get(b,0) for b in all_b}
        if not net:
            continue
        top_seller_net = min(net.values())
        top_seller_id  = min(net, key=net.get)

        if sell_ratio < 60 or top_seller_net > -200:
            continue

        ltp, change_pct = 0, 0
        if live_df is not None and 'symbol' in live_df.columns:
            row = live_df[live_df['symbol'] == sym]
            if not row.empty:
                ltp        = row['ltp'].values[0] if 'ltp' in row.columns else 0
                change_pct = row['change_pct'].values[0] if 'change_pct' in row.columns else 0

        results.append({
            'symbol': sym, 'sell_ratio': round(sell_ratio, 1),
            'top_seller': str(top_seller_id), 'net_sold': int(abs(top_seller_net)),
            'total_qty': int(total_qty), 'change_pct': change_pct, 'ltp': ltp,
        })

    if not results:
        console.print("[green]No strong sell signals detected today.[/green]")
        return []

    results = sorted(results, key=lambda x: x['sell_ratio'], reverse=True)

    t = Table(title="POWER SELL ALERTS", box=box.ROUNDED, border_style="red", header_style="bold red")
    t.add_column("Symbol",     width=10, style="bold white")
    t.add_column("LTP",        width=12, justify="right", no_wrap=True)
    t.add_column("Change",     width=10, justify="right", no_wrap=True)
    t.add_column("Sell Press", width=11, justify="right", style="red")
    t.add_column("Top Seller", width=10, justify="center", style="yellow")
    t.add_column("Net Sold",   width=12, justify="right", style="red")
    t.add_column("Signal",     width=28)

    for r in results[:15]:
        sig = "[red]STRONG SELL — exit now[/red]" if r['sell_ratio'] >= 75 else \
              "[yellow]MODERATE SELL — watch[/yellow]" if r['sell_ratio'] >= 65 else \
              "[dim]Light selling[/dim]"
        t.add_row(
            r['symbol'],
            f"Rs {r['ltp']:,.2f}" if r['ltp'] else "N/A",
            color_change(r['change_pct']),
            f"{r['sell_ratio']}%",
            r['top_seller'],
            f"{r['net_sold']:,}",
            sig,
        )
    console.print(t)
    return results

# ── SECTOR ROTATION ───────────────────────────────────────────────────────────



# ── SECTOR MOMENTUM ───────────────────────────────────────────────────────────

def _load_sector_prices(db_path="nepse_market_data.db", days=35):
    """Load recent closing prices for all equity symbols."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"""
        SELECT sp.symbol, c.sector, sp.date, sp.close
        FROM stock_prices sp
        JOIN companies c ON sp.symbol = c.symbol
        WHERE sp.date >= date('now', '-{days} days')
        ORDER BY sp.symbol, sp.date
    """, conn)
    conn.close()
    return df


def _sector_returns(prices_df, periods=(5, 10, 20)):
    """Compute equal-weighted sector returns over multiple periods."""
    if prices_df.empty:
        return {}

    import sqlite3
    conn = sqlite3.connect("nepse_market_data.db")
    cur = conn.cursor()
    cur.execute("SELECT symbol, sector FROM companies")
    sym_sector = {r[0]: r[1] for r in cur.fetchall()}
    conn.close()

    NAME_MAP = {
        "Hydro Power":                  "Hydropower",
        "Commercial Banks":             "Commercial Banks",
        "Development Banks":            "Development Banks",
        "Finance":                      "Finance",
        "Microfinance":                 "Microfinance",
        "Life Insurance":               "Life Insurance",
        "Non Life Insurance":           "Non-Life Insurance",
        "Manufacturing And Processing": "Manufacturing",
        "Hotels And Tourism":           "Hotel & Tourism",
        "Investment":                   "Investment",
        "Tradings":                     "Trading",
        "Others":                       "Others",
    }

    prices_df = prices_df.copy()
    prices_df["sector"] = prices_df["symbol"].map(
        lambda s: NAME_MAP.get(sym_sector.get(s, ""), "Others")
    )
    prices_df = prices_df[prices_df["sector"] != ""]

    pivot = prices_df.pivot_table(
        index="date", columns="symbol", values="close", aggfunc="last"
    ).sort_index()

    if pivot.empty or len(pivot) < 2:
        return {}

    results = {}
    for sector in prices_df["sector"].unique():
        syms     = prices_df[prices_df["sector"] == sector]["symbol"].unique()
        sec_piv  = pivot[[s for s in syms if s in pivot.columns]].dropna(how="all")
        sec_piv  = sec_piv.ffill().bfill()  # fill gaps so more stocks contribute
        if sec_piv.empty:
            continue

        sector_results = {"stocks": len(sec_piv.columns)}
        for period in periods:
            if len(sec_piv) < period + 1:
                sector_results[period] = None
                continue
            window      = sec_piv.iloc[-(period + 1):]
            start       = window.iloc[0]
            end         = window.iloc[-1]
            valid       = (start > 0) & (end > 0)
            if valid.sum() < 2:
                sector_results[period] = None
                continue
            returns = (end[valid] - start[valid]) / start[valid] * 100
            sector_results[period] = float(returns.mean())

        results[sector] = sector_results

    return results


def _momentum_label(r5, r10, r20):
    """Classify momentum from multi-period returns."""
    valid = [r for r in (r5, r10, r20) if r is not None]
    if not valid:
        return "No data       -", "dim"
    avg         = sum(valid) / len(valid)
    accelerating = (r5 is not None and r10 is not None and r5 > r10 / 2)
    if avg > 2.0 and accelerating:
        return "Strong uptrend  ", "bold green"
    elif avg > 0.5:
        return "Heating up      ", "green"
    elif avg > -0.5:
        return "Neutral         →",  "dim white"
    elif avg > -2.0:
        return "Cooling down    ", "red"
    else:
        return "Strong downtrend", "bold red"


def analyze_sector_trend(db_path="nepse_market_data.db"):
    """--sector-trend: 5/10/20 day sector momentum table."""
    console.print(Rule("[bold cyan]Sector Momentum[/bold cyan]", style="cyan"))
    console.print("[dim]Multi-period sector performance — spot rotation early[/dim]\n")

    with console.status("[cyan]Loading price history...[/cyan]"):
        prices_df = _load_sector_prices(db_path)

    if prices_df.empty:
        console.print("[red]No price data found.[/red]")
        return

    with console.status("[cyan]Computing sector returns...[/cyan]"):
        sector_data = _sector_returns(prices_df)

    if not sector_data:
        console.print("[red]Could not compute sector returns.[/red]")
        return

    sorted_sectors = sorted(
        sector_data.items(),
        key=lambda x: x[1].get(5) or -999,
        reverse=True
    )

    t = Table(
        title="Sector Momentum (Equal-Weighted)",
        box=box.SIMPLE_HEAVY, border_style="cyan", header_style="bold cyan",
        show_header=True,
    )
    t.add_column("Sector",   min_width=22, no_wrap=True, style="bold white")
    t.add_column("5D",       width=10, justify="right")
    t.add_column("10D",      width=10, justify="right")
    t.add_column("20D",      width=10, justify="right")
    t.add_column("Stocks",   width=8,  justify="center", style="dim")
    t.add_column("Momentum", width=26)

    def fmt_ret(v):
        if v is None:
            return Text("N/A", style="dim")
        return Text(f"{v:+.2f}%", style="green" if v > 0 else "red" if v < 0 else "dim")

    for sector, d in sorted_sectors:
        r5, r10, r20 = d.get(5), d.get(10), d.get(20)
        label, style = _momentum_label(r5, r10, r20)
        t.add_row(sector, fmt_ret(r5), fmt_ret(r10), fmt_ret(r20),
                  str(d.get("stocks", 0)), Text(label, style=style))

    console.print(t)
    console.print()

    top = sorted_sectors[0]
    bot = sorted_sectors[-1]
    if top[1].get(5) is not None:
        console.print(f"  [green]Strongest:[/green] {top[0]}  ({top[1].get(5):+.2f}% / 5d)")
    if bot[1].get(5) is not None:
        console.print(f"  [red]Weakest:  [/red] {bot[0]}  ({bot[1].get(5):+.2f}% / 5d)")
    console.print()


def analyze_sector_heatmap(db_path="nepse_market_data.db"):
    """--heatmap: color-coded sector heatmap."""
    console.print(Rule("[bold cyan]Sector Heatmap[/bold cyan]", style="cyan"))
    console.print("[dim]Where heat is building across timeframes[/dim]\n")

    with console.status("[cyan]Loading data...[/cyan]"):
        prices_df = _load_sector_prices(db_path)

    if prices_df.empty:
        console.print("[red]No price data.[/red]")
        return

    with console.status("[cyan]Computing returns...[/cyan]"):
        sector_data = _sector_returns(prices_df)

    if not sector_data:
        console.print("[red]Could not compute returns.[/red]")
        return

    def heat(v):
        if v is None:
            return "dim", "  N/A "
        s = f"{v:+.1f}%"
        if v >= 2.0:   return "bold green", s
        elif v >= 0.5: return "green",      s
        elif v >= -0.5:return "dim white",  s
        elif v >= -2.0:return "red",        s
        else:          return "bold red",   s

    sorted_sectors = sorted(
        sector_data.items(),
        key=lambda x: x[1].get(5) or -999,
        reverse=True
    )

    t = Table(
        title="Sector Heatmap",
        box=box.SIMPLE_HEAVY, border_style="cyan",
        header_style="bold cyan", show_lines=True,
    )
    t.add_column("Sector", min_width=22, style="bold white")
    t.add_column("5D",     width=10, justify="center")
    t.add_column("10D",    width=10, justify="center")
    t.add_column("20D",    width=10, justify="center")
    t.add_column("Heat Bar (20D avg)", width=22)

    for sector, d in sorted_sectors:
        r5, r10, r20 = d.get(5), d.get(10), d.get(20)
        c5,  v5  = heat(r5)
        c10, v10 = heat(r10)
        c20, v20 = heat(r20)

        valid = [r for r in (r5, r10, r20) if r is not None]
        avg   = sum(valid) / len(valid) if valid else 0
        filled = int(min(max(round((avg + 5) / 10 * 12), 0), 12))
        bar    = "█" * filled + "░" * (12 - filled)
        bar_style = "bold green" if avg > 1 else "bold red" if avg < -1 else "dim"

        t.add_row(
            sector,
            Text(v5,  style=c5),
            Text(v10, style=c10),
            Text(v20, style=c20),
            Text(bar, style=bar_style),
        )

    console.print(t)
    console.print()



# ── SECTOR MOMENTUM ───────────────────────────────────────────────────────────

def analyze_sector_rotation(full_df, live_df):
    """Show sector money flow with Traded/Listed counts."""
    console.print(Rule("[bold cyan]Sector Rotation[/bold cyan]", style="cyan"))
    console.print("[dim]Where is money flowing in and out today[/dim]\n")

    sector_data = {}

    # From floorsheet — turnover per sector (equity only)
    if full_df is not None and not full_df.empty:
        fdf = full_df.copy()
        fdf["sector"] = fdf["symbol"].apply(get_sector)
        fdf = fdf[fdf["sector"].notna()]          # drop non-equity
        for sector, grp in fdf.groupby("sector"):
            sector_data[sector] = {
                "turnover":   float(grp["amount"].sum()),
                "total_qty":  float(grp["quantity"].sum()) if "quantity" in grp else 0,
                "stocks":     grp["symbol"].nunique(),
            }

    # From live market — avg change, up/down per sector (equity only)
    if live_df is not None and not live_df.empty:
        ldf = live_df.copy()
        ldf["sector"] = ldf["symbol"].apply(get_sector)
        ldf = ldf[ldf["sector"].notna()]          # drop non-equity
        for sector, grp in ldf.groupby("sector"):
            avg_chg   = float(grp["change_pct"].mean()) if "change_pct" in grp else 0
            up_stocks = int((grp["change_pct"] > 0).sum()) if "change_pct" in grp else 0
            dn_stocks = int((grp["change_pct"] < 0).sum()) if "change_pct" in grp else 0
            if sector not in sector_data:
                sector_data[sector] = {"turnover": 0, "total_qty": 0, "stocks": grp["symbol"].nunique()}
            sector_data[sector]["avg_change"]  = avg_chg
            sector_data[sector]["up_stocks"]   = up_stocks
            sector_data[sector]["down_stocks"] = dn_stocks

    if not sector_data:
        console.print("[red]No sector data.[/red]")
        return

    t = Table(title="Sector Money Flow", box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("Sector",        min_width=22, style="bold white")
    t.add_column("Turnover",      width=14, justify="right",  style="yellow")
    t.add_column("Avg Chg",       width=10, justify="right")
    t.add_column("Up/Down",       width=10, justify="center")
    t.add_column("Traded/Listed", width=14, justify="center", style="cyan")
    t.add_column("Trend",         width=26)

    for sector, d in sorted(sector_data.items(), key=lambda x: x[1].get("turnover", 0), reverse=True):
        turnover  = d.get("turnover", 0)
        avg_chg   = d.get("avg_change", 0)
        up        = d.get("up_stocks", 0)
        dn        = d.get("down_stocks", 0)
        traded    = d.get("stocks", 0)
        listed    = SECTOR_LISTED.get(sector, "?")

        # Colour avg change
        if avg_chg > 0.5:
            chg_txt = Text(f"+{avg_chg:.2f}%", style="bold green")
        elif avg_chg < -0.5:
            chg_txt = Text(f"{avg_chg:.2f}%", style="bold red")
        else:
            chg_txt = Text(f"{avg_chg:+.2f}%", style="dim white")

        # Up/Down display
        updown = f"[green]{up}[/green]/[red]{dn}[/red]"

        # Traded/Listed
        tl_txt = Text(f"{traded}/{listed}", style="cyan")

        # Trend label
        if up > dn * 2 and avg_chg > 0.3:
            trend = Text("Buying pressure",   style="bold green")
        elif dn > up * 2 and avg_chg < -0.3:
            trend = Text("Selling pressure",  style="bold red")
        elif avg_chg > 0:
            trend = Text("Mild positive",     style="green")
        elif avg_chg < 0:
            trend = Text("Mild negative",     style="red")
        else:
            trend = Text("Neutral",           style="dim")

        t.add_row(sector, fmt_rs(turnover), chg_txt, updown, tl_txt, trend)

    console.print(t)


def analyze_whales(full_df):
    console.print()
    console.print(Rule("[bold magenta]Whale Tracker[/bold magenta]", style="magenta"))
    console.print("[dim]One broker controlling 40%+ of a stock's volume today[/dim]\n")

    if full_df is None or full_df.empty:
        console.print("[red]No floorsheet data.[/red]")
        return

    moves = []
    for sym, grp in full_df.groupby('symbol'):
        total_qty = grp['quantity'].sum()
        if total_qty < 1000:
            continue
        for action, col in [('BUY','buyer_broker'), ('SELL','seller_broker')]:
            by_broker = grp.groupby(col)['quantity'].sum()
            if by_broker.empty:
                continue
            top_b   = by_broker.idxmax()
            top_qty = by_broker.max()
            share   = top_qty / total_qty * 100
            amt     = grp[grp[col] == top_b]['amount'].sum()
            if share >= 40 and top_qty >= 1000:
                moves.append({
                    'symbol': sym, 'broker': str(top_b), 'action': action,
                    'qty': int(top_qty), 'share_pct': round(share,1),
                    'amount': amt, 'total_qty': int(total_qty),
                })

    if not moves:
        console.print("[green]No whale activity detected today.[/green]")
        return

    t = Table(title="Whale Activity", box=box.ROUNDED, border_style="magenta", header_style="bold magenta")
    t.add_column("Symbol",   width=10, style="bold white")
    t.add_column("Broker",   width=8,  justify="center", style="yellow")
    t.add_column("Action",   width=8,  justify="center")
    t.add_column("Qty",      width=12, justify="right")
    t.add_column("% of Vol", width=10, justify="right", style="magenta")
    t.add_column("Value",    width=14, justify="right", style="cyan")
    t.add_column("Reading",  width=28)

    for w in sorted(moves, key=lambda x: x['share_pct'], reverse=True)[:20]:
        action_s = "[green]BUY[/green]"  if w['action'] == 'BUY' else "[red]SELL[/red]"
        if w['share_pct'] >= 70:
            reading = "[red]Extreme control[/red]" if w['action']=='SELL' else "[green]Extreme accumulation[/green]"
        elif w['share_pct'] >= 55:
            reading = "[yellow]Heavy — watch for reversal[/yellow]"
        else:
            reading = "[dim]Notable — monitor[/dim]"
        t.add_row(w['symbol'], w['broker'], action_s, f"{w['qty']:,}",
                  f"{w['share_pct']}%", fmt_rs(w['amount']), reading)
    console.print(t)

# ── BROKER TRACKER ───────────────────────────────────────────────────────────

def analyze_broker_tracker(full_df, live_df, broker_id):
    broker_id = str(broker_id)
    console.print()
    console.print(Rule(f"[bold yellow]Broker {broker_id} Tracker[/bold yellow]", style="yellow"))
    console.print(f"[dim]Everything Broker {broker_id} is doing today[/dim]\n")

    if full_df is None or full_df.empty:
        console.print("[red]No floorsheet data.[/red]")
        return

    # All buys by this broker
    buys  = full_df[full_df['buyer_broker'].astype(str) == broker_id].copy()
    sells = full_df[full_df['seller_broker'].astype(str) == broker_id].copy()

    total_bought = buys['amount'].sum()
    total_sold   = sells['amount'].sum()
    net          = total_bought - total_sold

    console.print(Panel(
        f"[bold white]Broker:[/bold white] {broker_id}  "
        f"[bold white]Total Bought:[/bold white] [green]{fmt_rs(total_bought)}[/green]  "
        f"[bold white]Total Sold:[/bold white] [red]{fmt_rs(total_sold)}[/red]  "
        f"[bold white]Net Position:[/bold white] {'[green]+' if net >= 0 else '[red]'}{fmt_rs(net)}{'[/green]' if net >= 0 else '[/red]'}",
        border_style="yellow"
    ))

    # Top stocks bought
    if not buys.empty:
        buy_by_stock = buys.groupby('symbol').agg(
            qty=('quantity','sum'), amt=('amount','sum'), trades=('quantity','count')
        ).sort_values('amt', ascending=False)

        bt = Table(title=f"Broker {broker_id} — Stocks Bought Today",
                   box=box.ROUNDED, border_style="green", header_style="bold green")
        bt.add_column("Symbol",  width=12, style="bold white")
        bt.add_column("Qty",     width=12, justify="right", style="green")
        bt.add_column("Value",   width=14, justify="right", style="yellow")
        bt.add_column("Trades",  width=8,  justify="center", style="dim")
        bt.add_column("LTP",     width=12, justify="right", no_wrap=True)
        bt.add_column("Change",  width=10, justify="right", no_wrap=True)

        for sym, row in buy_by_stock.head(15).iterrows():
            ltp_s, chg_s = "N/A", "N/A"
            if live_df is not None and 'symbol' in live_df.columns:
                r = live_df[live_df['symbol'] == sym]
                if not r.empty:
                    ltp = r['ltp'].values[0]
                    chg = r['change_pct'].values[0]
                    ltp_s = f"Rs {ltp:,.2f}" if pd.notna(ltp) else "N/A"
                    chg_s = color_change(chg)
            bt.add_row(sym, f"{int(row['qty']):,}", fmt_rs(row['amt']),
                       str(int(row['trades'])), ltp_s, chg_s)
        console.print(bt)
        console.print()

    # Top stocks sold
    if not sells.empty:
        sell_by_stock = sells.groupby('symbol').agg(
            qty=('quantity','sum'), amt=('amount','sum'), trades=('quantity','count')
        ).sort_values('amt', ascending=False)

        st = Table(title=f"Broker {broker_id} — Stocks Sold Today",
                   box=box.ROUNDED, border_style="red", header_style="bold red")
        st.add_column("Symbol",  width=12, style="bold white")
        st.add_column("Qty",     width=12, justify="right", style="red")
        st.add_column("Value",   width=14, justify="right", style="yellow")
        st.add_column("Trades",  width=8,  justify="center", style="dim")
        st.add_column("LTP",     width=12, justify="right", no_wrap=True)
        st.add_column("Change",  width=10, justify="right", no_wrap=True)

        for sym, row in sell_by_stock.head(15).iterrows():
            ltp_s, chg_s = "N/A", "N/A"
            if live_df is not None and 'symbol' in live_df.columns:
                r = live_df[live_df['symbol'] == sym]
                if not r.empty:
                    ltp = r['ltp'].values[0]
                    chg = r['change_pct'].values[0]
                    ltp_s = f"Rs {ltp:,.2f}" if pd.notna(ltp) else "N/A"
                    chg_s = color_change(chg)
            st.add_row(sym, f"{int(row['qty']):,}", fmt_rs(row['amt']),
                       str(int(row['trades'])), ltp_s, chg_s)
        console.print(st)
        console.print()

    # Net position per stock
    all_syms = set(buys['symbol'].unique()) | set(sells['symbol'].unique())
    net_rows = []
    for sym in all_syms:
        bq = buys[buys['symbol']==sym]['quantity'].sum()
        sq = sells[sells['symbol']==sym]['quantity'].sum()
        ba = buys[buys['symbol']==sym]['amount'].sum()
        sa = sells[sells['symbol']==sym]['amount'].sum()
        net_rows.append({'symbol':sym,'net_qty':int(bq-sq),'net_amt':ba-sa,'buy_qty':int(bq),'sell_qty':int(sq)})

    if not net_rows:
        console.print('[yellow]??  No broker data from NEPSE API today. Try again tomorrow.[/yellow]')
        return
    net_df = pd.DataFrame(net_rows)
    if 'net_qty' in net_df.columns:
        net_df = net_df.sort_values('net_qty', ascending=False)
    accumulators = net_df[net_df['net_qty'] > 0]
    distributors = net_df[net_df['net_qty'] < 0]

    if not accumulators.empty or not distributors.empty:
        nt = Table(title=f"Broker {broker_id} — Net Position Summary",
                   box=box.ROUNDED, border_style="magenta", header_style="bold magenta")
        nt.add_column("Symbol",   width=12, style="bold white")
        nt.add_column("Bought",   width=10, justify="right", style="green")
        nt.add_column("Sold",     width=10, justify="right", style="red")
        nt.add_column("Net Qty",  width=12, justify="right")
        nt.add_column("Net Value",width=14, justify="right", style="yellow")
        nt.add_column("Stance",   width=16)

        for _, r in net_df.iterrows():
            net_q = r['net_qty']
            net_s = f"[green]+{net_q:,}[/green]" if net_q > 0 else f"[red]{net_q:,}[/red]"
            stance = "[green]Accumulating[/green]" if net_q > 0 else "[red]Distributing[/red]" if net_q < 0 else "[dim]Neutral[/dim]"
            nt.add_row(r['symbol'], f"{r['buy_qty']:,}", f"{r['sell_qty']:,}",
                       net_s, fmt_rs(r['net_amt']), stance)
        console.print(nt)

# ── SUPPORT / RESISTANCE ──────────────────────────────────────────────────────

def analyze_support_resistance(full_df, symbol):
    sym = symbol.upper()
    console.print()
    console.print(Rule(f"[bold yellow]Support / Resistance — {sym}[/bold yellow]", style="yellow"))

    df = get_floorsheet_of_symbol(full_df, sym)
    if df is None or df.empty:
        console.print(f"  [red]No data for {sym}[/red]")
        return

    total_qty  = df['quantity'].sum()
    mid_price  = df['rate'].median()
    buckets    = pd.cut(df['rate'], bins=12)
    vol_by_price = df.groupby(buckets, observed=True)['quantity'].sum().sort_values(ascending=False)

    t = Table(title=f"Price Clusters — {sym}", box=box.ROUNDED, border_style="yellow", header_style="bold yellow")
    t.add_column("Price Zone",   width=24, style="white")
    t.add_column("Volume",       width=12, justify="right", style="yellow")
    t.add_column("% of Day",     width=10, justify="right", style="cyan")
    t.add_column("Bar",          width=22)
    t.add_column("Level",        width=14, style="bold")

    for bucket, qty in vol_by_price.head(8).items():
        pct     = qty / total_qty * 100 if total_qty > 0 else 0
        bar_len = int(pct / 100 * 18)
        bar     = "█" * bar_len + "░" * (18 - bar_len)
        b_mid   = (bucket.left + bucket.right) / 2
        level   = "[green]SUPPORT[/green]" if b_mid < mid_price else "[red]RESISTANCE[/red]"
        strength_color = "red" if pct >= 20 else "yellow" if pct >= 10 else "dim"
        t.add_row(
            f"Rs {bucket.left:.2f} - {bucket.right:.2f}",
            f"{int(qty):,}", f"{pct:.1f}%",
            f"[{strength_color}]{bar}[/{strength_color}]", level,
        )
    console.print(t)

    mode_price = df['rate'].mode().values[0] if not df['rate'].mode().empty else mid_price
    console.print(Panel(
        f"[bold]Strongest zone:[/bold] Rs {vol_by_price.index[0].left:.2f} - {vol_by_price.index[0].right:.2f}\n"
        f"[bold]Most traded at:[/bold] Rs {mode_price:.2f}\n"
        f"[bold]Day range:[/bold]      Rs {df['rate'].min():.2f} - {df['rate'].max():.2f}\n"
        f"[dim]High-volume zones = support when price is above, resistance when below[/dim]",
        title="Key Levels", border_style="yellow"
    ))

# ── WATCHLIST ─────────────────────────────────────────────────────────────────

def analyze_watchlist(live_df):
    import json, sqlite3 as _sq
    from pathlib import Path
    console.print()
    console.print(Rule(chr(91)+chr(98)+chr(111)+chr(108)+chr(100)+chr(32)+chr(103)+chr(114)+chr(101)+chr(101)+chr(110)+chr(93)+chr(83)+chr(109)+chr(97)+chr(114)+chr(116)+chr(32)+chr(87)+chr(97)+chr(116)+chr(99)+chr(104)+chr(108)+chr(105)+chr(115)+chr(116)+chr(91)+chr(47)+chr(98)+chr(111)+chr(108)+chr(100)+chr(32)+chr(103)+chr(114)+chr(101)+chr(101)+chr(110)+chr(93), style=chr(103)+chr(114)+chr(101)+chr(101)+chr(110)))
    console.print()
    if live_df is None or live_df.empty:
        console.print(chr(91)+chr(114)+chr(101)+chr(100)+chr(93)+chr(78)+chr(111)+chr(32)+chr(108)+chr(105)+chr(118)+chr(101)+chr(32)+chr(100)+chr(97)+chr(116)+chr(97)+chr(46)+chr(91)+chr(47)+chr(114)+chr(101)+chr(100)+chr(93))
        return
    WL_PATH=Path(chr(100)+chr(97)+chr(116)+chr(97)+chr(47)+chr(114)+chr(117)+chr(110)+chr(116)+chr(105)+chr(109)+chr(101)+chr(47)+chr(97)+chr(99)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(115)+chr(47)+chr(97)+chr(99)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(95)+chr(49)+chr(47)+chr(119)+chr(97)+chr(116)+chr(99)+chr(104)+chr(108)+chr(105)+chr(115)+chr(116)+chr(46)+chr(106)+chr(115)+chr(111)+chr(110))
    wl_syms=WATCHLIST
    wl_scores={s:0 for s in wl_syms}
    if WL_PATH.exists():
        try:
            wl_data=json.load(open(WL_PATH,encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)))
            wl_syms=[e[chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)] for e in wl_data if e.get(chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108))]
            wl_scores={e[chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)]:e.get(chr(115)+chr(99)+chr(111)+chr(114)+chr(101),0) for e in wl_data if e.get(chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108))}
        except: pass
    if not wl_syms:
        console.print(chr(91)+chr(121)+chr(101)+chr(108)+chr(108)+chr(111)+chr(119)+chr(93)+chr(78)+chr(111)+chr(32)+chr(115)+chr(116)+chr(111)+chr(99)+chr(107)+chr(115)+chr(32)+chr(121)+chr(101)+chr(116)+chr(46)+chr(32)+chr(82)+chr(117)+chr(110)+chr(32)+chr(102)+chr(117)+chr(108)+chr(108)+chr(32)+chr(115)+chr(99)+chr(97)+chr(110)+chr(32)+chr(102)+chr(105)+chr(114)+chr(115)+chr(116)+chr(46)+chr(91)+chr(47)+chr(121)+chr(101)+chr(108)+chr(108)+chr(111)+chr(119)+chr(93))
        return
    t=Table(title=chr(83)+chr(109)+chr(97)+chr(114)+chr(116)+chr(32)+chr(87)+chr(97)+chr(116)+chr(99)+chr(104)+chr(108)+chr(105)+chr(115)+chr(116)+chr(32)+chr(45)+chr(32)+chr(84)+chr(111)+chr(112)+chr(32)+chr(80)+chr(105)+chr(99)+chr(107)+chr(115)+chr(32)+chr(98)+chr(121)+chr(32)+chr(83)+chr(99)+chr(111)+chr(114)+chr(101),box=box.ROUNDED,border_style=chr(103)+chr(114)+chr(101)+chr(101)+chr(110),header_style=chr(98)+chr(111)+chr(108)+chr(100)+chr(32)+chr(103)+chr(114)+chr(101)+chr(101)+chr(110))
    t.add_column(chr(35),width=4,style=chr(100)+chr(105)+chr(109))
    t.add_column(chr(83)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108),width=10,style=chr(98)+chr(111)+chr(108)+chr(100)+chr(32)+chr(119)+chr(104)+chr(105)+chr(116)+chr(101))
    t.add_column(chr(83)+chr(99)+chr(111)+chr(114)+chr(101),width=7,justify=chr(114)+chr(105)+chr(103)+chr(104)+chr(116),style=chr(98)+chr(111)+chr(108)+chr(100)+chr(32)+chr(99)+chr(121)+chr(97)+chr(110))
    t.add_column(chr(76)+chr(84)+chr(80),width=12,justify=chr(114)+chr(105)+chr(103)+chr(104)+chr(116))
    t.add_column(chr(67)+chr(104)+chr(103)+chr(37),width=9,justify=chr(114)+chr(105)+chr(103)+chr(104)+chr(116))
    t.add_column(chr(86)+chr(111)+chr(108)+chr(117)+chr(109)+chr(101),width=10,justify=chr(114)+chr(105)+chr(103)+chr(104)+chr(116))
    t.add_column(chr(84)+chr(117)+chr(114)+chr(110)+chr(111)+chr(118)+chr(101)+chr(114),width=14,style=chr(121)+chr(101)+chr(108)+chr(108)+chr(111)+chr(119))
    t.add_column(chr(83)+chr(116)+chr(97)+chr(116)+chr(117)+chr(115),width=28)
    _conn2=_sq.connect(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(95)+chr(100)+chr(97)+chr(116)+chr(97)+chr(46)+chr(100)+chr(98))
    _w52={}
    for _sym in wl_syms:
        try:
            _cur=_conn2.execute(chr(83)+chr(69)+chr(76)+chr(69)+chr(67)+chr(84)+chr(32)+chr(77)+chr(65)+chr(88)+chr(40)+chr(104)+chr(105)+chr(103)+chr(104)+chr(41)+chr(44)+chr(77)+chr(73)+chr(78)+chr(40)+chr(108)+chr(111)+chr(119)+chr(41)+chr(32)+chr(70)+chr(82)+chr(79)+chr(77)+chr(32)+chr(115)+chr(116)+chr(111)+chr(99)+chr(107)+chr(95)+chr(112)+chr(114)+chr(105)+chr(99)+chr(101)+chr(115)+chr(32)+chr(87)+chr(72)+chr(69)+chr(82)+chr(69)+chr(32)+chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)+chr(61)+chr(63)+chr(32)+chr(65)+chr(78)+chr(68)+chr(32)+chr(100)+chr(97)+chr(116)+chr(101)+chr(62)+chr(61)+chr(100)+chr(97)+chr(116)+chr(101)+chr(40)+chr(39)+chr(110)+chr(111)+chr(119)+chr(39)+chr(44)+chr(39)+chr(45)+chr(51)+chr(54)+chr(53)+chr(32)+chr(100)+chr(97)+chr(121)+chr(115)+chr(39)+chr(41),(_sym,))
            _row=_cur.fetchone()
            _w52[_sym]={chr(104)+chr(105)+chr(103)+chr(104):_row[0] or 0,chr(108)+chr(111)+chr(119):_row[1] or 0}
        except: _w52[_sym]={chr(104)+chr(105)+chr(103)+chr(104):0,chr(108)+chr(111)+chr(119):0}
    _conn2.close()
    sorted_syms=sorted(wl_syms,key=lambda s:wl_scores.get(s,0),reverse=True)
    for rank,sym in enumerate(sorted_syms,1):
        row=live_df[live_df[chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)].str.upper()==sym.upper()]
        if row.empty:
            t.add_row(str(rank),sym,chr(45),chr(78)+chr(47)+chr(65),chr(78)+chr(47)+chr(65),chr(78)+chr(47)+chr(65),chr(78)+chr(47)+chr(65),chr(91)+chr(100)+chr(105)+chr(109)+chr(93)+chr(78)+chr(111)+chr(116)+chr(32)+chr(116)+chr(114)+chr(97)+chr(100)+chr(105)+chr(110)+chr(103)+chr(91)+chr(47)+chr(100)+chr(105)+chr(109)+chr(93))
            continue
        r=row.iloc[0]
        ltp=r.get(chr(108)+chr(116)+chr(112),0)
        chg=r.get(chr(99)+chr(104)+chr(97)+chr(110)+chr(103)+chr(101)+chr(95)+chr(112)+chr(99)+chr(116),0)
        high52=_w52.get(sym,{}).get(chr(104)+chr(105)+chr(103)+chr(104),0)
        low52=_w52.get(sym,{}).get(chr(108)+chr(111)+chr(119),0)
        score=wl_scores.get(sym,0)
        parts=[]
        if pd.notna(high52) and high52>0 and pd.notna(ltp):
            dist_high=(high52-ltp)/high52*100
            dist_low=(ltp-low52)/low52*100 if pd.notna(low52) and low52>0 else 100
            if dist_high<=3: parts.append(chr(91)+chr(103)+chr(114)+chr(101)+chr(101)+chr(110)+chr(93)+chr(66)+chr(82)+chr(69)+chr(65)+chr(75)+chr(79)+chr(85)+chr(84)+chr(91)+chr(47)+chr(103)+chr(114)+chr(101)+chr(101)+chr(110)+chr(93))
            elif dist_low<=5 and chg>0: parts.append(chr(91)+chr(99)+chr(121)+chr(97)+chr(110)+chr(93)+chr(66)+chr(79)+chr(85)+chr(78)+chr(67)+chr(69)+chr(91)+chr(47)+chr(99)+chr(121)+chr(97)+chr(110)+chr(93))
            elif chg>=5: parts.append(chr(91)+chr(103)+chr(114)+chr(101)+chr(101)+chr(110)+chr(93)+chr(83)+chr(84)+chr(82)+chr(79)+chr(78)+chr(71)+chr(91)+chr(47)+chr(103)+chr(114)+chr(101)+chr(101)+chr(110)+chr(93))
            elif chg<=-3: parts.append(chr(91)+chr(114)+chr(101)+chr(100)+chr(93)+chr(68)+chr(82)+chr(79)+chr(80)+chr(80)+chr(73)+chr(78)+chr(71)+chr(91)+chr(47)+chr(114)+chr(101)+chr(100)+chr(93))
        status=chr(32).join(parts) if parts else chr(91)+chr(100)+chr(105)+chr(109)+chr(93)+chr(78)+chr(111)+chr(114)+chr(109)+chr(97)+chr(108)+chr(91)+chr(47)+chr(100)+chr(105)+chr(109)+chr(93)
        score_str=(chr(91)+chr(98)+chr(111)+chr(108)+chr(100)+chr(32)+chr(99)+chr(121)+chr(97)+chr(110)+chr(93)+str(score)+chr(91)+chr(47)+chr(98)+chr(111)+chr(108)+chr(100)+chr(32)+chr(99)+chr(121)+chr(97)+chr(110)+chr(93)) if score>0 else chr(45)
        ltp_str=(chr(82)+chr(115)+chr(32)+str(round(ltp,2))) if pd.notna(ltp) else chr(78)+chr(47)+chr(65)
        t.add_row(str(rank),sym,score_str,ltp_str,color_change(chg),fmt_vol(r.get(chr(118)+chr(111)+chr(108)+chr(117)+chr(109)+chr(101),0)),fmt_rs(r.get(chr(116)+chr(117)+chr(114)+chr(110)+chr(111)+chr(118)+chr(101)+chr(114),0)),status)
    console.print(t)
    console.print(chr(91)+chr(100)+chr(105)+chr(109)+chr(93)+chr(65)+chr(117)+chr(116)+chr(111)+chr(45)+chr(117)+chr(112)+chr(100)+chr(97)+chr(116)+chr(101)+chr(100)+chr(32)+chr(100)+chr(97)+chr(105)+chr(108)+chr(121)+chr(32)+chr(98)+chr(121)+chr(32)+chr(82)+chr(83)+chr(43)+chr(66)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(43)+chr(86)+chr(111)+chr(108)+chr(117)+chr(109)+chr(101)+chr(32)+chr(115)+chr(99)+chr(111)+chr(114)+chr(105)+chr(110)+chr(103)+chr(91)+chr(47)+chr(100)+chr(105)+chr(109)+chr(93))

def save_daily_report(summary, live_df, candidates, power_sell_results=None):
    today    = datetime.now().strftime("%Y-%m-%d")
    now      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/nepse_{today}.txt"

    lines = [
        "=" * 60,
        f"  NEPSE DAILY REPORT — {now}",
        "=" * 60, "",
    ]

    if summary:
        try:
            lines += [
                f"NEPSE Index : {summary.get('nepseIndex','N/A')}",
                f"Change      : {summary.get('change','N/A')}",
                f"Turnover    : {fmt_rs(summary.get('totalTurnover',0))}",
                "",
            ]
        except: pass

    if candidates is not None and not candidates.empty:
        lines += ["TOP SIGNAL CANDIDATES", "-" * 40]
        for i, row in candidates.head(15).iterrows():
            lines.append(
                f"  {i+1:2}. {row.get('symbol',''):10} | {row.get('signal',''):20} | "
                f"Rs {row.get('ltp',0):>8.2f} | {row.get('change_pct',0):+.2f}% | "
                f"Score {row.get('score',0):.2f} | {row.get('reason','')}"
            )
        lines.append("")

    if power_sell_results:
        lines += ["POWER SELL ALERTS", "-" * 40]
        for r in power_sell_results[:10]:
            lines.append(
                f"  {r['symbol']:10} | Sell Press: {r['sell_ratio']}% | "
                f"Top Seller: Broker {r['top_seller']} | Net Sold: {r['net_sold']:,}"
            )
        lines.append("")

    if live_df is not None:
        lines += ["WATCHLIST STATUS", "-" * 40]
        for sym in WATCHLIST:
            row = live_df[live_df['symbol'].str.upper() == sym.upper()]
            if not row.empty:
                r = row.iloc[0]
                lines.append(
                    f"  {sym:10} | Rs {r.get('ltp',0):>8.2f} | "
                    f"{r.get('change_pct',0):+.2f}% | Vol: {fmt_vol(r.get('volume',0))}"
                )
        lines.append("")

    lines += ["=" * 60, "Research only. Not financial advice.", "=" * 60]

    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    console.print(f"\n[green]Report saved:[/green] [cyan]{filename}[/cyan]")
    return filename

# ── SIGNAL ENGINES ────────────────────────────────────────────────────────────

def signal_volume_breakout(df):
    if 'volume' not in df.columns: return pd.DataFrame()
    r = df[df['volume'].notna() & df['ltp'].notna() & (df['volume'] > 0)].copy()
    med = r['volume'].median()
    r['vol_ratio'] = r['volume'] / med.clip(1)
    r = r[(r['vol_ratio'] >= 2.0) & (r['change_pct'] > 0)].copy()
    r['signal']   = 'VOLUME BREAKOUT'
    r['strength'] = (r['vol_ratio'] * r['change_pct']).round(2)
    r['reason']   = r.apply(lambda x: f"Vol {x['vol_ratio']:.1f}x median | +{x['change_pct']:.2f}%", axis=1)
    return r.sort_values('strength', ascending=False)

def signal_52week_high(df):
    if 'week52_high' not in df.columns: return pd.DataFrame()
    r = df[df['week52_high'].notna() & df['ltp'].notna() & (df['week52_high'] > 0)].copy()
    r['d'] = ((r['week52_high'] - r['ltp']) / r['week52_high'] * 100).round(2)
    r = r[r['d'].between(0, 3)].copy()
    r['signal']   = '52WK HIGH BREAKOUT'
    r['strength'] = (3 - r['d']).round(2)
    r['reason']   = r.apply(lambda x: f"{x['d']:.1f}% below 52wk high Rs {x['week52_high']:.2f}", axis=1)
    return r.sort_values('d')

def signal_52week_low_bounce(df):
    if 'week52_low' not in df.columns: return pd.DataFrame()
    r = df[df['week52_low'].notna() & df['ltp'].notna() & (df['week52_low'] > 0)].copy()
    r['d'] = ((r['ltp'] - r['week52_low']) / r['week52_low'] * 100).round(2)
    r = r[(r['d'].between(0, 5)) & (r['change_pct'] > 0)].copy()
    r['signal']   = '52WK LOW BOUNCE'
    r['strength'] = r['change_pct'].round(2)
    r['reason']   = r.apply(lambda x: f"Bouncing {x['d']:.1f}% above 52wk low Rs {x['week52_low']:.2f}", axis=1)
    return r.sort_values('strength', ascending=False)

def signal_momentum(df):
    if 'change_pct' not in df.columns: return pd.DataFrame()
    r = df[df['change_pct'].notna() & df['volume'].notna()].copy()
    r = r[(r['change_pct'] >= 2.0) & (r['volume'] >= r['volume'].quantile(0.10))].copy()
    r['signal']   = 'MOMENTUM'
    r['strength'] = r['change_pct'].round(2)
    def _reason(row):
        return f"+{row['change_pct']:.2f}% | Vol: {int(row['volume']):,}"
    r['reason'] = [_reason(row) for _, row in r.iterrows()]
    return r.sort_values('change_pct', ascending=False)

def signal_mean_reversion(df):
    if 'change_pct' not in df.columns or 'week52_high' not in df.columns: return pd.DataFrame()
    r = df[df['change_pct'].notna() & df['week52_high'].notna() & df['ltp'].notna()].copy()
    r = r[r['week52_high'] > 0].copy()
    r['fh'] = ((r['week52_high'] - r['ltp']) / r['week52_high'] * 100).round(2)
    r = r[(r['change_pct'] <= -2.0) & (r['fh'] >= 30)].copy()
    r['signal']   = 'MEAN REVERSION'
    r['strength'] = (r['fh'] - abs(r['change_pct'])).round(2)
    r['reason']   = r.apply(lambda x: f"{x['change_pct']:.2f}% today | {x['fh']:.1f}% below 52wk high", axis=1)
    return r.sort_values('fh', ascending=False)

def signal_range_compression(df):
    if not all(c in df.columns for c in ['high','low','ltp']): return pd.DataFrame()
    r = df[df['high'].notna() & df['low'].notna() & (df['ltp'] > 0)].copy()
    r['rng'] = ((r['high'] - r['low']) / r['ltp'] * 100).round(3)
    r = r[r['rng'] > 0].copy()
    thr = r['rng'].quantile(0.15)
    r = r[r['rng'] <= thr].copy()
    r['signal']   = 'RANGE COMPRESSION'
    r['strength'] = (thr - r['rng']).round(3)
    r['reason']   = r.apply(lambda x: f"Range {x['rng']:.2f}% | H:{x['high']:.2f} L:{x['low']:.2f}", axis=1)
    return r.sort_values('rng')

SIGNALS = {
    'volume': signal_volume_breakout, 'momentum': signal_momentum,
    'week52': signal_52week_high,     'bounce':   signal_52week_low_bounce,
    'reversion': signal_mean_reversion, 'compression': signal_range_compression,
}

def run_signals(df, selected):
    all_results = []
    for name in selected:
        fn = SIGNALS.get(name)
        if not fn: continue
        try:
            res = fn(df)
            if res is not None and not res.empty:
                all_results.append(res)
        except Exception as e:
            console.print(f"  [yellow]Signal '{name}' error: {e}[/yellow]")
    if not all_results: return pd.DataFrame()
    combined = pd.concat(all_results, ignore_index=True)
    score_map = combined.groupby('symbol')['strength'].sum().to_dict()
    conf_map  = combined.groupby('symbol')['signal'].count().to_dict()
    combined['score']         = combined['symbol'].map(score_map)
    combined['confirmations'] = combined['symbol'].map(conf_map)
    combined = combined.drop_duplicates(subset='symbol', keep='first').copy()

# ── DISPLAY ───────────────────────────────────────────────────────────────────

def print_header(summary):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"[bold cyan]NEPSE Scanner[/bold cyan]\n[dim]{now}[/dim]"
    if summary:
        try:
            idx = summary.get('nepseIndex', summary.get('index','N/A'))
            chg = summary.get('change', summary.get('percentChange','N/A'))
            to  = summary.get('totalTurnover', summary.get('turnover','N/A'))
            content = (
                f"[bold cyan]NEPSE INDEX:[/bold cyan] [bold white]{idx}[/bold white]  "
                f"[bold cyan]CHANGE:[/bold cyan] {color_change(chg)}  "
                f"[bold cyan]TURNOVER:[/bold cyan] [yellow]{fmt_rs(to)}[/yellow]\n"
                f"[dim]{now}[/dim]"
            )
        except: pass
    console.print(Panel(content, title="[bold green]NEPSE QUANT SCANNER[/bold green]", border_style="green"))

def print_signals_table(candidates, top_n):
    if candidates is None or candidates.empty:
        console.print("[yellow]No signals found.[/yellow]")
        return
    top = candidates.head(top_n)
    t = Table(title=f"Top {min(top_n, len(top))} Signal Candidates",
              box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("#",      style="dim",        width=3,  justify="right")
    t.add_column("Symbol", style="bold white", width=12)
    t.add_column("Signal", style="yellow",     width=20)
    t.add_column("LTP",    style="white",      width=13, justify="right", no_wrap=True)
    t.add_column("Change", style="white",      width=10, justify="right", no_wrap=True)
    t.add_column("Volume", style="white",      width=10, justify="right")
    t.add_column("Score",  style="magenta",    width=8,  justify="right")
    t.add_column("Conf",   style="cyan",       width=4,  justify="center")
    t.add_column("Reason", style="dim white",  min_width=30)
    for i, row in top.iterrows():
        conf  = int(row.get('confirmations',1))
        conf_s = f"[green]{conf}[/green]" if conf > 1 else f"[dim]{conf}[/dim]"
        ltp   = row.get('ltp')
        t.add_row(
            str(i+1), str(row.get('symbol','')), str(row.get('signal','')),
            f"Rs {ltp:,.2f}" if pd.notna(ltp) else "N/A",
            color_change(row.get('change_pct',0)),
            fmt_vol(row.get('volume',0)),
            f"{row.get('score',0):.2f}", conf_s,
            str(row.get('reason','')),
        )
    console.print(t)

def print_market_movers(gainers, losers, turnover_list):
    LTP_F = ['lastTradedPrice','ltp','closingPrice','closePrice','price','rate']
    CHG_F = ['percentageChange','changePercent','change','percentChange','perChange']
    SYM_F = ['symbol','stockSymbol','securitySymbol','scrip']

    def gf(item, fields):
        for f in fields:
            v = item.get(f)
            if v not in (None,''):
                try:
                    fv = float(v)
                    if fv != 0: return fv
                except: pass
        return 0

    def gs(item):
        for f in SYM_F:
            v = item.get(f)
            if v: return str(v)
        return ''

    panels = []
    if gainers:
        g = Table(box=box.SIMPLE, show_header=True, header_style="bold green")
        g.add_column("Symbol", style="white", width=10)
        g.add_column("LTP",    style="white", width=12, justify="right", no_wrap=True)
        g.add_column("Chg%",   style="green", width=8,  justify="right", no_wrap=True)
        for item in gainers[:8]:
            try:
                ltp = gf(item, LTP_F); chg = gf(item, CHG_F)
                g.add_row(gs(item), f"Rs {ltp:,.2f}" if ltp else "N/A", f"+{chg:.2f}%")
            except: pass
        panels.append(Panel(g, title="[green]Top Gainers[/green]", border_style="green"))

    if losers:
        l = Table(box=box.SIMPLE, show_header=True, header_style="bold red")
        l.add_column("Symbol", style="white", width=10)
        l.add_column("LTP",    style="white", width=12, justify="right", no_wrap=True)
        l.add_column("Chg%",   style="red",   width=8,  justify="right", no_wrap=True)
        for item in losers[:8]:
            try:
                ltp = gf(item, LTP_F); chg = gf(item, CHG_F)
                l.add_row(gs(item), f"Rs {ltp:,.2f}" if ltp else "N/A", f"{chg:.2f}%")
            except: pass
        panels.append(Panel(l, title="[red]Top Losers[/red]", border_style="red"))

    if turnover_list:
        t2 = Table(box=box.SIMPLE, show_header=True, header_style="bold yellow")
        t2.add_column("Symbol",   style="white",  width=10)
        t2.add_column("Turnover", style="yellow", width=14, justify="right")
        for item in turnover_list[:35]:
            try: t2.add_row(item.get('symbol',''), fmt_rs(item.get('turnover', item.get('totalTradeValue',0))))
            except: pass
        panels.append(Panel(t2, title="[yellow]Top Turnover[/yellow]", border_style="yellow"))

    if panels:
        console.print(Columns(panels))

def print_legend():
    t = Table(box=box.SIMPLE, show_header=False, padding=(0,2))
    t.add_column("Signal",  style="yellow",   width=22)
    t.add_column("Meaning", style="dim white")
    t.add_row("VOLUME BREAKOUT",    "Volume 2x+ median with positive price — accumulation")
    t.add_row("MOMENTUM",           "Strong % gainer with decent volume — trend continuation")
    t.add_row("52WK HIGH BREAKOUT", "Within 3% of yearly high — breakout setup")
    t.add_row("52WK LOW BOUNCE",    "Near yearly low but positive today — discount rejection")
    t.add_row("MEAN REVERSION",     "Down today but 30%+ below 52wk high — stretched discount")
    t.add_row("RANGE COMPRESSION",  "Tight H-L range — consolidation before expansion")
    console.print(Panel(t, title="Signal Legend", border_style="dim"))
    console.print()
    console.print(Panel(
        "[bold]New Commands:[/bold]\n"
        "  [cyan]--powersell[/cyan]          Stocks brokers are dumping\n"
        "  [cyan]--sector[/cyan]             Sector rotation map\n"
        "  [cyan]--whale[/cyan]              Single broker dominating a stock\n"
        "  [cyan]--sr NABIL[/cyan]           Support/resistance levels for NABIL\n"
        "  [cyan]--watchlist[/cyan]          Your personal watchlist\n"
        "  [cyan]--report[/cyan]             Save today's scan to reports/ folder\n\n"
        "[bold]Existing Commands:[/bold]\n"
        "  [cyan]--floor NABIL[/cyan]        Floorsheet for NABIL\n"
        "  [cyan]--brokers[/cyan]            Broker leaderboard\n"
        "  [cyan]--signals volume momentum[/cyan]  Only these signals\n"
        "  [cyan]--top 25[/cyan]             Show top 25 candidates\n"
        "  [cyan]--movers-only[/cyan]        Only gainers/losers/turnover",
        title="Usage Guide", border_style="dim"
    ))

def print_buy_sell_guide():
    console.print()
    console.rule("[bold cyan]Buy / Sell Decision Guide[/bold cyan]", style="cyan")
    console.print()
    console.print("[bold yellow]HOW TO FIND A BUY:[/bold yellow]")
    console.print()
    steps = [
        ("Step 1", "Run option 3 (Watchlist)", "Check your tracked stocks first — known stocks you follow."),
        ("Step 2", "Run option 4 (Quick Pick)", "Look for score 70+. New candidates from full market."),
        ("Step 3", "Run option 5 (Smart Pick)", "Confirms signals + broker + whale together. Strongest filter."),
        ("Step 4", "Run option 17f (Momentum Hunter)", "Stock must have 3+ consecutive buy days and score 80+."),
        ("Step 5", "Run option 17c -> latest date", "Verdict must say STRONG BUY or HOLD/ACCUMULATE.\n         If CAUTION or CONSIDER SELLING -> skip this stock."),
        ("Step 6", "Run option 17b -> same stock", "Same brokers buying 3+ days in a row = strong confirmation.\n         New brokers each day = weak signal, skip."),
        ("Step 7", "Run option 18 -> same stock", "Price near SUPPORT zone = BUY.\n         Price near RESISTANCE zone = wait for pullback.\n         Price in middle = small entry, add on dip."),
    ]
    for step, option, desc in steps:
        console.print(f"  [bold green]{step}[/bold green] — [cyan]{option}[/cyan]")
        console.print(f"         {desc}")
        console.print()
    console.print("[bold yellow]HOW TO DECIDE TO SELL:[/bold yellow]")
    console.print()
    sell_steps = [
        ("Signal 1", "Run 17c", "Known NET SELLERS appear + verdict changes to CAUTION -> sell 50%"),
        ("Signal 2", "Run 17d", "Trend score dropping 3 days in a row -> sell remaining"),
        ("Signal 3", "Check chart", "Price hits resistance zone -> take partial profits"),
        ("Signal 4", "Run 17b", "Top accumulating brokers now net selling -> exit"),
    ]
    for sig, option, desc in sell_steps:
        console.print(f"  [bold red]{sig}[/bold red] — [cyan]{option}[/cyan]")
        console.print(f"         {desc}")
        console.print()
    console.print("[bold yellow]ALL 7 MUST AGREE TO BUY. ANY 2 SELL SIGNALS = EXIT.[/bold yellow]")
    console.print()
    console.print("[bold cyan]EXAMPLE — JHAPA June 5:[/bold cyan]")
    console.print("  17f score: 98/100                    [green]PASS[/green]")
    console.print("  17c verdict: STRONG BUY, 6 net buyers [green]PASS[/green]")
    console.print("  17b: Broker 14, 25, 17 accumulating   [green]PASS[/green]")
    console.print("  18: Price at Rs 1,335 = support zone  [green]PASS[/green]")
    console.print("  Previous high Rs 1,860 = 39% upside   [green]PASS[/green]")
    console.print("  [bold green]Decision: BUY at support, target Rs 1,600+, stop Rs 1,250[/bold green]")
    console.print()
    console.print("  [dim]Research only. Not financial advice. Paper trade first.[/dim]")
    console.print()

def analyze_floorsheet_symbol(df, symbol):
    sym = symbol.upper()
    console.print()
    console.print(Rule(f"[bold cyan]Floorsheet — {sym}[/bold cyan]", style="cyan"))
    if df is None or df.empty:
        console.print(f"  [red]No data for {sym}. Available Sun-Thu 11am-3pm NST.[/red]")
        return
    total_qty = df['quantity'].sum()
    total_amt = df['amount'].sum()
    console.print(Panel(
        f"[bold white]Symbol:[/bold white] {sym}  [bold white]Contracts:[/bold white] {len(df):,}  "
        f"[bold white]Total Qty:[/bold white] {int(total_qty):,}  [bold white]Turnover:[/bold white] {fmt_rs(total_amt)}\n"
        f"[bold white]Avg Rate:[/bold white] Rs {df['rate'].mean():.2f}  "
        f"[bold white]High:[/bold white] Rs {df['rate'].max():.2f}  "
        f"[bold white]Low:[/bold white] Rs {df['rate'].min():.2f}",
        border_style="cyan"
    ))
    if 'buyer_broker' in df.columns:
        buy_qty  = df.groupby('buyer_broker')['quantity'].sum()
        sell_qty = df.groupby('seller_broker')['quantity'].sum()
        buy_amt  = df.groupby('buyer_broker')['amount'].sum()
        sell_amt = df.groupby('seller_broker')['amount'].sum()
        all_b    = set(buy_qty.index) | set(sell_qty.index)
        bdata    = [{'broker':str(b),'buy_qty':int(buy_qty.get(b,0)),'sell_qty':int(sell_qty.get(b,0)),
                     'net_qty':int(buy_qty.get(b,0)-sell_qty.get(b,0)),
                     'buy_amt':buy_amt.get(b,0),'sell_amt':sell_amt.get(b,0),
                     'net_amt':buy_amt.get(b,0)-sell_amt.get(b,0)} for b in all_b]
        bdf = pd.DataFrame(bdata)
        if bdf.empty or 'net_qty' not in bdf.columns:
            console.print('  No broker data available.', style='yellow')
            return
        bdf = bdf.sort_values('net_qty', ascending=False)

        acc = Table(title="Top Accumulators", box=box.ROUNDED, border_style="green", header_style="bold green")
        dis = Table(title="Top Distributors", box=box.ROUNDED, border_style="red",   header_style="bold red")
        for tbl in [acc, dis]:
            tbl.add_column("Broker", width=8, justify="center")
            tbl.add_column("Bought", width=10, justify="right", style="green")
            tbl.add_column("Sold",   width=10, justify="right", style="red")
            tbl.add_column("Net",    width=10, justify="right")
            tbl.add_column("Value",  width=14, justify="right", style="yellow")
        for _, r in bdf[bdf['net_qty'] > 0].head(10).iterrows():
            acc.add_row(r['broker'],f"{r['buy_qty']:,}",f"{r['sell_qty']:,}",f"[green]+{r['net_qty']:,}[/green]",fmt_rs(r['net_amt']))
        for _, r in bdf[bdf['net_qty'] < 0].sort_values('net_qty').head(10).iterrows():
            dis.add_row(r['broker'],f"{r['buy_qty']:,}",f"{r['sell_qty']:,}",f"[red]{r['net_qty']:,}[/red]",fmt_rs(r['net_amt']))
        console.print(Columns([acc, dis]))

        top3_share = bdf.nlargest(3,'buy_qty')['buy_qty'].sum() / max(bdf['buy_qty'].sum(),1) * 100
        net_bias   = bdf['net_qty'].sum()
        bias_s     = f"[green]BUYING (+{int(net_bias):,})[/green]" if net_bias > 0 else f"[red]SELLING ({int(net_bias):,})[/red]"
        conc_s     = f"[red]High ({top3_share:.1f}%)[/red]" if top3_share>=50 else f"[yellow]Moderate ({top3_share:.1f}%)[/yellow]" if top3_share>=30 else f"[green]Distributed ({top3_share:.1f}%)[/green]"
        console.print(Panel(
            f"Net bias: {bias_s}  |  Concentration: {conc_s}\n"
            f"Top buyers:  {', '.join(bdf.nlargest(3,'buy_qty')['broker'].tolist())}\n"
            f"Top sellers: {', '.join(bdf.nlargest(3,'sell_qty')['broker'].tolist())}",
            title="Smart Money Reading", border_style="magenta"
        ))

def analyze_broker_market(df):
    console.print()
    console.print(Rule("[bold cyan]Market-Wide Broker Analysis[/bold cyan]", style="cyan"))
    if df is None or df.empty:
        console.print("[red]No data.[/red]")
        return
    console.print(f"[dim]Analyzing {len(df):,} contracts...[/dim]\n")
    # Fix broker column - API may use different names
    if df['buyer_broker'].isna().all():
        if 'buyerBrokerName' in df.columns:
            df['buyer_broker'] = df['buyerBrokerName']
            df['seller_broker'] = df['sellerBrokerName']
    df = df.dropna(subset=['buyer_broker','seller_broker'])
    df['buyer_broker'] = df['buyer_broker'].astype(str)
    df['seller_broker'] = df['seller_broker'].astype(str)
    buy_vol  = df.groupby('buyer_broker')['quantity'].sum()
    sell_vol = df.groupby('seller_broker')['quantity'].sum()
    buy_amt  = df.groupby('buyer_broker')['amount'].sum()
    sell_amt = df.groupby('seller_broker')['amount'].sum()
    all_b    = set(buy_vol.index) | set(sell_vol.index)
    rows = [{'broker':str(b),'buy_qty':int(buy_vol.get(b,0)),'sell_qty':int(sell_vol.get(b,0)),
             'net_qty':int(buy_vol.get(b,0)-sell_vol.get(b,0)),'buy_amt':buy_amt.get(b,0),
             'sell_amt':sell_amt.get(b,0),'net_amt':buy_amt.get(b,0)-sell_amt.get(b,0),
             'total_amt':buy_amt.get(b,0)+sell_amt.get(b,0)} for b in all_b]
    bdf = pd.DataFrame(rows)
    if bdf.empty or "total_amt" not in bdf.columns:
        console.print("[yellow]Broker data unavailable — NEPSE API is not returning broker IDs today.[/]")
        console.print("[dim]This is an API-side limitation. Try again later or on a different trading day.[/]")
        return

    at = Table(title="Most Active Brokers", box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    at.add_column("Broker", width=8, justify="center", style="bold white")
    at.add_column("Total",  width=16, justify="right", style="yellow")
    at.add_column("Bought", width=14, justify="right", style="green")
    at.add_column("Sold",   width=14, justify="right", style="red")
    at.add_column("Net",    width=16, justify="right")
    for _, r in bdf.nlargest(15,'total_amt').iterrows():
        ns = f"[green]+{fmt_rs(r['net_amt'])}[/green]" if r['net_amt']>=0 else f"[red]{fmt_rs(r['net_amt'])}[/red]"
        at.add_row(r['broker'],fmt_rs(r['total_amt']),fmt_rs(r['buy_amt']),fmt_rs(r['sell_amt']),ns)
    console.print(at)
    console.print()

    bt = Table(title="Biggest Net Buyers",  box=box.ROUNDED, border_style="green", header_style="bold green")
    st = Table(title="Biggest Net Sellers", box=box.ROUNDED, border_style="red",   header_style="bold red")
    for tbl in [bt, st]:
        tbl.add_column("Broker",  width=8,  justify="center")
        tbl.add_column("Net Qty", width=12, justify="right")
        tbl.add_column("Value",   width=14, justify="right", style="yellow")
    for _, r in bdf.nlargest(10,'net_qty').iterrows():
        bt.add_row(r['broker'],f"[green]+{r['net_qty']:,}[/green]",fmt_rs(r['net_amt']))
    for _, r in bdf.nsmallest(10,'net_qty').iterrows():
        st.add_row(r['broker'],f"[red]{r['net_qty']:,}[/red]",fmt_rs(r['net_amt']))
    console.print(Columns([bt, st]))

# ── QUICK PICK ───────────────────────────────────────────────────────────────

def analyze_quick_pick(live_df, top_n=10, db_path="nepse_market_data.db", offline=False):
    console.print()
    console.print(Rule("[bold green]Quick Stock Pick[/bold green]", style="green"))
    console.print("[dim]Best stocks for 10%+ gain in 7 days to 1 month — signals only[/dim]\n")

    console.print(f"[dim]offline={offline} live_df rows={len(live_df) if live_df is not None else 0}[/dim]")
    if live_df is None or live_df.empty:
        console.print("[red]No live data.[/red]")
        return []

    df = live_df.copy()
    df = df[df["ltp"].notna() & df["volume"].notna() & (df["ltp"] > 0)].copy()

    # --- Load DB data ---
    db_vol_avg = {}
    db_rs = {}
    db_broker_net = {}
    db_sector_scores = {}

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # 20-day avg volume per stock
        c.execute("""
            SELECT symbol, AVG(volume) as avg_vol
            FROM (
                SELECT symbol, volume FROM stock_prices
                ORDER BY date DESC LIMIT 99999
            )
            GROUP BY symbol
        """)
        for sym, avg_vol in c.fetchall():
            db_vol_avg[sym] = avg_vol or 0

        # RS proxy from fundamentals (ROE - sector avg ROE)
        c.execute("SELECT symbol, roe, sector FROM fundamentals WHERE date = (SELECT MAX(date) FROM fundamentals)")
        rows = c.fetchall()
        sector_roe = {}
        for sym, roe, sector in rows:
            if roe and sector:
                if sector not in sector_roe:
                    sector_roe[sector] = []
                sector_roe[sector].append(roe)
        sector_roe_avg = {s: sum(v)/len(v) for s,v in sector_roe.items() if v}
        for sym, roe, sector in rows:
            if roe and sector and sector in sector_roe_avg:
                db_rs[sym] = roe - sector_roe_avg[sector]

        # Broker net buy (last 3 days)
        c.execute("""
            SELECT symbol, SUM(net_qty) as net
            FROM broker_activity
            WHERE date >= date('now', '-3 days')
            GROUP BY symbol
        """)
        for sym, net in c.fetchall():
            db_broker_net[sym] = net or 0

        # Sector momentum — avg % change per sector today
        if "sector" in df.columns:
            for sector in df["sector"].dropna().unique():
                sector_df = df[df["sector"] == sector]
                if not sector_df.empty:
                    db_sector_scores[sector] = float(sector_df["change_pct"].mean())

        conn.close()
    except Exception as e:
        pass  # DB unavailable, continue without it

    scores = []
    vol_median  = df["volume"].median()
    turn_median = df["turnover"].median() if "turnover" in df.columns else 0

    for _, row in df.iterrows():
        sym    = row.get("symbol", "")
        if sym in NON_EQUITY_SYMBOLS: continue
        # Skip debentures/bonds by pattern
        import re as _re
        if _re.search(r'(LD|BD|CD|BLD|CBD|NBD|NILD|BILD)\d{2}$', sym): continue
        if _re.search(r'(MF|SF|GF)\d+$', sym): continue
        ltp    = row.get("ltp", 0)
        chg    = row.get("change_pct", 0) or 0
        vol    = row.get("volume", 0) or 0
        turn   = row.get("turnover", 0) or 0
        h52    = row.get("week52_high", 0) or 0
        l52    = row.get("week52_low", 0) or 0
        high   = row.get("high", 0) or 0
        low    = row.get("low", 0) or 0
        sector = row.get("sector", "") or ""

        score   = 0
        reasons = []

        # 1. Momentum (max 25 pts)
        if chg >= 5:
            score += 25; reasons.append("Strong momentum")
        elif chg >= 3:
            score += 18; reasons.append("Good momentum")
        elif chg >= 1:
            score += 10; reasons.append("Positive")
        elif chg < 0:
            score -= 10

        # 2. Volume surge — use stock own 20D avg if available (max 25 pts)
        own_avg_vol = db_vol_avg.get(sym, 0)
        base_vol    = own_avg_vol if own_avg_vol > 0 else vol_median
        if base_vol > 0:
            vol_ratio = vol / base_vol
            if vol_ratio >= 5:
                score += 25; reasons.append(f"Vol {vol_ratio:.1f}x own avg surge")
            elif vol_ratio >= 3:
                score += 20; reasons.append(f"Vol {vol_ratio:.1f}x own avg high")
            elif vol_ratio >= 2:
                score += 12; reasons.append(f"Vol {vol_ratio:.1f}x own avg")

        # 3. 52-week position (max 20 pts)
        if h52 > 0 and ltp > 0:
            dist_high = (h52 - ltp) / h52 * 100
            dist_low  = (ltp - l52) / l52 * 100 if l52 > 0 else 100
            if dist_high <= 3:
                score += 20; reasons.append("Near 52W breakout")
            elif dist_high <= 10:
                score += 14; reasons.append("Close to 52W high")
            elif dist_low <= 10 and chg > 0:
                score += 16; reasons.append("Bouncing from 52W low")
            elif dist_high >= 40:
                score -= 5

        # 4. Liquidity (max 15 pts)
        if turn_median > 0:
            turn_ratio = turn / turn_median
            if turn_ratio >= 3:
                score += 15; reasons.append("Very liquid")
            elif turn_ratio >= 1.5:
                score += 10; reasons.append("Good liquidity")
            elif turn_ratio < 0.3:
                score -= 10; reasons.append("Low liquidity")

        # 5. Day range tightness (max 15 pts)
        if high > 0 and low > 0 and ltp > 0:
            rng_pct = (high - low) / ltp * 100
            if rng_pct <= 1.5 and chg > 0:
                score += 15; reasons.append("Tight range breakout")
            elif rng_pct <= 3 and chg > 0:
                score += 8; reasons.append("Controlled move")

        # 6. RS from fundamentals DB (max 20 pts) — NEW
        rs_val = db_rs.get(sym, None)
        if rs_val is not None:
            if rs_val >= 10:
                score += 20; reasons.append(f"Strong RS vs sector")
            elif rs_val >= 5:
                score += 14; reasons.append(f"Good RS vs sector")
            elif rs_val >= 0:
                score += 7; reasons.append(f"Positive RS")
            else:
                score -= 5

        # 7. Broker net buy last 3 days (max 15 pts) — NEW
        broker_net = db_broker_net.get(sym, None)
        if broker_net is not None:
            if broker_net > 50000:
                score += 15; reasons.append("Strong broker accumulation")
            elif broker_net > 10000:
                score += 10; reasons.append("Broker buying")
            elif broker_net < -50000:
                score -= 10; reasons.append("Broker selling")

        # 8. Sector momentum (max 10 pts) — NEW
        if sector and sector in db_sector_scores:
            sec_chg = db_sector_scores[sector]
            if sec_chg >= 2:
                score += 10; reasons.append(f"Hot sector (+{sec_chg:.1f}%)")
            elif sec_chg >= 0.5:
                score += 5; reasons.append(f"Sector positive")
            elif sec_chg < -1:
                score -= 5

        # Filter - relax in offline mode
        if offline:
            if score < 15: continue
        else:
            if chg <= 0 or score < 30: continue

        # Upside estimate
        if h52 > 0 and ltp > 0:
            upside = (h52 - ltp) / ltp * 100
        else:
            upside = chg * 4

        scores.append({
            "symbol":  sym,
            "score":   min(score, 100),
            "ltp":     ltp,
            "change":  chg,
            "volume":  vol,
            "upside":  round(upside, 1),
            "change_pct": chg,
            "reasons": " | ".join(reasons[:4]),
        })

    if not scores:
        console.print("[yellow]No quick pick candidates today.[/yellow]")
        return []

    scores = sorted(scores, key=lambda x: x["score"], reverse=True)

    t = Table(title="Quick Pick — Top Candidates (10%+ Potential)",
              box=box.ROUNDED, border_style="green", header_style="bold green")
    t.add_column("#",        width=3,  justify="right", style="dim")
    t.add_column("Symbol",   width=10, style="bold white")
    t.add_column("LTP",      width=13, justify="right", no_wrap=True)
    t.add_column("Chg%",     width=8,  justify="right", no_wrap=True)
    t.add_column("Score",    width=7,  justify="right")
    t.add_column("Upside",   width=8,  justify="right")
    t.add_column("Why",      min_width=30)

    for rank, r in enumerate(scores[:top_n], 1):
        chg = r.get("change_pct", 0) or 0
        chg_col = "green" if chg >= 0 else "red"
        upside = r.get("upside", 0) or 0
        t.add_row(
            str(rank),
            r["symbol"],
            f'{r["ltp"]:.2f}',
            f'[{chg_col}]{chg:+.2f}%[/{chg_col}]',
            str(r["score"]),
            f'+{upside:.1f}%' if upside > 0 else "-",
            r.get("reasons", ""),
        )

    console.print(t)
    return scores[:top_n]

def analyze_smart_pick(live_df, full_df, top_n=10):
    console.print()
    console.print(Rule("[bold cyan]Smart Stock Pick[/bold cyan]", style="cyan"))
    console.print("[dim]Best stocks for 10%+ gain — signals + broker activity + whale confirmation[/dim]\n")

    if live_df is None or live_df.empty:
        console.print("[red]No live data.[/red]")
        return

    # Start with quick pick scores as base
    quick_scores = analyze_quick_pick(live_df, top_n=50)
    if not quick_scores:
        return

    score_map = {r['symbol']: r for r in quick_scores}

    if full_df is None or full_df.empty:
        console.print("[yellow]No floorsheet — showing quick pick scores only.[/yellow]")
        return

    # Broker activity boost
    # 1. Is a top broker (58, 44, 42) buying this stock?
    top_brokers = ['58', '44', '42', '49', '25']

    broker_buying = set()
    broker_selling = set()
    for tb in top_brokers:
        tb_buys  = full_df[full_df['buyer_broker'].astype(str) == tb]
        tb_sells = full_df[full_df['seller_broker'].astype(str) == tb]
        buy_syms  = tb_buys.groupby('symbol')['quantity'].sum()
        sell_syms = tb_sells.groupby('symbol')['quantity'].sum()
        for sym in buy_syms.index:
            net = buy_syms.get(sym,0) - sell_syms.get(sym,0)
            if net > 0:
                broker_buying.add(sym)
            elif net < 0:
                broker_selling.add(sym)

    # 2. Net buying pressure per stock from floorsheet
    stock_pressure = {}
    for sym, grp in full_df.groupby('symbol'):
        buy_qty  = grp.groupby('buyer_broker')['quantity'].sum()
        sell_qty = grp.groupby('seller_broker')['quantity'].sum()
        all_b    = set(buy_qty.index) | set(sell_qty.index)
        net_qty  = sum(buy_qty.get(b,0) - sell_qty.get(b,0) for b in all_b)
        total_qty = grp['quantity'].sum()
        stock_pressure[sym] = net_qty / max(total_qty, 1) * 100

    # 3. Whale buying
    whale_buying = set()
    for sym, grp in full_df.groupby('symbol'):
        total_qty = grp['quantity'].sum()
        if total_qty < 500:
            continue
        buy_by = grp.groupby('buyer_broker')['quantity'].sum()
        if not buy_by.empty:
            top_share = buy_by.max() / total_qty * 100
            if top_share >= 40:
                whale_buying.add(sym)

    # Boost scores
    final_scores = []
    for r in quick_scores:
        sym   = r['symbol']
        score = r['score']
        boost_reasons = []

        # Top broker buying = +20 pts
        if sym in broker_buying:
            score += 20
            boost_reasons.append("Top broker buying")

        # Top broker selling = -15 pts
        if sym in broker_selling:
            score -= 15
            boost_reasons.append("Top broker selling")

        # Net buying pressure > 20% = +10 pts
        pressure = stock_pressure.get(sym, 0)
        if pressure > 20:
            score += 10
            boost_reasons.append(f"Net buy pressure {pressure:.0f}%")
        elif pressure < -20:
            score -= 10

        # Whale accumulating = +10 pts
        if sym in whale_buying:
            score += 10
            boost_reasons.append("Whale accumulating")

        all_reasons = r['reasons']
        if boost_reasons:
            all_reasons = ' | '.join(boost_reasons) + ' | ' + r['reasons']

        final_scores.append({
            'symbol':  sym,
            'score':   min(score, 100),
            'ltp':     r['ltp'],
            'change':  r['change'],
            'upside':  r['upside'],
            'reasons': all_reasons,
        })

    final_scores = sorted(final_scores, key=lambda x: x['score'], reverse=True)
    # Filter only high probability — score >= 50 and upside >= 10%
    final_scores = [r for r in final_scores if r['score'] >= 50 and r['upside'] >= 10]

    if not final_scores:
        console.print("[yellow]No high-probability picks today. Market may be extended.[/yellow]")
        return

    t = Table(title="Smart Pick — High Probability 10%+ Gain",
              box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    t.add_column("#",          width=3,  justify="right", style="dim")
    t.add_column("Symbol",     width=10, style="bold white")
    t.add_column("LTP",        width=13, justify="right", no_wrap=True)
    t.add_column("Today",      width=10, justify="right", no_wrap=True)
    t.add_column("Upside",     width=10, justify="right", style="cyan")
    t.add_column("Score",      width=8,  justify="right", style="magenta")
    t.add_column("Confidence", width=14)
    t.add_column("Why",        min_width=35, style="dim white")

    for i, r in enumerate(final_scores[:top_n], 1):
        sc = r['score']
        if sc >= 80:
            conf = "[green]HIGH[/green]"
        elif sc >= 65:
            conf = "[yellow]MODERATE[/yellow]"
        else:
            conf = "[dim]SPECULATIVE[/dim]"

        upside_s = f"[green]+{r['upside']:.1f}%[/green]"

        t.add_row(
            str(i),
            r['symbol'],
            f"Rs {r['ltp']:,.2f}",
            color_change(r['change']),
            upside_s,
            f"{sc}/100",
            conf,
            r['reasons'][:60],
        )

    console.print(t)
    console.print(Panel(
        f"[bold]Found {len(final_scores)} high-probability candidates[/bold]\n"
        "[dim]Score 80+  = HIGH confidence — multiple signals + broker confirmation\n"
        "Score 65-79 = MODERATE — good signals, some broker activity\n"
        "Score 50-64 = SPECULATIVE — signals present but less confirmation\n"
        "Upside = distance to 52W high (realistic target in 1 month)[/dim]",
        border_style="cyan"
    ))

# ── MAIN ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="NEPSE Scanner — Full Edition")
    p.add_argument('--signals',     nargs='+', choices=list(SIGNALS.keys()), default=list(SIGNALS.keys()))
    p.add_argument('--top',         type=int, default=15)
    p.add_argument('--floor',       nargs='+', metavar='SYMBOL')
    p.add_argument('--brokers',     action='store_true')
    p.add_argument('--powersell',   action='store_true')
    p.add_argument('--sector-trend', action='store_true', help='Sector momentum 5/10/20d')
    p.add_argument('--heatmap',      action='store_true', help='Sector heatmap')
    p.add_argument('--sector',      action='store_true')
    p.add_argument('--whale',       action='store_true')
    p.add_argument('--sr',          nargs='+', metavar='SYMBOL')
    p.add_argument('--watchlist',   action='store_true')
    p.add_argument('--broker',      type=str, metavar='ID', help='Track a specific broker e.g. --broker 58')
    p.add_argument('--quickpick',   action='store_true', help='Quick stock pick — signals only')
    p.add_argument('--smartpick',   action='store_true', help='Smart stock pick — signals + broker + whale')
    p.add_argument('--report',      action='store_true')
    p.add_argument('--offline',     action='store_true', help='Use DB data instead of live API')
    p.add_argument('--movers-only', action='store_true')
    p.add_argument('--legend',      action='store_true')
    p.add_argument('--guide',       action='store_true', dest='buy_sell_guide')
    p.add_argument('--full-report',  metavar='SYMBOL', dest='full_report', default=None)
    p.add_argument('--best-rr',       action='store_true', dest='best_rr', help='Best R/R scanner')
    p.add_argument('--sector-season', action='store_true', dest='sector_season', help='Sector seasonality')
    p.add_argument('--market-phase',   action='store_true', dest='market_phase', help='Market phase detector')
    p.add_argument('--seasonality',    action='store_true', dest='seasonality', help='Seasonality analysis')
    p.add_argument('--nepali-season', action='store_true', dest='nepali_season', help='Nepali calendar seasonality')
    p.add_argument('--portfolio',   nargs='*', metavar='SYMBOL', help='Position sizing + correlation for a set of stocks')
    p.add_argument('--corr',        action='store_true', help='Sector correlation heatmap')
    p.add_argument('--size',        nargs=2, metavar=('SYMBOL','AMOUNT'), help='Volatility-adjusted sizing e.g. --size AKJCL 100000')
    p.add_argument('--broker-rs',   action='store_true', help='Broker accumulation on RS leaders')
    p.add_argument('--week52',       action='store_true', help='52-week high/low alerts + RS cross-check')
    p.add_argument('--rs',           action='store_true', help='Relative strength vs sector')
    p.add_argument('--why',          action='store_true', help='Show Why block — broker+RS+52W+unlock reasoning')
    p.add_argument('--fundamental', metavar='SYMBOL', help='Fundamental snapshot e.g. --fundamental NABIL')
    p.add_argument('--earnings',    metavar='SYMBOL', help='Quarterly earnings e.g. --earnings AKJCL')
    p.add_argument('--value',       nargs='?', const='ALL', metavar='SECTOR', help='Peer value screen e.g. --value or --value Hydropower')
    p.add_argument('--float',       metavar='SYMBOL', dest='float_sym', help='Float vs promoter e.g. --float NABIL')
    p.add_argument('--unlock',      nargs='+', metavar='ARG', help='Unlock dates: list/upcoming/add')
    p.add_argument('--broker-date', nargs=2, metavar=('SYMBOL', 'DATE'), default=None, help='Broker activity for a stock on a specific date')
    p.add_argument('--broker-trend', metavar='SYMBOL', default=None, help='7-day broker trend analysis')
    p.add_argument('--broker-impact', action='store_true', default=False, help='Broker impact ranking')
    p.add_argument('--momentum-hunter',action='store_true',default=False,help='Momentum hunter')
    p.add_argument('--broker-holders', metavar='SYMBOL', default=None, help='Top 15 broker holders for a stock')
    p.add_argument('--preopen', nargs='*', metavar='SYMBOL', help='Pre-open band calculator')
    return p.parse_args()



# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  PHASE 5 — PORTFOLIO INTELLIGENCE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def _get_returns(symbols, days=60):
    """Return a dict {symbol: pd.Series of daily pct returns} for the last N days."""
    import sqlite3, pandas as pd
    # Use absolute path so it works from any working directory
    _db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nepse_market_data.db')
    conn = sqlite3.connect(_db)
    placeholders = ','.join('?' * len(symbols))
    # Use hardcoded recent cutoff to avoid SQLite date() issues
    import datetime
    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    df = pd.read_sql_query(f"""
        SELECT symbol, date, close FROM stock_prices
        WHERE symbol IN ({placeholders})
          AND date >= ?
        ORDER BY symbol, date
    """, conn, params=symbols + [cutoff])
    conn.close()
    if df.empty:
        return {}
    pivot = df.pivot(index='date', columns='symbol', values='close')
    returns = pivot.pct_change(fill_method=None).dropna(how='all')
    result = {}
    for col in returns.columns:
        s = returns[col].dropna()
        if len(s) >= 5:  # need at least 5 data points
            result[col] = s
    return result


def analyze_portfolio(symbols):
    """--portfolio SYM1 SYM2 ... — position sizing + correlation + diversification."""
    import sqlite3, math
    import pandas as pd
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()
    console.print()
    console.print(f"[bold cyan]{'─'*30} Portfolio Intelligence {'─'*30}[/bold cyan]")

    if not symbols:
        import sqlite3 as _sq
        _conn = _sq.connect("nepse_market_data.db")
        _cur = _conn.cursor()
        _cur.execute("SELECT DISTINCT symbol FROM portfolio_positions WHERE status='open'")
        pp = [r[0] for r in _cur.fetchall()]
        _cur.execute("SELECT DISTINCT symbol FROM watchlist_items")
        wl = [r[0] for r in _cur.fetchall()]
        _conn.close()
        symbols = list(dict.fromkeys(pp + wl))
        if not symbols:
            console.print("[yellow]No symbols found. Use: --portfolio AKJCL BUNGAL[/yellow]")
            return
        console.print(f"[dim]  Auto-loaded {len(symbols)} symbols from watchlist/portfolio[/dim]")
    else:
        symbols = [s.upper() for s in symbols]

    # ── Price data ──────────────────────────────────────────────────────────
    returns_map = _get_returns(symbols, days=90)
    missing = [s for s in symbols if s not in returns_map]
    if missing:
        console.print(f"[yellow]No price data for: {', '.join(missing)}[/yellow]")
        symbols = [s for s in symbols if s in returns_map]
    if not symbols:
        console.print("[red]No valid symbols.[/red]")
        return

    # ── Volatility & stats per symbol ───────────────────────────────────────
    import numpy as np
    stats = {}
    for sym in symbols:
        r = returns_map[sym]
        vol   = r.std() * math.sqrt(252) * 100          # annualised vol %
        ret5  = ((1 + r.tail(5)).prod() - 1) * 100      # 5d return
        ret20 = ((1 + r.tail(20)).prod() - 1) * 100     # 20d return
        sharpe = (r.mean() / r.std() * math.sqrt(252)) if r.std() > 0 else 0
        stats[sym] = dict(vol=vol, ret5=ret5, ret20=ret20, sharpe=sharpe)

    # ── Inverse-volatility weights ───────────────────────────────────────────
    inv_vols = {s: 1 / max(stats[s]['vol'], 0.1) for s in symbols}
    total_inv = sum(inv_vols.values())
    weights = {s: inv_vols[s] / total_inv * 100 for s in symbols}

    # ── Correlation matrix (top 20 by weight only) ──────────────────────────
    top20 = sorted(symbols, key=lambda s: -weights[s])[:20]
    df_ret = pd.DataFrame({s: returns_map[s] for s in top20 if s in returns_map})
    corr = df_ret.corr(min_periods=10) if len(df_ret.columns) > 1 else None
    corr_symbols = list(df_ret.columns)

    # Average pairwise correlation → diversification score
    if corr is not None and len(corr_symbols) > 1:
        pairs = []
        for i, a in enumerate(corr_symbols):
            for j, b in enumerate(corr_symbols):
                if j > i:
                    v = corr.loc[a, b]
                    if v == v:  # skip NaN
                        pairs.append(v)
        avg_corr = float(np.mean(pairs)) if pairs else 0.0
        avg_corr = avg_corr if avg_corr == avg_corr else 0.0
        div_score = max(0, int((1 - avg_corr) * 100))
    else:
        avg_corr = 0
        div_score = 100

    # ── Table 1: Per-stock stats + suggested weight ──────────────────────────
    t1 = Table(title="Position Sizing (Inverse-Volatility Weighted)",
               box=box.SIMPLE_HEAD, show_lines=False)
    t1.add_column("Symbol",   style="bold white")
    t1.add_column("Ann.Vol%", justify="right")
    t1.add_column("5D Ret%",  justify="right")
    t1.add_column("20D Ret%", justify="right")
    t1.add_column("Sharpe",   justify="right")
    t1.add_column("Weight%",  justify="right", style="bold cyan")
    t1.add_column("Rs 1L →",  justify="right", style="bold green")

    for sym in sorted(symbols, key=lambda s: -weights[s]):
        s = stats[sym]
        w = weights[sym]
        color_5d  = "green" if s['ret5']  >= 0 else "red"
        color_20d = "green" if s['ret20'] >= 0 else "red"
        t1.add_row(
            sym,
            f"{s['vol']:.1f}%",
            f"[{color_5d}]{s['ret5']:+.1f}%[/{color_5d}]",
            f"[{color_20d}]{s['ret20']:+.1f}%[/{color_20d}]",
            f"{s['sharpe']:.2f}",
            f"{w:.1f}%",
            f"Rs {w*1000:.0f}",
        )
    console.print(t1)

    # ── Table 2: Correlation matrix ──────────────────────────────────────────
    if corr is not None and len(corr_symbols) > 1:
        t2 = Table(title=f"Correlation Matrix — Top {len(corr_symbols)} by Weight (60-day)",
                   box=box.SIMPLE_HEAD, show_lines=False)
        t2.add_column("", style="bold white")
        for sym in corr_symbols:
            t2.add_column(sym, justify="right")

        for a in corr_symbols:
            row = [a]
            for b in corr_symbols:
                v = corr.loc[a, b]
                if a == b:
                    row.append("[dim]  1.00[/dim]")
                elif v >= 0.8:
                    row.append(f"[red]{v:.2f}[/red]")
                elif v >= 0.5:
                    row.append(f"[yellow]{v:.2f}[/yellow]")
                else:
                    row.append(f"[green]{v:.2f}[/green]")
            t2.add_row(*row)
        console.print(t2)

    # ── Diversification score ────────────────────────────────────────────────
    if div_score >= 70:
        div_color = "green"
        div_label = "Well diversified"
    elif div_score >= 40:
        div_color = "yellow"
        div_label = "Moderate overlap"
    else:
        div_color = "red"
        div_label = "High overlap — consider swapping one stock"

    console.print(
        f"  Diversification Score: [{div_color}]{div_score}/100[/{div_color}]  "
        f"[dim]{div_label}  (avg pairwise corr: {avg_corr:.2f})[/dim]"
    )
    console.print()


def analyze_corr():
    """--corr — sector-level correlation heatmap across all stocks."""
    import sqlite3, os, datetime
    import pandas as pd, numpy as np
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()
    console.print()
    console.print(f"[bold cyan]{'─'*28} Sector Correlation Heatmap {'─'*28}[/bold cyan]")
    console.print("[dim]  How correlated are sectors? Red = move together, Green = independent[/dim]")
    console.print()

    _db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nepse_market_data.db')
    conn = sqlite3.connect(_db)

    sectors_df = pd.read_sql_query(
        "SELECT symbol, sector FROM companies WHERE sector IS NOT NULL", conn)
    sector_map = dict(zip(sectors_df.symbol, sectors_df.sector))

    cutoff = (datetime.date.today() - datetime.timedelta(days=75)).isoformat()
    df = pd.read_sql_query(
        "SELECT symbol, date, close FROM stock_prices WHERE date >= ? ORDER BY symbol, date",
        conn, params=[cutoff])
    conn.close()

    if df.empty:
        console.print("[red]No price data.[/red]")
        return

    pivot = df.pivot(index='date', columns='symbol', values='close')
    returns = pivot.pct_change(fill_method=None).dropna(how='all')

    # Build sector returns as mean of member stocks
    sectors = sorted(set(sector_map.values()))
    sector_returns = {}
    for sec in sectors:
        members = [s for s in returns.columns if sector_map.get(s) == sec]
        if len(members) >= 3:
            sr = returns[members].mean(axis=1)
            if sr.notna().sum() >= 10:
                sector_returns[sec] = sr

    if len(sector_returns) < 2:
        console.print("[yellow]Not enough sector data.[/yellow]")
        return

    sec_df = pd.DataFrame(sector_returns)
    corr = sec_df.corr(min_periods=10)
    sec_list = list(corr.columns)

    t = Table(box=box.SIMPLE_HEAD, show_lines=False)
    # Abbreviate sector names for column headers
    abbrev = {
        'Commercial Bank': 'ComBnk',
        'Development Bank': 'DevBnk',
        'Finance': 'Fin',
        'Hotel & Tourism': 'Hotel',
        'Hotels And Tourism': 'Hotel',
        'Hydropower': 'Hydro',
        'Hydro Power': 'Hydro',
        'Investment': 'Invest',
        'Life Insurance': 'LifeIns',
        'Manufacturing and Processing': 'Manuf',
        'Manufacturing And Processing': 'Manuf',
        'Microfinance': 'MicroFin',
        'Non-Life Insurance': 'NonLife',
        'Non Life Insurance': 'NonLife',
        'Others': 'Others',
        'Trading': 'Trade',
    }
    t.add_column("Sector", style="bold white", min_width=20, no_wrap=True)
    for s in sec_list:
        short = abbrev.get(s, s[:7])
        t.add_column(short, justify="right", min_width=6, no_wrap=True)

    # Short row labels
    row_abbrev = {
        'Commercial Bank': 'Commercial Bank',
        'Development Bank': 'Development Bank',
        'Finance': 'Finance',
        'Hotel & Tourism': 'Hotel & Tourism',
        'Hotels And Tourism': 'Hotel & Tourism',
        'Hydropower': 'Hydropower',
        'Hydro Power': 'Hydropower',
        'Investment': 'Investment',
        'Life Insurance': 'Life Insurance',
        'Manufacturing and Processing': 'Manufacturing & Processing',
        'Manufacturing And Processing': 'Manufacturing & Processing',
        'Microfinance': 'Microfinance',
        'Non-Life Insurance': 'Non-Life Insurance',
        'Non Life Insurance': 'Non-Life Insurance',
        'Others': 'Others',
        'Trading': 'Trading',
    }
    for a in sec_list:
        row = [row_abbrev.get(a, a)]
        for b in sec_list:
            v = corr.loc[a, b]
            if v != v:  # NaN
                row.append("[dim] ---[/dim]")
            elif a == b:
                row.append("[dim] 1.00[/dim]")
            elif v >= 0.85:
                row.append(f"[red]{v:.2f}[/red]")
            elif v >= 0.60:
                row.append(f"[yellow]{v:.2f}[/yellow]")
            else:
                row.append(f"[green]{v:.2f}[/green]")
        t.add_row(*row)

    console.print(t)
    console.print(
        "  [green]Green < 0.60[/green]  [yellow]Yellow 0.60-0.85[/yellow]  "
        "[red]Red > 0.85 (highly correlated)[/red]"
    )
    console.print()
    console.print("  [bold white]Portfolio Diversification Guide:[/bold white]")
    console.print("  [red]ðŸ”´ Red  > 0.85[/red]  — Move together always    → Avoid holding both, no diversification")
    console.print("  [yellow]ðŸŸ¡ Yellow 0.60-0.85[/yellow] — Move together usually  → Partial diversification, acceptable")
    console.print("  [green]ðŸŸ¢ Green < 0.60[/green]  — Move independently    → Best diversification, hold both")
    console.print()
    # Build recommendations from correlation data
    console.print("  [bold white]Sector Pair Recommendations:[/bold white]")
    pairs_red = []
    pairs_yellow = []
    pairs_green = []
    # Normalize correlation matrix sector names
    norm_map = {'Hotels And Tourism': 'Hotel & Tourism', 'Hydro Power': 'Hydropower', 'Manufacturing And Processing': 'Manufacturing & Processing', 'Non Life Insurance': 'Non-Life Insurance'}
    corr.index = [norm_map.get(s, s) for s in corr.index]
    corr.columns = [norm_map.get(s, s) for s in corr.columns]
    sec_list2 = list(corr.columns)
    for i in range(len(sec_list2)):
        for j in range(i+1, len(sec_list2)):
            a, b = sec_list2[i], sec_list2[j]
            v = corr.loc[a, b]
            if v != v:
                continue
            pair = f"{a} + {b}"
            if v >= 0.85:
                pairs_red.append((v, pair))
            elif v >= 0.60:
                pairs_yellow.append((v, pair))
            else:
                pairs_green.append((v, pair))
    pairs_red.sort()
    pairs_yellow.sort()
    pairs_green.sort(reverse=True)
    if pairs_green:
        console.print("  [green]âœ… Best pairs to hold together (independent):[/green]")
        for v, p in pairs_green[:5]:
            console.print(f"     {p}  ({v:.2f})")
    else:
        console.print("  [yellow]⚠ï¸  No green pairs in NEPSE — all sectors are correlated[/yellow]")
        console.print("  [yellow]   Best available pairs (lowest correlation):[/yellow]")
        for v, p in pairs_yellow[:5]:
            console.print(f"     [green]{p}  ({v:.2f})[/green]")
    console.print()
    console.print("  [red]âŒ Avoid holding together (move in sync):[/red]")
    for v, p in sorted(pairs_red, reverse=True)[:5]:
        console.print(f"     [red]{p}  ({v:.2f})[/red]")
    console.print()
def analyze_size(symbol, capital):
    """--size SYM AMOUNT — volatility-adjusted position sizing."""
    import sqlite3, math
    import pandas as pd
    from rich.console import Console
    from rich import box
    from rich.table import Table

    console = Console()
    symbol = symbol.upper()
    console.print()
    console.print(f"[bold cyan]{'─'*30} Position Sizer: {symbol} {'─'*30}[/bold cyan]")

    conn = sqlite3.connect('nepse_market_data.db')
    df = pd.read_sql_query("""
        SELECT date, close, high, low FROM stock_prices
        WHERE symbol = ? AND date >= date('now', '-90 days')
        ORDER BY date
    """, conn, params=[symbol])
    conn.close()

    if df.empty or len(df) < 10:
        console.print(f"[red]No price data for {symbol}.[/red]")
        return

    ltp = df['close'].iloc[-1]
    returns = df['close'].pct_change().dropna()
    daily_vol = returns.std()
    ann_vol   = daily_vol * math.sqrt(252) * 100

    # ATR (14-day)
    df['tr'] = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift()).abs(),
        (df['low']  - df['close'].shift()).abs(),
    ], axis=1).max(axis=1)
    atr = df['tr'].tail(14).mean()

    # Risk-based sizing (1% account risk per trade, 2xATR stop)
    stop_distance = atr * 2
    risk_amt_1pct = capital * 0.01
    risk_amt_2pct = capital * 0.02
    shares_1pct = int(risk_amt_1pct / stop_distance) if stop_distance > 0 else 0
    shares_2pct = int(risk_amt_2pct / stop_distance) if stop_distance > 0 else 0
    cost_1pct = shares_1pct * ltp
    cost_2pct = shares_2pct * ltp

    # Kelly fraction (simplified)
    win_rate = (returns > 0).mean()
    avg_win  = returns[returns > 0].mean() if (returns > 0).any() else 0
    avg_loss = abs(returns[returns < 0].mean()) if (returns < 0).any() else 0.001
    kelly = win_rate - (1 - win_rate) / (avg_win / avg_loss) if avg_loss > 0 else 0
    kelly_pct = max(0, min(kelly * 100, 25))  # cap at 25%
    kelly_amt = capital * kelly_pct / 100
    kelly_shares = int(kelly_amt / ltp)

    t = Table(box=box.SIMPLE_HEAD, show_lines=False)
    t.add_column("Method",        style="bold white", min_width=28)
    t.add_column("Shares",        justify="right", style="bold cyan")
    t.add_column("Capital Used",  justify="right", style="bold green")
    t.add_column("% of Capital",  justify="right")

    t.add_row("1% Risk / 2Ã—ATR stop",
              str(shares_1pct), f"Rs {cost_1pct:,.0f}", f"{cost_1pct/capital*100:.1f}%")
    t.add_row("2% Risk / 2Ã—ATR stop",
              str(shares_2pct), f"Rs {cost_2pct:,.0f}", f"{cost_2pct/capital*100:.1f}%")
    t.add_row(f"Half-Kelly ({kelly_pct/2:.1f}%)",
              str(kelly_shares//2), f"Rs {kelly_shares//2*ltp:,.0f}",
              f"{kelly_shares//2*ltp/capital*100:.1f}%")

    console.print(t)
    console.print(
        f"  LTP: Rs {ltp:.1f}  |  ATR(14): Rs {atr:.1f}  |  "
        f"Ann.Vol: {ann_vol:.1f}%  |  Stop level: Rs {ltp - stop_distance:.1f}"
    )
    console.print(
        f"  [dim]Capital: Rs {capital:,.0f}  |  "
        f"Win rate(60d): {win_rate*100:.0f}%[/dim]"
    )
    console.print()


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
        for table in ["stock_prices", "daily_prices", "prices", "market_data"]:
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

def analyze_full_stock_report(symbol=None, db_path='nepse_market_data.db'):
    """Option 35 - Full Stock Report: Fundamentals + Supply + Brokers + Technical + Verdict"""
    from rich.table import Table
    from rich.rule import Rule
    from rich.panel import Panel
    import sqlite3

    if not symbol:
        console.print()
        symbol = input('  Enter stock symbol (e.g. NABIL): ').strip().upper()
    if not symbol:
        console.print('  Missing symbol.', style='yellow')
        return

    console.print()
    console.rule(f'[bold cyan]Full Stock Report — {symbol}[/bold cyan]', style='cyan')
    console.print()

    conn = sqlite3.connect(db_path)
    total_score = 0
    max_score = 0
    section_verdicts = []

    # ─────────────────────────────────────────
    # SECTION 1 — FUNDAMENTALS
    # ─────────────────────────────────────────
    console.rule('[bold yellow]Section 1 — Fundamentals[/bold yellow]', style='yellow')
    console.print()
    fund_score = 0
    try:
        f = conn.execute(
            'SELECT eps, book_value_per_share, pe_ratio, pb_ratio, roe, market_cap, sector, shares_outstanding '
            'FROM fundamentals WHERE symbol=? ORDER BY date DESC LIMIT 1',
            (symbol,)
        ).fetchone()

        quarters = conn.execute(
            'SELECT fiscal_year, quarter, eps, book_value, net_profit FROM quarterly_earnings '
            'WHERE symbol=? ORDER BY fiscal_year DESC, quarter DESC LIMIT 4',
            (symbol,)
        ).fetchall()

        if f:
            eps, bv, pe, pb, roe, mcap, sector, shares_outstanding = f
            console.print(f'  Sector: [cyan]{sector}[/cyan]')
            console.print(f'  Market Cap: [white]{_fmt_rs_val(mcap) if mcap else "N/A"}[/white]')
            console.print()

            # Helper: estimate EPS from net_profit if eps column is null
            def _calc_eps(net_profit, shares):
                if net_profit and shares and shares > 0:
                    return net_profit / shares
                return None

            # EPS trend
            if len(quarters) >= 2:
                q_label = f'FY{quarters[0][0]} Q{quarters[0][1]}'
                q_prev_label = f'FY{quarters[1][0]} Q{quarters[1][1]}'
                eps_curr = quarters[0][2] or _calc_eps(quarters[0][4], shares_outstanding)
                eps_prev = quarters[1][2] or _calc_eps(quarters[1][4], shares_outstanding)
                eps_src = '' if quarters[0][2] else ' [dim](est. from net profit)[/dim]'
                if eps_curr and eps_prev:
                    eps_chg = ((eps_curr - eps_prev) / abs(eps_prev)) * 100
                    eps_col = 'green' if eps_chg > 0 else 'red'
                    eps_arrow = '+' if eps_chg > 0 else ''
                    if abs(eps_chg) > 500:
                        console.print(f'  EPS: [{eps_col}]Rs {eps_curr:.2f} vs Rs {eps_prev:.2f} prev quarter (large swing)[/{eps_col}] [dim]({q_label})[/dim]{eps_src}')
                    else:
                        console.print(f'  EPS: [{eps_col}]Rs {eps_curr:.2f} ({eps_arrow}{eps_chg:.1f}% vs {q_prev_label})[/{eps_col}] [dim]({q_label})[/dim]{eps_src}')
                    if eps_chg > 10: fund_score += 25
                    elif eps_chg > 0: fund_score += 15
                    else: fund_score -= 10
                elif eps_curr:
                    console.print(f'  EPS: Rs {eps_curr:.2f} [dim]({q_label} — prev quarter no data)[/dim]{eps_src}')
                    if eps_curr > 0: fund_score += 10
                else:
                    console.print('  EPS: N/A')
            elif eps:
                q_label = f'FY{quarters[0][0]} Q{quarters[0][1]}' if quarters else 'latest'
                console.print(f'  EPS: Rs {eps:.2f} [dim]({q_label})[/dim]')
                if eps > 0: fund_score += 10

            # Book Value trend
            if len(quarters) >= 2 and quarters[0][3] and quarters[1][3]:
                bv_curr = quarters[0][3]
                bv_prev = quarters[1][3]
                q_label = f'FY{quarters[0][0]} Q{quarters[0][1]}'
                q_prev_label = f'FY{quarters[1][0]} Q{quarters[1][1]}'
                bv_chg = ((bv_curr - bv_prev) / abs(bv_prev)) * 100
                bv_col = 'green' if bv_chg > 0 else 'red'
                bv_arrow = '+' if bv_chg > 0 else ''
                console.print(f'  Book Value: [{bv_col}]Rs {bv_curr:.2f} ({bv_arrow}{bv_chg:.1f}% vs {q_prev_label})[/{bv_col}] [dim]({q_label})[/dim]')
                if bv_chg > 0: fund_score += 15
            elif bv:
                q_label = f'FY{quarters[0][0]} Q{quarters[0][1]}' if quarters else 'latest'
                if len(quarters) >= 2 and quarters[0][4] and quarters[1][4]:
                    np_chg = ((quarters[0][4] - quarters[1][4]) / abs(quarters[1][4])) * 100
                    np_col = 'green' if np_chg > 0 else 'red'
                    np_arrow = '+' if np_chg > 0 else ''
                    np_disp = min(np_chg, 999.9) if np_chg > 0 else max(np_chg, -999.9)
                    q_prev_label = f'FY{quarters[1][0]} Q{quarters[1][1]}'
                    if abs(np_chg) > 500:
                        np_curr_m = quarters[0][4]/1000000
                        np_prev_m = quarters[1][4]/1000000
                        console.print(f'  Book Value: Rs {bv:.2f} [dim]({q_label})[/dim]  Net Profit: [{np_col}]Rs {np_curr_m:.1f}M vs Rs {np_prev_m:.1f}M prev (large swing)[/{np_col}]')
                    else:
                        console.print(f'  Book Value: Rs {bv:.2f} [dim]({q_label})[/dim]  Net Profit: [{np_col}]{np_arrow}{np_disp:.1f}% vs {q_prev_label}[/{np_col}]')
                else:
                    console.print(f'  Book Value: Rs {bv:.2f} [dim]({q_label})[/dim]')
                if bv > 0: fund_score += 10

            # PE and ROE
            if pe:
                pe_col = 'green' if pe < 20 else 'yellow' if pe < 35 else 'red'
                console.print(f'  PE Ratio: [{pe_col}]{pe:.1f}x[/{pe_col}] {"(cheap)" if pe < 20 else "(fair)" if pe < 35 else "(expensive)"}')
                if pe < 20: fund_score += 20
                elif pe < 35: fund_score += 10
            if roe:
                roe_col = 'green' if roe > 15 else 'yellow' if roe > 8 else 'red'
                console.print(f'  ROE: [{roe_col}]{roe:.1f}%[/{roe_col}] {"(strong)" if roe > 15 else "(moderate)" if roe > 8 else "(weak)"}')
                if roe > 15: fund_score += 15
                elif roe > 8: fund_score += 8

            fund_score = max(0, min(100, fund_score))
            f_verdict = 'STRONG' if fund_score >= 60 else 'MODERATE' if fund_score >= 35 else 'WEAK'
            f_col = 'green' if fund_score >= 60 else 'yellow' if fund_score >= 35 else 'red'
            console.print()
            console.print(f'  Fundamentals Score: [{f_col}]{fund_score}/100 — {f_verdict}[/{f_col}]')
            section_verdicts.append(('Fundamentals', fund_score, f_verdict, f_col))
            total_score += fund_score
            max_score += 100
        else:
            console.print(f'  No fundamental data for {symbol}. Run option 34 first.', style='yellow')
            section_verdicts.append(('Fundamentals', 0, 'NO DATA', 'dim'))
            max_score += 100
    except Exception as e:
        console.print(f'  Error: {e}', style='red')
        max_score += 100

    # ─────────────────────────────────────────
    # SECTION 2 — SUPPLY POWER
    # ─────────────────────────────────────────
    console.print()
    console.rule('[bold yellow]Section 2 — Supply Power[/bold yellow]', style='yellow')
    console.print()
    supply_score = 50
    try:
        f2 = conn.execute(
            'SELECT shares_outstanding, sector, promoter_pct, public_shares, promoter_shares FROM fundamentals WHERE symbol=? ORDER BY date DESC LIMIT 1',
            (symbol,)
        ).fetchone()
        shares_out = f2[0] if f2 and f2[0] else None
        sector_name = f2[1] if f2 and f2[1] else ''
        promoter_pct = (f2[2] / 100) if f2 and f2[2] else 0.51
        real_public_shares = f2[3] if f2 and f2[3] else None
        real_promoter_shares = f2[4] if f2 and f2[4] else None

        # Check if still locked from unlock_dates
        unlock_row = conn.execute(
            'SELECT unlock_date, note FROM unlock_dates WHERE symbol=? ORDER BY unlock_date DESC LIMIT 1',
            (symbol,)
        ).fetchone()

        from datetime import date as _date
        today_str = str(_date.today())
        still_locked = False
        unlock_info = ''
        if unlock_row:
            unlock_date = unlock_row[0]
            note = unlock_row[1] or ''
            if 'STILL_LOCKED' in note and unlock_date > today_str:
                still_locked = True
                unlock_info = f'locked till {unlock_date}'
            elif unlock_date <= today_str:
                unlock_info = f'unlocked since {unlock_date}'
            else:
                unlock_info = f'unlocks {unlock_date}'

        # Calculate real tradeable float
        if shares_out:
            if still_locked:
                locked_shares = real_promoter_shares if real_promoter_shares else shares_out * promoter_pct
                tradeable_float = real_public_shares if real_public_shares else shares_out - locked_shares
                lock_col = 'yellow'
            else:
                locked_shares = 0
                tradeable_float = shares_out
                lock_col = 'green'

            console.print(f'  Total Listed Shares: [white]{shares_out:,.0f}[/white]')
            if still_locked:
                console.print(f'  Promoter Locked: [{lock_col}]{locked_shares:,.0f} ({promoter_pct*100:.1f}%) — {unlock_info}[/{lock_col}]')
                console.print(f'  Real Tradeable Float: [cyan]{tradeable_float:,.0f} shares ({100-promoter_pct*100:.1f}% public)[/cyan]')
            else:
                console.print(f'  Lock-in Status: [green]UNLOCKED ({unlock_info})[/green]')
                console.print(f'  Real Tradeable Float: [green]{shares_out:,.0f} shares (all tradeable)[/green]')
        else:
            tradeable_float = None

        # Recent volume from broker_activity
        vol_rows = conn.execute(
            'SELECT date, SUM(buy_qty) as total_vol FROM broker_activity '
            'WHERE symbol=? AND broker_id GLOB "[0-9]*" GROUP BY date ORDER BY date DESC LIMIT 10',
            (symbol,)
        ).fetchall()

        if vol_rows:
            vols = [r[1] for r in vol_rows if r[1]]
            avg_vol = sum(vols) / len(vols) if vols else 0
            latest_vol = vols[0] if vols else 0
            vol_ratio = latest_vol / avg_vol if avg_vol > 0 else 1

            # Volume ratio scoring
            if vol_ratio >= 3.0: supply_score += 30
            elif vol_ratio >= 2.0: supply_score += 20
            elif vol_ratio >= 1.5: supply_score += 10
            elif vol_ratio < 0.8: supply_score -= 10
            elif vol_ratio < 0.5: supply_score -= 20

            vol_col = 'green' if vol_ratio >= 1.5 else 'yellow' if vol_ratio >= 0.8 else 'red'
            console.print(f'  Latest Day Volume: [{vol_col}]{latest_vol:,.0f}[/{vol_col}]')
            console.print(f'  Avg Volume (10d): [white]{avg_vol:,.0f}[/white]')
            console.print(f'  Volume Ratio: [{vol_col}]{vol_ratio:.1f}x avg[/{vol_col}] {"(HIGH demand)" if vol_ratio >= 1.5 else "(normal)" if vol_ratio >= 0.8 else "(LOW demand)"}')

            # Use correct base for float calculation
            # If locked: use public_shares only
            # If unlocked: use total shares (all tradeable)
            base_shares = tradeable_float if (still_locked and tradeable_float) else shares_out

            if base_shares and avg_vol > 0:
                float_pct = (avg_vol / base_shares) * 100

                # Float turnover scoring
                if float_pct < 0.5: supply_score += 25
                elif float_pct < 1.5: supply_score += 15
                elif float_pct < 3.0: supply_score += 5
                elif float_pct < 5.0: supply_score -= 10
                else: supply_score -= 20

                float_label = 'ILLIQUID' if float_pct < 0.5 else 'LOW LIQUID' if float_pct < 1.5 else 'LIQUID' if float_pct < 3 else 'HIGH LIQUID' if float_pct < 5 else 'HYPER LIQUID'
                float_col = 'green' if float_pct < 1.5 else 'yellow' if float_pct < 3 else 'cyan' if float_pct < 5 else 'blue'
                float_base = 'public float' if still_locked else 'total shares'
                console.print(f'  Float Turnover: [{float_col}]{float_pct:.2f}% of {float_base}[/{float_col}] — {float_label}')

            # Float Market Cap
            cur_price = conn.execute(
                'SELECT close_price FROM market_quotes WHERE symbol=? ORDER BY fetched_at_utc DESC LIMIT 1',
                (symbol,)
            ).fetchone()
            if cur_price and cur_price[0] and base_shares:
                float_mcap = base_shares * cur_price[0]
                float_mcap_m = float_mcap / 1_000_000
                if float_mcap < 200_000_000:
                    cap_label = 'MICRO CAP'
                    cap_col = 'red'
                elif float_mcap < 1_000_000_000:
                    cap_label = 'SMALL CAP'
                    cap_col = 'yellow'
                elif float_mcap < 5_000_000_000:
                    cap_label = 'MID CAP'
                    cap_col = 'cyan'
                elif float_mcap < 15_000_000_000:
                    cap_label = 'LARGE CAP'
                    cap_col = 'green'
                else:
                    cap_label = 'MEGA CAP'
                    cap_col = 'bold green'

                cap_note = '(locked float only)' if still_locked else '(full float)'
                console.print(f'  Float Market Cap: [{cap_col}]Rs {float_mcap_m:,.0f}M — {cap_label}[/{cap_col}] [dim]{cap_note}[/dim]')

        supply_score = max(0, min(100, supply_score))
        s_verdict = 'TIGHT' if supply_score >= 65 else 'NORMAL' if supply_score >= 40 else 'HEAVY'
        s_col = 'green' if supply_score >= 65 else 'yellow' if supply_score >= 40 else 'red'
        console.print()
        console.print(f'  Supply Score: [{s_col}]{supply_score}/100 — {s_verdict} supply[/{s_col}]')
        section_verdicts.append(('Supply Power', supply_score, s_verdict, s_col))
        total_score += supply_score
        max_score += 100
    except Exception as e:
        console.print(f'  Error: {e}', style='red')
        max_score += 100

    # ─────────────────────────────────────────
    # SECTION 3 — TOP BROKER ACTIVITY
    # ─────────────────────────────────────────
    console.print()
    console.rule('[bold yellow]Section 3 — Top Broker Activity[/bold yellow]', style='yellow')
    console.print()
    broker_score = 50
    try:
        broker_score_done = False
    except Exception as e:
        console.print(f'  Error in broker section: {e}', style='red')
        broker_score_done = False

    broker_score = 50
    try:
        # Top holders from broker_holdings
        # Calculate estimated current holders from broker_activity (dynamic, updates daily)
        holders = conn.execute(
            '''SELECT broker_id,
                SUM(buy_qty) as total_bought,
                SUM(sell_qty) as total_sold,
                SUM(buy_qty) - SUM(sell_qty) as net_held,
                CASE WHEN SUM(buy_qty)>0 THEN SUM(buy_val)/SUM(buy_qty) ELSE 0 END as avg_buy
            FROM broker_activity
            WHERE symbol=? AND broker_id GLOB "[0-9]*"
            GROUP BY broker_id
            HAVING net_held > 0
            ORDER BY net_held DESC LIMIT 5''',
            (symbol,)
        ).fetchall()
        latest_date = conn.execute(
            'SELECT MAX(date) FROM broker_activity WHERE symbol=? AND broker_id GLOB "[0-9]*"',
            (symbol,)
        ).fetchone()[0] or 'unknown'
        if holders:
            console.print(f'  [bold]Top Estimated Holders:[/bold] [dim](calculated from all activity up to {latest_date})[/dim]')
            for h in holders:
                console.print(f'    Broker {h[0]} — est. holds {h[3]:,.0f} shares (avg buy Rs {h[4]:,.1f}, bought {h[1]:,.0f} sold {h[2]:,.0f})')
            console.print()
        else:
            console.print(f'  [dim]No holder data available from broker activity[/dim]')
            console.print()

        # Recent broker activity trend
        dates = conn.execute(
            'SELECT DISTINCT date FROM broker_activity WHERE symbol=? '
            'AND broker_id GLOB "[0-9]*" ORDER BY date DESC LIMIT 5',
            (symbol,)
        ).fetchall()
        dates = [d[0] for d in dates]

        buy_days = 0
        sell_days = 0
        dominant_buy_days = 0
        dominant_sell_days = 0
        for d in dates:
            # Broker count
            counts = conn.execute(
                'SELECT COUNT(CASE WHEN net_val>0 THEN 1 END), COUNT(CASE WHEN net_val<0 THEN 1 END) '
                'FROM broker_activity WHERE symbol=? AND date=? AND broker_id GLOB "[0-9]*"',
                (symbol, d)
            ).fetchone()
            nb = counts[0] or 0
            ns = counts[1] or 0
            if nb > ns: buy_days += 1
            else: sell_days += 1

            # Dominant flow - biggest single player
            dom = conn.execute(
                'SELECT net_val FROM broker_activity WHERE symbol=? AND date=? '
                'AND broker_id GLOB "[0-9]*" ORDER BY ABS(net_val) DESC LIMIT 1',
                (symbol, d)
            ).fetchone()
            if dom and dom[0] and dom[0] > 0: dominant_buy_days += 1
            else: dominant_sell_days += 1

        bd_col = 'green' if buy_days > sell_days else 'red'
        console.print(f'  Broker count ({len(dates)} days): [{bd_col}]{buy_days} buy days, {sell_days} sell days[/{bd_col}]')
        dom_col = 'green' if dominant_buy_days > dominant_sell_days else 'red'
        console.print(f'  Dominant flow ({len(dates)} days): [{dom_col}]{dominant_buy_days} dominant buyer days, {dominant_sell_days} dominant seller days[/{dom_col}]')

        # Score uses both
        if buy_days > sell_days: broker_score += 15
        else: broker_score -= 15
        if dominant_buy_days > dominant_sell_days: broker_score += 10
        else: broker_score -= 10

        # Net buyers from DB
        _all = conn.execute(
            'SELECT broker_id, SUM(CASE WHEN net_val>0 THEN net_val ELSE 0 END) as tb, '
            'SUM(CASE WHEN net_val<0 THEN ABS(net_val) ELSE 0 END) as ts '
            'FROM broker_activity WHERE broker_id GLOB "[0-9]*" GROUP BY broker_id',
        ).fetchall()
        _net_buyers = set(str(r[0]) for r in sorted(_all, key=lambda x: x[1]-x[2], reverse=True)[:8] if r[1] > r[2])

        # Check if known net buyers active in this stock
        recent = conn.execute(
            'SELECT broker_id, SUM(net_val) as nv FROM broker_activity '
            'WHERE symbol=? AND broker_id GLOB "[0-9]*" '
            'AND date IN ({}) GROUP BY broker_id'.format(','.join(['?']*len(dates))),
            [symbol] + dates
        ).fetchall()

        active_buyers = [str(r[0]) for r in recent if str(r[0]) in _net_buyers and (r[1] or 0) > 0]
        if active_buyers:
            console.print(f'  [green]Known NET BUYERS active: Broker {", ".join(active_buyers)} — STRONG signal[/green]')
            broker_score += 30
        else:
            console.print('  [dim]No known market-wide net buyers active recently[/dim]')

        if buy_days > sell_days: broker_score += 20
        else: broker_score -= 20

        # ── Holder vs Seller comparison (latest date) ──
        try:
            latest = conn.execute(
                'SELECT MAX(date) FROM broker_activity WHERE symbol=? AND broker_id GLOB "[0-9]*"',
                (symbol,)
            ).fetchone()[0]
            if latest and holders:
                _holder_ids = set(str(h[0]) for h in holders)
                latest_rows = conn.execute(
                    'SELECT broker_id, net_val, net_qty FROM broker_activity '
                    'WHERE symbol=? AND date=? AND broker_id GLOB "[0-9]*"',
                    (symbol, latest)
                ).fetchall()

                # Market-wide net sellers
                _mkt_sellers = set(str(r[0]) for r in _all if r[2] > r[1])

                # Your holders activity today
                _buying_holders  = [(str(r[0]), r[1]) for r in latest_rows if str(r[0]) in _holder_ids and r[1] > 0]
                _selling_holders = [(str(r[0]), r[1]) for r in latest_rows if str(r[0]) in _holder_ids and r[1] < 0]

                # Net sellers selling this stock today
                _smart_selling = [(str(r[0]), r[1]) for r in latest_rows
                    if str(r[0]) in _mkt_sellers and r[1] < 0 and str(r[0]) not in _holder_ids]
                _smart_selling.sort(key=lambda x: x[1])

                total_holder_buy  = sum(nv for _, nv in _buying_holders)
                total_smart_sell  = sum(abs(nv) for _, nv in _smart_selling)
                net_flow_today    = total_holder_buy - total_smart_sell

                console.print(f'  [bold]Latest date ({latest}) holder vs seller:[/bold]')
                if _buying_holders:
                    console.print(f'  [green]Your holders buying:  Rs {total_holder_buy/1e6:.2f}M[/green]')
                if _selling_holders:
                    console.print(f'  [red]Your holders SELLING: Rs {sum(abs(nv) for _,nv in _selling_holders)/1e6:.2f}M  <- WARNING[/red]')
                if _smart_selling:
                    console.print(f'  [red]Net sellers selling:  Rs {total_smart_sell/1e6:.2f}M ({len(_smart_selling)} brokers)[/red]')
                    nf_col = 'green' if net_flow_today > 0 else 'red'
                    console.print(f'  Net flow:             [{nf_col}]Rs {net_flow_today/1e6:.2f}M[/{nf_col}] {"(holders winning)" if net_flow_today > 0 else "(sellers winning)"}')

                # Adjust broker score based on net flow
                if _selling_holders:
                    broker_score -= 20
                elif net_flow_today > 0:
                    broker_score += 10
                elif total_smart_sell > total_holder_buy * 1.5:
                    broker_score -= 15

                console.print()

                # Verdict
                _total_hbuy  = sum(r[1] for r in latest_rows if str(r[0]) in _holder_ids and r[1] > 0)
                _total_hsell = sum(abs(r[1]) for r in latest_rows if str(r[0]) in _holder_ids and r[1] < 0)
                _sell_ratio  = _total_hsell / _total_hbuy if _total_hbuy > 0 else 0
                if _selling_holders and _sell_ratio > 0.10:
                    console.print('  [bold red]ALERT: Your holders selling today — exit signal![/bold red]')
                elif _smart_selling and total_smart_sell > total_holder_buy * 1.5:
                    console.print('  [bold yellow]CAUTION: Net sellers outweigh holders buying — tighten stop loss[/bold yellow]')
                elif _buying_holders and net_flow_today > 0:
                    console.print('  [bold green]GOOD: Holders winning vs net sellers — strong hold[/bold green]')
                elif _buying_holders:
                    console.print('  [bold yellow]HOLD: Holders accumulating but net sellers active — watch tomorrow[/bold yellow]')
                console.print()
        except Exception:
            pass

        broker_score = max(0, min(100, broker_score))
        b_verdict = 'ACCUMULATING' if broker_score >= 65 else 'NEUTRAL' if broker_score >= 40 else 'DISTRIBUTING'
        b_col = 'green' if broker_score >= 65 else 'yellow' if broker_score >= 40 else 'red'
        console.print()
        console.print(f'  Broker Score: [{b_col}]{broker_score}/100 — {b_verdict}[/{b_col}]')
        section_verdicts.append(('Broker Activity', broker_score, b_verdict, b_col))
        total_score += broker_score
        max_score += 100
    except Exception as e:
        console.print(f'  Error: {e}', style='red')
        max_score += 100

    # ─────────────────────────────────────────
    # SECTION 4 — TECHNICAL / MOMENTUM
    # ─────────────────────────────────────────
    # SECTION 4 — TECHNICAL / MOMENTUM
    # ─────────────────────────────────────────
    console.print()
    console.rule('[bold yellow]Section 4 — Technical / Momentum[/bold yellow]', style='yellow')
    console.print()
    tech_score = 50
    try:
        # ── Price Analysis from stock_prices ──
        prices = conn.execute(
            'SELECT date, close, high, low, volume FROM stock_prices '
            'WHERE symbol=? AND close > 0 ORDER BY date DESC LIMIT 25',
            (symbol,)
        ).fetchall()

        if prices:
            curr_price = prices[0][1]
            curr_date = prices[0][0]

            yr = conn.execute(
                'SELECT MAX(high), MIN(low) FROM stock_prices '
                'WHERE symbol=? AND date >= date(?, "-365 days") AND close > 0',
                (symbol, curr_date)
            ).fetchone()
            wk52_high = yr[0] or curr_price
            wk52_low = yr[1] or curr_price
            yr_range = wk52_high - wk52_low
            price_pos = ((curr_price - wk52_low) / yr_range * 100) if yr_range > 0 else 50
            pos_col = 'green' if price_pos < 40 else 'yellow' if price_pos < 70 else 'red'
            console.print(f'  Current Price: [bold]Rs {curr_price:,.1f}[/bold]')
            console.print(f'  52W High: [red]Rs {wk52_high:,.1f}[/red]  |  52W Low: [green]Rs {wk52_low:,.1f}[/green]')
            pos_note = "(near 52W low — potential opportunity)" if price_pos < 25 else "(near 52W high — caution)" if price_pos > 80 else "(mid range)"
            console.print(f'  Price Position: [{pos_col}]{price_pos:.0f}% from 52W low[/{pos_col}] {pos_note}')
            if price_pos < 25: tech_score += 20
            elif price_pos > 85: tech_score -= 15
            elif price_pos > 60: tech_score += 5

            valid_prices = [p[1] for p in prices[:7] if p[1] and p[1] > 0]
            if len(valid_prices) >= 3:
                up_days = sum(1 for i in range(len(valid_prices)-1) if valid_prices[i] > valid_prices[i+1])
                down_days = len(valid_prices) - 1 - up_days
                trend_col = 'green' if up_days > down_days else 'red' if down_days > up_days else 'yellow'
                trend_str = 'UPTREND' if up_days > down_days else 'DOWNTREND' if down_days > up_days else 'SIDEWAYS'
                recent_str = ' -> '.join([f'Rs {c:,.0f}' for c in valid_prices[:4][::-1]])
                console.print(f'  Price Trend (5d): [{trend_col}]{trend_str}[/{trend_col}] — {recent_str}')
                if up_days > down_days: tech_score += 15
                elif down_days > up_days: tech_score -= 15

            valid_closes = [p[1] for p in prices if p[1] and p[1] > 0]
            if len(valid_closes) >= 5:
                ma20 = sum(valid_closes[:20]) / min(20, len(valid_closes))
                ma_col = 'green' if curr_price >= ma20 else 'red'
                ma_str = 'ABOVE' if curr_price >= ma20 else 'BELOW'
                pct_from_ma = ((curr_price - ma20) / ma20) * 100
                console.print(f'  20-day MA: Rs {ma20:,.1f} — [{ma_col}]price {ma_str} MA ({pct_from_ma:+.1f}%)[/{ma_col}]')
                if curr_price >= ma20: tech_score += 10
                else: tech_score -= 10

            vols = [p[4] for p in prices[:10] if p[4] and p[4] > 0]
            if len(vols) >= 3:
                avg_vol = sum(vols[1:]) / len(vols[1:])
                vol_ratio = vols[0] / avg_vol if avg_vol > 0 else 1
                vol_col = 'green' if vol_ratio >= 1.5 else 'yellow' if vol_ratio >= 0.7 else 'red'
                vol_note = "(HIGH demand)" if vol_ratio >= 1.5 else "(low demand)" if vol_ratio < 0.7 else "(normal)"
                console.print(f'  Volume: {vols[0]:,.0f} vs avg {avg_vol:,.0f} — [{vol_col}]{vol_ratio:.1f}x {vol_note}[/{vol_col}]')
                if vol_ratio >= 1.5: tech_score += 10
                elif vol_ratio < 0.5: tech_score -= 10
        else:
            console.print('  No price data available.', style='yellow')

        console.print()

        # ── RS vs Sector + RSI ──
        try:
            rs_data = _calc_relative_strength(db_path=db_path)
            rs_row = next((r for r in rs_data if r['symbol'] == symbol), None)
            if rs_row:
                rs5 = rs_row.get('rs5', 0) or 0
                rs20 = rs_row.get('rs20', 0) or 0
                rs_col = 'green' if rs5 > 0 else 'red'
                rs20_col = 'green' if rs20 > 0 else 'red'
                console.print(f'  RS vs Sector (5d): [{rs_col}]{rs5:+.1f}%[/{rs_col}]  |  RS vs Sector (20d): [{rs20_col}]{rs20:+.1f}%[/{rs20_col}]')
                if rs5 > 2: tech_score += 15
                elif rs5 > 0: tech_score += 8
                elif rs5 < -2: tech_score -= 15
                elif rs5 < 0: tech_score -= 8
            else:
                console.print('  RS vs Sector: [dim]not enough data[/dim]')
        except Exception:
            pass

        # ── RSI(14) ──
        try:
            rsi_prices = conn.execute(
                'SELECT close FROM stock_prices WHERE symbol=? AND close > 0 ORDER BY date DESC LIMIT 20',
                (symbol,)
            ).fetchall()
            if len(rsi_prices) >= 10:
                rsi_closes = [p[0] for p in reversed(rsi_prices)]
                gains = [max(rsi_closes[i]-rsi_closes[i-1], 0) for i in range(1, len(rsi_closes))]
                losses = [max(rsi_closes[i-1]-rsi_closes[i], 0) for i in range(1, len(rsi_closes))]
                avg_gain = sum(gains[-14:]) / min(14, len(gains)) if gains else 0
                avg_loss = sum(losses[-14:]) / min(14, len(losses)) if losses else 1
                rsi = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss > 0 else 100
                rsi_col = 'red' if rsi > 70 else 'green' if rsi < 30 else 'yellow'
                rsi_note = '— OVERBOUGHT (consider selling)' if rsi > 70 else '— OVERSOLD (potential bounce)' if rsi < 30 else '— NEUTRAL'
                console.print(f'  RSI(14): [{rsi_col}]{rsi:.1f}[/{rsi_col}] {rsi_note}')
                if rsi < 30: tech_score += 15
                elif rsi > 70: tech_score -= 15
                elif rsi < 45: tech_score += 5
        except Exception:
            pass

        console.print()

        # ── Broker Momentum ──
        all_dates = conn.execute(
            'SELECT DISTINCT date FROM broker_activity WHERE symbol=? '
            'AND broker_id GLOB "[0-9]*" ORDER BY date DESC LIMIT 7',
            (symbol,)
        ).fetchall()
        all_dates = [d[0] for d in all_dates]
        consec = 0
        momentum_scores = []
        for d in all_dates:
            counts = conn.execute(
                'SELECT COUNT(CASE WHEN net_val>0 THEN 1 END), COUNT(CASE WHEN net_val<0 THEN 1 END), COUNT(*) '
                'FROM broker_activity WHERE symbol=? AND date=? AND broker_id GLOB "[0-9]*"',
                (symbol, d)
            ).fetchone()
            nb = counts[0] or 0
            ns = counts[1] or 0
            total = counts[2] or 1
            momentum_scores.append(int((nb / total) * 100))
            if nb > ns: consec += 1
            else: break

        avg_momentum = sum(momentum_scores) / len(momentum_scores) if momentum_scores else 50
        consec_col = 'green' if consec >= 3 else 'yellow' if consec >= 1 else 'red'
        mom_col = 'green' if avg_momentum >= 60 else 'yellow' if avg_momentum >= 40 else 'red'
        console.print(f'  Broker Momentum: [{consec_col}]{consec} consecutive buy days[/{consec_col}]  |  Avg score: [{mom_col}]{avg_momentum:.0f}/100[/{mom_col}]')
        if consec >= 4: tech_score += 20
        elif consec >= 2: tech_score += 10
        elif consec == 0: tech_score -= 15
        if avg_momentum >= 60: tech_score += 5
        elif avg_momentum < 40: tech_score -= 5

        tech_score = max(0, min(100, tech_score))
        t_verdict = 'BULLISH' if tech_score >= 65 else 'NEUTRAL' if tech_score >= 40 else 'BEARISH'
        t_col = 'green' if tech_score >= 65 else 'yellow' if tech_score >= 40 else 'red'
        console.print()
        console.print(f'  Technical Score: [{t_col}]{tech_score}/100 — {t_verdict}[/{t_col}]')

        # Smart interpretation
        try:
            broker_s_temp = next((s for n,s,v,c in section_verdicts if n == 'Broker Activity'), 50)
            if broker_s_temp >= 70 and tech_score < 50:
                console.print('  [dim]-> Price falling but brokers accumulating — classic dip buying. Wait for price to stabilize.[/dim]')
            elif broker_s_temp >= 70 and tech_score >= 65:
                console.print('  [dim]-> Both price momentum and broker accumulation aligned — strong entry signal.[/dim]')
            elif broker_s_temp < 40 and tech_score >= 65:
                console.print('  [dim]-> Price rising but institutions not buying — momentum only, high risk.[/dim]')
            elif tech_score < 35 and broker_s_temp < 40:
                console.print('  [dim]-> Price falling and brokers selling — avoid, wait for reversal signal.[/dim]')
            elif 'rsi' in dir() and rsi < 30:
                console.print('  [dim]-> RSI oversold — price may bounce soon. Watch for broker accumulation.[/dim]')
        except Exception:
            pass

        # ── Sector Momentum ──
        try:
            _sect_prices = _load_sector_prices(db_path=db_path, days=35)
            _sect_rets = _sector_returns(_sect_prices)
            # Find this stock's sector
            import sqlite3 as _sq3
            _sc3 = _sq3.connect(db_path)
            _stock_sector = (_sc3.execute(
                "SELECT sector FROM companies WHERE symbol=?", (symbol,)
            ).fetchone() or [None])[0]
            _sc3.close()
            if _stock_sector and _sect_rets:
                # Normalize sector name
                _NAME_MAP = {
                    "Hydro Power": "Hydropower",
                    "Commercial Banks": "Commercial Banks",
                    "Development Banks": "Development Banks",
                    "Finance": "Finance",
                    "Microfinance": "Microfinance",
                    "Life Insurance": "Life Insurance",
                    "Non Life Insurance": "Non-Life Insurance",
                    "Manufacturing And Processing": "Manufacturing",
                    "Hotels And Tourism": "Hotel & Tourism",
                    "Investment": "Investment",
                    "Tradings": "Trading",
                    "Others": "Others",
                }
                _sect_key = _NAME_MAP.get(_stock_sector, _stock_sector)
                _sd = _sect_rets.get(_sect_key) or _sect_rets.get(_stock_sector)
                if _sd:
                    _s5  = _sd.get(5)
                    _s10 = _sd.get(10)
                    _s20 = _sd.get(20)
                    _s5s  = f'{_s5:+.1f}%'  if _s5  is not None else 'N/A'
                    _s10s = f'{_s10:+.1f}%' if _s10 is not None else 'N/A'
                    _s20s = f'{_s20:+.1f}%' if _s20 is not None else 'N/A'
                    _sc  = 'green' if (_s5 or 0) > 0 else 'red' if (_s5 or 0) < 0 else 'yellow'
                    _sc2 = 'green' if (_s20 or 0) > 0 else 'red' if (_s20 or 0) < 0 else 'yellow'
                    console.print(f'  Sector ({_stock_sector}): 5d [{_sc}]{_s5s}[/{_sc}]  10d {_s10s}  20d [{_sc2}]{_s20s}[/{_sc2}]')
                    # Sector momentum signal
                    if (_s5 or 0) > 1 and (_s20 or 0) > 1:
                        console.print('  [dim green]-> Sector in uptrend — tailwind for stock[/dim green]')
                        tech_score = min(tech_score + 5, 100)
                    elif (_s5 or 0) < -1 and (_s20 or 0) < -1:
                        console.print('  [dim red]-> Sector in downtrend — headwind for stock[/dim red]')
                        tech_score = max(tech_score - 5, 0)
                    else:
                        console.print('  [dim]-> Sector mixed — no strong directional bias[/dim]')
        except Exception:
            pass

        section_verdicts.append(('Technical', tech_score, t_verdict, t_col))
        total_score += tech_score
        max_score += 100
    except Exception as e:
        console.print(f'  Error in Section 4: {e}', style='red')
        max_score += 100


    # -----------------------------------------
    # SECTION 5 - TRADE PLAN
    # -----------------------------------------
    console.print()
    console.rule('[bold yellow]Section 5 -- Trade Plan[/bold yellow]', style='yellow')
    console.print()
    try:
        prices_tp = conn.execute(
            'SELECT date, high, low, close FROM stock_prices '
            'WHERE symbol=? AND close > 0 ORDER BY date DESC LIMIT 60',
            (symbol,)
        ).fetchall()

        if prices_tp:
            curr_p = prices_tp[0][3]
            zone   = curr_p * 0.02

            # Build real S/R clusters — levels touched 2+ times
            _levels = []
            for _p in prices_tp:
                _levels.append(_p[1])  # high
                _levels.append(_p[2])  # low

            _used = set()
            _clusters = []
            for _i, _v1 in enumerate(_levels):
                if _i in _used: continue
                _grp = [_v1]
                _idx = [_i]
                for _j, _v2 in enumerate(_levels):
                    if _j != _i and _j not in _used and abs(_v1-_v2) <= zone:
                        _grp.append(_v2)
                        _idx.append(_j)
                if len(_grp) >= 2:
                    _clusters.append(sum(_grp)/len(_grp))
                    _used.update(_idx)

            _supports    = sorted([l for l in _clusters if l < curr_p], reverse=True)
            _resistances = sorted([l for l in _clusters if l > curr_p])

            support    = round(_supports[0], 1) if _supports else round(min(p[2] for p in prices_tp[:5]), 1)

            # Skip resistances too close to current price (< 3% away) — use next meaningful level
            _valid_res = [l for l in _resistances if l > curr_p * 1.03]
            resistance = round(_valid_res[0], 1) if _valid_res else round(_resistances[0], 1) if _resistances else round(max(p[1] for p in prices_tp[:10]), 1)
            stop_loss  = round(support * 0.97, 1)
            target     = round(resistance * 0.99, 1)  # just below resistance (1%)

            # Show all levels found
            console.print('  [bold]Key S/R Levels (cluster method):[/bold]')
            if _supports:
                for _l in _supports[:3]:
                    _tag = ' <- STOP ZONE' if abs(_l - support) < 1 else ''
                    console.print(f'  [green]  Support:    Rs {_l:,.1f}{_tag}[/green]')
            if _resistances:
                for _l in _resistances[:3]:
                    _tag = ' <- TARGET ZONE' if abs(_l - resistance) < 1 else ''
                    console.print(f'  [red]  Resistance: Rs {_l:,.1f}{_tag}[/red]')
            console.print()
            risk       = curr_p - stop_loss
            reward     = target - curr_p
            rr         = round(reward / risk, 2) if risk > 0 else 0

            if curr_p <= support * 1.02:
                entry_note   = '[bold green]AT SUPPORT -- good entry zone right now[/bold green]'
                entry_action = 'BUY NOW'
            elif curr_p <= support * 1.05:
                entry_note   = '[bold yellow]NEAR SUPPORT -- acceptable entry, small position[/bold yellow]'
                entry_action = 'BUY SMALL'
            elif curr_p >= resistance * 0.97:
                entry_note   = '[bold red]NEAR RESISTANCE -- wait for pullback[/bold red]'
                entry_action = 'WAIT'
            else:
                entry_note   = '[bold yellow]MID RANGE -- wait for dip toward support[/bold yellow]'
                entry_action = 'WAIT FOR DIP'

            console.print(f'  Current Price:    [bold]Rs {curr_p:,.1f}[/bold]')
            console.print()
            console.print(f'  Support Zone:     [green]Rs {support:,.1f}[/green]')
            console.print(f'  Resistance Zone:  [red]Rs {resistance:,.1f}[/red]')
            console.print()
            console.print(f'  Entry Action:     {entry_note}')
            console.print()
            console.print(f'  Stop Loss:        [red]Rs {stop_loss:,.1f}[/red]  (3% below support)')
            console.print(f'  Target:           [green]Rs {target:,.1f}[/green]  (5% below resistance)')
            console.print()
            rr_col  = 'green' if rr >= 2 else 'yellow' if rr >= 1.5 else 'red'
            rr_note = '(GOOD -- take the trade)' if rr >= 2 else '(MARGINAL -- smaller position)' if rr >= 1.5 else '(POOR -- skip or wait)'
            console.print(f'  Risk:             Rs {risk:,.1f} per share')
            console.print(f'  Reward:           Rs {reward:,.1f} per share')
            console.print(f'  Risk/Reward:      [{rr_col}]1:{rr} {rr_note}[/{rr_col}]')
            console.print()
            upside_pct   = ((target - curr_p) / curr_p) * 100
            downside_pct = ((curr_p - stop_loss) / curr_p) * 100
            console.print(f'  Upside potential: [green]+{upside_pct:.1f}%[/green]  |  Downside risk: [red]-{downside_pct:.1f}%[/red]')
            console.print()
            console.print('  [bold]Position Sizing:[/bold]')
            console.print(f'    Risk Rs 10,000 max  -->  buy {int(10000/risk):,} shares at Rs {curr_p:,.1f}')
            console.print(f'    Risk Rs 25,000 max  -->  buy {int(25000/risk):,} shares at Rs {curr_p:,.1f}')
            console.print()
            broker_s_tp = next((s for n,s,v,c in section_verdicts if n == "Broker Activity"), 50)
            if entry_action in ("BUY NOW", "BUY SMALL") and broker_s_tp >= 70 and rr >= 2:
                action_msg = '[bold green]ACTION: ENTER TRADE -- price at support, institutions accumulating, good R/R[/bold green]'
            elif entry_action == "WAIT FOR DIP" and broker_s_tp >= 70:
                action_msg = f'[bold yellow]ACTION: SET ALERT at Rs {support:,.1f} -- wait for pullback to support[/bold yellow]'
            elif entry_action == "WAIT":
                action_msg = '[bold red]ACTION: DO NOT BUY -- price near resistance, wait for pullback[/bold red]'
            elif rr < 1.5:
                action_msg = '[bold red]ACTION: SKIP -- risk/reward too poor at current price[/bold red]'
            else:
                action_msg = f'[bold yellow]ACTION: WATCH -- set alert at Rs {support:,.1f} for better entry[/bold yellow]'
            console.print(f'  {action_msg}')

            # Better Entry suggestion when R/R is poor
            if rr < 1.5 and len(_supports) >= 2:
                next_support  = round(_supports[1], 1)
                better_stop   = round(next_support * 0.97, 1)
                better_risk   = next_support - better_stop
                better_reward = target - next_support
                better_rr     = round(better_reward / better_risk, 2) if better_risk > 0 else 0
                console.print()
                console.print('  [bold cyan]Better Entry Zone:[/bold cyan]')
                console.print(f'  [cyan]  Wait for price to drop to Rs {next_support:,.1f} (next support)[/cyan]')
                console.print(f'  [cyan]  Entry:     Rs {next_support:,.1f}[/cyan]')
                console.print(f'  [cyan]  Stop Loss: Rs {better_stop:,.1f}[/cyan]')
                console.print(f'  [cyan]  Target:    Rs {target:,.1f}[/cyan]')
                better_rr_col  = 'green' if better_rr >= 2 else 'yellow' if better_rr >= 1.5 else 'red'
                better_rr_note = '(GOOD -- worth waiting for)' if better_rr >= 2 else '(MARGINAL)' if better_rr >= 1.5 else '(still poor -- skip stock)'
                console.print(f'  [cyan]  R/R:       [{better_rr_col}]1:{better_rr} {better_rr_note}[/{better_rr_col}][/cyan]')
                console.print(f'  [cyan]  Set price alert at Rs {next_support:,.1f}[/cyan]')
        else:
            console.print('  No price data for trade plan.', style='yellow')
    except Exception as e:
        console.print(f'  Error in Section 5: {e}', style='red')

    conn.close()

    # ─────────────────────────────────────────
    # SECTION 6 — SEASONALITY CONTEXT
    # ─────────────────────────────────────────
    console.print()
    console.rule('[bold yellow]Section 6 — Seasonality Context[/bold yellow]', style='yellow')
    console.print()
    try:
        from datetime import date as _date
        from collections import defaultdict as _dd
        import sqlite3 as _sq

        # BS converter
        _baisakh_start = {
            2077:(2020,4,13),2078:(2021,4,14),2079:(2022,4,14),
            2080:(2023,4,14),2081:(2024,4,13),2082:(2025,4,14),2083:(2026,4,14),
        }
        _bs_month_days = {
            2077:[31,31,31,32,31,31,30,29,30,29,30,30],
            2078:[31,31,32,31,31,31,30,29,30,29,30,30],
            2079:[31,32,31,32,31,30,30,29,30,29,30,30],
            2080:[31,31,31,32,31,31,30,29,30,29,30,30],
            2081:[31,31,32,31,31,31,30,29,30,29,30,30],
            2082:[31,32,31,32,31,30,30,29,30,29,30,30],
            2083:[31,31,31,32,31,31,30,29,30,29,30,30],
        }
        _bs_names = {1:'Baisakh',2:'Jestha',3:'Ashadh',4:'Shrawan',5:'Bhadra',
                     6:'Ashwin',7:'Kartik',8:'Mangsir',9:'Poush',10:'Magh',
                     11:'Falgun',12:'Chaitra'}
        _greg_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                       7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}

        def _to_bs(d):
            for yr in sorted(_baisakh_start.keys(), reverse=True):
                g = _baisakh_start[yr]
                s = _date(g[0],g[1],g[2])
                if d >= s:
                    days = (d-s).days
                    for mi,md in enumerate(_bs_month_days.get(yr,[])):
                        if days < md: return yr, mi+1
                        days -= md
                    return yr+1,1
            return None,None

        def _sig(avg):
            if avg >= 5:  return 'STR.BUY','green'
            if avg >= 2:  return 'BUY','green'
            if avg >= -1: return 'NTRL','yellow'
            if avg >= -3: return 'AVOID','red'
            return 'STR.AVD','red'

        def _char(up, dn, avg):
            if up > abs(dn)*2 and avg >= 3:
                return f'Rally +{up:.1f}% dip -{dn:.1f}%'
            elif up > abs(dn)*2 and avg < 3:
                return f'Rally+fade +{up:.1f}%'
            elif abs(dn) > up*1.5:
                return f'Drop -{dn:.1f}% / bounce +{up:.1f}%'
            else:
                return f'Mixed +{up:.1f}% / -{dn:.1f}%'

        _today = _date.today()
        _curr_gm  = _today.month
        _next_gm  = (_curr_gm % 12) + 1
        _bs_yr, _curr_bm = _to_bs(_today)
        _next_bm  = (_curr_bm % 12) + 1

        # Load NEPSE data
        _c1 = _sq.connect(db_path)
        _nepse = _c1.execute(
            "SELECT date,close,high,low FROM stock_prices "
            "WHERE symbol='NEPSE' AND close>0 ORDER BY date"
        ).fetchall()
        # Load stock data
        _stock = _c1.execute(
            "SELECT date,close,high,low FROM stock_prices "
            "WHERE symbol=? AND close>0 ORDER BY date", (symbol,)
        ).fetchall()
        _c1.close()

        def _build_greg(rows):
            _by = _dd(list)
            for d_str,c,h,l in rows:
                d = _date.fromisoformat(d_str)
                _by[(d.year,d.month)].append((c,h,l))
            _rets = _dd(list)
            _hl   = _dd(list)
            _db_first_g = (_date(2021,5,25).year, _date(2021,5,25).month)
            _today_g    = (_date.today().year, _date.today().month)
            for (yr,m),entries in _by.items():
                if len(entries)<5: continue
                if (yr,m) == _db_first_g: continue
                if (yr,m) == _today_g: continue
                oc=entries[0][0]; cc=entries[-1][0]
                hh=max(e[1] for e in entries)
                ll=min(e[2] for e in entries if e[2]>0)
                _rets[m].append((cc-oc)/oc*100)
                _hl[m].append(((hh-oc)/oc*100,(oc-ll)/oc*100))
            return _rets, _hl

        def _build_bs(rows):
            _by = _dd(list)
            for d_str,c,h,l in rows:
                d = _date.fromisoformat(d_str)
                by,bm = _to_bs(d)
                if by and bm:
                    _by[(by,bm)].append((c,h,l))
            _rets = _dd(list)
            _hl   = _dd(list)
            _db_first_bs = _to_bs(_date(2021,5,25))
            _today_bs3   = _to_bs(_date.today())
            for (yr,m),entries in _by.items():
                if len(entries)<5: continue
                if (yr,m) == _db_first_bs: continue
                if (yr,m) == _today_bs3: continue
                oc=entries[0][0]; cc=entries[-1][0]
                hh=max(e[1] for e in entries)
                ll=min(e[2] for e in entries if e[2]>0)
                _rets[m].append((cc-oc)/oc*100)
                _hl[m].append(((hh-oc)/oc*100,(oc-ll)/oc*100))
            return _rets, _hl

        def _stats(rets, hl, m):
            r = rets[m]
            if not r: return None
            avg  = sum(r)/len(r)
            wins = sum(1 for x in r if x>0)
            h    = hl[m]
            up   = sum(x[0] for x in h)/len(h) if h else 0
            dn   = sum(x[1] for x in h)/len(h) if h else 0
            return avg, wins, len(r), up, dn

        # Build all 4 datasets
        _ng_rets, _ng_hl = _build_greg(_nepse)
        _nb_rets, _nb_hl = _build_bs(_nepse)
        _sg_rets, _sg_hl = _build_greg(_stock)
        _sb_rets, _sb_hl = _build_bs(_stock)

        console.print(f'  [bold]Today:[/bold] {_today}  |  '
                      f'Gregorian: [cyan]{_greg_names[_curr_gm]}[/cyan]  |  '
                      f'BS: [cyan]{_bs_names[_curr_bm]}[/cyan]')
        console.print()

        # ── Table ──
        _t = Table(show_header=True, header_style='bold cyan', box=None, padding=(0,1))
        _t.add_column('System',   width=6)
        _t.add_column('Month',    width=13)
        _t.add_column('NEPSE',    justify='right', width=12)
        _t.add_column('Sig',      width=8)
        _t.add_column('Character',width=28)
        _t.add_column(f'{symbol}', justify='right', width=12)
        _t.add_column('Sig ',     width=8)

        for _sys, _gm, _bm in [('NOW', _curr_gm, _curr_bm), ('NEXT', _next_gm, _next_bm)]:
            # Gregorian row
            _ng = _stats(_ng_rets, _ng_hl, _gm)
            _sg = _stats(_sg_rets, _sg_hl, _gm)
            if _ng:
                _na,_nw,_nt,_nu,_nd = _ng
                _nsig,_ncol = _sig(_na)
                _nchar = _char(_nu,_nd,_na)
                _n_str = f'[{_ncol}]{_na:+.1f}% {_nw}/{_nt}[/{_ncol}]'
                _ns_str= f'[{_ncol}]{_nsig}[/{_ncol}]'
            else:
                _nchar='N/A'; _n_str='N/A'; _ns_str='N/A'; _ncol='dim'
            if _sg:
                _sa,_sw,_st,_su,_sd = _sg
                _ssig,_scol = _sig(_sa)
                _s_str = f'[{_scol}]{_sa:+.1f}% {_sw}/{_st}[/{_scol}]'
                _ss_str= f'[{_scol}]{_ssig}[/{_scol}]'
            else:
                _s_str='[dim]N/A[/dim]'; _ss_str='[dim]N/A[/dim]'
            _t.add_row(
                f'[cyan]GREG[/cyan]',
                f'[bold]{_greg_names[_gm]}({_sys})[/bold]',
                _n_str, _ns_str, f'[dim]{_nchar}[/dim]',
                _s_str, _ss_str,
            )

            # BS row
            _nb = _stats(_nb_rets, _nb_hl, _bm)
            _sb = _stats(_sb_rets, _sb_hl, _bm)
            if _nb:
                _na,_nw,_nt,_nu,_nd = _nb
                _nsig,_ncol = _sig(_na)
                _nchar = _char(_nu,_nd,_na)
                _n_str = f'[{_ncol}]{_na:+.1f}% {_nw}/{_nt}[/{_ncol}]'
                _ns_str= f'[{_ncol}]{_nsig}[/{_ncol}]'
            else:
                _nchar='N/A'; _n_str='N/A'; _ns_str='N/A'; _ncol='dim'
            if _sb:
                _sa,_sw,_st,_su,_sd = _sb
                _ssig,_scol = _sig(_sa)
                _s_str = f'[{_scol}]{_sa:+.1f}% {_sw}/{_st}[/{_scol}]'
                _ss_str= f'[{_scol}]{_ssig}[/{_scol}]'
            else:
                _s_str='[dim]N/A[/dim]'; _ss_str='[dim]N/A[/dim]'
            _t.add_row(
                f'[magenta]BS[/magenta]',
                f'[bold]{_bs_names[_bm]}({_sys})[/bold]',
                _n_str, _ns_str, f'[dim]{_nchar}[/dim]',
                _s_str, _ss_str,
            )
            # Spacer between NOW and NEXT
            if _sys == 'NOW':
                _t.add_row('','','','','','','')

        console.print(_t)
        console.print()

        # ── Seasonal verdict combining both systems ──
        _ng_c = _stats(_ng_rets, _ng_hl, _curr_gm)
        _nb_c = _stats(_nb_rets, _nb_hl, _curr_bm)
        _sg_c = _stats(_sg_rets, _sg_hl, _curr_gm)
        _sb_c = _stats(_sb_rets, _sb_hl, _curr_bm)

        _n_g_avg = _ng_c[0] if _ng_c else 0
        _n_b_avg = _nb_c[0] if _nb_c else 0
        _s_g_avg = _sg_c[0] if _sg_c else 0
        _s_b_avg = _sb_c[0] if _sb_c else 0

        # FYQ signal for current quarter
        _fyq_stock_avg = 0
        _fyq_nepse_avg = 0
        try:
            from datetime import date as _dtt
            _bs_st2 = {2077:(2020,4,13),2078:(2021,4,14),2079:(2022,4,14),
                       2080:(2023,4,14),2081:(2024,4,13),2082:(2025,4,14),2083:(2026,4,14)}
            _bs_md2 = {2077:[31,31,31,32,31,31,30,29,30,29,30,30],
                       2078:[31,31,32,31,31,31,30,29,30,29,30,30],
                       2079:[31,32,31,32,31,30,30,29,30,29,30,30],
                       2080:[31,31,31,32,31,31,30,29,30,29,30,30],
                       2081:[31,31,32,31,31,31,30,29,30,29,30,30],
                       2082:[31,32,31,32,31,30,30,29,30,29,30,30],
                       2083:[31,31,31,32,31,31,30,29,30,29,30,30]}
            _fq_map2 = {4:'FYQ1',5:'FYQ1',6:'FYQ1',7:'FYQ2',8:'FYQ2',9:'FYQ2',
                        10:'FYQ3',11:'FYQ3',12:'FYQ3',1:'FYQ4',2:'FYQ4',3:'FYQ4'}
            def _bs2(d):
                for yr in sorted(_bs_st2.keys(),reverse=True):
                    g=_bs_st2[yr]; s=_dtt(g[0],g[1],g[2])
                    if d>=s:
                        days=(d-s).days
                        for mi,md in enumerate(_bs_md2.get(yr,[])):
                            if days<md: return yr,mi+1
                            days-=md
                        return yr+1,1
                return None,None
            def _fly2(by,bm):
                return by if bm in (4,5,6,7,8,9,10,11,12) else by-1
            _today_bm2 = _bs2(_dtt.today())
            _fyq_now = _fq_map2[_today_bm2[1]]
            _curr_fk = (_fly2(_today_bm2[0],_today_bm2[1]), _fyq_now)
            _first_d2 = _bs2(_dtt(2021,5,25))
            _first_fk = (_fly2(_first_d2[0],_first_d2[1]), _fq_map2[_first_d2[1]])
            # Build FYQ on the fly from _stock rows (already loaded)
            from collections import defaultdict as _dd3
            _fyq_s_raw = _dd3(list)
            for _sd,_sc,_sh,_sl in _stock:
                _sd2 = _dtt.fromisoformat(_sd)
                _sby,_sbm = _bs2(_sd2)
                if _sby and _sbm:
                    _sfyq = _fq_map2[_sbm]
                    _sfy  = _fly2(_sby,_sbm)
                    _fyq_s_raw[(_sfy,_sfyq)].append(_sc)
            _fyq_s_rets = []
            for (_fk_fy,_fk_fq),_fk_entries in _fyq_s_raw.items():
                if _fk_fq != _fyq_now: continue
                if (_fk_fy,_fk_fq) == _curr_fk: continue
                if (_fk_fy,_fk_fq) == _first_fk: continue
                if len(_fk_entries) < 10: continue
                _fyq_s_rets.append((_fk_entries[-1]-_fk_entries[0])/_fk_entries[0]*100)
            _fyq_n_rets = []
            # Build NEPSE FYQ inline
            _nfyq_raw2 = _dd3(list)
            _conn_nfyq = sqlite3.connect(db_path)
            _nfyq_rows = _conn_nfyq.execute(
                "SELECT date, close FROM stock_prices WHERE symbol='NEPSE' AND close>0 ORDER BY date"
            ).fetchall()
            _conn_nfyq.close()
            for _nd, _nc in _nfyq_rows:
                _nd2 = _dtt.fromisoformat(_nd)
                _nby, _nbm = _bs2(_nd2)
                if _nby and _nbm:
                    _nfyq = _fq_map2[_nbm]
                    _nfy  = _fly2(_nby, _nbm)
                    _nfyq_raw2[(_nfy,_nfyq)].append(_nc)
            for _k2,_v2 in _nfyq_raw2.items():
                if len(_v2)<10: continue
                if _k2 == _curr_fk: continue
                if _k2 == _first_fk: continue
                _nfy2,_nfyq2 = _k2
                if _nfyq2 == _fyq_now:
                    _fyq_n_rets.append((_v2[-1]-_v2[0])/_v2[0]*100)
            if _fyq_s_rets: _fyq_stock_avg = sum(_fyq_s_rets)/len(_fyq_s_rets)
            if _fyq_n_rets: _fyq_nepse_avg = sum(_fyq_n_rets)/len(_fyq_n_rets)
            _fyq_stock_sufficient = len(_fyq_s_rets) >= 3
            _fyq_nepse_sufficient = len(_fyq_n_rets) >= 3
        except: pass

        # Agreement score — Greg + BS monthly + FYQ quarterly (3 signals each)
        # Only include FYQ in scoring if sufficient history (>=3 complete quarters)
        _fyq_nepse_ok = getattr(_fyq_nepse_avg, '__ok__', None) or _fyq_nepse_sufficient if '_fyq_nepse_sufficient' in dir() else False
        try: _fyq_nepse_ok = _fyq_nepse_sufficient
        except: _fyq_nepse_ok = False
        try: _fyq_stock_ok = _fyq_stock_sufficient
        except: _fyq_stock_ok = False
        _nepse_bull  = (_n_g_avg >= 2) + (_n_b_avg >= 2) + ((_fyq_nepse_avg >= 1.5) if _fyq_nepse_ok else 0)
        _nepse_bear  = (_n_g_avg <= -2) + (_n_b_avg <= -2) + ((_fyq_nepse_avg <= -1.5) if _fyq_nepse_ok else 0)
        _stock_bull  = (_s_g_avg >= 2) + (_s_b_avg >= 2) + ((_fyq_stock_avg >= 1.5) if _fyq_stock_ok else 0)
        _stock_bear  = (_s_g_avg <= -2) + (_s_b_avg <= -2) + ((_fyq_stock_avg <= -1.5) if _fyq_stock_ok else 0)

        if _nepse_bull >= 2 and _stock_bull >= 2:
            _sv = '[bold green]STRONG TAILWIND — multiple calendars bullish for NEPSE and stock[/bold green]'
            _ss = 85
        elif _nepse_bull >= 1 and _stock_bull >= 2:
            _sv = '[bold green]TAILWIND — FYQ + BS/Greg confirm bullish seasonal edge[/bold green]'
            _ss = 75
        elif _nepse_bull >= 1 and _stock_bull >= 1:
            _sv = '[bold green]TAILWIND — at least one calendar bullish for both NEPSE and stock[/bold green]'
            _ss = 65
        elif _nepse_bull >= 2 and _stock_bear >= 1:
            _sv = '[bold yellow]MIXED — NEPSE strong but stock weak this period[/bold yellow]'
            _ss = 45
        elif _nepse_bear >= 2 and _stock_bear >= 2:
            _sv = '[bold red]STRONG HEADWIND — multiple calendars show weakness this period[/bold red]'
            _ss = 10
        elif _nepse_bear >= 1 and _stock_bear >= 1:
            _sv = '[bold red]HEADWIND — seasonal weakness confirmed across calendars[/bold red]'
            _ss = 20
        elif _nepse_bear >= 1 or _stock_bear >= 1:
            _sv = '[bold yellow]CAUTION — at least one calendar showing weakness[/bold yellow]'
            _ss = 40
        else:
            _sv = '[bold yellow]NEUTRAL — no strong seasonal edge either way[/bold yellow]'
            _ss = 50

        # Agreement note
        _sg_str = ('+' if _s_g_avg>=0 else '') + f'{_s_g_avg:.1f}%' if _s_g_avg != 0 else 'N/A'
        _sb_str = ('+' if _s_b_avg>=0 else '') + f'{_s_b_avg:.1f}%' if _s_b_avg != 0 else 'N/A'
        _greg_agree = ('Greg: NEPSE ' + ('+' if _n_g_avg>=0 else '') + f'{_n_g_avg:.1f}% / '
                      + symbol + ' ' + _sg_str)
        _bs_agree   = ('BS:   NEPSE ' + ('+' if _n_b_avg>=0 else '') + f'{_n_b_avg:.1f}% / '
                      + symbol + ' ' + _sb_str)

        # ── QUARTERLY ──
        console.print()
        console.rule('[dim]Quarterly Seasonality[/dim]')
        console.print()

        def _build_greg_q(rows):
            _by = _dd(list)
            for d_str,c,h,l in rows:
                d = _date.fromisoformat(d_str)
                q = f'Q{(d.month-1)//3+1}'
                _by[(d.year,q)].append((c,h,l))
            _rets = _dd(list)
            _curr_gq2 = f'Q{(_date.today().month-1)//3+1}'
            _curr_gyr2 = _date.today().year
            _first_gq2 = f'Q{(_date(2021,5,25).month-1)//3+1}'
            _first_gyr2 = _date(2021,5,25).year
            for (yr,q),entries in _by.items():
                if len(entries)<10: continue
                if (yr,q) == (_curr_gyr2, _curr_gq2): continue
                if (yr,q) == (_first_gyr2, _first_gq2): continue
                oc=entries[0][0]; cc=entries[-1][0]
                _rets[q].append((cc-oc)/oc*100)
            return _rets

        def _build_bs_q(rows):
            _nq_map = {1:'NQ1',2:'NQ1',3:'NQ1',4:'NQ2',5:'NQ2',6:'NQ2',
                       7:'NQ3',8:'NQ3',9:'NQ3',10:'NQ4',11:'NQ4',12:'NQ4'}
            _by = _dd(list)
            for d_str,c,h,l in rows:
                d = _date.fromisoformat(d_str)
                by,bm = _to_bs(d)
                if by and bm:
                    nq = _nq_map[bm]
                    _by[(by,nq)].append((c,h,l))
            _rets = _dd(list)
            _nq_map2 = {1:'NQ1',2:'NQ1',3:'NQ1',4:'NQ2',5:'NQ2',6:'NQ2',
                        7:'NQ3',8:'NQ3',9:'NQ3',10:'NQ4',11:'NQ4',12:'NQ4'}
            _curr_bq2  = _nq_map2[_to_bs(_date.today())[1]]
            _curr_byr2 = _to_bs(_date.today())[0]
            _first_bq2  = _nq_map2[_to_bs(_date(2021,5,25))[1]]
            _first_byr2 = _to_bs(_date(2021,5,25))[0]
            for (yr,nq),entries in _by.items():
                if len(entries)<10: continue
                if (yr,nq) == (_curr_byr2, _curr_bq2): continue
                if (yr,nq) == (_first_byr2, _first_bq2): continue
                oc=entries[0][0]; cc=entries[-1][0]
                _rets[nq].append((cc-oc)/oc*100)
            return _rets

        _ng_qrets = _build_greg_q(_nepse)
        _nb_qrets = _build_bs_q(_nepse)
        _sg_qrets = _build_greg_q(_stock)
        _sb_qrets = _build_bs_q(_stock)

        # Current/next quarter
        _curr_gq  = f'Q{(_today.month-1)//3+1}'
        _next_gq  = f'Q{((_today.month-1)//3+1)%4+1}'
        _nq_map2  = {1:'NQ1',2:'NQ1',3:'NQ1',4:'NQ2',5:'NQ2',6:'NQ2',
                     7:'NQ3',8:'NQ3',9:'NQ3',10:'NQ4',11:'NQ4',12:'NQ4'}
        _nq_next_map = {'NQ1':'NQ2','NQ2':'NQ3','NQ3':'NQ4','NQ4':'NQ1'}
        _curr_bq  = _nq_map2[_curr_bm]
        _next_bq  = _nq_next_map[_curr_bq]

        def _qstats(rets, q):
            r = rets[q]
            if not r: return None
            avg  = sum(r)/len(r)
            wins = sum(1 for x in r if x>0)
            return avg, wins, len(r)

        _qt = Table(show_header=True, header_style='bold cyan', box=None, padding=(0,1))
        _qt.add_column('System', width=6)
        _qt.add_column('Quarter', width=12)
        _qt.add_column('NEPSE', justify='right', width=12)
        _qt.add_column('Sig', width=8)
        _qt.add_column(f'{symbol}', justify='right', width=12)
        _qt.add_column('Sig ', width=8)

        for _sys2, _gq, _bq in [('NOW', _curr_gq, _curr_bq), ('NEXT', _next_gq, _next_bq)]:
            # Greg quarter
            _ngs = _qstats(_ng_qrets, _gq)
            _sgs = _qstats(_sg_qrets, _gq)
            if _ngs:
                _na,_nw,_nt = _ngs
                _nsig,_ncol = _sig(_na)
                _n_str = f'[{_ncol}]{_na:+.1f}% {_nw}/{_nt}[/{_ncol}]'
                _ns_str= f'[{_ncol}]{_nsig}[/{_ncol}]'
            else:
                _n_str='N/A'; _ns_str='N/A'
            if _sgs:
                _sa,_sw,_st = _sgs
                _ssig,_scol = _sig(_sa)
                _s_str = f'[{_scol}]{_sa:+.1f}% {_sw}/{_st}[/{_scol}]'
                _ss_str= f'[{_scol}]{_ssig}[/{_scol}]'
            else:
                _s_str='[dim]N/A[/dim]'; _ss_str='[dim]N/A[/dim]'
            _qt.add_row(
                '[cyan]GREG[/cyan]',
                f'[bold]{_gq}({_sys2})[/bold]',
                _n_str, _ns_str, _s_str, _ss_str,
            )
            # BS quarter
            _nbs = _qstats(_nb_qrets, _bq)
            _sbs = _qstats(_sb_qrets, _bq)
            if _nbs:
                _na,_nw,_nt = _nbs
                _nsig,_ncol = _sig(_na)
                _n_str = f'[{_ncol}]{_na:+.1f}% {_nw}/{_nt}[/{_ncol}]'
                _ns_str= f'[{_ncol}]{_nsig}[/{_ncol}]'
            else:
                _n_str='N/A'; _ns_str='N/A'
            if _sbs:
                _sa,_sw,_st = _sbs
                _ssig,_scol = _sig(_sa)
                _s_str = f'[{_scol}]{_sa:+.1f}% {_sw}/{_st}[/{_scol}]'
                _ss_str= f'[{_scol}]{_ssig}[/{_scol}]'
            else:
                _s_str='[dim]N/A[/dim]'; _ss_str='[dim]N/A[/dim]'
            _qt.add_row(
                '[magenta]BS[/magenta]',
                f'[bold]{_bq}({_sys2})[/bold]',
                _n_str, _ns_str, _s_str, _ss_str,
            )
            if _sys2 == 'NOW':
                _qt.add_row('','','','','','')

        console.print(_qt)
        console.print()

        console.print(f'  Verdict  : {_sv}')
        console.print(f'  [dim]{_greg_agree}[/dim]')
        console.print(f'  [dim]{_bs_agree}[/dim]')
        try:
            _fyq_s_str = f'{_fyq_stock_avg:+.1f}%' if _fyq_stock_ok else 'N/A (<3 qtrs)'
            _fyq_n_str = f'{_fyq_nepse_avg:+.1f}%' if _fyq_nepse_ok else 'N/A'
            _fyq_note = f'  [dim]FYQ: NEPSE {_fyq_n_str} / {symbol} {_fyq_s_str} ({_fyq_now})[/dim]'
        except:
            _fyq_note = f'  [dim]FYQ: insufficient data[/dim]'
        console.print(_fyq_note)
        if not _fyq_stock_ok:
            console.print(f'  [dim yellow]Note: {symbol} listed <3 years — seasonal data limited, using NEPSE signals only[/dim yellow]')
        console.print()

        _seas_col = 'green' if _ss>=70 else 'yellow' if _ss>=40 else 'red'
        _sv_clean = _sv.split(']')[1].split('[')[0].strip() if ']' in _sv else _sv
        section_verdicts.append(('Seasonality', _ss, _sv_clean, _seas_col))
        max_score   += 100
        total_score += _ss

    except Exception as e:
        console.print(f'  [red]Seasonality error: {e}[/red]')
        console.print()

    # ─────────────────────────────────────────
    # FINAL VERDICT
    # ─────────────────────────────────────────
    console.print()
    # === NEPALI FY QUARTERLY (Shrawan-based) ===
    console.print()
    console.rule('[bold]Nepali FY Quarterly Seasonality (Shrawan-based)[/bold]')
    console.print()
    console.print('  [dim]FYQ1=Shrawan-Ashwin  FYQ2=Kartik-Poush  FYQ3=Magh-Chaitra  FYQ4=Baisakh-Ashadh[/dim]')
    console.print()

    # Map BS months to FY quarters
    fy_q_map = {4:'FYQ1',5:'FYQ1',6:'FYQ1',
                7:'FYQ2',8:'FYQ2',9:'FYQ2',
                10:'FYQ3',11:'FYQ3',12:'FYQ3',
                1:'FYQ4',2:'FYQ4',3:'FYQ4'}
    fy_q_labels = {
        'FYQ1':'Shrawan-Bhadra-Ashwin (Jul-Oct)',
        'FYQ2':'Kartik-Mangsir-Poush  (Oct-Jan)',
        'FYQ3':'Magh-Falgun-Chaitra   (Jan-Apr)',
        'FYQ4':'Baisakh-Jestha-Ashadh (Apr-Jul)',
    }

    def _fy_label(bs_yr, bs_m):
        if bs_m in (4,5,6,7,8,9,10,11,12): return bs_yr
        else: return bs_yr - 1

    # Build FY quarterly data from monthly data
    from collections import defaultdict as _dd2
    from datetime import date as _dt_fyq2
    _bs_start_fyq = {
        2077:(2020,4,13),2078:(2021,4,14),2079:(2022,4,14),
        2080:(2023,4,14),2081:(2024,4,13),2082:(2025,4,14),2083:(2026,4,14),
    }
    _bs_mdays_fyq = {
        2077:[31,31,31,32,31,31,30,29,30,29,30,30],
        2078:[31,31,32,31,31,31,30,29,30,29,30,30],
        2079:[31,32,31,32,31,30,30,29,30,29,30,30],
        2080:[31,31,31,32,31,31,30,29,30,29,30,30],
        2081:[31,31,32,31,31,31,30,29,30,29,30,30],
        2082:[31,32,31,32,31,30,30,29,30,29,30,30],
        2083:[31,31,31,32,31,31,30,29,30,29,30,30],
    }
    def _to_bs_fyq(d):
        for yr in sorted(_bs_start_fyq.keys(), reverse=True):
            g = _bs_start_fyq[yr]
            s = _dt_fyq2(g[0],g[1],g[2])
            if d >= s:
                days = (d-s).days
                for mi,md in enumerate(_bs_mdays_fyq.get(yr,[])):
                    if days < md: return yr, mi+1
                    days -= md
                return yr+1,1
        return None,None
    by_fyq      = _dd2(list)
    by_fyq_hl   = _dd2(list)
    _fyq_raw = _dd2(list)
    _fyq_hl_raw = _dd2(list)

    # Load raw trading days grouped by FY quarter
    conn2 = sqlite3.connect(db_path)
    conn2.row_factory = sqlite3.Row
    rows2 = conn2.execute(
        "SELECT date, close, high, low FROM stock_prices "
        "WHERE symbol=? AND close>0 ORDER BY date", (symbol,)
    ).fetchall()
    conn2.close()

    for r in rows2:
        try:
            d = _dt_fyq2.fromisoformat(r['date'])
            bs_yr2, bs_m2 = _to_bs_fyq(d)
            if bs_yr2 and bs_m2:
                fyq  = fy_q_map[bs_m2]
                fy   = _fy_label(bs_yr2, bs_m2)
                key  = (fy, fyq)
                _fyq_raw[key].append((r['close'], r['high'], r['low']))
        except: pass

    # DB first and current FY quarter to skip
    from datetime import date as _dt_fyq
    _today_bs2 = _to_bs_fyq(_dt_fyq2.today())
    _curr_fyq_key = (_fy_label(_today_bs2[0], _today_bs2[1]), fy_q_map[_today_bs2[1]])
    _first_bs2 = _to_bs_fyq(_dt_fyq2(2021,5,25))
    _first_fyq_key = (_fy_label(_first_bs2[0], _first_bs2[1]), fy_q_map[_first_bs2[1]])

    for key, entries in sorted(_fyq_raw.items()):
        if len(entries) < 10: continue
        if key == _curr_fyq_key: continue
        if key == _first_fyq_key: continue
        fy, fyq = key
        oc = entries[0][0]; cc = entries[-1][0]
        hh = max(e[1] for e in entries)
        ll = min(e[2] for e in entries if e[2]>0)
        ret   = (cc-oc)/oc*100
        swing = (hh-ll)/ll*100
        up    = (hh-oc)/oc*100
        dn    = (oc-ll)/oc*100
        by_fyq[fyq].append((fy, ret))
        by_fyq_hl[fyq].append((fy, swing, up, dn))

    # Current and next FY quarter
    curr_fyq = fy_q_map[_today_bs2[1]]
    fyq_order = ['FYQ1','FYQ2','FYQ3','FYQ4']
    curr_fyq_idx = fyq_order.index(curr_fyq)
    next_fyq = fyq_order[(curr_fyq_idx+1) % 4]

    fyqtable = Table(show_header=True, header_style='bold cyan', box=None, padding=(0,1))
    fyqtable.add_column('Quarter',      width=22)
    fyqtable.add_column('Avg Ret',      justify='right', width=8)
    fyqtable.add_column('W/T',          justify='center', width=5)
    fyqtable.add_column('Best',         justify='right', width=7)
    fyqtable.add_column('Worst',        justify='right', width=7)
    fyqtable.add_column('Signal',       width=8)
    fyqtable.add_column('Swing(rng)',   justify='center', width=14)
    fyqtable.add_column('Up',           justify='right', width=6)
    fyqtable.add_column('Dn',           justify='right', width=6)

    for fyq in fyq_order:
        rets = by_fyq[fyq]
        if not rets: continue
        avg   = sum(r for _,r in rets)/len(rets)
        wins  = sum(1 for _,r in rets if r>0)
        best  = max(r for _,r in rets)
        worst = min(r for _,r in rets)
        rng   = by_fyq_hl[fyq]
        avg_sw = sum(r[1] for r in rng)/len(rng) if rng else 0
        min_sw = min(r[1] for r in rng) if rng else 0
        max_sw = max(r[1] for r in rng) if rng else 0
        avg_up = sum(r[2] for r in rng)/len(rng) if rng else 0
        avg_dn = sum(r[3] for r in rng)/len(rng) if rng else 0
        col    = 'green' if avg>=2 else 'yellow' if avg>=-1 else 'red'
        sig    = 'STR.BUY' if avg>=5 else 'BUY' if avg>=2 else 'NTRL' if avg>=-1 else 'AVOID' if avg>=-4 else 'STR.AVD'
        marker = ' <-NOW' if fyq==curr_fyq else (' <-NXT' if fyq==next_fyq else '')
        sw_str = f'{avg_sw:.0f}%({min_sw:.0f}-{max_sw:.0f})'
        lim_tag = ' [dim](limited)[/dim]' if len(rets) < 3 else ''
        fyqtable.add_row(
            f'[bold]{fyq}{marker}[/bold]{lim_tag}',
            f'[{col}]{avg:+.1f}%[/{col}]',
            f'[{col}]{wins}/{len(rets)}[/{col}]',
            f'[green]{best:+.1f}%[/green]',
            f'[red]{worst:+.1f}%[/red]',
            f'[{col}]{sig}[/{col}]',
            f'[yellow]{sw_str}[/yellow]',
            f'[green]+{avg_up:.1f}%[/green]',
            f'[red]-{avg_dn:.1f}%[/red]',
        )

    console.print(fyqtable)
    console.print()

    # FYQ Trading Guide
    console.rule('[bold]Nepali FY Quarter Trading Guide[/bold]')
    console.print()
    for fyq in fyq_order:
        rets = by_fyq[fyq]
        if not rets: continue
        avg   = sum(r for _,r in rets)/len(rets)
        wins  = sum(1 for _,r in rets if r>0)
        rng   = by_fyq_hl[fyq]
        avg_up = round(sum(r[2] for r in rng)/len(rng),1) if rng else 0
        avg_dn = round(sum(r[3] for r in rng)/len(rng),1) if rng else 0
        avg_sw = round(sum(r[1] for r in rng)/len(rng),1) if rng else 0
        marker = ' <-- NOW' if fyq==curr_fyq else (' <- NEXT' if fyq==next_fyq else '')
        col    = 'green' if avg>=2 else 'yellow' if avg>=-1 else 'red'
        if avg_up > abs(avg_dn)*2 and avg>=3:
            char = f'Strong rally — up {avg_up:.1f}% dominates'
        elif avg_up > abs(avg_dn)*2 and avg<3:
            char = f'Rally then fade — up {avg_up:.1f}% given back'
        elif abs(avg_dn) > avg_up*1.5:
            char = f'Downside dominated — drops {avg_dn:.1f}%'
        elif avg_sw > 25:
            char = f'Extreme volatility — {avg_sw:.0f}% swing'
        else:
            char = f'Mixed — up {avg_up:.1f}% / dn {avg_dn:.1f}%'
        if avg>=5:   action = f'Deploy capital — strong tailwind +{avg_up:.1f}%'
        elif avg>=2: action = f'Lean bullish. Dip {avg_dn:.1f}% then rally {avg_up:.1f}%.'
        elif avg>=-1:action = f'Neutral — selective only. Up {avg_up:.1f}% vs dn {avg_dn:.1f}%.'
        elif avg>=-4:action = f'Avoid longs. Drops {avg_dn:.1f}%, recovers {avg_up:.1f}%.'
        else:        action = f'Stay cash. Heavy selling {avg_dn:.1f}% down.'
        console.print(f'  [{col}][bold]{fyq}{marker}[/bold]  ({fy_q_labels[fyq]})  avg={avg:+.1f}%  ({wins}/{len(rets)} up)[/{col}]')
        console.print(f'    Character : {char}')
        console.print(f'    Action    : [{col}]{action}[/{col}]')
        console.print()

    console.print('  [dim]Research only. Not financial advice. Paper trade first.[/dim]')
    console.print()

    console.print()
    console.rule('[bold cyan]Final Verdict[/bold cyan]', style='cyan')
    console.print()

    # Summary table
    t = Table(show_header=True, header_style='bold cyan', box=None, padding=(0,2))
    t.add_column('Section', width=20)
    t.add_column('Score', width=10, justify='right')
    t.add_column('Verdict', width=30)
    for name, score, verdict, col in section_verdicts:
        t.add_row(name, f'[{col}]{score}/100[/{col}]', f'[{col}]{verdict}[/{col}]')
    console.print(t)
    console.print()

    final_pct = (total_score / max_score * 100) if max_score > 0 else 0
    broker_s = next((s for n,s,v,c in section_verdicts if n == 'Broker Activity'), 50)
    tech_s = next((s for n,s,v,c in section_verdicts if n == 'Technical'), 50)
    fund_s = next((s for n,s,v,c in section_verdicts if n == 'Fundamentals'), 50)
    if broker_s <= 40:
        # Broker distributing — never show BUY regardless of other scores
        if final_pct >= 55 and tech_s >= 70:
            final_verdict = '[bold yellow]MOMENTUM ONLY — Price rising but institutions distributing. High risk.[/bold yellow]'
        elif final_pct >= 45:
            final_verdict = '[bold yellow]CAUTION — Institutions distributing. Avoid new entry.[/bold yellow]'
        else:
            final_verdict = '[bold red]AVOID / SELL — Distribution confirmed. Exit or avoid.[/bold red]'
    elif final_pct >= 70 or (broker_s >= 80 and tech_s >= 60):
        final_verdict = '[bold green]STRONG BUY — Strong accumulation and momentum. Good entry.[/bold green]'
    elif final_pct >= 55 or (broker_s >= 70 and final_pct >= 45):
        final_verdict = '[bold green]BUY / ACCUMULATE — Institutional buying active. Consider entering.[/bold green]'
    elif final_pct >= 45 or (broker_s >= 60 and fund_s >= 40):
        final_verdict = '[bold yellow]HOLD / WATCH — Mixed signals. Wait for more confirmation.[/bold yellow]'
    elif final_pct >= 35:
        final_verdict = '[bold yellow]CAUTION — More negatives than positives. Avoid new entry.[/bold yellow]'
    else:
        final_verdict = '[bold red]AVOID / SELL — Weak fundamentals, distribution, bearish trend.[/bold red]'

    # Trading vs Investing label
    if fund_s >= 60 and broker_s >= 60:
        trade_label = '[bold green]INVESTOR + TRADER stock — Strong fundamentals AND momentum[/bold green]'
    elif fund_s >= 60 and broker_s < 60:
        trade_label = '[bold cyan]INVESTOR stock — Good fundamentals but weak momentum. Long term hold.[/bold cyan]'
    elif fund_s < 40 and broker_s >= 70:
        trade_label = '[bold yellow]TRADER stock only — Weak fundamentals but strong momentum. Short term trade, set stop loss.[/bold yellow]'
    elif fund_s < 40 and tech_s >= 60:
        trade_label = '[bold yellow]SPECULATIVE TRADE — Price momentum only. High risk, tight stop loss required.[/bold yellow]'
    else:
        trade_label = '[dim]NEUTRAL — No strong edge for trading or investing right now.[/dim]'

    console.print(f'  Overall Score: [bold]{total_score}/{max_score} ({final_pct:.0f}%)[/bold]')
    console.print()
    console.print(f'  {final_verdict}')
    console.print()
    console.print(f'  {trade_label}')

def analyze_seasonality(db_path='nepse_market_data.db'):
    """Option 38 - Seasonality Analysis"""
    from rich.console import Console
    from rich.rule import Rule
    from rich.table import Table
    console = Console()
    import sqlite3
    from collections import defaultdict
    from datetime import datetime

    console.print()
    console.rule('[bold yellow]Option 38 — NEPSE Seasonality (2021-2026)[/bold yellow]', style='yellow')
    console.print()

    conn = sqlite3.connect(db_path)
    nepse = conn.execute(
        "SELECT date, close FROM stock_prices WHERE symbol='NEPSE' AND close>0 ORDER BY date"
    ).fetchall()
    conn.close()

    if len(nepse) < 100:
        console.print('  Not enough NEPSE data.', style='red')
        return

    month_names = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    # Monthly cumulative returns
    monthly = defaultdict(list)
    for d, c in nepse:
        monthly[d[:7]].append(c)

    by_month = defaultdict(list)
    for ym, closes in sorted(monthly.items()):
        if len(closes) >= 5:
            ret = (closes[-1] - closes[0]) / closes[0] * 100
            by_month[int(ym[5:7])].append((ym[:4], ret))

    # Current month
    today = datetime.now()
    curr_month = today.month
    curr_month_name = month_names[curr_month]
    next_month = (curr_month % 12) + 1
    next_month_name = month_names[next_month]

    # === DISPLAY ===
    # Current + next month highlight
    console.rule(f'[bold]Current Month: {curr_month_name}  |  Next Month: {next_month_name}[/bold]')
    console.print()

    for m in [curr_month, next_month]:
        rets = [r for _, r in by_month[m]]
        if not rets: continue
        avg = sum(rets)/len(rets)
        wins = sum(1 for r in rets if r > 0)
        best = max(rets)
        worst = min(rets)
        col = 'green' if avg >= 2 else 'yellow' if avg >= 0 else 'red'
        verdict = 'STRONG BUY' if avg>=5 and wins==len(rets) else 'BUY' if avg>=2 else 'NEUTRAL' if avg>=-1 else 'AVOID' if avg>=-4 else 'STRONG AVOID'
        console.print(f'  [bold]{month_names[m]}[/bold]  avg=[{col}]{avg:+.1f}%[/{col}]  up={wins}/{len(rets)}  best={best:+.1f}%  worst={worst:+.1f}%  -> [{col}]{verdict}[/{col}]')
        # Year breakdown
        for yr, r in sorted(by_month[m]):
            r_col = 'green' if r > 0 else 'red'
            bar = ('█' if r>0 else '▓') * min(int(abs(r)/2), 20)
            console.print(f'    [{r_col}]{yr}: {r:+.1f}%  {bar}[/{r_col}]')
        console.print()

    # Full year calendar
    console.rule('[bold]Full Year Seasonal Calendar[/bold]')
    console.print()

    # Build high/low range data per month from DB
    import sqlite3 as _sq
    _conn = _sq.connect(db_path)
    _nepse_hl = _conn.execute(
        "SELECT date, high, low, close FROM stock_prices "
        "WHERE symbol='NEPSE' AND close>0 ORDER BY date"
    ).fetchall()
    _conn.close()

    _monthly_hl = defaultdict(list)
    for _d, _h, _l, _c in _nepse_hl:
        _monthly_hl[_d[:7]].append((_h, _l, _c))

    by_month_range = defaultdict(list)
    for ym in sorted(_monthly_hl.keys()):
        rows = _monthly_hl[ym]
        if len(rows) < 5: continue
        ph  = max(r[0] for r in rows)
        pl  = min(r[1] for r in rows if r[1] > 0)
        fc  = rows[0][2]
        lc  = rows[-1][2]
        swing   = (ph-pl)/pl*100
        up_move = (ph-fc)/fc*100
        dn_move = (fc-pl)/fc*100
        m = int(ym[5:7])
        by_month_range[m].append((ym[:4], swing, up_move, dn_move))

    table = Table(show_header=True, header_style='bold cyan', box=None, padding=(0,1))
    table.add_column('Month',    width=10)
    table.add_column('Avg Ret',  justify='right', width=8)
    table.add_column('Up/Total', justify='center', width=9)
    table.add_column('Best',     justify='right', width=8)
    table.add_column('Worst',    justify='right', width=8)
    table.add_column('Signal',   width=8)
    table.add_column('Swing(min-max)', justify='center', width=16)
    table.add_column('Up Move',  justify='right', width=9)
    table.add_column('Dn Move',  justify='right', width=9)

    for m in range(1, 13):
        rets = [r for _, r in by_month[m]]
        if not rets: continue
        avg  = sum(rets)/len(rets)
        wins = sum(1 for r in rets if r > 0)
        best = max(rets)
        worst= min(rets)
        col  = 'green' if avg >= 2 else 'yellow' if avg >= 0 else 'red'
        verdict = 'STR.BUY' if avg>=5 and wins==len(rets) else 'BUY' if avg>=2 else 'NTRL' if avg>=-1 else 'AVOID' if avg>=-3 else 'STR.AVD'
        marker = ' <--' if m == curr_month else ''

        rng = by_month_range[m]
        if rng:
            avg_swing = sum(r[1] for r in rng)/len(rng)
            min_swing = min(r[1] for r in rng)
            max_swing = max(r[1] for r in rng)
            avg_up    = sum(r[2] for r in rng)/len(rng)
            avg_dn    = sum(r[3] for r in rng)/len(rng)
            swing_str = f'{avg_swing:.1f}%({min_swing:.0f}-{max_swing:.0f}%)'
        else:
            swing_str = 'N/A'
            avg_up = avg_dn = 0

        table.add_row(
            f'[bold]{month_names[m]}{marker}[/bold]',
            f'[{col}]{avg:+.1f}%[/{col}]',
            f'[{col}]{wins}/{len(rets)}[/{col}]',
            f'[green]{best:+.1f}%[/green]',
            f'[red]{worst:+.1f}%[/red]',
            f'[{col}]{verdict}[/{col}]',
            f'[yellow]{swing_str}[/yellow]',
            f'[green]+{avg_up:.1f}%[/green]',
            f'[red]-{avg_dn:.1f}%[/red]',
        )

    console.print(table)
    console.print()

    # Best/worst summary
    sorted_months = sorted(range(1,13), key=lambda m: sum(r for _,r in by_month[m])/len(by_month[m]) if by_month[m] else 0, reverse=True)
    console.rule('[bold]Ranked by Average Return[/bold]')
    console.print()
    console.print('  [green]Best months to be invested:[/green]')
    for m in sorted_months[:3]:
        rets = [r for _,r in by_month[m]]
        avg = sum(rets)/len(rets)
        wins = sum(1 for r in rets if r>0)
        console.print(f'    [green]{month_names[m]:>3}: avg {avg:+.1f}%  ({wins}/{len(rets)} up)[/green]')
    console.print()
    console.print('  [red]Worst months — stay in cash:[/red]')
    for m in sorted_months[-3:]:
        rets = [r for _,r in by_month[m]]
        avg = sum(rets)/len(rets)
        wins = sum(1 for r in rets if r>0)
        console.print(f'    [red]{month_names[m]:>3}: avg {avg:+.1f}%  ({wins}/{len(rets)} up)[/red]')
    console.print()

    # Actionable advice
    curr_rets = [r for _,r in by_month[curr_month]]
    curr_avg  = sum(curr_rets)/len(curr_rets) if curr_rets else 0
    console.rule(f'[bold]What To Do in {curr_month_name}[/bold]')
    console.print()

    # Monthly character
    _m_rng = by_month_range[today.month]
    _m_up  = round(sum(r[2] for r in _m_rng)/len(_m_rng),1) if _m_rng else 0
    _m_dn  = round(sum(r[3] for r in _m_rng)/len(_m_rng),1) if _m_rng else 0
    _m_sw  = round(sum(r[1] for r in _m_rng)/len(_m_rng),1) if _m_rng else 0
    if _m_up > abs(_m_dn)*2 and curr_avg >= 3:
        _m_char = f'Strong one-way rally — up {_m_up:.1f}% with only -{_m_dn:.1f}% dip'
    elif _m_up > abs(_m_dn)*2 and curr_avg < 3:
        _m_char = f'Big rally then reversal — up {_m_up:.1f}% but gains given back'
    elif abs(_m_dn) > _m_up*1.5:
        _m_char = f'Downside dominated — drops {_m_dn:.1f}% from open, only bounces {_m_up:.1f}%'
    elif _m_sw > 15:
        _m_char = f'High volatility — {_m_sw:.1f}% swing, choppy both ways'
    elif _m_sw < 8:
        _m_char = f'Quiet month — only {_m_sw:.1f}% total range'
    elif curr_avg >= 2:
        _m_char = f'Bullish bias — up {_m_up:.1f}% vs dn {_m_dn:.1f}%, trend favors longs'
    else:
        _m_char = f'Mixed — up {_m_up:.1f}% / dn {_m_dn:.1f}% from open'

    _m_col = 'green' if curr_avg >= 2 else 'yellow' if curr_avg >= -1 else 'red'
    console.print(f'  Character : [{_m_col}]{_m_char}[/{_m_col}]')
    console.print(f'  Swing     : [yellow]{_m_sw:.1f}%[/yellow]  Up={_m_up:.1f}%  Dn={_m_dn:.1f}%')
    console.print()

    if curr_avg >= 5:
        console.print(f'  [bold green]{curr_month_name} is historically the strongest month.[/bold green]')
        console.print('  [green]-> Deploy capital now — seasonal tailwind is strong[/green]')
        console.print('  [green]-> Look for breakouts — market tends to rally hard[/green]')
        console.print('  [green]-> Run option 36 daily for R/R setups[/green]')
    elif curr_avg >= 2:
        console.print(f'  [bold green]{curr_month_name} is a positive month historically.[/bold green]')
        console.print('  [green]-> Lean bullish — seasonal tailwind[/green]')
        console.print('  [green]-> Take setups from option 36 with confidence[/green]')
    elif curr_avg >= -1:
        console.print(f'  [bold yellow]{curr_month_name} is neutral historically.[/bold yellow]')
        console.print('  [yellow]-> No seasonal edge — rely on option 37 market phase[/yellow]')
        console.print('  [yellow]-> Be selective, normal position sizes[/yellow]')
    elif curr_avg >= -3:
        console.print(f'  [bold red]{curr_month_name} is a weak month historically.[/bold red]')
        console.print('  [red]-> Reduce position sizes[/red]')
        console.print('  [red]-> Tighten stop losses[/red]')
        console.print('  [red]-> Only enter if option 37 shows ACCUMULATION or better[/red]')
    else:
        console.print(f'  [bold red]{curr_month_name} is historically the worst period.[/bold red]')
        console.print('  [red]-> Stay in cash — seasonal headwind is strong[/red]')
        console.print('  [red]-> Do not buy dips — they tend to get worse[/red]')
        console.print('  [red]-> Wait for next month[/red]')
    console.print()

    # === QUARTERLY SEASONALITY ===
    console.rule('[bold]Quarterly Seasonality (Calendar Year)[/bold]')
    console.print()

    quarterly = defaultdict(list)
    for d, c in nepse:
        m = int(d[5:7])
        q = (m-1)//3 + 1
        key = f'{d[:4]}-Q{q}'
        quarterly[key].append(c)

    from datetime import date as _dt38
    _curr_q38 = f'Q{(_dt38.today().month-1)//3+1}'
    _curr_yr38 = str(_dt38.today().year)
    _first_q38 = f'Q{(5-1)//3+1}'
    _first_yr38 = '2021'

    by_q = defaultdict(list)
    for k, closes in sorted(quarterly.items()):
        if len(closes) >= 10:
            yr38 = k[:4]
            q38  = k[-2:]
            if (yr38, q38) == (_curr_yr38, _curr_q38): continue
            if (yr38, q38) == (_first_yr38, _first_q38): continue
            ret = (closes[-1]-closes[0])/closes[0]*100
            by_q[q38].append((yr38, ret))

    # Quarterly range from HL data
    import sqlite3 as _sq2
    _conn2 = _sq2.connect(db_path)
    _hl2 = _conn2.execute(
        "SELECT date, high, low, close FROM stock_prices "
        "WHERE symbol='NEPSE' AND close>0 ORDER BY date"
    ).fetchall()
    _conn2.close()
    _qhl = defaultdict(list)
    for _d, _h, _l, _c in _hl2:
        _m = int(_d[5:7]); _qq = f'Q{(_m-1)//3+1}'
        _qhl[f'{_d[:4]}-{_qq}'].append((_h, _l, _c))
    by_q_range = defaultdict(list)
    for _k in sorted(_qhl.keys()):
        _rows = _qhl[_k]
        if len(_rows) < 10: continue
        _ph = max(r[0] for r in _rows)
        _pl = min(r[1] for r in _rows if r[1]>0)
        _fc = _rows[0][2]; _lc = _rows[-1][2]
        _swing = (_ph-_pl)/_pl*100
        _up    = (_ph-_fc)/_fc*100
        _dn    = (_fc-_pl)/_fc*100
        _qq = _k.split('-')[1]
        by_q_range[_qq].append((_k[:4], _swing, _up, _dn))

    curr_q = f'Q{(today.month-1)//3+1}'
    next_q = f'Q{((today.month-1)//3+1)%4+1}'

    qtable = Table(show_header=True, header_style='bold cyan', box=None, padding=(0,1))
    qtable.add_column('Quarter', width=10)
    qtable.add_column('Avg Ret', justify='right', width=8)
    qtable.add_column('W/T',     justify='center', width=5)
    qtable.add_column('Best',    justify='right', width=7)
    qtable.add_column('Worst',   justify='right', width=7)
    qtable.add_column('Signal',  width=8)
    qtable.add_column('Swing(rng)', justify='center', width=14)
    qtable.add_column('Up',      justify='right', width=6)
    qtable.add_column('Dn',      justify='right', width=6)
    qtable.add_column('Years',   width=30)

    for q in ['Q1','Q2','Q3','Q4']:
        rets = [r for _,r in by_q[q]]
        if not rets: continue
        avg  = sum(rets)/len(rets)
        wins = sum(1 for r in rets if r>0)
        best = max(rets)
        worst= min(rets)
        col  = 'green' if avg>=3 else 'yellow' if avg>=0 else 'red'
        verdict = 'STR.BUY' if avg>=8 else 'BUY' if avg>=3 else 'NTRL' if avg>=-1 else 'AVOID' if avg>=-4 else 'STR.AVD'
        marker = ' <--' if q == curr_q else (' next' if q == next_q else '')
        yr_detail = '  '.join(f'{yr}:{r:+.0f}%' for yr,r in sorted(by_q[q]))
        rng_q = by_q_range[q]
        if rng_q:
            avg_sw_q = sum(r[1] for r in rng_q)/len(rng_q)
            min_sw_q = min(r[1] for r in rng_q)
            max_sw_q = max(r[1] for r in rng_q)
            avg_up_q = sum(r[2] for r in rng_q)/len(rng_q)
            avg_dn_q = sum(r[3] for r in rng_q)/len(rng_q)
            sw_str_q = f'{avg_sw_q:.1f}%({min_sw_q:.0f}-{max_sw_q:.0f}%)'
        else:
            sw_str_q = 'N/A'; avg_up_q = avg_dn_q = 0
        qtable.add_row(
            f'[bold]{q}{marker}[/bold]',
            f'[{col}]{avg:+.1f}%[/{col}]',
            f'[{col}]{wins}/{len(rets)}[/{col}]',
            f'[green]{best:+.1f}%[/green]',
            f'[red]{worst:+.1f}%[/red]',
            f'[{col}]{verdict}[/{col}]',
            f'[yellow]{sw_str_q}[/yellow]',
            f'[green]+{avg_up_q:.1f}%[/green]',
            f'[red]-{avg_dn_q:.1f}%[/red]',
            f'[dim]{yr_detail}[/dim]',
        )

    console.print(qtable)
    console.print()

    # Quarterly insights
    console.rule('[bold]Quarterly Trading Guide[/bold]')
    console.print()
    for q in ['Q1','Q2','Q3','Q4']:
        rets = [r for _,r in by_q[q]]
        if not rets: continue
        avg  = sum(rets)/len(rets)
        wins = sum(1 for r in rets if r>0)
        rng  = by_q_range[q]
        avg_up = round(sum(r[2] for r in rng)/len(rng),1) if rng else 0
        avg_dn = round(sum(r[3] for r in rng)/len(rng),1) if rng else 0
        avg_sw = round(sum(r[1] for r in rng)/len(rng),1) if rng else 0
        marker = ' <-- NOW' if q==curr_q else (' <- NEXT' if q==next_q else '')
        col = 'green' if avg>=2 else 'yellow' if avg>=-1 else 'red'

        # Character assessment
        if avg_up > abs(avg_dn)*2 and avg >= 3:
            char = f'Strong directional rally — up {avg_up:.1f}% dominates, minimal pullback'
        elif avg_up > abs(avg_dn)*2 and avg < 3:
            char = f'Big rally then reversal — up {avg_up:.1f}% but gains given back, volatile'
        elif abs(avg_dn) > avg_up*1.5:
            char = f'Downside dominated — drops {avg_dn:.1f}% from open, bounces only {avg_up:.1f}%'
        elif avg_sw > 25:
            char = f'Extreme volatility — {avg_sw:.0f}% total swing, both sides active'
        elif avg_sw < 12:
            char = f'Low volatility — quiet quarter, only {avg_sw:.0f}% total range'
        elif avg >= 2:
            char = f'Bullish bias — up {avg_up:.1f}% vs dn {avg_dn:.1f}%, trend favors longs'
        else:
            char = f'Mixed — up {avg_up:.1f}% / dn {avg_dn:.1f}% from open, no clear edge'

        # Action
        if avg >= 5:
            action = f'Deploy capital — strong seasonal tailwind. Rally avg +{avg_up:.1f}% from open.'
        elif avg >= 2:
            action = f'Lean bullish. Dip only {avg_dn:.1f}% before rallying {avg_up:.1f}% — tight stops work.'
        elif avg >= -1:
            if avg_up > abs(avg_dn):
                action = f'Neutral but upside bias (+{avg_up:.1f}% up vs -{avg_dn:.1f}% dn) — selective entries only.'
            else:
                action = f'Neutral with downside risk (-{avg_dn:.1f}% dn vs +{avg_up:.1f}% up) — reduce size.'
        elif avg >= -4:
            action = f'Avoid new longs. Drops -{avg_dn:.1f}% from open, only recovers +{avg_up:.1f}%.'
        else:
            action = f'Stay in cash. Heavy selling quarter — down {avg_dn:.1f}% with {avg_sw:.0f}% total swing.'

        console.print(f'  [{col}][bold]{q}{marker}[/bold]  avg={avg:+.1f}%  ({wins}/{len(rets)} up)  swing={avg_sw:.1f}%[/{col}]')
        console.print(f'    Character : {char}')
        console.print(f'    Action    : [{col}]{action}[/{col}]')
        console.print()

    # === YEARLY SEASONALITY ===
    console.rule('[bold]Yearly Performance[/bold]')
    console.print()

    yearly = defaultdict(list)
    for d, c in nepse:
        yearly[d[:4]].append((d, c))

    # Yearly range from HL data
    import sqlite3 as _sq3
    _conn3 = _sq3.connect(db_path)
    _hl3 = _conn3.execute(
        "SELECT date, high, low, close FROM stock_prices "
        "WHERE symbol='NEPSE' AND close>0 ORDER BY date"
    ).fetchall()
    _conn3.close()
    _yhl = defaultdict(list)
    for _d, _h, _l, _c in _hl3:
        _yhl[_d[:4]].append((_h, _l, _c))
    yr_range = {}
    for _yr, _rows in _yhl.items():
        if len(_rows) < 5: continue
        _ph = max(r[0] for r in _rows)
        _pl = min(r[1] for r in _rows if r[1]>0)
        _fc = _rows[0][2]
        yr_range[_yr] = (
            (_ph-_pl)/_pl*100,
            (_ph-_fc)/_fc*100,
            (_fc-_pl)/_fc*100,
        )

    ytable = Table(show_header=True, header_style='bold cyan', box=None, padding=(0,1))
    ytable.add_column('Year',    width=10)
    ytable.add_column('Start',   justify='right', width=8)
    ytable.add_column('End',     justify='right', width=8)
    ytable.add_column('Return',  justify='right', width=8)
    ytable.add_column('Days',    justify='right', width=6)
    ytable.add_column('Swing',   justify='center', width=8)
    ytable.add_column('Up Move', justify='right', width=9)
    ytable.add_column('Dn Move', justify='right', width=9)

    for yr in sorted(yearly.keys()):
        closes = [c for _, c in sorted(yearly[yr])]
        if len(closes) < 5: continue
        ret = (closes[-1]-closes[0])/closes[0]*100
        col = 'green' if ret>0 else 'red'
        marker = ' <--' if yr == str(today.year) else ''
        sw, up, dn = yr_range.get(yr, (0,0,0))
        ytable.add_row(
            f'[bold]{yr}{marker}[/bold]',
            f'{closes[0]:,.1f}',
            f'{closes[-1]:,.1f}',
            f'[{col}]{ret:+.1f}%[/{col}]',
            str(len(closes)),
            f'[yellow]{sw:.1f}%[/yellow]',
            f'[green]+{up:.1f}%[/green]',
            f'[red]-{dn:.1f}%[/red]',
        )

    console.print(ytable)
    console.print()

    # Year summary
    all_yr_rets = []
    for yr in sorted(yearly.keys()):
        closes = [c for _,c in sorted(yearly[yr])]
        if len(closes)>=20:
            all_yr_rets.append((yr, (closes[-1]-closes[0])/closes[0]*100))
    if all_yr_rets:
        up_yrs = sum(1 for _,r in all_yr_rets if r>0)
        avg_yr = sum(r for _,r in all_yr_rets)/len(all_yr_rets)
        console.print(f'  Full years: {up_yrs}/{len(all_yr_rets)-1} up  |  avg annual return: {avg_yr:+.1f}%')
        console.print()

    # Yearly insights
    console.rule('[bold]Yearly Cycle Insights[/bold]')
    console.print()
    yr_list = sorted(yr_range.keys())
    for yr in yr_list:
        sw, up, dn = yr_range[yr]
        closes_yr = [c for _,c in sorted(yearly.get(yr,[]))]
        if len(closes_yr) < 5: continue
        ret = (closes_yr[-1]-closes_yr[0])/closes_yr[0]*100
        col = 'green' if ret>0 else 'red'
        marker = ' <-- NOW' if yr==str(today.year) else ''

        if up > abs(dn)*3:
            char = f'One-way bull — rallied +{up:.1f}% with only -{dn:.1f}% drawdown'
        elif abs(dn) > up*2:
            char = f'One-way bear — dropped -{dn:.1f}% with only +{up:.1f}% bounce'
        elif sw > 50:
            char = f'Extreme volatility — {sw:.0f}% total swing, both sides active'
        elif sw < 20:
            char = f'Quiet year — only {sw:.0f}% total range'
        else:
            char = f'Two-sided — up {up:.1f}% / dn {dn:.1f}% from year open'

        if ret >= 15:
            action = f'Strong bull year. Enter early, hold through dips (only -{dn:.1f}%).'
        elif ret >= 5:
            action = f'Positive year. Selective entries work — avg rally +{up:.1f}% from open.'
        elif ret >= -2:
            action = f'Flat year. Trading range only — no trend following.'
        elif ret >= -15:
            action = f'Down year. Cash preservation beats stock holding.'
        else:
            action = f'Crash year. Heavy losses — staying out was the right call.'

        console.print(f'  [{col}][bold]{yr}{marker}[/bold]  {ret:+.1f}%  swing={sw:.1f}%[/{col}]')
        console.print(f'    Character : {char}')
        console.print(f'    Action    : [{col}]{action}[/{col}]')
        console.print()

    # === NEPALI FISCAL YEAR QUARTERLY SEASONALITY ===
    console.rule('[bold]Nepali Fiscal Year Quarterly Seasonality[/bold]')
    console.print()

    # True BS date boundaries for NQ quarters
    _bs38_start = {
        2077:(2020,4,13),2078:(2021,4,14),2079:(2022,4,14),
        2080:(2023,4,14),2081:(2024,4,13),2082:(2025,4,14),2083:(2026,4,14),
    }
    _bs38_mdays = {
        2077:[31,31,31,32,31,31,30,29,30,29,30,30],
        2078:[31,31,32,31,31,31,30,29,30,29,30,30],
        2079:[31,32,31,32,31,30,30,29,30,29,30,30],
        2080:[31,31,31,32,31,31,30,29,30,29,30,30],
        2081:[31,31,32,31,31,31,30,29,30,29,30,30],
        2082:[31,32,31,32,31,30,30,29,30,29,30,30],
        2083:[31,31,31,32,31,31,30,29,30,29,30,30],
    }
    # BS month -> NQ quarter (Shrawan=4 is NQ1)
    _bs38_nq = {4:'NQ1',5:'NQ1',6:'NQ1',
                7:'NQ2',8:'NQ2',9:'NQ2',
                10:'NQ3',11:'NQ3',12:'NQ3',
                1:'NQ4',2:'NQ4',3:'NQ4'}
    # BS month -> FY offset (months before Shrawan belong to previous FY)
    # Shrawan(4)-Ashadh(3) = same FY as BS year
    # Baisakh(1)-Ashadh(3) = NQ4 of previous BS year's FY

    def _to_bs38(d_str):
        from datetime import date as _d
        d = _d.fromisoformat(d_str)
        for yr in sorted(_bs38_start.keys(), reverse=True):
            g = _bs38_start[yr]
            s = _d(g[0],g[1],g[2])
            if d >= s:
                days = (d-s).days
                for mi,md in enumerate(_bs38_mdays.get(yr,[])):
                    if days < md: return yr, mi+1
                    days -= md
                return yr+1, 1
        return None, None

    def _bs38_fy(bs_yr, bs_m):
        # NQ1=Shrawan-Ashwin(m4-6), NQ2=Kartik-Poush(m7-9)
        # NQ3=Magh-Chaitra(m10-12), NQ4=Baisakh-Ashadh(m1-3)
        # FY label = BS year when Shrawan starts
        if bs_m in (4,5,6,7,8,9,10,11,12):
            return bs_yr
        else:  # m 1,2,3 = NQ4 of previous FY
            return bs_yr - 1

    nq_data = defaultdict(list)
    for d, c in nepse:
        bs_yr, bs_m = _to_bs38(d)
        if bs_yr and bs_m:
            nq  = _bs38_nq[bs_m]
            fy  = _bs38_fy(bs_yr, bs_m)
            key = f'{fy}-{nq}'
            nq_data[key].append(c)

    # Current and first partial NQ filters
    _today_bs38 = _to_bs38(str(today.date()))
    _curr_nq_key  = f'{_bs38_fy(_today_bs38[0], _today_bs38[1])}-{_bs38_nq[_today_bs38[1]]}'
    _first_bs38   = _to_bs38('2021-05-25')
    _first_nq_key = f'{_bs38_fy(_first_bs38[0], _first_bs38[1])}-{_bs38_nq[_first_bs38[1]]}'

    by_nq = defaultdict(list)
    for k in sorted(nq_data.keys()):
        closes = nq_data[k]
        if len(closes) >= 10:
            if k == _curr_nq_key: continue
            if k == _first_nq_key: continue
            ret = (closes[-1]-closes[0])/closes[0]*100
            nq = k.split('-')[1]
            fy = k.split('-')[0]
            by_nq[nq].append((fy, ret))

    curr_nq = _bs38_nq[_to_bs38(str(today.date()))[1]]
    next_nq = {'NQ1':'NQ2','NQ2':'NQ3','NQ3':'NQ4','NQ4':'NQ1'}[curr_nq]
    nq_labels = {'NQ1':'Jul-Sep','NQ2':'Oct-Dec','NQ3':'Jan-Mar','NQ4':'Apr-Jun'}

    # NQ range from HL data
    import sqlite3 as _sq4
    _conn4 = _sq4.connect(db_path)
    _hl4 = _conn4.execute(
        "SELECT date, high, low, close FROM stock_prices "
        "WHERE symbol='NEPSE' AND close>0 ORDER BY date"
    ).fetchall()
    _conn4.close()
    _nqhl = defaultdict(list)
    for _d, _h, _l, _c in _hl4:
        _bs_yr38, _bs_m38 = _to_bs38(_d)
        if _bs_yr38 and _bs_m38:
            _nqk = f'{_bs38_fy(_bs_yr38, _bs_m38)}-{_bs38_nq[_bs_m38]}'
            _nqhl[_nqk].append((_h, _l, _c))
    by_nq_range = defaultdict(list)
    for _k in sorted(_nqhl.keys()):
        _rows = _nqhl[_k]
        if len(_rows) < 10: continue
        _ph = max(r[0] for r in _rows)
        _pl = min(r[1] for r in _rows if r[1]>0)
        _fc = _rows[0][2]
        _nq = _k.split('-')[1]
        by_nq_range[_nq].append((
            _k[:4],
            (_ph-_pl)/_pl*100,
            (_ph-_fc)/_fc*100,
            (_fc-_pl)/_fc*100,
        ))

    nqtable = Table(show_header=True, header_style='bold cyan', box=None, padding=(0,1))
    nqtable.add_column('Quarter',       width=18)
    nqtable.add_column('Ret',           justify='right', width=7)
    nqtable.add_column('W/T',           justify='center', width=5)
    nqtable.add_column('Best',          justify='right', width=7)
    nqtable.add_column('Worst',         justify='right', width=7)
    nqtable.add_column('Signal',        width=8)
    nqtable.add_column('Swing(rng)',    justify='center', width=14)
    nqtable.add_column('Up',            justify='right', width=6)
    nqtable.add_column('Dn',            justify='right', width=6)
    nqtable.add_column('History',       width=32)

    for nq in ['NQ1','NQ2','NQ3','NQ4']:
        rets = [r for _,r in by_nq[nq]]
        if not rets: continue
        avg   = sum(rets)/len(rets)
        wins  = sum(1 for r in rets if r>0)
        best  = max(rets)
        worst = min(rets)
        col   = 'green' if avg>=3 else 'yellow' if avg>=0 else 'red'
        verdict = 'STR.BUY' if avg>=8 else 'BUY' if avg>=3 else 'NTRL' if avg>=-1 else 'AVOID' if avg>=-4 else 'STR.AVD'
        marker = ' <-NOW' if nq==curr_nq else (' <-NXT' if nq==next_nq else '')
        yr_detail = '  '.join(f'{fy}:{r:+.0f}%' for fy,r in sorted(by_nq[nq]))
        rng_nq = by_nq_range[nq]
        if rng_nq:
            avg_sw_nq = sum(r[1] for r in rng_nq)/len(rng_nq)
            min_sw_nq = min(r[1] for r in rng_nq)
            max_sw_nq = max(r[1] for r in rng_nq)
            avg_up_nq = sum(r[2] for r in rng_nq)/len(rng_nq)
            avg_dn_nq = sum(r[3] for r in rng_nq)/len(rng_nq)
            sw_str_nq = f'{avg_sw_nq:.1f}%({min_sw_nq:.0f}-{max_sw_nq:.0f}%)'
        else:
            sw_str_nq = 'N/A'; avg_up_nq = avg_dn_nq = 0
        nqtable.add_row(
            f'[bold]{nq} ({nq_labels[nq]}){marker}[/bold]',
            f'[{col}]{avg:+.1f}%[/{col}]',
            f'[{col}]{wins}/{len(rets)}[/{col}]',
            f'[green]{best:+.1f}%[/green]',
            f'[red]{worst:+.1f}%[/red]',
            f'[{col}]{verdict}[/{col}]',
            f'[yellow]{sw_str_nq}[/yellow]',
            f'[green]+{avg_up_nq:.1f}%[/green]',
            f'[red]-{avg_dn_nq:.1f}%[/red]',
            f'[dim]{yr_detail}[/dim]',
        )

    console.print(nqtable)
    console.print()

    # NQ insights
    console.rule('[bold]Nepali FY Quarterly Trading Guide[/bold]')
    console.print()
    for nq in ['NQ1','NQ2','NQ3','NQ4']:
        rets = [r for _,r in by_nq[nq]]
        if not rets: continue
        avg  = sum(rets)/len(rets)
        wins = sum(1 for r in rets if r>0)
        rng  = by_nq_range[nq]
        avg_up = round(sum(r[2] for r in rng)/len(rng),1) if rng else 0
        avg_dn = round(sum(r[3] for r in rng)/len(rng),1) if rng else 0
        avg_sw = round(sum(r[1] for r in rng)/len(rng),1) if rng else 0
        marker = ' <-- NOW' if nq==curr_nq else (' <- NEXT' if nq==next_nq else '')
        col = 'green' if avg>=2 else 'yellow' if avg>=-1 else 'red'
        label = nq_labels[nq]

        if avg_up > abs(avg_dn)*2 and avg >= 3:
            char = f'Strong directional rally — up {avg_up:.1f}% dominates, minimal pullback'
        elif avg_up > abs(avg_dn)*2 and avg < 3:
            char = f'Big rally then reversal — up {avg_up:.1f}% but gains given back, volatile'
        elif abs(avg_dn) > avg_up*1.5:
            char = f'Downside dominated — drops {avg_dn:.1f}% from open, bounces only {avg_up:.1f}%'
        elif avg_sw > 25:
            char = f'Extreme volatility — {avg_sw:.0f}% total swing, both sides active'
        elif avg_sw < 12:
            char = f'Low volatility — quiet quarter, only {avg_sw:.0f}% total range'
        elif avg >= 2:
            char = f'Bullish bias — up {avg_up:.1f}% vs dn {avg_dn:.1f}%, trend favors longs'
        else:
            char = f'Mixed — up {avg_up:.1f}% / dn {avg_dn:.1f}% from open, no clear edge'

        if avg >= 5:
            action = f'Deploy capital — strong seasonal tailwind. Rally avg +{avg_up:.1f}% from open.'
        elif avg >= 2:
            action = f'Lean bullish. Dip only {avg_dn:.1f}% before rallying {avg_up:.1f}% — tight stops work.'
        elif avg >= -1:
            if avg_up > abs(avg_dn):
                action = f'Neutral but upside bias (+{avg_up:.1f}% up vs -{avg_dn:.1f}% dn) — selective entries only.'
            else:
                action = f'Neutral with downside risk (-{avg_dn:.1f}% dn vs +{avg_up:.1f}% up) — reduce size.'
        elif avg >= -4:
            action = f'Avoid new longs. Drops -{avg_dn:.1f}% from open, only recovers +{avg_up:.1f}%.'
        else:
            action = f'Stay in cash. Heavy selling quarter — down {avg_dn:.1f}% with {avg_sw:.0f}% total swing.'

        console.print(f'  [{col}][bold]{nq} ({label}){marker}[/bold]  avg={avg:+.1f}%  ({wins}/{len(rets)} up)  swing={avg_sw:.1f}%[/{col}]')
        console.print(f'    Character : {char}')
        console.print(f'    Action    : [{col}]{action}[/{col}]')
        console.print()

    # Current NQ advice
    curr_rets = [r for _,r in by_nq[curr_nq]]
    curr_avg  = sum(curr_rets)/len(curr_rets) if curr_rets else 0
    next_rets = [r for _,r in by_nq[next_nq]]
    next_avg  = sum(next_rets)/len(next_rets) if next_rets else 0
    col_now  = 'green' if curr_avg>=3 else 'yellow' if curr_avg>=-1 else 'red'
    col_next = 'green' if next_avg>=3 else 'yellow' if next_avg>=-1 else 'red'
    console.print(f'  Now  ({curr_nq} {nq_labels[curr_nq]}): [{col_now}]avg {curr_avg:+.1f}%[/{col_now}]')
    console.print(f'  Next ({next_nq} {nq_labels[next_nq]}): [{col_next}]avg {next_avg:+.1f}%[/{col_next}]')
    console.print()

    # === YEAR CYCLE ANALYSIS ===
    console.rule('[bold]Year Cycle Analysis & 2026 Projection[/bold]')
    console.print()

    # Build full year returns
    yearly2 = defaultdict(list)
    for d, c in nepse:
        yearly2[d[:4]].append((d, c))

    yr_rets = {}
    for yr in sorted(yearly2.keys()):
        closes = [c for _, c in sorted(yearly2[yr])]
        if len(closes) >= 20:
            yr_rets[yr] = round((closes[-1]-closes[0])/closes[0]*100, 1)

    # Classify each year
    def yr_label(r):
        if r >= 15:  return ('BULL',   'green')
        if r >= 5:   return ('UP',     'green')
        if r >= -2:  return ('FLAT',   'yellow')
        if r >= -10: return ('DOWN',   'red')
        return           ('CRASH',  'red')

    console.print('  [bold]Historical Year Cycle:[/bold]')
    console.print()
    yrs = sorted(yr_rets.keys())
    for i, yr in enumerate(yrs):
        r = yr_rets[yr]
        label, col = yr_label(r)
        arrow = ''
        if i > 0:
            prev = yr_rets[yrs[i-1]]
            arrow = '[green]▲[/green]' if r > prev else '[red]▼[/red]' if r < prev else '[yellow]=[/yellow]'
        bar_len = min(int(abs(r)/2), 15)
        bar = ('█' if r>=0 else '▓') * bar_len
        console.print(f'  {arrow} [bold]{yr}[/bold]: [{col}]{r:+.1f}%  {label}[/{col}]  [{col}]{bar}[/{col}]')

    console.print()

    # Cycle pattern detection
    console.print('  [bold]Cycle Pattern (2021-2026):[/bold]')
    console.print()
    pattern = []
    for yr in yrs:
        l, _ = yr_label(yr_rets[yr])
        pattern.append(f'{yr}:{l}')
    console.print('  ' + '  ->  '.join(pattern))
    console.print()

    # 2026 projection
    curr_yr = str(today.year)
    curr_yr_days = len(yearly2.get(curr_yr, []))
    curr_yr_ret  = yr_rets.get(curr_yr, 0)

    # Remaining months in year
    remaining_months = 12 - today.month
    # Sum seasonality for remaining months
    remaining_seasonal = sum(
        sum(r for _,r in by_month[m])/len(by_month[m])
        for m in range(today.month+1, 13)
        if by_month[m]
    )
    projected_additional = round(remaining_seasonal, 1)
    projected_total = round(curr_yr_ret + projected_additional, 1)
    proj_label, proj_col = yr_label(projected_total)

    console.rule(f'[bold cyan]2026 Projection[/bold cyan]')
    console.print()
    console.print(f'  Year to date ({curr_yr_days} trading days): [bold]{curr_yr_ret:+.1f}%[/bold]')
    console.print(f'  Remaining months: {remaining_months}')
    console.print(f'  Historical avg for remaining months: {projected_additional:+.1f}%')
    console.print()
    console.print(f'  [bold cyan]Projected full year 2026: [{proj_col}]{projected_total:+.1f}% ({proj_label})[/{proj_col}][/bold cyan]')
    console.print()

    # Key dates coming up
    console.rule('[bold]Key Seasonal Dates Ahead[/bold]')
    console.print()
    upcoming = [
        (7,  'Jul',  'STRONG BUY',  'green',  'Best month of year — deploy capital'),
        (8,  'Aug',  'AVOID',       'red',    'Exit July positions — historically -4.4%'),
        (9,  'Sep',  'STRONG AVOID','red',    'Worst month — stay in cash'),
        (10, 'Oct',  'NEUTRAL',     'yellow', 'Cautious re-entry possible'),
        (1,  'Jan',  'BUY',         'green',  'Second best month — avg +4.5%'),
    ]
    for m, name, sig, col, note in upcoming:
        if m > today.month or (m < today.month and m == 1):
            console.print(f'  [{col}]{name:>4}: {sig:<12} — {note}[/{col}]')
    console.print()

    # === MASTER SUMMARY ===
    console.rule('[bold yellow]MASTER SUMMARY — All Timeframes[/bold yellow]')
    console.print()

    # Current conditions
    curr_m_avg  = sum(r for _,r in by_month[today.month]) / len(by_month[today.month]) if by_month[today.month] else 0
    curr_q_avg  = sum(r for _,r in by_q[curr_q]) / len(by_q[curr_q]) if by_q[curr_q] else 0
    curr_nq_avg = sum(r for _,r in by_nq[curr_nq]) / len(by_nq[curr_nq]) if by_nq[curr_nq] else 0
    curr_yr_ret = yr_rets.get(str(today.year), 0)

    # Upcoming conditions
    next_m      = today.month % 12 + 1
    next_m_avg  = sum(r for _,r in by_month[next_m]) / len(by_month[next_m]) if by_month[next_m] else 0
    next_q_avg  = sum(r for _,r in by_q[next_q]) / len(by_q[next_q]) if by_q[next_q] else 0
    next_nq_avg = sum(r for _,r in by_nq[next_nq]) / len(by_nq[next_nq]) if by_nq[next_nq] else 0

    def _sig(avg):
        if avg >= 5:   return ('STRONG BUY',  'green')
        if avg >= 2:   return ('BUY',         'green')
        if avg >= -1:  return ('NEUTRAL',      'yellow')
        if avg >= -4:  return ('AVOID',        'red')
        return              ('STRONG AVOID', 'red')

    # Current row
    cm_sig, cm_col   = _sig(curr_m_avg)
    cq_sig, cq_col   = _sig(curr_q_avg)
    cnq_sig, cnq_col = _sig(curr_nq_avg)
    cy_sig, cy_col   = _sig(curr_yr_ret)

    # Upcoming row
    nm_sig, nm_col   = _sig(next_m_avg)
    nq_sig, nq_col   = _sig(next_q_avg)
    nnq_sig, nnq_col = _sig(next_nq_avg)

    # Overall current bias
    curr_scores = [curr_m_avg, curr_q_avg, curr_nq_avg, curr_yr_ret]
    curr_bias   = sum(curr_scores) / len(curr_scores)
    next_scores = [next_m_avg, next_q_avg, next_nq_avg]
    next_bias   = sum(next_scores) / len(next_scores)
    bias_sig, bias_col = _sig(curr_bias)
    next_bias_sig, next_bias_col = _sig(next_bias)

    month_names2 = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                    7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
    curr_m_name = month_names2[today.month]
    next_m_name = month_names2[next_m]

    # Build character strings for summary
    def _char_short(avg_up, avg_dn, avg_sw, avg):
        if avg_up > abs(avg_dn)*2 and avg >= 3:
            return f'One-way rally (+{avg_up:.0f}% up / -{avg_dn:.0f}% dip)'
        elif avg_up > abs(avg_dn)*2 and avg < 3:
            return f'Rally+reversal (+{avg_up:.0f}% then giveback)'
        elif abs(avg_dn) > avg_up*1.5:
            return f'Downside bias (-{avg_dn:.0f}% drop / +{avg_up:.0f}% bounce)'
        elif avg_sw > 25:
            return f'Extreme volatility ({avg_sw:.0f}% swing)'
        elif avg_sw < 10:
            return f'Quiet / low range ({avg_sw:.0f}% swing)'
        else:
            return f'Mixed (+{avg_up:.0f}% up / -{avg_dn:.0f}% dn)'

    # Current month char
    _cm_rng = by_month_range[today.month]
    _cm_up = sum(r[2] for r in _cm_rng)/len(_cm_rng) if _cm_rng else 0
    _cm_dn = sum(r[3] for r in _cm_rng)/len(_cm_rng) if _cm_rng else 0
    _cm_sw = sum(r[1] for r in _cm_rng)/len(_cm_rng) if _cm_rng else 0
    cm_char = _char_short(_cm_up, _cm_dn, _cm_sw, curr_m_avg)

    # Next month char
    _nm_rng = by_month_range[next_m]
    _nm_up = sum(r[2] for r in _nm_rng)/len(_nm_rng) if _nm_rng else 0
    _nm_dn = sum(r[3] for r in _nm_rng)/len(_nm_rng) if _nm_rng else 0
    _nm_sw = sum(r[1] for r in _nm_rng)/len(_nm_rng) if _nm_rng else 0
    nm_char = _char_short(_nm_up, _nm_dn, _nm_sw, next_m_avg)

    # Current quarter char
    _cq_rng = by_q_range[curr_q]
    _cq_up = sum(r[2] for r in _cq_rng)/len(_cq_rng) if _cq_rng else 0
    _cq_dn = sum(r[3] for r in _cq_rng)/len(_cq_rng) if _cq_rng else 0
    _cq_sw = sum(r[1] for r in _cq_rng)/len(_cq_rng) if _cq_rng else 0
    cq_char = _char_short(_cq_up, _cq_dn, _cq_sw, curr_q_avg)

    # Next quarter char
    _nq_rng = by_q_range[next_q]
    _nq_up = sum(r[2] for r in _nq_rng)/len(_nq_rng) if _nq_rng else 0
    _nq_dn = sum(r[3] for r in _nq_rng)/len(_nq_rng) if _nq_rng else 0
    _nq_sw = sum(r[1] for r in _nq_rng)/len(_nq_rng) if _nq_rng else 0
    nq_char = _char_short(_nq_up, _nq_dn, _nq_sw, next_q_avg)

    proj_yr = round(curr_yr_ret + projected_additional, 1)
    proj_col2 = 'green' if proj_yr > 0 else 'red'

    console.print(f'  [bold]{"Timeframe":<14} {"NOW Signal":<14} {"Character (Now)":<32} {"NEXT Signal":<14} {"Character (Next)"}[/bold]')
    console.print(f'  {"-"*100}')
    # NQ char for summary
    _cnq_rng = by_nq_range[curr_nq]
    _cnq_up = sum(r[2] for r in _cnq_rng)/len(_cnq_rng) if _cnq_rng else 0
    _cnq_dn = sum(r[3] for r in _cnq_rng)/len(_cnq_rng) if _cnq_rng else 0
    _cnq_sw = sum(r[1] for r in _cnq_rng)/len(_cnq_rng) if _cnq_rng else 0
    cnq_char = _char_short(_cnq_up, _cnq_dn, _cnq_sw, curr_nq_avg)

    _nnq_rng = by_nq_range[next_nq]
    _nnq_up = sum(r[2] for r in _nnq_rng)/len(_nnq_rng) if _nnq_rng else 0
    _nnq_dn = sum(r[3] for r in _nnq_rng)/len(_nnq_rng) if _nnq_rng else 0
    _nnq_sw = sum(r[1] for r in _nnq_rng)/len(_nnq_rng) if _nnq_rng else 0
    nnq_char = _char_short(_nnq_up, _nnq_dn, _nnq_sw, next_nq_avg)

    console.print(f'  {"Month":<14} [{cm_col}]{(curr_m_name+": "+cm_sig):<14}[/{cm_col}] [{cm_col}]{cm_char:<32}[/{cm_col}] [{nm_col}]{(next_m_name+": "+nm_sig):<14}[/{nm_col}] [{nm_col}]{nm_char}[/{nm_col}]')
    console.print(f'  {"Cal Qtr":<14} [{cq_col}]{(curr_q+": "+cq_sig):<14}[/{cq_col}] [{cq_col}]{cq_char:<32}[/{cq_col}] [{nq_col}]{(next_q+": "+nq_sig):<14}[/{nq_col}] [{nq_col}]{nq_char}[/{nq_col}]')
    console.print(f'  {"NQ Qtr":<14} [{cnq_col}]{(curr_nq+": "+cnq_sig):<14}[/{cnq_col}] [{cnq_col}]{cnq_char:<32}[/{cnq_col}] [{nnq_col}]{(next_nq+": "+nnq_sig):<14}[/{nnq_col}] [{nnq_col}]{nnq_char}[/{nnq_col}]')
    console.print(f'  {"Year 2026":<14} [{cy_col}]{cy_sig:<14}[/{cy_col}] [{cy_col}]{("+"+str(curr_yr_ret)+"%  YTD"):<32}[/{cy_col}] [{proj_col2}]{"Proj: "+str(proj_yr)+"%":<14}[/{proj_col2}] [{proj_col2}]{"Based on historical seasonality"}[/{proj_col2}]')
    console.print(f'  {"-"*100}')
    console.print(f'  {"OVERALL":<14} [{bias_col}]{bias_sig:<14}[/{bias_col}] [dim]{"avg="+str(round(curr_bias,1))+"%":<32}[/dim] [{next_bias_col}]{next_bias_sig:<14}[/{next_bias_col}] [dim]{"avg="+str(round(next_bias,1))+"%"}[/dim]')
    console.print()

    # One-line verdict
    if next_bias >= 5:
        verdict_msg = 'Upcoming conditions are STRONGLY BULLISH — prepare to deploy capital.'
    elif next_bias >= 2:
        verdict_msg = 'Upcoming conditions lean BULLISH — start building positions.'
    elif curr_bias <= -2 and next_bias >= 2:
        verdict_msg = 'Current weakness, upcoming strength — hold cash now, deploy next timeframe.'
    elif curr_bias >= 2 and next_bias <= -2:
        verdict_msg = 'Current strength fading — take profits before next timeframe.'
    elif next_bias >= -1:
        verdict_msg = 'Mixed signals ahead — stay selective, rely on option 37 for confirmation.'
    else:
        verdict_msg = 'Upcoming conditions are BEARISH — reduce exposure, protect capital.'

    bias_arrow = '▲' if next_bias > curr_bias else '▼' if next_bias < curr_bias else '='
    console.print(f'  [bold]Seasonal Shift: [{bias_col}]{bias_sig}[/{bias_col}] {bias_arrow} [{next_bias_col}]{next_bias_sig}[/{next_bias_col}][/bold]')
    console.print(f'  [bold yellow]{verdict_msg}[/bold yellow]')
    console.print()


def analyze_nepali_seasonality(db_path='nepse_market_data.db'):
    """Option 39 - Nepali Calendar Month Seasonality (Baisakh-based)"""
    import sqlite3
    from datetime import date, timedelta
    from collections import defaultdict
    from rich.console import Console
    from rich.table import Table
    from rich.rule import Rule

    console = Console()

    # === BS DATE CONVERTER ===
    baisakh_start = {
        2077: (2020, 4, 13), 2078: (2021, 4, 14), 2079: (2022, 4, 14),
        2080: (2023, 4, 14), 2081: (2024, 4, 13), 2082: (2025, 4, 14),
        2083: (2026, 4, 14),
    }
    bs_month_days = {
        2077: [31,31,31,32,31,31,30,29,30,29,30,30],
        2078: [31,31,32,31,31,31,30,29,30,29,30,30],
        2079: [31,32,31,32,31,30,30,29,30,29,30,30],
        2080: [31,31,31,32,31,31,30,29,30,29,30,30],
        2081: [31,31,32,31,31,31,30,29,30,29,30,30],
        2082: [31,32,31,32,31,30,30,29,30,29,30,30],
        2083: [31,31,31,32,31,31,30,29,30,29,30,30],
    }
    bs_month_names = {
        1:'Baisakh',2:'Jestha',3:'Ashadh',4:'Shrawan',5:'Bhadra',6:'Ashwin',
        7:'Kartik',8:'Mangsir',9:'Poush',10:'Magh',11:'Falgun',12:'Chaitra'
    }
    # Nepali quarter groupings (true Nepali calendar)
    # NQ1=Baisakh-Jestha-Ashadh, NQ2=Shrawan-Bhadra-Ashwin
    # NQ3=Kartik-Mangsir-Poush, NQ4=Magh-Falgun-Chaitra
    nq_map = {1:'NQ1',2:'NQ1',3:'NQ1',4:'NQ2',5:'NQ2',6:'NQ2',
              7:'NQ3',8:'NQ3',9:'NQ3',10:'NQ4',11:'NQ4',12:'NQ4'}
    nq_labels = {
        'NQ1':'Baisakh-Jestha-Ashadh (Apr-Jul)',
        'NQ2':'Shrawan-Bhadra-Ashwin (Jul-Oct)',
        'NQ3':'Kartik-Mangsir-Poush  (Oct-Jan)',
        'NQ4':'Magh-Falgun-Chaitra   (Jan-Apr)',
    }

    def gregorian_to_bs(greg_date):
        for bs_yr in sorted(baisakh_start.keys(), reverse=True):
            g = baisakh_start[bs_yr]
            start = date(g[0], g[1], g[2])
            if greg_date >= start:
                days = (greg_date - start).days
                for m_idx, mdays in enumerate(bs_month_days.get(bs_yr, [])):
                    if days < mdays:
                        return bs_yr, m_idx + 1
                    days -= mdays
                return bs_yr + 1, 1
        return None, None

    # === LOAD DATA ===
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT date, close, high, low FROM stock_prices "
        "WHERE symbol='NEPSE' AND close>0 ORDER BY date"
    ).fetchall()
    conn.close()

    if not rows:
        console.print('[red]No NEPSE data found.[/red]')
        return

    today = date.today()
    curr_bs_yr, curr_bs_m = gregorian_to_bs(today)

    # === MAP EACH ROW TO BS MONTH ===
    by_bs = defaultdict(list)   # (bs_yr, bs_m) -> [(date, close, high, low)]
    for r in rows:
        try:
            d = date.fromisoformat(r['date'])
            bs_yr, bs_m = gregorian_to_bs(d)
            if bs_yr and bs_m:
                by_bs[(bs_yr, bs_m)].append((r['date'], r['close'], r['high'], r['low']))
        except:
            pass

    # === AGGREGATE BY BS MONTH NUMBER ===
    by_m = defaultdict(list)      # bs_m -> [(bs_yr, ret)]
    by_m_hl = defaultdict(list)   # bs_m -> [(bs_yr, swing, up, dn)]

    # DB start = 2021-05-25 = BS 2078 Jestha (month 2)
    # Skip first partial month and current running month
    _db_first_bs = (2078, 2)
    _today_bs    = gregorian_to_bs(date.today())

    for (bs_yr, bs_m) in sorted(by_bs.keys()):
        entries = by_bs[(bs_yr, bs_m)]
        if len(entries) < 5:
            continue
        # Skip first partial month (DB started mid-month)
        if (bs_yr, bs_m) == _db_first_bs:
            continue
        # Skip current running month (not complete yet)
        if (bs_yr, bs_m) == _today_bs:
            continue
        open_c  = entries[0][1]
        close_c = entries[-1][1]
        high_c  = max(r[2] for r in entries)
        low_c   = min(r[3] for r in entries if r[3] > 0)
        ret     = (close_c - open_c) / open_c * 100
        swing   = (high_c - low_c) / low_c * 100
        up_move = (high_c - open_c) / open_c * 100
        dn_move = (open_c - low_c) / open_c * 100
        by_m[bs_m].append((bs_yr, ret))
        by_m_hl[bs_m].append((bs_yr, swing, up_move, dn_move))

    # === AGGREGATE BY NQ ===
    by_nq = defaultdict(list)
    by_nq_hl = defaultdict(list)
    for bs_m in range(1, 13):
        nq = nq_map[bs_m]
        for yr, ret in by_m[bs_m]:
            by_nq[nq].append((yr, ret))
        for yr, sw, up, dn in by_m_hl[bs_m]:
            by_nq_hl[nq].append((yr, sw, up, dn))

    # === HEADER ===
    console.rule(f'[bold cyan]Option 39 - NEPSE Nepali Calendar Seasonality[/bold cyan]')
    console.print()
    console.print(f'  [dim]Each month = Baisakh 1 to Baisakh last (true BS calendar boundaries)[/dim]')
    console.print(f'  [dim]Current: BS {curr_bs_yr} {bs_month_names.get(curr_bs_m,"?")} | Data: 2078-2083[/dim]')
    console.print()

    # === MONTHLY TABLE ===
    console.rule('[bold]Monthly Seasonality (Nepali Calendar)[/bold]')
    console.print()

    table = Table(show_header=True, header_style='bold cyan', box=None, padding=(0,1))
    table.add_column('Month',     width=10)
    table.add_column('Avg Ret',   justify='right', width=8)
    table.add_column('Up/Total',  justify='center', width=9)
    table.add_column('Best',      justify='right', width=8)
    table.add_column('Worst',     justify='right', width=8)
    table.add_column('Signal',    width=8)
    table.add_column('Swing(rng)',justify='center', width=15)
    table.add_column('Up Move',   justify='right', width=8)
    table.add_column('Dn Move',   justify='right', width=8)

    ranked = []
    for bs_m in range(1, 13):
        rets = by_m[bs_m]
        if not rets:
            continue
        avg   = sum(r for _,r in rets) / len(rets)
        wins  = sum(1 for _,r in rets if r > 0)
        best  = max(r for _,r in rets)
        worst = min(r for _,r in rets)
        rng   = by_m_hl[bs_m]
        avg_sw = sum(r[1] for r in rng)/len(rng) if rng else 0
        min_sw = min(r[1] for r in rng) if rng else 0
        max_sw = max(r[1] for r in rng) if rng else 0
        avg_up = sum(r[2] for r in rng)/len(rng) if rng else 0
        avg_dn = sum(r[3] for r in rng)/len(rng) if rng else 0
        col    = 'green' if avg >= 2 else 'yellow' if avg >= 0 else 'red'
        sig    = 'STR.BUY' if avg>=5 and wins==len(rets) else 'BUY' if avg>=2 else 'NTRL' if avg>=-1 else 'AVOID' if avg>=-3 else 'STR.AVD'
        marker = ' <--' if bs_m == curr_bs_m else ''
        sw_str = f'{avg_sw:.0f}%({min_sw:.0f}-{max_sw:.0f})'
        table.add_row(
            f'[bold]{bs_month_names[bs_m]}{marker}[/bold]',
            f'[{col}]{avg:+.1f}%[/{col}]',
            f'[{col}]{wins}/{len(rets)}[/{col}]',
            f'[green]{best:+.1f}%[/green]',
            f'[red]{worst:+.1f}%[/red]',
            f'[{col}]{sig}[/{col}]',
            f'[yellow]{sw_str}[/yellow]',
            f'[green]+{avg_up:.1f}%[/green]',
            f'[red]-{avg_dn:.1f}%[/red]',
        )
        ranked.append((avg, bs_m, avg_up, avg_dn, avg_sw, wins, len(rets)))

    console.print(table)
    console.print()

    # === RANKED ===
    console.rule('[bold]Ranked by Average Return[/bold]')
    console.print()
    ranked_sorted = sorted(ranked, reverse=True)
    console.print('  [bold green]Best months to invest:[/bold green]')
    for avg, bs_m, up, dn, sw, wins, total in ranked_sorted[:3]:
        col = 'green' if avg >= 2 else 'yellow'
        console.print(f'    [{col}]{bs_month_names[bs_m]}: avg {avg:+.1f}%  ({wins}/{total} up)  up={up:.1f}%  dn={dn:.1f}%[/{col}]')
    console.print()
    console.print('  [bold red]Worst months — stay in cash:[/bold red]')
    for avg, bs_m, up, dn, sw, wins, total in ranked_sorted[-3:]:
        console.print(f'    [red]{bs_month_names[bs_m]}: avg {avg:+.1f}%  ({wins}/{total} up)  up={up:.1f}%  dn={dn:.1f}%[/red]')
    console.print()

    # === WHAT TO DO THIS MONTH ===
    console.rule(f'[bold]What To Do in {bs_month_names.get(curr_bs_m,"?")}[/bold]')
    console.print()
    curr_rets = by_m[curr_bs_m]
    if curr_rets:
        curr_avg = sum(r for _,r in curr_rets) / len(curr_rets)
        curr_rng = by_m_hl[curr_bs_m]
        c_up = sum(r[2] for r in curr_rng)/len(curr_rng) if curr_rng else 0
        c_dn = sum(r[3] for r in curr_rng)/len(curr_rng) if curr_rng else 0
        c_sw = sum(r[1] for r in curr_rng)/len(curr_rng) if curr_rng else 0
        c_col = 'green' if curr_avg >= 2 else 'yellow' if curr_avg >= -1 else 'red'
        if c_up > abs(c_dn)*2 and curr_avg >= 3:
            c_char = f'Strong one-way rally — up {c_up:.1f}% with only -{c_dn:.1f}% dip'
        elif c_up > abs(c_dn)*2 and curr_avg < 3:
            c_char = f'Big rally then reversal — up {c_up:.1f}% but gains given back'
        elif abs(c_dn) > c_up*1.5:
            c_char = f'Downside dominated — drops {c_dn:.1f}% from open, bounces {c_up:.1f}%'
        elif c_sw > 15:
            c_char = f'High volatility — {c_sw:.1f}% swing, choppy both ways'
        else:
            c_char = f'Mixed — up {c_up:.1f}% / dn {c_dn:.1f}% from open'
        console.print(f'  Character : [{c_col}]{c_char}[/{c_col}]')
        console.print(f'  Swing     : [yellow]{c_sw:.1f}%[/yellow]  Up={c_up:.1f}%  Dn={c_dn:.1f}%')
        console.print()
        if curr_avg >= 5:
            console.print(f'  [bold green]{bs_month_names[curr_bs_m]} is historically the strongest month.[/bold green]')
            console.print('  [green]-> Deploy capital now — seasonal tailwind strong[/green]')
        elif curr_avg >= 2:
            console.print(f'  [bold green]{bs_month_names[curr_bs_m]} is a positive month historically.[/bold green]')
            console.print('  [green]-> Lean bullish — seasonal tailwind[/green]')
        elif curr_avg >= -1:
            console.print(f'  [bold yellow]{bs_month_names[curr_bs_m]} is neutral historically.[/bold yellow]')
            console.print('  [yellow]-> No seasonal edge — rely on option 37 market phase[/yellow]')
        elif curr_avg >= -3:
            console.print(f'  [bold red]{bs_month_names[curr_bs_m]} is a weak month.[/bold red]')
            console.print('  [red]-> Reduce position sizes, tighten stops[/red]')
        else:
            console.print(f'  [bold red]{bs_month_names[curr_bs_m]} is historically the worst period.[/bold red]')
            console.print('  [red]-> Stay in cash — seasonal headwind strong[/red]')
    console.print()

    # === NQ QUARTERLY TABLE ===
    console.rule('[bold]Nepali Calendar Quarterly Seasonality[/bold]')
    console.print()
    curr_nq = nq_map[curr_bs_m]
    nq_order = ['NQ1','NQ2','NQ3','NQ4']
    curr_idx = nq_order.index(curr_nq)
    next_nq  = nq_order[(curr_idx+1) % 4]

    nqtable = Table(show_header=True, header_style='bold cyan', box=None, padding=(0,1))
    nqtable.add_column('Quarter',        width=22)
    nqtable.add_column('Avg Ret',        justify='right', width=8)
    nqtable.add_column('W/T',            justify='center', width=5)
    nqtable.add_column('Best',           justify='right', width=7)
    nqtable.add_column('Worst',          justify='right', width=7)
    nqtable.add_column('Signal',         width=8)
    nqtable.add_column('Swing(rng)',     justify='center', width=14)
    nqtable.add_column('Up',             justify='right', width=6)
    nqtable.add_column('Dn',             justify='right', width=6)

    for nq in nq_order:
        rets = by_nq[nq]
        if not rets: continue
        avg   = sum(r for _,r in rets) / len(rets)
        wins  = sum(1 for _,r in rets if r > 0)
        best  = max(r for _,r in rets)
        worst = min(r for _,r in rets)
        rng   = by_nq_hl[nq]
        avg_sw = sum(r[1] for r in rng)/len(rng) if rng else 0
        min_sw = min(r[1] for r in rng) if rng else 0
        max_sw = max(r[1] for r in rng) if rng else 0
        avg_up = sum(r[2] for r in rng)/len(rng) if rng else 0
        avg_dn = sum(r[3] for r in rng)/len(rng) if rng else 0
        col    = 'green' if avg >= 2 else 'yellow' if avg >= -1 else 'red'
        sig    = 'STR.BUY' if avg>=5 else 'BUY' if avg>=2 else 'NTRL' if avg>=-1 else 'AVOID' if avg>=-4 else 'STR.AVD'
        marker = ' <-NOW' if nq==curr_nq else (' <-NXT' if nq==next_nq else '')
        sw_str = f'{avg_sw:.0f}%({min_sw:.0f}-{max_sw:.0f})'
        nqtable.add_row(
            f'[bold]{nq}{marker}[/bold]',
            f'[{col}]{avg:+.1f}%[/{col}]',
            f'[{col}]{wins}/{len(rets)}[/{col}]',
            f'[green]{best:+.1f}%[/green]',
            f'[red]{worst:+.1f}%[/red]',
            f'[{col}]{sig}[/{col}]',
            f'[yellow]{sw_str}[/yellow]',
            f'[green]+{avg_up:.1f}%[/green]',
            f'[red]-{avg_dn:.1f}%[/red]',
        )

    console.print(nqtable)
    console.print()

    # === NQ TRADING GUIDE ===
    console.rule('[bold]Nepali Quarter Trading Guide[/bold]')
    console.print()
    for nq in nq_order:
        rets = by_nq[nq]
        if not rets: continue
        avg   = sum(r for _,r in rets) / len(rets)
        wins  = sum(1 for _,r in rets if r > 0)
        rng   = by_nq_hl[nq]
        avg_up = round(sum(r[2] for r in rng)/len(rng),1) if rng else 0
        avg_dn = round(sum(r[3] for r in rng)/len(rng),1) if rng else 0
        avg_sw = round(sum(r[1] for r in rng)/len(rng),1) if rng else 0
        marker = ' <-- NOW' if nq==curr_nq else (' <- NEXT' if nq==next_nq else '')
        col    = 'green' if avg >= 2 else 'yellow' if avg >= -1 else 'red'
        if avg_up > abs(avg_dn)*2 and avg >= 3:
            char = f'Strong directional rally — up {avg_up:.1f}% dominates'
        elif avg_up > abs(avg_dn)*2 and avg < 3:
            char = f'Big rally then reversal — up {avg_up:.1f}% but gains given back'
        elif abs(avg_dn) > avg_up*1.5:
            char = f'Downside dominated — drops {avg_dn:.1f}% from open'
        elif avg_sw > 25:
            char = f'Extreme volatility — {avg_sw:.0f}% total swing'
        else:
            char = f'Mixed — up {avg_up:.1f}% / dn {avg_dn:.1f}% from open'
        if avg >= 5:
            action = f'Deploy capital — strong tailwind. Rally avg +{avg_up:.1f}% from open.'
        elif avg >= 2:
            action = f'Lean bullish. Dip only {avg_dn:.1f}% before rallying {avg_up:.1f}%.'
        elif avg >= -1:
            action = f'Neutral — selective entries only. Up {avg_up:.1f}% vs dn {avg_dn:.1f}%.'
        elif avg >= -4:
            action = f'Avoid longs. Drops {avg_dn:.1f}%, recovers only {avg_up:.1f}%.'
        else:
            action = f'Stay cash. Heavy selling — {avg_dn:.1f}% down, {avg_sw:.0f}% swing.'
        console.print(f'  [{col}][bold]{nq}{marker}[/bold]  ({nq_labels[nq]})  avg={avg:+.1f}%  ({wins}/{len(rets)} up)[/{col}]')
        console.print(f'    Character : {char}')
        console.print(f'    Action    : [{col}]{action}[/{col}]')
        console.print()

    # === NEPALI FY QUARTERLY (Shrawan-based) ===
    console.print()
    console.rule('[bold]Nepali FY Quarterly Seasonality (Shrawan-based)[/bold]')
    console.print()
    console.print('  [dim]FYQ1=Shrawan-Ashwin  FYQ2=Kartik-Poush  FYQ3=Magh-Chaitra  FYQ4=Baisakh-Ashadh[/dim]')
    console.print()

    # Map BS months to FY quarters
    fy_q_map = {4:'FYQ1',5:'FYQ1',6:'FYQ1',
                7:'FYQ2',8:'FYQ2',9:'FYQ2',
                10:'FYQ3',11:'FYQ3',12:'FYQ3',
                1:'FYQ4',2:'FYQ4',3:'FYQ4'}
    fy_q_labels = {
        'FYQ1':'Shrawan-Bhadra-Ashwin (Jul-Oct)',
        'FYQ2':'Kartik-Mangsir-Poush  (Oct-Jan)',
        'FYQ3':'Magh-Falgun-Chaitra   (Jan-Apr)',
        'FYQ4':'Baisakh-Jestha-Ashadh (Apr-Jul)',
    }

    def _fy_label(bs_yr, bs_m):
        if bs_m in (4,5,6,7,8,9,10,11,12): return bs_yr
        else: return bs_yr - 1

    # Build FY quarterly data from monthly data
    from collections import defaultdict as _dd2
    from datetime import date as _dt_fyq2
    _bs_start_fyq = {
        2077:(2020,4,13),2078:(2021,4,14),2079:(2022,4,14),
        2080:(2023,4,14),2081:(2024,4,13),2082:(2025,4,14),2083:(2026,4,14),
    }
    _bs_mdays_fyq = {
        2077:[31,31,31,32,31,31,30,29,30,29,30,30],
        2078:[31,31,32,31,31,31,30,29,30,29,30,30],
        2079:[31,32,31,32,31,30,30,29,30,29,30,30],
        2080:[31,31,31,32,31,31,30,29,30,29,30,30],
        2081:[31,31,32,31,31,31,30,29,30,29,30,30],
        2082:[31,32,31,32,31,30,30,29,30,29,30,30],
        2083:[31,31,31,32,31,31,30,29,30,29,30,30],
    }
    def _to_bs_fyq(d):
        for yr in sorted(_bs_start_fyq.keys(), reverse=True):
            g = _bs_start_fyq[yr]
            s = _dt_fyq2(g[0],g[1],g[2])
            if d >= s:
                days = (d-s).days
                for mi,md in enumerate(_bs_mdays_fyq.get(yr,[])):
                    if days < md: return yr, mi+1
                    days -= md
                return yr+1,1
        return None,None
    by_fyq      = _dd2(list)
    by_fyq_hl   = _dd2(list)
    _fyq_raw = _dd2(list)
    _fyq_hl_raw = _dd2(list)

    # Load raw trading days grouped by FY quarter
    conn2 = sqlite3.connect(db_path)
    conn2.row_factory = sqlite3.Row
    rows2 = conn2.execute(
        "SELECT date, close, high, low FROM stock_prices "
        "WHERE symbol=? AND close>0 ORDER BY date", (symbol,)
    ).fetchall()
    conn2.close()

    for r in rows2:
        try:
            d = _dt_fyq2.fromisoformat(r['date'])
            bs_yr2, bs_m2 = _to_bs_fyq(d)
            if bs_yr2 and bs_m2:
                fyq  = fy_q_map[bs_m2]
                fy   = _fy_label(bs_yr2, bs_m2)
                key  = (fy, fyq)
                _fyq_raw[key].append((r['close'], r['high'], r['low']))
        except: pass

    # DB first and current FY quarter to skip
    from datetime import date as _dt_fyq
    _today_bs2 = _to_bs_fyq(_dt_fyq2.today())
    _curr_fyq_key = (_fy_label(_today_bs2[0], _today_bs2[1]), fy_q_map[_today_bs2[1]])
    _first_bs2 = _to_bs_fyq(_dt_fyq2(2021,5,25))
    _first_fyq_key = (_fy_label(_first_bs2[0], _first_bs2[1]), fy_q_map[_first_bs2[1]])

    for key, entries in sorted(_fyq_raw.items()):
        if len(entries) < 10: continue
        if key == _curr_fyq_key: continue
        if key == _first_fyq_key: continue
        fy, fyq = key
        oc = entries[0][0]; cc = entries[-1][0]
        hh = max(e[1] for e in entries)
        ll = min(e[2] for e in entries if e[2]>0)
        ret   = (cc-oc)/oc*100
        swing = (hh-ll)/ll*100
        up    = (hh-oc)/oc*100
        dn    = (oc-ll)/oc*100
        by_fyq[fyq].append((fy, ret))
        by_fyq_hl[fyq].append((fy, swing, up, dn))

    # Current and next FY quarter
    curr_fyq = fy_q_map[_today_bs2[1]]
    fyq_order = ['FYQ1','FYQ2','FYQ3','FYQ4']
    curr_fyq_idx = fyq_order.index(curr_fyq)
    next_fyq = fyq_order[(curr_fyq_idx+1) % 4]

    fyqtable = Table(show_header=True, header_style='bold cyan', box=None, padding=(0,1))
    fyqtable.add_column('Quarter',      width=22)
    fyqtable.add_column('Avg Ret',      justify='right', width=8)
    fyqtable.add_column('W/T',          justify='center', width=5)
    fyqtable.add_column('Best',         justify='right', width=7)
    fyqtable.add_column('Worst',        justify='right', width=7)
    fyqtable.add_column('Signal',       width=8)
    fyqtable.add_column('Swing(rng)',   justify='center', width=14)
    fyqtable.add_column('Up',           justify='right', width=6)
    fyqtable.add_column('Dn',           justify='right', width=6)

    for fyq in fyq_order:
        rets = by_fyq[fyq]
        if not rets: continue
        avg   = sum(r for _,r in rets)/len(rets)
        wins  = sum(1 for _,r in rets if r>0)
        best  = max(r for _,r in rets)
        worst = min(r for _,r in rets)
        rng   = by_fyq_hl[fyq]
        avg_sw = sum(r[1] for r in rng)/len(rng) if rng else 0
        min_sw = min(r[1] for r in rng) if rng else 0
        max_sw = max(r[1] for r in rng) if rng else 0
        avg_up = sum(r[2] for r in rng)/len(rng) if rng else 0
        avg_dn = sum(r[3] for r in rng)/len(rng) if rng else 0
        col    = 'green' if avg>=2 else 'yellow' if avg>=-1 else 'red'
        sig    = 'STR.BUY' if avg>=5 else 'BUY' if avg>=2 else 'NTRL' if avg>=-1 else 'AVOID' if avg>=-4 else 'STR.AVD'
        marker = ' <-NOW' if fyq==curr_fyq else (' <-NXT' if fyq==next_fyq else '')
        sw_str = f'{avg_sw:.0f}%({min_sw:.0f}-{max_sw:.0f})'
        lim_tag = ' [dim](limited)[/dim]' if len(rets) < 3 else ''
        fyqtable.add_row(
            f'[bold]{fyq}{marker}[/bold]{lim_tag}',
            f'[{col}]{avg:+.1f}%[/{col}]',
            f'[{col}]{wins}/{len(rets)}[/{col}]',
            f'[green]{best:+.1f}%[/green]',
            f'[red]{worst:+.1f}%[/red]',
            f'[{col}]{sig}[/{col}]',
            f'[yellow]{sw_str}[/yellow]',
            f'[green]+{avg_up:.1f}%[/green]',
            f'[red]-{avg_dn:.1f}%[/red]',
        )

    console.print(fyqtable)
    console.print()

    # FYQ Trading Guide
    console.rule('[bold]Nepali FY Quarter Trading Guide[/bold]')
    console.print()
    for fyq in fyq_order:
        rets = by_fyq[fyq]
        if not rets: continue
        avg   = sum(r for _,r in rets)/len(rets)
        wins  = sum(1 for _,r in rets if r>0)
        rng   = by_fyq_hl[fyq]
        avg_up = round(sum(r[2] for r in rng)/len(rng),1) if rng else 0
        avg_dn = round(sum(r[3] for r in rng)/len(rng),1) if rng else 0
        avg_sw = round(sum(r[1] for r in rng)/len(rng),1) if rng else 0
        marker = ' <-- NOW' if fyq==curr_fyq else (' <- NEXT' if fyq==next_fyq else '')
        col    = 'green' if avg>=2 else 'yellow' if avg>=-1 else 'red'
        if avg_up > abs(avg_dn)*2 and avg>=3:
            char = f'Strong rally — up {avg_up:.1f}% dominates'
        elif avg_up > abs(avg_dn)*2 and avg<3:
            char = f'Rally then fade — up {avg_up:.1f}% given back'
        elif abs(avg_dn) > avg_up*1.5:
            char = f'Downside dominated — drops {avg_dn:.1f}%'
        elif avg_sw > 25:
            char = f'Extreme volatility — {avg_sw:.0f}% swing'
        else:
            char = f'Mixed — up {avg_up:.1f}% / dn {avg_dn:.1f}%'
        if avg>=5:   action = f'Deploy capital — strong tailwind +{avg_up:.1f}%'
        elif avg>=2: action = f'Lean bullish. Dip {avg_dn:.1f}% then rally {avg_up:.1f}%.'
        elif avg>=-1:action = f'Neutral — selective only. Up {avg_up:.1f}% vs dn {avg_dn:.1f}%.'
        elif avg>=-4:action = f'Avoid longs. Drops {avg_dn:.1f}%, recovers {avg_up:.1f}%.'
        else:        action = f'Stay cash. Heavy selling {avg_dn:.1f}% down.'
        console.print(f'  [{col}][bold]{fyq}{marker}[/bold]  ({fy_q_labels[fyq]})  avg={avg:+.1f}%  ({wins}/{len(rets)} up)[/{col}]')
        console.print(f'    Character : {char}')
        console.print(f'    Action    : [{col}]{action}[/{col}]')
        console.print()

    console.print('  [dim]Research only. Not financial advice. Paper trade first.[/dim]')
    console.print()


def analyze_market_phase(db_path='nepse_market_data.db'):
    """Option 37 - Market Phase Detector"""
    from rich.console import Console
    from rich.rule import Rule
    from rich.table import Table
    console = Console()
    import sqlite3

    console.print()
    console.rule('[bold yellow]Option 37 — Market Phase Detector[/bold yellow]', style='yellow')
    console.print()

    conn = sqlite3.connect(db_path)

    # === SIGNAL 1: NEPSE TREND ===
    nepse = conn.execute(
        "SELECT date, close FROM stock_prices WHERE symbol='NEPSE' AND close>0 ORDER BY date DESC LIMIT 50"
    ).fetchall()
    nepse_dates  = [r[0] for r in nepse]
    nepse_closes = [r[1] for r in nepse]
    curr_nepse = nepse_closes[0] if nepse_closes else 0
    ma20 = sum(nepse_closes[:20])/20 if len(nepse_closes)>=20 else curr_nepse
    ma50 = sum(nepse_closes[:50])/50 if len(nepse_closes)>=50 else curr_nepse
    trend_5d = round((nepse_closes[0]-nepse_closes[min(4,len(nepse_closes)-1)])/nepse_closes[min(4,len(nepse_closes)-1)]*100,1) if len(nepse_closes)>=2 else 0
    nepse_score = 0
    if curr_nepse > ma20: nepse_score += 25
    if ma20 > ma50:       nepse_score += 25
    nepse_note = 'last available' if nepse_dates[0] < '2026-06-01' else 'current'

    # === SIGNAL 2: BREADTH (5 days) ===
    dates = conn.execute(
        "SELECT DISTINCT date FROM stock_prices WHERE symbol!='NEPSE' ORDER BY date DESC LIMIT 7"
    ).fetchall()
    dates = [d[0] for d in dates]
    adv_total = dec_total = 0
    daily_breadth = []
    for i in range(min(5,len(dates)-1)):
        d1,d2 = dates[i],dates[i+1]
        a = conn.execute(
            "SELECT COUNT(*) FROM stock_prices t1 JOIN stock_prices t2 ON t1.symbol=t2.symbol "
            "AND t2.date=? WHERE t1.date=? AND t1.close>t2.close",(d2,d1)
        ).fetchone()[0]
        d = conn.execute(
            "SELECT COUNT(*) FROM stock_prices t1 JOIN stock_prices t2 ON t1.symbol=t2.symbol "
            "AND t2.date=? WHERE t1.date=? AND t1.close<t2.close",(d2,d1)
        ).fetchone()[0]
        adv_total+=a; dec_total+=d
        daily_breadth.append((d1,a,d))
    breadth_ratio = round(adv_total/(adv_total+dec_total)*100) if (adv_total+dec_total)>0 else 50
    breadth_score = 25 if breadth_ratio>=55 else 15 if breadth_ratio>=45 else 0

    # === SIGNAL 3: % STOCKS ABOVE 20MA ===
    all_syms = [s[0] for s in conn.execute(
        "SELECT DISTINCT symbol FROM stock_prices WHERE date=? AND symbol!='NEPSE' AND close>0",
        (dates[0],)
    ).fetchall()]
    above20=total20=0
    for sym in all_syms:
        p = conn.execute(
            "SELECT close FROM stock_prices WHERE symbol=? AND close>0 ORDER BY date DESC LIMIT 20",
            (sym,)
        ).fetchall()
        if len(p)>=20:
            if p[0][0] > sum(x[0] for x in p)/20: above20+=1
            total20+=1
    pct_above = round(above20/total20*100) if total20 else 0
    above_score = 25 if pct_above>=55 else 15 if pct_above>=45 else 0

    # === SIGNAL 4: SMART MONEY DOMINANCE ===
    sm_buy_days=0
    for d in dates[:5]:
        rows = conn.execute("SELECT net_val FROM broker_activity WHERE date=?",(d,)).fetchall()
        vals = [r[0] for r in rows]
        t5b = sum(sorted([v for v in vals if v>0],reverse=True)[:5])
        t5s = sum(sorted([abs(v) for v in vals if v<0],reverse=True)[:5])
        if t5b > t5s: sm_buy_days+=1
    sm_score = 25 if sm_buy_days>=4 else 15 if sm_buy_days>=3 else 5 if sm_buy_days>=2 else 0

    # === SIGNAL 5: VOLUME CONFIRMATION ===
    vol_data = conn.execute(
        "SELECT date, volume FROM stock_prices WHERE symbol='NEPSE' AND volume>0 ORDER BY date DESC LIMIT 25"
    ).fetchall()
    vol_score = 0
    vol_note  = 'No volume data'
    vol_ratio = 0
    if len(vol_data) >= 10:
        avg_vol_5d  = sum(r[1] for r in vol_data[:5])  / 5
        avg_vol_20d = sum(r[1] for r in vol_data[:20]) / 20
        vol_ratio   = round(avg_vol_5d / avg_vol_20d * 100) if avg_vol_20d > 0 else 100
        price_up    = trend_5d >= 0
        high_vol    = vol_ratio >= 110  # 10% above average
        low_vol     = vol_ratio <= 90   # 10% below average
        if price_up and high_vol:
            vol_score = 25
            vol_note  = f'Rally on HIGH volume ({vol_ratio}% of avg) — strong accumulation'
        elif price_up and low_vol:
            vol_score = 10
            vol_note  = f'Rally on LOW volume ({vol_ratio}% of avg) — weak, suspect'
        elif price_up:
            vol_score = 15
            vol_note  = f'Rally on normal volume ({vol_ratio}% of avg) — OK'
        elif not price_up and high_vol:
            vol_score = 0
            vol_note  = f'Drop on HIGH volume ({vol_ratio}% of avg) — strong distribution'
        elif not price_up and low_vol:
            vol_score = 15
            vol_note  = f'Drop on LOW volume ({vol_ratio}% of avg) — weak selling, not panic'
        else:
            vol_score = 10
            vol_note  = f'Drop on normal volume ({vol_ratio}% of avg) — normal selling'

    conn.close()

    # === TOTAL SCORE & PHASE ===
    total = nepse_score + breadth_score + above_score + sm_score + vol_score

    if total >= 80:
        phase='MARKUP';        phase_col='green';  phase_note='Strong uptrend — buy breakouts, ride momentum'
    elif total >= 60:
        phase='ACCUMULATION';  phase_col='cyan';   phase_note='Institutions building positions — look for setups'
    elif total >= 40:
        phase='TRANSITION';    phase_col='yellow'; phase_note='Mixed signals — be selective, reduce size'
    elif total >= 20:
        phase='DISTRIBUTION';  phase_col='orange'; phase_note='Institutions selling — avoid new entries'
    else:
        phase='MARKDOWN';      phase_col='red';    phase_note='Downtrend — stay in cash, wait for reversal'

    # === DISPLAY ===
    console.print(f'  Latest data: {dates[0]}')
    console.print()

    # Phase banner
    console.print(f'  [bold {phase_col}]{"="*50}[/bold {phase_col}]')
    console.print(f'  [bold {phase_col}]  MARKET PHASE: {phase}  ({total}/100)[/bold {phase_col}]')
    console.print(f'  [bold {phase_col}]{"="*50}[/bold {phase_col}]')
    console.print()
    console.print(f'  [{phase_col}]{phase_note}[/{phase_col}]')
    console.print()

    # Signal breakdown
    console.rule('[bold]Signal Breakdown[/bold]')
    console.print()

    # NEPSE trend
    n_col = 'green' if nepse_score>=40 else 'yellow' if nepse_score>=20 else 'red'
    console.print(f'  [bold]1. NEPSE Index ({nepse_note})[/bold]')
    console.print(f'     Index:  {curr_nepse:,.1f}  |  MA20: {ma20:,.1f}  |  MA50: {ma50:,.1f}')
    console.print(f'     5d change: {trend_5d:+.1f}%')
    above_ma = curr_nepse > ma20
    golden = ma20 > ma50
    console.print(f'     Price vs MA20: [{"green" if above_ma else "red"}]{"ABOVE" if above_ma else "BELOW"}[/{"green" if above_ma else "red"}]  |  MA20 vs MA50: [{"green" if golden else "red"}]{"GOLDEN CROSS" if golden else "DEATH CROSS"}[/{"green" if golden else "red"}]')
    console.print(f'     Score: [{n_col}]{nepse_score}/50[/{n_col}]')
    console.print()

    # Breadth
    b_col = 'green' if breadth_score>=20 else 'yellow' if breadth_score>=15 else 'red'
    console.print(f'  [bold]2. Market Breadth (5-day)[/bold]')
    for d,a,dec in daily_breadth:
        bar = '▲'*min(a//20,10) + '▼'*min(dec//20,10)
        b_c = 'green' if a>dec else 'red'
        console.print(f'     {d}: [{b_c}]+{a} / -{dec}[/{b_c}]')
    console.print(f'     Advance ratio: [{b_col}]{breadth_ratio}% ({"bullish" if breadth_ratio>=55 else "neutral" if breadth_ratio>=45 else "bearish"})[/{b_col}]')
    console.print(f'     Score: [{b_col}]{breadth_score}/25[/{b_col}]')
    console.print()

    # % above 20MA
    a_col = 'green' if above_score>=20 else 'yellow' if above_score>=15 else 'red'
    console.print(f'  [bold]3. Stocks Above 20-day MA[/bold]')
    bar_len = pct_above // 5
    bar = '█'*bar_len + '░'*(20-bar_len)
    console.print(f'     [{a_col}]{bar} {pct_above}%[/{a_col}]  ({above20}/{total20} stocks)')
    status = 'broad participation' if pct_above>=55 else 'mixed' if pct_above>=45 else 'narrow — weak market'
    console.print(f'     [{a_col}]{status}[/{a_col}]')
    console.print(f'     Score: [{a_col}]{above_score}/25[/{a_col}]')
    console.print()

    # Smart money
    s_col = 'green' if sm_score>=20 else 'yellow' if sm_score>=15 else 'red'
    console.print(f'  [bold]4. Smart Money Dominance (5-day)[/bold]')
    console.print(f'     Buy-dominant days: [{s_col}]{sm_buy_days}/5[/{s_col}]')
    sm_note = 'accumulating' if sm_buy_days>=4 else 'mixed' if sm_buy_days>=2 else 'distributing'
    console.print(f'     Smart money: [{s_col}]{sm_note}[/{s_col}]')
    console.print(f'     Score: [{s_col}]{sm_score}/25[/{s_col}]')
    console.print()

    # Volume
    v_col = 'green' if vol_score>=20 else 'yellow' if vol_score>=10 else 'red'
    console.print('  [bold]5. Volume Confirmation (5d vs 20d avg)[/bold]')
    console.print(f'     {vol_note}')
    console.print(f'     Score: [{v_col}]{vol_score}/25[/{v_col}]')
    console.print()

    # Trading guidance
    console.rule('[bold]What To Do Now[/bold]')
    console.print()
    if phase == 'MARKUP':
        console.print('  [green]-> Buy breakouts above resistance with volume[/green]')
        console.print('  [green]-> Trail stop losses, let winners run[/green]')
        console.print('  [green]-> Focus on sector leaders[/green]')
    elif phase == 'ACCUMULATION':
        console.print('  [cyan]-> Look for stocks at support with broker accumulation[/cyan]')
        console.print('  [cyan]-> Run option 36 daily — good R/R setups appearing[/cyan]')
        console.print('  [cyan]-> Build positions slowly, keep stops tight[/cyan]')
    elif phase == 'TRANSITION':
        console.print('  [yellow]-> Be very selective — only highest quality setups[/yellow]')
        console.print('  [yellow]-> Reduce position sizes by 50%[/yellow]')
        console.print('  [yellow]-> Run option 35 before any entry[/yellow]')
    elif phase == 'DISTRIBUTION':
        console.print('  [yellow]-> Avoid new entries[/yellow]')
        console.print('  [yellow]-> Start reducing existing positions[/yellow]')
        console.print('  [yellow]-> Watch for holders selling in option 17c[/yellow]')
    else:  # MARKDOWN
        console.print('  [red]-> Stay in cash — do not buy dips[/red]')
        console.print('  [red]-> Wait for breadth to improve above 50%[/red]')
        console.print('  [red]-> Wait for % above 20MA to cross 50%[/red]')
        console.print('  [red]-> Only act when smart money buy days >= 3/5[/red]')
    console.print()

    # Recovery signals to watch
    if phase in ('MARKDOWN','DISTRIBUTION'):
        console.rule('[bold cyan]Recovery Signals To Watch[/bold cyan]')
        console.print()
        need_breadth = 55 - breadth_ratio
        need_above   = 55 - pct_above
        need_sm      = 3 - sm_buy_days
        console.print(f'  Breadth needs: +{max(0,need_breadth)}% more advances (currently {breadth_ratio}%, need 55%)')
        console.print(f'  Above 20MA needs: +{max(0,need_above)}% more stocks (currently {pct_above}%, need 55%)')
        console.print(f'  Smart money needs: {max(0,need_sm)} more buy days (currently {sm_buy_days}/5, need 3+)')
        if vol_ratio < 100:
            console.print(f'  Volume: {vol_ratio}% of avg — watch for capitulation flush on high volume')
        else:
            console.print(f'  Volume: {vol_ratio}% of avg — needs rally on 110%+ volume to confirm reversal')
        console.print()

    # === SECTION 6: SECTOR PHASE BREAKDOWN ===
    import datetime
    from collections import defaultdict as _dd

    console.rule('[bold cyan]Sector Phase Breakdown[/bold cyan]', style='cyan')
    console.print()

    NAME_MAP2 = {
        'Hydro Power':'Hydropower','Commercial Banks':'Commercial Banks',
        'Development Banks':'Development Banks','Finance':'Finance',
        'Microfinance':'Microfinance','Life Insurance':'Life Insurance',
        'Non Life Insurance':'Non-Life Insurance',
        'Manufacturing And Processing':'Manufacturing',
        'Hotels And Tourism':'Hotel & Tourism',
        'Investment':'Investment','Tradings':'Trading','Others':'Others',
    }

    conn2 = sqlite3.connect(db_path)
    sect_rows = conn2.execute(
        "SELECT sp.symbol, c.sector, sp.date, sp.close "
        "FROM stock_prices sp JOIN companies c ON sp.symbol=c.symbol "
        "WHERE sp.close>0 AND sp.date>=date(?,'-60 days') "
        "ORDER BY sp.symbol, sp.date",
        (dates[0],)
    ).fetchall()

    sym_prices2 = _dd(list)
    sym_sector2 = {}
    for sym,sect,dt,cl in sect_rows:
        sym_sector2[sym] = NAME_MAP2.get(sect, sect)
        sym_prices2[sym].append((dt,cl))

    sect_data2 = _dd(lambda: {'above20':0,'total':0,'ret5d':[],'adv':0,'dec':0})
    for sym,prices in sym_prices2.items():
        sect = sym_sector2[sym]
        if len(prices) < 20: continue
        closes = [p[1] for p in prices]
        ma20s = sum(closes[-20:])/20
        if closes[-1] > ma20s: sect_data2[sect]['above20'] += 1
        sect_data2[sect]['total'] += 1
        if len(closes) >= 6:
            ret = (closes[-1]-closes[-6])/closes[-6]*100
            sect_data2[sect]['ret5d'].append(ret)
        if len(closes) >= 2:
            if closes[-1] > closes[-2]: sect_data2[sect]['adv'] += 1
            elif closes[-1] < closes[-2]: sect_data2[sect]['dec'] += 1

    sect_broker2 = _dd(int)
    for d in dates[:5]:
        brows = conn2.execute(
            "SELECT ba.net_val, c.sector FROM broker_activity ba "
            "JOIN companies c ON ba.symbol=c.symbol WHERE ba.date=?", (d,)
        ).fetchall()
        for val,sect in brows:
            sect_broker2[NAME_MAP2.get(sect,sect)] += val if val else 0
    conn2.close()

    sect_phases2 = []
    for sect in sorted(sect_data2.keys()):
        sd = sect_data2[sect]
        if sd['total'] < 3: continue
        pct_ab2  = sd['above20']/sd['total']*100 if sd['total'] else 0
        avg_ret2 = sum(sd['ret5d'])/len(sd['ret5d']) if sd['ret5d'] else 0
        adv_r2   = sd['adv']/(sd['adv']+sd['dec'])*100 if (sd['adv']+sd['dec'])>0 else 50
        bflow2   = sect_broker2.get(sect, 0)
        sc2 = 0
        if pct_ab2  >= 55: sc2 += 2
        elif pct_ab2 >= 45: sc2 += 1
        if avg_ret2 >= 2:  sc2 += 2
        elif avg_ret2 >= 0: sc2 += 1
        if adv_r2   >= 55: sc2 += 2
        elif adv_r2 >= 45: sc2 += 1
        if bflow2 > 0:     sc2 += 2
        elif bflow2 == 0:  sc2 += 1
        if sc2 >= 7:   sph='MARKUP';   sco='green'
        elif sc2 >= 5: sph='ACCUM';    sco='cyan'
        elif sc2 >= 3: sph='TRANSIT';  sco='yellow'
        elif sc2 >= 1: sph='DISTRIB';  sco='red'
        else:          sph='MARKDOWN'; sco='red'
        sect_phases2.append((sc2,sect,sph,sco,pct_ab2,avg_ret2,bflow2))

    sect_phases2.sort(reverse=True)
    console.print(f'  {"Sector":<22} {"Phase":<10} {"%>MA20":>7} {"5d Ret":>7} {"Broker":>9}')
    console.print(f'  {"-"*22} {"-"*10} {"-"*7} {"-"*7} {"-"*9}')
    for sc2,sect,sph,sco,pct_ab2,avg_ret2,bflow2 in sect_phases2:
        bf_s = f'+{bflow2/1e3:.0f}K' if bflow2>1000 else f'{bflow2/1e3:.0f}K' if bflow2<-1000 else 'flat'
        bf_c = 'green' if bflow2>0 else 'red' if bflow2<0 else 'dim'
        console.print(
            f'  [{sco}]{sect:<22}[/{sco}] [{sco}]{sph:<10}[/{sco}] '
            f'[{"green" if pct_ab2>=55 else "red"}]{pct_ab2:>6.0f}%[/{"green" if pct_ab2>=55 else "red"}] '
            f'[{"green" if avg_ret2>=0 else "red"}]{avg_ret2:>+6.1f}%[/{"green" if avg_ret2>=0 else "red"}] '
            f'[{bf_c}]{bf_s:>9}[/{bf_c}]', highlight=False)
    console.print()

    # === SECTION 7: HISTORICAL PHASE COMPARISON ===
    console.rule('[bold cyan]Historical Phase Comparison[/bold cyan]', style='cyan')
    console.print()
    hist_nepse2 = sqlite3.connect(db_path).execute(
        "SELECT date,close FROM stock_prices WHERE symbol='NEPSE' AND close>0 ORDER BY date"
    ).fetchall()
    if len(hist_nepse2) >= 60:
        hd = [r[0] for r in hist_nepse2]
        hc = [r[1] for r in hist_nepse2]
        similar = []
        for i in range(50, len(hc)-20):
            ma20h = sum(hc[i-20:i])/20
            ma50h = sum(hc[i-50:i])/50
            approx = (25 if hc[i]>ma20h else 0) + (25 if ma20h>ma50h else 0)
            if abs(approx-total) <= 15:
                fwd = (hc[i+20]-hc[i])/hc[i]*100
                similar.append((hd[i], hc[i], approx, fwd))
        if similar:
            fwd_r = [p[3] for p in similar]
            avg_f = sum(fwd_r)/len(fwd_r)
            pos_c = sum(1 for r in fwd_r if r>0)
            console.print(f'  Found {len(similar)} similar conditions  |  Avg 20d forward: [{"green" if avg_f>=0 else "red"}]{avg_f:+.1f}%[/{"green" if avg_f>=0 else "red"}]  |  Positive: {pos_c}/{len(similar)} ({pos_c/len(similar)*100:.0f}%)', highlight=False)
            console.print()
            console.print('  [dim]Recent similar periods:[/dim]')
            for dt,px,sc3,fwd in sorted(similar,key=lambda x:x[0],reverse=True)[:5]:
                col = 'green' if fwd>=0 else 'red'
                console.print(f'  [dim]{dt}[/dim]  NEPSE:{px:,.0f}  Score~{sc3}  +20d: [{col}]{fwd:+.1f}%[/{col}]', highlight=False)
        else:
            console.print('  [dim]Not enough similar history found.[/dim]')
    console.print()

    # === SECTION 8: COMBINED PHASE + SEASONAL SIGNAL ===
    console.rule('[bold yellow]Combined Signal — Phase + Seasonality[/bold yellow]', style='yellow')
    console.print()
    import datetime as _dt2
    today2    = _dt2.date.today()
    curr_m2   = today2.month
    next_m2   = today2.month % 12 + 1
    MN2       = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    nep_hist2 = sqlite3.connect(db_path).execute(
        "SELECT date,close FROM stock_prices WHERE symbol='NEPSE' AND close>0 ORDER BY date"
    ).fetchall()
    by_m2 = _dd(list)
    for j in range(len(nep_hist2)):
        r = nep_hist2[j]
        d2 = _dt2.date.fromisoformat(r[0])
        if (d2.year,d2.month)==(today2.year,today2.month): continue
        month_rows2 = [x for x in nep_hist2 if x[0][:7]==f'{d2.year}-{d2.month:02d}']
        if len(month_rows2)>=10:
            ret2=(month_rows2[-1][1]-month_rows2[0][1])/month_rows2[0][1]*100
            if ret2 not in by_m2[d2.month]: by_m2[d2.month].append(ret2)

    def _msig2(m):
        rets=by_m2.get(m,[])
        if not rets: return 'UNKN','dim',0,0
        avg=sum(rets)/len(rets); wins=sum(1 for r in rets if r>0)
        if avg>=5:  return 'S.BUY','green',avg,wins
        if avg>=2:  return 'BUY','green',avg,wins
        if avg>=-1: return 'NTRL','yellow',avg,wins
        if avg>=-3: return 'AVOID','red',avg,wins
        return 'S.AVD','red',avg,wins

    cs,cc,ca,cw = _msig2(curr_m2)
    ns,nc,na,nw = _msig2(next_m2)
    nm = len(by_m2.get(curr_m2,[]))
    nnm= len(by_m2.get(next_m2,[]))
    console.print(f'  Phase:          [{phase_col}]{phase} ({total}/100)[/{phase_col}]')
    console.print(f'  This month ({MN2[curr_m2-1]}):  [{cc}]{cs} ({ca:+.1f}% avg, {cw}/{nm} up)[/{cc}]')
    console.print(f'  Next month ({MN2[next_m2-1]}):  [{nc}]{ns} ({na:+.1f}% avg, {nw}/{nnm} up)[/{nc}]')
    console.print()
    pb = phase in ('MARKUP','ACCUMULATION')
    pba= phase in ('MARKDOWN','DISTRIBUTION')
    sb = cs in ('S.BUY','BUY'); sba= cs in ('S.AVD','AVOID')
    nb = ns in ('S.BUY','BUY'); nba= ns in ('S.AVD','AVOID')
    console.print('  [bold]Combined Action:[/bold]')
    if pb and sb:    console.print('  [green]STRONG BUY — Phase bullish + seasonal bullish. Full size.[/green]')
    elif pb and sba: console.print('  [yellow]CAUTION — Phase bullish but seasonal weak. Half size, tight stops.[/yellow]')
    elif pba and sba:console.print('  [red]STRONG AVOID — Phase bearish + seasonal bearish. Cash only.[/red]')
    elif pba and sb: console.print('  [yellow]CONFLICT — Phase bearish but seasonal strong. Wait for phase to improve.[/yellow]')
    elif sb:         console.print('  [cyan]SELECTIVE — Transition + seasonal support. Best setups only.[/cyan]')
    else:            console.print('  [yellow]MIXED — No clear edge. Reduce exposure.[/yellow]')
    console.print()
    if nb and pba:   console.print(f'  [cyan]PREPARE — {MN2[next_m2-1]} seasonal {ns}. Watch for entries as phase improves.[/cyan]')
    elif nba and pb: console.print(f'  [yellow]WARNING — {MN2[next_m2-1]} seasonal {ns}. Consider taking profits soon.[/yellow]')
    console.print()


def analyze_best_rr(db_path='nepse_market_data.db'):
    """Option 36 - Best R/R Scanner: finds stocks with good R/R at current price"""
    from rich.console import Console
    from rich.table import Table
    from rich.rule import Rule
    console = Console(width=120)
    import sqlite3

    console.print()
    console.rule('[bold yellow]Option 36 — Best R/R Scanner[/bold yellow]', style='yellow')
    console.print()
    console.print('  Scanning all stocks for R/R >= 1.5 at current price...', style='dim')
    console.print()

    conn = sqlite3.connect(db_path)
    symbols = [s[0] for s in conn.execute(
        'SELECT DISTINCT symbol FROM broker_activity ORDER BY symbol'
    ).fetchall()]

    # Pre-load sector data once
    _sect_data = {}
    try:
        _sp = _load_sector_prices(db_path)
        _sect_data = _sector_returns(_sp)
    except: pass

    results = []
    for symbol in symbols:
        try:
            prices = conn.execute(
                'SELECT date, high, low, close, volume FROM stock_prices '
                'WHERE symbol=? AND close > 0 ORDER BY date DESC LIMIT 200',
                (symbol,)
            ).fetchall()
            if len(prices) < 10:
                continue

            curr = prices[0][3]
            # Adaptive zone based on ATR(14)
            _tr_list = []
            for i in range(1, min(15, len(prices))):
                h, l, pc = prices[i][1], prices[i][2], prices[i][3]
                _tr_list.append(max(h-l, abs(h-pc), abs(l-pc)))
            atr = sum(_tr_list)/len(_tr_list) if _tr_list else curr*0.02
            zone = max(atr * 1.5, curr * 0.01)

            # Build volume-weighted touch levels
            _highs  = [(p[1], p[4] or 1) for p in prices]
            _lows   = [(p[2], p[4] or 1) for p in prices]
            _levels = _highs + _lows

            # Cluster with touch count + volume weighting
            _used = set()
            _clusters = []
            for i, (v1, vol1) in enumerate(_levels):
                if i in _used: continue
                grp_v, grp_vol, idx = [v1], [vol1], [i]
                for j, (v2, vol2) in enumerate(_levels):
                    if j != i and j not in _used and abs(v1-v2) <= zone:
                        grp_v.append(v2); grp_vol.append(vol2); idx.append(j)
                touches = len(grp_v)
                if touches >= 2:
                    avg_price  = sum(grp_v)/touches
                    avg_vol    = sum(grp_vol)/touches
                    # Recency bonus: more recent touches score higher
                    recency = sum(1/(k+1) for k in sorted(idx))
                    strength = touches * 0.5 + (avg_vol/max(p[4] or 1 for p in prices)) * 2 + recency
                    _clusters.append((avg_price, strength, touches))
                    _used.update(idx)

            # Select strongest support and resistance
            _sup_candidates = [(p, s, t) for p, s, t in _clusters if p < curr * 0.999]
            _res_candidates = [(p, s, t) for p, s, t in _clusters if p > curr * 1.02]

            if not _sup_candidates or not _res_candidates:
                continue

            # Pick nearest strong support (within 8% below) with best strength
            _sup_near = [(p, s, t) for p, s, t in _sup_candidates if p >= curr * 0.92]
            if not _sup_near:
                _sup_near = _sup_candidates
            support_level = max(_sup_near, key=lambda x: x[1])
            support = support_level[0]

            # Pick nearest strong resistance (within 15% above) with best strength
            _res_near = [(p, s, t) for p, s, t in _res_candidates if p <= curr * 1.15]
            if not _res_near:
                _res_near = _res_candidates
            resistance_level = max(_res_near, key=lambda x: x[1])
            resistance = resistance_level[0]
            stop_loss  = support * 0.97
            target     = resistance * 0.99
            risk       = curr - stop_loss
            reward     = target - curr
            rr         = round(reward / risk, 2) if risk > 0 else 0
            if rr < 1.5:
                continue

            # Broker score
            dates = [d[0] for d in conn.execute(
                'SELECT DISTINCT date FROM broker_activity WHERE symbol=? ORDER BY date DESC LIMIT 5',
                (symbol,)
            ).fetchall()]
            buy_days = sum(1 for d in dates if (conn.execute(
                'SELECT SUM(net_val) FROM broker_activity WHERE symbol=? AND date=?',
                (symbol, d)
            ).fetchone()[0] or 0) > 0)
            broker_pct = round((buy_days / len(dates)) * 100) if dates else 0

            # RSI
            closes = [p[3] for p in prices[:15]]
            gains  = [max(closes[i-1]-closes[i], 0) for i in range(1, len(closes))]
            losses = [max(closes[i]-closes[i-1], 0) for i in range(1, len(closes))]
            avg_g  = sum(gains)/len(gains) if gains else 0
            avg_l  = sum(losses)/len(losses) if losses else 1
            rsi    = round(100 - (100/(1 + avg_g/avg_l)), 1) if avg_l > 0 else 50

            # Sector momentum
            sect_5d = 0.0
            try:
                _sym_sect = (conn.execute(
                    "SELECT sector FROM companies WHERE symbol=?", (symbol,)
                ).fetchone() or [None])[0]
                if _sym_sect and _sect_data:
                    _NMAP = {
                        "Hydro Power":"Hydropower","Commercial Banks":"Commercial Banks",
                        "Development Banks":"Development Banks","Finance":"Finance",
                        "Microfinance":"Microfinance","Life Insurance":"Life Insurance",
                        "Non Life Insurance":"Non-Life Insurance",
                        "Manufacturing And Processing":"Manufacturing",
                        "Hotels And Tourism":"Hotel & Tourism",
                        "Investment":"Investment","Tradings":"Trading","Others":"Others",
                    }
                    _sk = _NMAP.get(_sym_sect, _sym_sect)
                    _sd = _sect_data.get(_sk) or _sect_data.get(_sym_sect)
                    if _sd:
                        sect_5d = _sd.get(5) or 0.0
            except: pass

            results.append((symbol, curr, round(support,1), round(resistance,1),
                           round(stop_loss,1), round(target,1), rr, broker_pct, rsi, sect_5d))
        except:
            continue

    conn.close()
    results.sort(key=lambda x: x[6], reverse=True)

    # ── Sector phase map (from option 37 logic) ──
    import datetime as _dt36
    from collections import defaultdict as _dd36
    _NAME_MAP36 = {
        'Hydro Power':'Hydropower','Commercial Banks':'Commercial Banks',
        'Development Banks':'Development Banks','Finance':'Finance',
        'Microfinance':'Microfinance','Life Insurance':'Life Insurance',
        'Non Life Insurance':'Non-Life Insurance',
        'Manufacturing And Processing':'Manufacturing',
        'Hotels And Tourism':'Hotel & Tourism',
        'Investment':'Investment','Tradings':'Trading','Others':'Others',
    }
    _conn36 = sqlite3.connect(db_path)
    _latest36 = _conn36.execute(
        "SELECT MAX(date) FROM stock_prices WHERE close>0"
    ).fetchone()[0]
    _sect_rows36 = _conn36.execute(
        "SELECT sp.symbol, c.sector, sp.close "
        "FROM stock_prices sp JOIN companies c ON sp.symbol=c.symbol "
        "WHERE sp.close>0 AND sp.date>=date(?,'-60 days') "
        "ORDER BY sp.symbol, sp.date",
        (_latest36,)
    ).fetchall()
    _sym_prices36 = _dd36(list)
    _sym_sect36   = {}
    for sym,sect,cl in _sect_rows36:
        _sym_sect36[sym] = _NAME_MAP36.get(sect, sect)
        _sym_prices36[sym].append(cl)
    _sect_phase36 = {}
    _sect_data36  = _dd36(lambda: {'above20':0,'total':0,'adv':0,'dec':0})
    for sym,closes in _sym_prices36.items():
        sect = _sym_sect36[sym]
        if len(closes) < 20: continue
        ma20 = sum(closes[-20:])/20
        if closes[-1] > ma20: _sect_data36[sect]['above20'] += 1
        _sect_data36[sect]['total'] += 1
        if len(closes)>=2:
            if closes[-1]>closes[-2]: _sect_data36[sect]['adv'] += 1
            elif closes[-1]<closes[-2]: _sect_data36[sect]['dec'] += 1
    for sect,sd in _sect_data36.items():
        if sd['total'] < 3: continue
        pab = sd['above20']/sd['total']*100
        adr = sd['adv']/(sd['adv']+sd['dec'])*100 if (sd['adv']+sd['dec'])>0 else 50
        sc = 0
        if pab>=55: sc+=2
        elif pab>=45: sc+=1
        if adr>=55: sc+=2
        elif adr>=45: sc+=1
        if sc>=4: _sect_phase36[sect]='MARKUP'
        elif sc>=3: _sect_phase36[sect]='ACCUM'
        elif sc>=2: _sect_phase36[sect]='TRANSIT'
        else: _sect_phase36[sect]='DISTRIB'

    # ── Seasonal map for current month ──
    _today36  = _dt36.date.today()
    _curr_m36 = _today36.month
    _nep_hist36 = _conn36.execute(
        "SELECT date,close FROM stock_prices WHERE symbol='NEPSE' AND close>0 ORDER BY date"
    ).fetchall()
    _conn36.close()
    _by_m36 = _dd36(list)
    for _r36 in _nep_hist36:
        _d36 = _dt36.date.fromisoformat(_r36[0])
        if (_d36.year,_d36.month)==(_today36.year,_today36.month): continue
        _mrows = [x for x in _nep_hist36 if x[0][:7]==f'{_d36.year}-{_d36.month:02d}']
        if len(_mrows)>=10:
            _ret36=(_mrows[-1][1]-_mrows[0][1])/_mrows[0][1]*100
            if _ret36 not in _by_m36[_d36.month]: _by_m36[_d36.month].append(_ret36)
    _curr_seas_avg = sum(_by_m36[_curr_m36])/len(_by_m36[_curr_m36]) if _by_m36[_curr_m36] else 0
    _curr_seas_sig = 'S.BUY' if _curr_seas_avg>=5 else 'BUY' if _curr_seas_avg>=2 else 'NTRL' if _curr_seas_avg>=-1 else 'AVOID'

    console.print(f'  Stocks with R/R >= 1.5 at current price: [bold]{len(results)}[/bold]')
    console.print(f'  Market seasonal ({_dt36.date.today().strftime("%b")}): [{("green" if _curr_seas_sig in ("S.BUY","BUY") else "yellow" if _curr_seas_sig=="NTRL" else "red")}]{_curr_seas_sig} ({_curr_seas_avg:+.1f}%)[/{"green" if _curr_seas_sig in ("S.BUY","BUY") else "yellow" if _curr_seas_sig=="NTRL" else "red"}]', highlight=False)
    console.print()

    if not results:
        console.print('  No stocks found with good R/R right now. Market may be extended.', style='yellow')
        return

    # ── Get volume data per symbol ──
    _conn_vol = sqlite3.connect(db_path)
    _vol_map = {}
    for sym,*_ in results:
        _vrows = _conn_vol.execute(
            "SELECT close, volume FROM stock_prices WHERE symbol=? AND close>0 ORDER BY date DESC LIMIT 20",
            (sym,)
        ).fetchall()
        if len(_vrows) >= 10:
            _closes_v = [r[0] for r in _vrows]
            _vols_v   = [r[1] or 0 for r in _vrows]
            # Volume trend: avg vol last 5 vs avg vol 6-20
            _v5  = sum(_vols_v[:5])/5
            _v15 = sum(_vols_v[5:15])/10 if len(_vols_v)>=15 else sum(_vols_v[5:])/max(len(_vols_v[5:]),1)
            _vol_ratio = _v5/_v15 if _v15>0 else 1.0
            # Up-volume vs down-volume last 10 days
            _up_vol = sum(_vols_v[i] for i in range(1,min(10,len(_vrows))) if _closes_v[i]>_closes_v[i+1] if i+1<len(_closes_v))
            _dn_vol = sum(_vols_v[i] for i in range(1,min(10,len(_vrows))) if _closes_v[i]<_closes_v[i+1] if i+1<len(_closes_v))
            _vol_map[sym] = (_vol_ratio, _up_vol, _dn_vol)
    _conn_vol.close()

    # ── Get sector per symbol ──
    _conn_s2 = sqlite3.connect(db_path)
    _sym_to_sect = {}
    for sym,*_ in results:
        _sr = _conn_s2.execute("SELECT sector FROM companies WHERE symbol=?", (sym,)).fetchone()
        if _sr: _sym_to_sect[sym] = _NAME_MAP36.get(_sr[0], _sr[0])
    _conn_s2.close()

    # ── Composite score with new factors ──
    scored = []
    for row in results:
        sym, curr, sup, res, sl, tgt, rr, bs, rsi, s5d = row
        sect      = _sym_to_sect.get(sym, '')
        phase     = _sect_phase36.get(sect, 'UNKNOWN')
        vol_r, up_v, dn_v = _vol_map.get(sym, (1.0, 0, 0))

        # Distance to support (tighter = better entry)
        dist_sup  = (curr - sup) / curr * 100 if curr > 0 else 99

        rr_score   = min(rr * 20, 40)                          # max 40
        br_score   = bs * 0.3                                   # max 30
        rsi_score  = 15 if rsi < 40 else 8 if rsi < 55 else 0  # max 15
        sect_score = 10 if s5d >= 2 else 5 if s5d >= 0 else 0  # max 10
        # Phase bonus
        phase_score = 10 if phase in ('MARKUP','ACCUM') else 5 if phase=='TRANSIT' else 0  # max 10
        # Volume confirmation bonus
        vol_score  = 8 if vol_r >= 1.2 else 4 if vol_r >= 0.9 else 0  # max 8
        # Proximity bonus: within 3% of support = best entry
        prox_score = 7 if dist_sup <= 3 else 4 if dist_sup <= 6 else 0  # max 7

        score = round(rr_score + br_score + rsi_score + sect_score + phase_score + vol_score + prox_score, 1)

        # HOT tag: MARKUP/ACCUM phase + seasonal BUY/S.BUY + good R/R
        hot = phase in ('MARKUP','ACCUM') and _curr_seas_sig in ('S.BUY','BUY') and rr >= 2.0
        scored.append((sym, curr, sup, res, sl, tgt, rr, bs, rsi, s5d, score, phase, vol_r, dist_sup, hot))
    scored.sort(key=lambda x: x[10], reverse=True)

    table = Table(show_header=True, header_style='bold cyan', box=None, padding=(0,1), min_width=80)
    table.add_column('Sym',    style='bold', width=7, no_wrap=True)
    table.add_column('Price',  justify='right', width=7, no_wrap=True)
    table.add_column('Supp',   justify='right', width=7, no_wrap=True)
    table.add_column('Stop',   justify='right', width=7, no_wrap=True)
    table.add_column('Tgt',    justify='right', width=7, no_wrap=True)
    table.add_column('R/R',    justify='right', width=6, no_wrap=True)
    table.add_column('Dst%',   justify='right', width=6, no_wrap=True)
    table.add_column('Vol',    justify='right', width=6, no_wrap=True)
    table.add_column('RSI',    justify='right', width=4, no_wrap=True)
    table.add_column('Phase',  width=8, no_wrap=True)
    table.add_column('Sc',     justify='right', width=4, no_wrap=True)
    table.add_column('Tag',    width=8, no_wrap=True)

    for sym, curr, sup, res, sl, tgt, rr, bs, rsi, s5d, score, phase, vol_r, dist_sup, hot in scored:
        rr_col   = 'green'  if rr >= 2    else 'yellow'
        rsi_col  = 'green'  if rsi < 35   else 'red' if rsi > 70 else 'white'
        sc_col   = 'green'  if score >= 70 else 'yellow' if score >= 50 else 'red'
        ph_col   = 'green'  if phase in ('MARKUP','ACCUM') else 'yellow' if phase=='TRANSIT' else 'red'
        vol_col  = 'green'  if vol_r >= 1.2 else 'yellow' if vol_r >= 0.9 else 'red'
        dst_col  = 'green'  if dist_sup <= 3 else 'yellow' if dist_sup <= 6 else 'red'
        tag = '[bold green]★ HOT[/bold green]' if hot else ('[green]OVERSOLD[/green]' if rsi < 35 else '[red]OVERBOUGHT[/red]' if rsi > 70 else '')
        table.add_row(
            sym,
            f'{curr:,.0f}',
            f'{sup:,.0f}',
            f'{sl:,.0f}',
            f'{tgt:,.0f}',
            f'[{rr_col}]1:{rr:.1f}[/{rr_col}]',
            f'[{dst_col}]{dist_sup:.1f}%[/{dst_col}]',
            f'[{vol_col}]{vol_r:.1f}x[/{vol_col}]',
            f'[{rsi_col}]{rsi}[/{rsi_col}]',
            f'[{ph_col}]{phase:<8}[/{ph_col}]',
            f'[{sc_col}]{score:.0f}[/{sc_col}]',
            tag,
        )

    console.print(table)
    console.print()
    console.print('  [dim]Dst% = distance from support | Vol = 5d vs 15d volume ratio | ★ HOT = phase+seasonal+RR aligned[/dim]')
    console.print('  [dim]Tip: Run option 35 on any stock above for full trade plan.[/dim]')
    console.print()





def analyze_sector_seasonality(db_path='nepse_market_data.db'):
    """Option 40 - Sector Seasonality with sub-menu"""
    from rich.console import Console
    from rich.table import Table
    from rich.rule import Rule
    from rich import box
    import sqlite3, datetime
    from collections import defaultdict

    console = Console()

    # ── Sub-menu ──
    console.print()
    console.rule('[bold yellow]Option 40 — Sector Seasonality[/bold yellow]', style='yellow')
    console.print()
    console.print('  [bold]Select view:[/bold]')
    console.print('  [cyan]a[/cyan]  Greg Monthly (Jan-Dec)')
    console.print('  [cyan]b[/cyan]  Nepali Monthly (Baisakh-Chaitra)')
    console.print('  [cyan]c[/cyan]  FYQ Quarterly (Shrawan-based)')
    console.print('  [cyan]d[/cyan]  Greg Quarterly (Jan-based)')
    console.print('  [cyan]e[/cyan]  Full Summary (current + upcoming all timeframes)')
    console.print()
    choice = input('  Choice [a/b/c/d/e]: ').strip().lower()
    if choice not in ('a','b','c','d','e'):
        console.print('[red]Invalid choice.[/red]')
        return

    # ── BS conversion ──
    _baisakh_start = {
        2077:(2020,4,13),2078:(2021,4,14),2079:(2022,4,14),
        2080:(2023,4,14),2081:(2024,4,13),2082:(2025,4,14),2083:(2026,4,14),
    }
    _bs_month_days = {
        2077:[31,31,31,32,31,31,30,29,30,29,30,30],
        2078:[31,31,32,31,31,31,30,29,30,29,30,30],
        2079:[31,32,31,32,31,30,30,29,30,29,30,30],
        2080:[31,31,31,32,31,31,30,29,30,29,30,30],
        2081:[31,31,32,31,31,31,30,29,30,29,30,30],
        2082:[31,32,31,32,31,30,30,29,30,29,30,30],
        2083:[31,31,31,32,31,31,30,29,30,29,30,30],
    }
    _bs_names = {1:'Baisakh',2:'Jestha',3:'Ashadh',4:'Shrawan',5:'Bhadra',
                 6:'Ashwin',7:'Kartik',8:'Mangsir',9:'Poush',10:'Magh',
                 11:'Falgun',12:'Chaitra'}
    _date = datetime.date

    def _to_bs(d):
        for yr in sorted(_baisakh_start.keys(), reverse=True):
            g = _baisakh_start[yr]
            s = _date(g[0],g[1],g[2])
            if d >= s:
                days = (d-s).days
                for mi,md in enumerate(_bs_month_days.get(yr,[])):
                    if days < md: return yr, mi+1
                    days -= md
                return yr+1,1
        return None,None

    def _fyq(bsm):
        if   bsm in (1,2,3):   return 'FYQ4'
        elif bsm in (4,5,6):   return 'FYQ1'
        elif bsm in (7,8,9):   return 'FYQ2'
        else:                   return 'FYQ3'

    def _gq(m):
        if   m in (1,2,3):   return 'Q1'
        elif m in (4,5,6):   return 'Q2'
        elif m in (7,8,9):   return 'Q3'
        else:                 return 'Q4'

    def _sig(avg):
        if avg >=  5: return 'S.BUY','green'
        if avg >=  2: return 'BUY','green'
        if avg >= -1: return 'NTRL','yellow'
        if avg >= -3: return 'AVOID','red'
        return 'S.AVD','red'

    NAME_MAP = {
        'Hydro Power':'Hydropower','Commercial Banks':'Commercial Banks',
        'Development Banks':'Development Banks','Finance':'Finance',
        'Microfinance':'Microfinance','Life Insurance':'Life Insurance',
        'Non Life Insurance':'Non-Life Insurance',
        'Manufacturing And Processing':'Manufacturing',
        'Hotels And Tourism':'Hotel & Tourism',
        'Investment':'Investment','Tradings':'Trading','Others':'Others',
    }

    MONTH_NAMES  = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    FYQ_LABELS   = {'FYQ1':'Shr-Ash','FYQ2':'Kar-Pou','FYQ3':'Mag-Cha','FYQ4':'Bai-Ash'}
    GQ_LABELS    = {'Q1':'Jan-Mar','Q2':'Apr-Jun','Q3':'Jul-Sep','Q4':'Oct-Dec'}
    FYQ_ORDER    = ['FYQ1','FYQ2','FYQ3','FYQ4']
    GQ_ORDER     = ['Q1','Q2','Q3','Q4']

    GM_CHAR = {
        1:'Jan(Poush-Magh) — Tax selling + Dev Banks/Hydro surge. Jan is S.BUY for Dev Banks, Hydro, Investment.',
        2:'Feb(Magh-Falgun) — Broad weakness. Dev Banks S.AVD. Manufacturing outlier S.BUY.',
        3:'Mar(Falgun-Chaitra) — Mixed. Recovery in some. Pre-Baisakh positioning begins.',
        4:'Apr(Chaitra-Baisakh) — New Year transition. Mostly weak. Hotel & Tourism S.BUY.',
        5:'May(Baisakh-Jestha) — Manufacturing monster month (+41% avg, 5/5 up). Others weak.',
        6:'Jun(Jestha-Ashadh) — Finance S.BUY (+11.8%). Others BUY. FY year-end deployment.',
        7:'Jul(Ashadh-Shrawan) — NEW FISCAL YEAR. Strongest month. All sectors S.BUY or BUY. Deploy capital.',
        8:'Aug(Shrawan-Bhadra) — Post-July correction. Manufacturing exception (+30%). Most S.AVD.',
        9:'Sep(Bhadra-Ashwin) — Weakest month. Pre-Dashain profit booking. Avoid most sectors.',
        10:'Oct(Ashwin-Kartik) — Dashain/Tihar festive rally begins. Mixed — selective buying.',
        11:'Nov(Kartik-Mangsir) — Dev Banks, Hotel, Hydro BUY. Manufacturing S.BUY. Others mixed.',
        12:'Dec(Mangsir-Poush) — Hydropower BUY. Manufacturing S.BUY. Most others weak.',
    }
    BS_CHAR = {
        1:'Baisakh — New Year euphoria. Hotel & Tourism, Finance strong. FYQ4 start.',
        2:'Jestha — Finance S.BUY. FY year-end positioning. Broad mixed.',
        3:'Ashadh — New FY eve. Deployment begins. Finance/Microfinance strong.',
        4:'Shrawan — New FY month 1. Monsoon starts. Hydropower peaks. Broad rally.',
        5:'Bhadra — Mid-monsoon. Mixed. Post-Shrawan consolidation.',
        6:'Ashwin — Pre-Dashain. Profit booking. Weak for most sectors.',
        7:'Kartik — Dashain/Tihar. Festive rally. Dev Banks historically very strong.',
        8:'Mangsir — Post-Tihar. Dev Banks, Hydropower continue. Others mixed.',
        9:'Poush — FYQ2 end. Year-end window dressing. Mixed signals.',
        10:'Magh — Dev Banks S.BUY (Jan effect). Hydropower strong. Broad positive.',
        11:'Falgun — Broad weakness. Dev Banks S.AVD. Most sectors negative.',
        12:'Chaitra — FYQ3 end. Mixed recovery. Pre-Baisakh positioning.',
    }
    FYQ_CHAR = {
        'FYQ1':'Shr-Ash — New FY deployment + monsoon. Hydropower FYQ2 peak. Equal-weighted index mixed/weak despite NEPSE index strength.',
        'FYQ2':'Kar-Pou — Post-Dashain/Tihar. Dev Banks 5/5 up (+16%). Hydropower S.BUY. Strongest FYQ for most sectors.',
        'FYQ3':'Mag-Cha — Mid-year lull. Tax pressure. Weakest FYQ for most sectors.',
        'FYQ4':'Bai-Ash — New Year euphoria + FY-end buying. Hotel, Finance, Microfinance S.BUY. Strong for 8/12 sectors.',
    }
    GQ_CHAR = {
        'Q1':'Jan-Mar — Dev Banks, Hydro, Investment S.BUY. Commercial Banks S.AVD. Mixed overall.',
        'Q2':'Apr-Jun — Finance BUY, Hotel S.BUY. Hydropower S.AVD. Mixed quarter.',
        'Q3':'Jul-Sep — Strongest Greg quarter for NEPSE index. Dev Banks, Finance BUY. Aug/Sep drag.',
        'Q4':'Oct-Dec — Hydro, Others S.BUY. Manufacturing mixed. Broad moderate signals.',
    }

    today = datetime.date.today()
    bs_yr, curr_bsm = _to_bs(today)
    curr_fyq  = _fyq(curr_bsm)
    curr_gq   = _gq(today.month)
    curr_bsm_name = _bs_names.get(curr_bsm, '')
    next_gm   = today.month % 12 + 1
    next_bsm  = curr_bsm % 12 + 1
    next_fyq  = FYQ_ORDER[(FYQ_ORDER.index(curr_fyq)+1) % 4]
    next_gq   = GQ_ORDER [(GQ_ORDER.index(curr_gq)  +1) % 4]
    curr_fyq_key = (bs_yr if curr_bsm>=4 else bs_yr-1, curr_fyq)
    curr_gq_key  = (today.year, curr_gq)

    # ── Load OHLC ──
    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT sp.symbol, c.sector, sp.date, sp.open, sp.high, sp.low, sp.close
        FROM stock_prices sp JOIN companies c ON sp.symbol=c.symbol
        WHERE sp.close>0 AND sp.date>='2021-01-01'
        ORDER BY sp.symbol, sp.date
    """).fetchall()
    conn.close()
    if not rows:
        console.print('[red]No data.[/red]'); return

    sym_sector = {}
    sym_ohlc   = defaultdict(dict)
    for sym,sect,dt,op,hi,lo,cl in rows:
        sym_sector[sym] = NAME_MAP.get(sect, sect)
        sym_ohlc[sym][dt] = (op or cl, hi or cl, lo or cl, cl)

    sect_daily = defaultdict(lambda: defaultdict(list))
    for sym,dmap in sym_ohlc.items():
        sect = sym_sector[sym]
        for dt,ohlc in dmap.items():
            sect_daily[sect][dt].append(ohlc)

    sect_index = {}
    for sect,dmap in sect_daily.items():
        sect_index[sect] = {}
        for dt,ohlcs in dmap.items():
            n = len(ohlcs)
            sect_index[sect][dt] = (
                sum(o[0] for o in ohlcs)/n,
                sum(o[1] for o in ohlcs)/n,
                sum(o[2] for o in ohlcs)/n,
                sum(o[3] for o in ohlcs)/n,
            )

    # ── Group into periods ──
    gm_g  = defaultdict(lambda: defaultdict(list))
    bsm_g = defaultdict(lambda: defaultdict(list))
    fyq_g = defaultdict(lambda: defaultdict(list))
    gq_g  = defaultdict(lambda: defaultdict(list))

    for sect,dmap in sect_index.items():
        for dt_str in sorted(dmap.keys()):
            d = _date.fromisoformat(dt_str)
            o,h,l,c = dmap[dt_str]
            entry = (dt_str,o,h,l,c)
            bsy,bsm = _to_bs(d)
            if bsy and bsm:
                fy = bsy if bsm>=4 else bsy-1
                fyq_g [sect][(fy, _fyq(bsm))].append(entry)
                bsm_g [sect][(bsy, bsm)].append(entry)
            gm_g[sect][(d.year, d.month)].append(entry)
            gq_g[sect][(d.year, _gq(d.month))].append(entry)

    # ── _calc ──
    def _calc(groups, curr_key, label_fn, min_days=10):
        by_label = defaultdict(list)
        all_keys = sorted(groups.keys())
        first_k  = all_keys[0] if all_keys else None
        for key,entries in groups.items():
            if key == curr_key: continue
            if key == first_k:  continue
            if len(entries) < min_days: continue
            op = entries[0][1]; cl = entries[-1][4]
            hi = max(e[2] for e in entries)
            lo = min(e[3] for e in entries if e[3]>0)
            if op <= 0: continue
            ret = (cl-op)/op*100
            up  = (hi-op)/op*100
            dn  = (op-lo)/op*100 if lo>0 else 0
            sw  = (hi-lo)/lo*100 if lo>0 else 0
            lbl = label_fn(key)
            fy_str = str(key[0])
            by_label[lbl].append((fy_str, ret, up, dn, sw))
        result = {}
        for lbl,vals in by_label.items():
            rets = [v[1] for v in vals]
            ups  = [v[2] for v in vals]
            dns  = [v[3] for v in vals]
            sws  = [v[4] for v in vals]
            n    = len(rets)
            wins = sum(1 for r in rets if r>0)
            result[lbl] = (
                sum(rets)/n, wins, n,
                max(rets), min(rets),
                sum(ups)/n, sum(dns)/n,
                sum(sws)/n, min(sws), max(sws),
                sorted((v[0],v[1]) for v in vals)
            )
        return result

    # ── Table helpers ──
    def _make_table():
        t = Table(show_header=True, header_style='bold cyan', box=box.SIMPLE_HEAVY,
                  border_style='cyan', padding=(0,1))
        t.add_column('Period',     width=20, justify='left',   no_wrap=True)
        t.add_column('Ret',        width=8,  justify='right',  no_wrap=True)
        t.add_column('W/T',        width=5,  justify='center', no_wrap=True)
        t.add_column('Sig',        width=7,  justify='left',   no_wrap=True)
        t.add_column('Swing(rng)', width=12, justify='left',   no_wrap=True)
        t.add_column('Up',         width=8,  justify='right',  no_wrap=True)
        t.add_column('Dn',         width=8,  justify='right',  no_wrap=True)
        return t

    def _row(label, stats, marker, col):
        avg,wins,total,best,worst,avg_up,avg_dn,avg_sw,min_sw,max_sw,hist = stats
        sig,_ = _sig(avg)
        sw_str = f'{avg_sw:.0f}%({min_sw:.0f}-{max_sw:.0f})'
        return [
            f'[bold]{label}{marker}[/bold]',
            f'[{col}]{avg:+.1f}%[/{col}]',
            f'[{col}]{wins}/{total}[/{col}]',
            f'[{col}]{sig}[/{col}]',
            f'[yellow]{sw_str}[/yellow]',
            f'[green]+{avg_up:.1f}%[/green]',
            f'[red]-{avg_dn:.1f}%[/red]',
        ]

    def _hist(stats, label):
        hist = stats[10]
        return f'   [dim]{label}: ' + '  '.join(f'{fy}:{r:+.0f}%' for fy,r in hist) + '[/dim]'

    def _print_section(title, all_sectors, stats_map, order, label_fn, curr_lbl, next_lbl):
        console.rule(f'[bold cyan]{title}[/bold cyan]', style='cyan')
        console.print()
        for sect in all_sectors:
            stats = stats_map.get(sect, {})
            if not stats: continue
            console.print(f'  [bold white]{sect}[/bold white]')
            t = _make_table()
            for key in order:
                if key not in stats: continue
                lbl = label_fn(key)
                marker = ' <-NOW' if key==curr_lbl else (' <-NXT' if key==next_lbl else '')
                _,col = _sig(stats[key][0])
                t.add_row(*_row(lbl, stats[key], marker, col))
            console.print(t)
            for key in order:
                if key not in stats: continue
                lbl = label_fn(key)
                marker = ' <-NOW' if key==curr_lbl else (' <-NXT' if key==next_lbl else '')
                console.print(_hist(stats[key], f'{lbl}{marker}'))
            console.print()

    all_sectors = sorted(sect_index.keys())

    with console.status('[cyan]Computing...[/cyan]'):
        gm_stats  = {}
        bsm_stats = {}
        fyq_stats = {}
        gq_stats  = {}
        curr_bsm_key = (bs_yr, curr_bsm)
        for sect in all_sectors:
            gm_stats [sect] = _calc(gm_g [sect], (today.year, today.month), lambda k: k[1])
            bsm_stats[sect] = _calc(bsm_g[sect], curr_bsm_key,              lambda k: k[1])
            fyq_stats[sect] = _calc(fyq_g[sect], curr_fyq_key,              lambda k: k[1])
            gq_stats [sect] = _calc(gq_g [sect], curr_gq_key,               lambda k: k[1])

    # ── Render chosen section ──
    console.print()

    if choice == 'a':
        _print_section('Greg Monthly Seasonality', all_sectors, gm_stats,
            list(range(1,13)), lambda k: MONTH_NAMES[k-1],
            today.month, next_gm)

    elif choice == 'b':
        _print_section('Nepali Monthly Seasonality (BS)', all_sectors, bsm_stats,
            list(range(1,13)), lambda k: _bs_names.get(k, str(k)),
            curr_bsm, next_bsm)

    elif choice == 'c':
        _print_section('FYQ Seasonality — Shrawan-based Quarters', all_sectors, fyq_stats,
            FYQ_ORDER, lambda k: f'{k}({FYQ_LABELS[k]})',
            curr_fyq, next_fyq)

    elif choice == 'd':
        _print_section('Greg Quarterly Seasonality', all_sectors, gq_stats,
            GQ_ORDER, lambda k: f'{k}({GQ_LABELS[k]})',
            curr_gq, next_gq)

    elif choice == 'e':
        # ══ FULL SUMMARY ══
        curr_mn   = MONTH_NAMES[today.month-1]
        next_mn   = MONTH_NAMES[next_gm-1]
        curr_bsnm = _bs_names.get(curr_bsm,'')
        next_bsnm = _bs_names.get(next_bsm,'')

        console.rule(f'[bold yellow]Sector Seasonality — Full Summary[/bold yellow]', style='yellow')
        console.print()

        def _rank(stats_map, key):
            rows = []
            for sect in all_sectors:
                v = stats_map.get(sect,{}).get(key)
                if v:
                    sig,col = _sig(v[0])
                    rows.append((v[0], sect, sig, col, v[1], v[2]))
            rows.sort(reverse=True)
            return rows

        def _print_rank(rows, indent='  '):
            for ret,sect,sig,col,wins,total in rows:
                console.print(f'{indent}[{col}]{sig:7s}[/{col}]  {sect:<22}  [{col}]{ret:+.1f}%[/{col}]  [dim]{wins}/{total} up[/dim]', highlight=False)

        def _situation(rows):
            buys  = [(s,r) for r,s,sig,col,w,t in rows if sig in ('S.BUY','BUY')]
            avds  = [(s,r) for r,s,sig,col,w,t in rows if sig in ('S.AVD','AVOID')]
            ntrl  = [(s,r) for r,s,sig,col,w,t in rows if sig == 'NTRL']
            parts = []
            if buys:  parts.append(f'[green]BUY:[/green] {", ".join(s for s,r in buys[:4])}')
            if ntrl:  parts.append(f'[yellow]NTRL:[/yellow] {", ".join(s for s,r in ntrl[:3])}')
            if avds:  parts.append(f'[red]AVOID:[/red] {", ".join(s for s,r in avds[:4])}')
            return '  |  '.join(parts)

        # ── CURRENT ──
        console.rule('[bold]▶ CURRENT SITUATION[/bold]')
        console.print()

        # Greg Month
        gm_rows = _rank(gm_stats, today.month)
        console.print(f'  [bold cyan]Greg Month — {curr_mn}[/bold cyan]')
        console.print(f'  [dim]{GM_CHAR.get(today.month,"")}[/dim]')
        console.print(f'  {_situation(gm_rows)}')
        console.print()
        _print_rank(gm_rows)
        console.print()

        # BS Month
        bsm_rows = _rank(bsm_stats, curr_bsm)
        console.print(f'  [bold cyan]Nepali Month — {curr_bsnm}[/bold cyan]')
        console.print(f'  [dim]{BS_CHAR.get(curr_bsm,"")}[/dim]')
        console.print(f'  {_situation(bsm_rows)}')
        console.print()
        _print_rank(bsm_rows)
        console.print()

        # FYQ
        fyq_rows = _rank(fyq_stats, curr_fyq)
        console.print(f'  [bold cyan]FYQ — {curr_fyq} ({FYQ_LABELS[curr_fyq]})[/bold cyan]')
        console.print(f'  [dim]{FYQ_CHAR.get(curr_fyq,"")}[/dim]')
        console.print(f'  {_situation(fyq_rows)}')
        console.print()
        _print_rank(fyq_rows)
        console.print()

        # Greg Q
        gq_rows = _rank(gq_stats, curr_gq)
        console.print(f'  [bold cyan]Greg Quarter — {curr_gq} ({GQ_LABELS[curr_gq]})[/bold cyan]')
        console.print(f'  [dim]{GQ_CHAR.get(curr_gq,"")}[/dim]')
        console.print(f'  {_situation(gq_rows)}')
        console.print()
        _print_rank(gq_rows)
        console.print()

        # ── UPCOMING ──
        console.rule('[bold yellow]▶ UPCOMING[/bold yellow]', style='yellow')
        console.print()

        # Next Greg Month
        ngm_rows = _rank(gm_stats, next_gm)
        console.print(f'  [bold cyan]Next Greg Month — {next_mn}[/bold cyan]')
        console.print(f'  [dim]{GM_CHAR.get(next_gm,"")}[/dim]')
        console.print(f'  {_situation(ngm_rows)}')
        console.print()
        _print_rank(ngm_rows)
        console.print()

        # Next BS Month
        nbsm_rows = _rank(bsm_stats, next_bsm)
        console.print(f'  [bold cyan]Next Nepali Month — {next_bsnm}[/bold cyan]')
        console.print(f'  [dim]{BS_CHAR.get(next_bsm,"")}[/dim]')
        console.print(f'  {_situation(nbsm_rows)}')
        console.print()
        _print_rank(nbsm_rows)
        console.print()

        # Next FYQ
        nfyq_rows = _rank(fyq_stats, next_fyq)
        console.print(f'  [bold cyan]Next FYQ — {next_fyq} ({FYQ_LABELS[next_fyq]})[/bold cyan]')
        console.print(f'  [dim]{FYQ_CHAR.get(next_fyq,"")}[/dim]')
        console.print(f'  {_situation(nfyq_rows)}')
        console.print()
        _print_rank(nfyq_rows)
        console.print()

        # Next Greg Q
        ngq_rows = _rank(gq_stats, next_gq)
        console.print(f'  [bold cyan]Next Greg Quarter — {next_gq} ({GQ_LABELS[next_gq]})[/bold cyan]')
        console.print(f'  [dim]{GQ_CHAR.get(next_gq,"")}[/dim]')
        console.print(f'  {_situation(ngq_rows)}')
        console.print()
        _print_rank(ngq_rows)
        console.print()

    # ══ RECOMMENDATION ══
    if choice == 'e':
        console.rule('[bold green]▶ RECOMMENDATION[/bold green]', style='green')
        console.print()

        # Best current sectors — consensus across timeframes
        score = defaultdict(int)
        for sect in all_sectors:
            for stats,key in [(gm_stats,today.month),(bsm_stats,curr_bsm),(fyq_stats,curr_fyq),(gq_stats,curr_gq)]:
                v = stats.get(sect,{}).get(key)
                if v:
                    sig,_ = _sig(v[0])
                    if sig == 'S.BUY': score[sect] += 2
                    elif sig == 'BUY': score[sect] += 1
                    elif sig == 'AVOID': score[sect] -= 1
                    elif sig == 'S.AVD': score[sect] -= 2

        ranked = sorted(score.items(), key=lambda x: -x[1])
        top3    = [s for s,sc in ranked if sc > 0][:3]
        avoid3  = [s for s,sc in ranked[::-1] if sc < 0][:3]

        # Best upcoming sectors
        uscore = defaultdict(int)
        for sect in all_sectors:
            for stats,key in [(gm_stats,next_gm),(bsm_stats,next_bsm),(fyq_stats,next_fyq),(gq_stats,next_gq)]:
                v = stats.get(sect,{}).get(key)
                if v:
                    sig,_ = _sig(v[0])
                    if sig == 'S.BUY': uscore[sect] += 2
                    elif sig == 'BUY': uscore[sect] += 1
                    elif sig == 'AVOID': uscore[sect] -= 1
                    elif sig == 'S.AVD': uscore[sect] -= 2

        uranked = sorted(uscore.items(), key=lambda x: -x[1])
        utop3   = [s for s,sc in uranked if sc > 0][:3]
        uavoid3 = [s for s,sc in uranked[::-1] if sc < 0][:3]

        curr_mn   = MONTH_NAMES[today.month-1]
        next_mn   = MONTH_NAMES[next_gm-1]

        console.print(f'  [bold]NOW ({curr_mn} / {curr_fyq} / {curr_gq}):[/bold]')
        if top3:
            console.print(f'  [green]Best sectors:[/green] {", ".join(top3)}')
            console.print(f'  [dim]These sectors score positively across monthly + quarterly timeframes. Historically favourable now.[/dim]')
        if avoid3:
            console.print(f'  [red]Avoid:[/red] {", ".join(avoid3)}')
            console.print(f'  [dim]These sectors score negatively across multiple timeframes. Historically weak now.[/dim]')
        console.print()

        console.print(f'  [bold]UPCOMING ({next_mn} / {next_fyq} / {next_gq}):[/bold]')
        if utop3:
            console.print(f'  [green]Best sectors to position for:[/green] {", ".join(utop3)}')
            console.print(f'  [dim]Strongest seasonal setup across all upcoming timeframes. Consider accumulating before period starts.[/dim]')
        if uavoid3:
            console.print(f'  [red]Avoid next period:[/red] {", ".join(uavoid3)}')
            console.print(f'  [dim]Weak seasonal setup ahead. Consider reducing exposure.[/dim]')
        console.print()

        # Conflict check — sectors good now but bad upcoming
        good_now_bad_next = [s for s in top3 if s in uavoid3]
        bad_now_good_next = [s for s in avoid3 if s in utop3]
        if good_now_bad_next:
            console.print(f'  [yellow]⚠ Rotation alert:[/yellow] {", ".join(good_now_bad_next)} — good NOW but weak UPCOMING. Consider taking profits.')
            console.print()
        if bad_now_good_next:
            console.print(f'  [cyan]⚡ Early entry alert:[/cyan] {", ".join(bad_now_good_next)} — weak NOW but strong UPCOMING. Accumulation opportunity.')
            console.print()

    console.print('  [dim]All returns based on complete periods only. Research only. Not financial advice.[/dim]')
    console.print()


def main():
    args = parse_args()

    if getattr(args, 'preopen', None) is not None:
        cmd_preopen(args.preopen if args.preopen else None)
        return
    if args.legend:
        print_legend()
    elif getattr(args, "buy_sell_guide", False):
        print_buy_sell_guide()
        return
    elif getattr(args, 'full_report', None):
        analyze_full_stock_report(args.full_report)
        return
    elif getattr(args, 'best_rr', False):
        analyze_best_rr()
        return
    elif getattr(args, 'sector_season', False):
        analyze_sector_seasonality()
        return
    elif getattr(args, 'market_phase', False):
        analyze_market_phase()
        return
    elif getattr(args, 'seasonality', False):
        analyze_seasonality()
        return
    elif getattr(args, 'nepali_season', False):
        analyze_nepali_seasonality()
        return
    if getattr(args, "unlock", None) and args.unlock[0].lower() in ("add","delete","list","upcoming"):
        _unlock_db()
        analyze_unlock(args.unlock)
        return
    if getattr(args, "fundamental", None):
        analyze_fundamental(args.fundamental)
        return
    if getattr(args, "earnings", None):
        analyze_earnings(args.earnings)
        return
    if getattr(args, 'momentum_hunter', False):
        analyze_momentum_hunter()
        return
    if getattr(args, 'broker_impact', False):
        analyze_broker_impact()
        return
    if getattr(args, 'broker_trend', None):
        analyze_broker_trend(args.broker_trend)
        return
    if getattr(args, 'broker_date', None):
        analyze_broker_date(args.broker_date[0],args.broker_date[1])
        return
    if getattr(args, 'broker_holders', None):
        analyze_broker_holders(args.broker_holders)
        return

    console.print()
    console.print("[bold green]NEPSE Scanner Starting...[/bold green]")
    console.print()

    n = init_nepse()

    with console.status("[cyan]Fetching market overview...[/cyan]"):
        summary  = get_summary(n)
        gainers  = get_top_gainers(n)
        losers   = get_top_losers(n)
        turnover = get_top_turnover(n)

    print_header(summary)
    console.print()
    if args.movers_only or not any([args.watchlist, args.powersell, args.sector, args.whale, args.sr, args.floor, args.brokers, args.quickpick, args.smartpick, args.broker, args.rs, args.week52, args.portfolio, args.corr, args.size, args.value, args.broker_rs]):
        if gainers or losers or turnover:
            print_market_movers(gainers, losers, turnover)
            console.print()

    if args.movers_only:
        return

    # Decide what to fetch
    need_live  = not (args.floor or args.brokers) or any([args.watchlist, args.powersell, args.sector, args.report, args.sr, args.quickpick, args.smartpick])
    need_floor = any([args.floor, args.brokers, args.powersell, args.sector, args.whale, args.sr, args.broker, args.smartpick])

    live_df = None
    if getattr(args, "offline", False):
        try:
            import sqlite3 as _sq, pandas as _pd
            _conn = _sq.connect("nepse_market_data.db")
            _lat = _conn.execute("SELECT MAX(date) FROM stock_prices").fetchone()[0]
            _rows = _conn.execute("""
                SELECT t.symbol, t.close as ltp, t.open, t.high, t.low, t.volume,
                       ((t.close - y.close) / y.close) * 100 as change_pct,
                       t.close * t.volume as turnover
                FROM stock_prices t
                JOIN stock_prices y ON t.symbol = y.symbol
                WHERE t.date = ? AND y.date = (
                    SELECT MAX(date) FROM stock_prices WHERE date < ?)
            """, (_lat, _lat)).fetchall()
            _conn.close()
            if _rows:
                live_df = _pd.DataFrame(_rows, columns=["symbol","ltp","open","high","low","volume","change_pct","turnover"])
                console.print(f"[dim yellow]OFFLINE MODE - {len(live_df)} securities from DB ({_lat})[/dim yellow]\n")
        except Exception as _oe:
            console.print(f"[red]DB load failed: {_oe}[/red]")
    elif need_live:
        with console.status("[cyan]Fetching live market data...[/cyan]"):
            live_df = get_live_market(n)
        if live_df is not None and not live_df.empty:
            console.print(f"[dim]Loaded {len(live_df)} securities.[/dim]\n")
        else:
            console.print("[dim yellow]Live fetch empty - falling back to DB...[/dim yellow]")
            _force_offline = True

    full_fs = None
    if need_floor:
        full_fs = get_full_floorsheet(n)
        try:
            log_broker_activity(full_fs)
        except Exception:
            pass

    # Run requested features
    if args.watchlist:
        auto_update_watchlist(rs_data=None,full_fs=full_fs,db_path='nepse_market_data.db',top_n=15,silent=True)
        analyze_watchlist(live_df)
        console.print()

    power_sell_results = []
    if args.powersell:
        power_sell_results = analyze_power_sell(full_fs, live_df)
        console.print()

    elif args.week52:
        analyze_week52()
        if getattr(args, "why", False):
            analyze_why(live_df, full_fs)
    elif args.portfolio is not None:
        analyze_portfolio(args.portfolio)
    elif args.corr:
        analyze_corr()
    elif args.size:
        analyze_size(args.size[0], float(args.size[1]))
    elif args.broker_rs:
        analyze_broker_rs()
    if args.fundamental:
        analyze_fundamental(args.fundamental)
        console.print()
    elif args.earnings:
        analyze_earnings(args.earnings)
        console.print()
    elif args.value:
        sector_filter = None if args.value == "ALL" else args.value
        analyze_value(sector_filter)
        console.print()
        console.print()
    elif args.float_sym:
        analyze_float(args.float_sym)
        console.print()
    if args.unlock:
        analyze_unlock(args.unlock)
        console.print()
    if args.sector_trend:
        analyze_sector_trend()
        console.print()
    if args.heatmap:
        analyze_sector_heatmap()
        console.print()
    if getattr(args, 'broker_date', None):
        _bd = args.broker_date
        _date = None if (len(_bd) < 2 or _bd[1].lower() == 'prompt') else _bd[1]
        analyze_broker_date(_bd[0], _date)
        return
    if getattr(args, 'broker_trend', None):
        analyze_broker_trend(symbol=args.broker_trend)
        return
    if getattr(args, "broker_impact", False):
        analyze_broker_impact()
        return
    if getattr(args, "momentum_hunter", False):
        analyze_momentum_hunter()
        return
    if getattr(args, 'broker_holders', None):
        analyze_broker_holders(args.broker_holders)
        return
    if getattr(args, 'broker_holders', None):
        analyze_broker_holders(args.broker_holders)
        return
    if args.rs:
        analyze_relative_strength()
        console.print()
        if getattr(args, "why", False):
            analyze_why(live_df, full_fs)
    if args.sector:
        analyze_sector_rotation(full_fs, live_df)
        console.print()

    if args.whale:
        analyze_whales(full_fs)
        console.print()

    if args.broker:
        analyze_broker_tracker(full_fs, live_df, args.broker)
        console.print()

    if args.quickpick:
        analyze_quick_pick(live_df, offline=getattr(args, "offline", False))
        console.print()

    if args.smartpick:
        analyze_smart_pick(live_df, full_fs)
        console.print()

    if args.sr:
        for sym in args.sr:
            analyze_support_resistance(full_fs, sym)
            console.print()

    if args.floor:
        for sym in args.floor:
            analyze_floorsheet_symbol(get_floorsheet_of_symbol(full_fs, sym), sym)
            console.print()

    if args.brokers:
        analyze_broker_market(full_fs)
        console.print()

    # Default mode — signals
    candidates = pd.DataFrame()
    if not any([args.floor, args.brokers, args.powersell, args.sector,
                args.whale, args.sr, args.watchlist, args.movers_only, args.broker,
                args.quickpick, args.smartpick]):
        if live_df is not None and not live_df.empty:
            with console.status(f"[cyan]Running signals: {', '.join(args.signals)}...[/cyan]"):
                candidates = run_signals(live_df, args.signals)
            print_signals_table(candidates, args.top)
            console.print()
            # Auto-log signals for performance tracking
            try:
                from signal_tracker import log_signals
                log_signals(candidates)
            except Exception as e:
                pass

    if args.report:
        save_daily_report(summary, live_df, candidates, power_sell_results)
    try:
        _rs=_calc_relative_strength()
        auto_update_watchlist(rs_data=_rs,full_fs=full_fs,db_path=chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(95)+chr(100)+chr(97)+chr(116)+chr(97)+chr(46)+chr(100)+chr(98),top_n=15)
    except Exception:
        pass

    console.print(Panel("[dim]Research only. Not financial advice. Paper trade first.[/dim]", border_style="dim"))
    console.print()


# ── RELATIVE STRENGTH ─────────────────────────────────────────────────────────

def _calc_relative_strength(db_path="nepse_market_data.db"):
    """
    For every equity stock, compute 5D/10D/20D return and compare
    to its sector average return over the same window.
    Returns a list of dicts sorted by 5D RS score descending.
    """
    import sqlite3, pandas as pd

    conn = sqlite3.connect(db_path)

    # Pull last 25 trading days for all equity stocks
    df = pd.read_sql_query("""
        SELECT sp.symbol, c.sector, sp.date, sp.close
        FROM stock_prices sp
        JOIN companies c ON sp.symbol = c.symbol
        WHERE sp.date >= date('now', '-35 days')
        ORDER BY sp.symbol, sp.date
    """, conn)
    conn.close()

    if df.empty:
        return []

    df["date"] = pd.to_datetime(df["date"])
    results = []

    for symbol, grp in df.groupby("symbol"):
        grp = grp.sort_values("date").drop_duplicates("date")
        if len(grp) < 6:
            continue
        sector = grp["sector"].iloc[0]
        closes = grp["close"].values

        def pct(n):
            if len(closes) <= n:
                return None
            return (closes[-1] / closes[-n-1] - 1) * 100

        results.append({
            "symbol": symbol,
            "sector": sector,
            "ret5":  pct(5),
            "ret10": pct(10),
            "ret20": pct(20),
        })

    if not results:
        return []

    import pandas as pd
    rdf = pd.DataFrame(results).dropna(subset=["ret5"])

    # Sector averages
    savg = rdf.groupby("sector")[["ret5","ret10","ret20"]].mean().rename(
        columns={"ret5":"sec5","ret10":"sec10","ret20":"sec20"})
    rdf = rdf.join(savg, on="sector")

    rdf["rs5"]  = rdf["ret5"]  - rdf["sec5"]
    rdf["rs10"] = rdf["ret10"] - rdf["sec10"]
    rdf["rs20"] = rdf["ret20"] - rdf["sec20"]

    # Composite RS score: weighted 50/30/20
    rdf["rs_score"] = rdf["rs5"]*0.50 + rdf["rs10"].fillna(0)*0.30 + rdf["rs20"].fillna(0)*0.20

    return rdf.sort_values("rs_score", ascending=False).to_dict("records")


def analyze_relative_strength():
    from rich.table import Table
    from rich.panel import Panel
    from rich import box

    console.rule("[bold cyan]Relative Strength — Stocks vs Their Sector[/]")
    console.print("[dim]Stocks gaining MORE than their sector = early movers[/]\n")

    data = _calc_relative_strength()
    if not data:
        console.print("[red]No data available.[/]")
        return

    # ── TOP OUTPERFORMERS ────────────────────────────────────────────────────
    top = [r for r in data if r["rs5"] > 0][:20]
    bot = [r for r in reversed(data) if r["rs5"] < 0][:10]

    def _fmt(v, show_sign=True):
        if v is None: return "[dim]n/a[/]"
        color = "green" if v >= 0 else "red"
        sign  = "+" if v >= 0 else ""
        return f"[{color}]{sign}{v:.2f}%[/]"

    def _star(rs5):
        if rs5 >= 5:   return "[bold green]★★★ Strong[/]"
        if rs5 >= 2:   return "[green]★★  Leading[/]"
        if rs5 >= 0.5: return "[cyan]★   Outperform[/]"
        if rs5 >= -1:  return "[dim]—   Inline[/]"
        return "[red]â–¼   Lagging[/]"

    tbl = Table(
        title="Top Outperformers (Stock Return âˆ’ Sector Avg)",
        box=box.SIMPLE_HEAVY, show_lines=False,
        title_style="bold white"
    )
    tbl.add_column("#",         style="dim", width=4)
    tbl.add_column("Symbol",    style="bold cyan", width=10)
    tbl.add_column("Sector",    style="white", width=22)
    tbl.add_column("5D Stock",  justify="right", width=10)
    tbl.add_column("5D Sector", justify="right", width=10)
    tbl.add_column("RS (5D)",   justify="right", width=10)
    tbl.add_column("RS (10D)",  justify="right", width=10)
    tbl.add_column("RS (20D)",  justify="right", width=10)
    tbl.add_column("Signal",    width=20)

    for i, r in enumerate(top, 1):
        tbl.add_row(
            str(i),
            r["symbol"],
            r["sector"],
            _fmt(r["ret5"]),
            _fmt(r.get("sec5")),
            _fmt(r["rs5"]),
            _fmt(r.get("rs10")),
            _fmt(r.get("rs20")),
            _star(r["rs5"]),
        )

    console.print(tbl)

    # ── SECTOR SUMMARY ───────────────────────────────────────────────────────
    import pandas as pd
    df = pd.DataFrame(data)
    sec_summary = (
        df.groupby("sector")
        .apply(lambda g: pd.Series({
            "total":  len(g),
            "above":  (g["rs5"] > 0).sum(),
            "below":  (g["rs5"] < 0).sum(),
            "best_symbol": g.loc[g["rs5"].idxmax(), "symbol"] if len(g) > 0 else "",
            "best_rs5":    g["rs5"].max(),
        }))
        .reset_index()
        .sort_values("best_rs5", ascending=False)
    )

    stbl = Table(
        title="Sector Breadth — How Many Stocks Are Outperforming?",
        box=box.SIMPLE_HEAVY, show_lines=False,
        title_style="bold white"
    )
    stbl.add_column("Sector",       style="white", width=24)
    stbl.add_column("Above Sector", justify="right", width=14)
    stbl.add_column("Below Sector", justify="right", width=14)
    stbl.add_column("Best Stock",   style="cyan",  width=12)
    stbl.add_column("Best RS",      justify="right", width=10)

    for _, row in sec_summary.iterrows():
        above_pct = int(row["above"] / max(row["total"],1) * 100)
        stbl.add_row(
            str(row["sector"]),
            f'[green]{int(row["above"])}/{int(row["total"])}  ({above_pct}%)[/]',
            f'[red]{int(row["below"])}/{int(row["total"])}[/]',
            str(row["best_symbol"]),
            _fmt(row["best_rs5"]),
        )

    console.print(stbl)

    # ── BOTTOM LAGGARDS ──────────────────────────────────────────────────────
    if bot:
        btbl = Table(
            title="Bottom Laggards (Underperforming their sector most)",
            box=box.SIMPLE_HEAVY, show_lines=False,
            title_style="bold white"
        )
        btbl.add_column("Symbol",   style="bold red", width=10)
        btbl.add_column("Sector",   style="white",    width=22)
        btbl.add_column("5D Stock", justify="right",  width=10)
        btbl.add_column("RS (5D)",  justify="right",  width=10)
        for r in bot:
            btbl.add_row(
                r["symbol"], r["sector"],
                _fmt(r["ret5"]), _fmt(r["rs5"])
            )
        console.print(btbl)

    console.print(
        f"\n  [bold green]Best RS stock:[/] {data[0]['symbol']} "
        f"(+{data[0]['rs5']:.2f}% vs sector)"
    )
    console.print(
        f"  [bold red]Worst RS stock:[/] {data[-1]['symbol']} "
        f"({data[-1]['rs5']:.2f}% vs sector)"
    )



# ── BROKER ACCUMULATION on RS LEADERS ────────────────────────────────────────

def analyze_broker_rs():
    """
    Cross-reference top RS stocks with today's floorsheet broker activity.
    Shows which brokers are accumulating stocks that are outperforming their sector.
    """
    from rich.table import Table
    from rich.panel import Panel
    from rich import box

    console.rule("[bold cyan]Broker Accumulation on High-RS Stocks[/]")
    console.print("[dim]Smart money confirmation — brokers buying stocks already outperforming their sector[/]\n")

    # ── Step 1: Get top RS stocks ─────────────────────────────────────────────
    rs_data = _calc_relative_strength()
    if not rs_data:
        console.print("[red]No RS data available.[/]")
        return

    # Top 15 outperformers with RS > 0
    top_rs = [r for r in rs_data if r.get("rs5", 0) > 0][:15]
    top_symbols = {r["symbol"] for r in top_rs}
    rs_lookup = {r["symbol"]: r for r in top_rs}

    # ── Step 2: Get floorsheet ────────────────────────────────────────────────
    n = Nepse()
    n.setTLSVerification(False)
    console.print("  [yellow]Fetching floorsheet for broker analysis — 30-60 seconds...[/yellow]")
    raw = fetch_with_retry(lambda: n.getFloorSheet(show_progress=False), "floorsheet", retries=2, delay=3)
    if raw is None or (hasattr(raw, "__len__") and len(raw) == 0):
        console.print("[red]No floorsheet data available.[/]")
        return

    import pandas as pd
    df = raw if isinstance(raw, pd.DataFrame) else pd.DataFrame(raw)
    if df.empty:
        console.print("[red]Floorsheet empty.[/]")
        return

    # Normalize columns
    # Map to standard column names
    if 'stockSymbol' in df.columns:
        df['symbol'] = df['stockSymbol']
    if 'contractQuantity' in df.columns:
        df['quantity'] = pd.to_numeric(df['contractQuantity'], errors='coerce').fillna(0)
    if 'contractAmount' in df.columns:
        df['amount'] = pd.to_numeric(df['contractAmount'], errors='coerce').fillna(0)
    # Use broker IDs only
    if 'buyerMemberId' in df.columns:
        df['buyer_broker'] = df['buyerMemberId'].fillna('Unknown')
    elif 'buyerBrokerName' in df.columns:
        df['buyer_broker'] = df['buyerBrokerName'].fillna('Unknown')
    # Use broker IDs only
    if 'sellerMemberId' in df.columns:
        df['seller_broker'] = df['sellerMemberId'].fillna('Unknown')
    elif 'sellerBrokerName' in df.columns:
        df['seller_broker'] = df['sellerBrokerName'].fillna('Unknown')
    for col in ['quantity', 'amount']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Filter to top RS symbols only
    rs_floor = df[df['symbol'].isin(top_symbols)].copy()
    if rs_floor.empty:
        console.print("[yellow]None of the top RS stocks traded in floorsheet today.[/]")
        return

    # ── Step 3: Broker net activity per RS stock ──────────────────────────────
    results = []
    for symbol in top_symbols:
        sym_df = rs_floor[rs_floor['symbol'] == symbol]
        if sym_df.empty:
            continue

        buy_qty  = sym_df.groupby('buyer_broker')['quantity'].sum()
        sell_qty = sym_df.groupby('seller_broker')['quantity'].sum()

        all_brokers = set(buy_qty.index) | set(sell_qty.index)
        for broker in all_brokers:
            b = float(buy_qty.get(broker, 0))
            s = float(sell_qty.get(broker, 0))
            net = b - s
            total = b + s
            if total == 0:
                continue
            results.append({
                "symbol":  symbol,
                "sector":  rs_lookup[symbol]["sector"],
                "rs5":     rs_lookup[symbol]["rs5"],
                "rs10":    rs_lookup[symbol].get("rs10", 0),
                "broker":  str(broker),
                "buy_qty": b,
                "sell_qty": s,
                "net_qty": net,
                "total_qty": total,
                "dominance": abs(net) / total * 100,
            })

    if not results:
        console.print("[red]No broker data for top RS stocks.[/]")
        return

    import pandas as pd
    rdf = pd.DataFrame(results)

    # ── Step 4: Top accumulators (net buyers in RS leaders) ──────────────────
    accum = rdf[rdf["net_qty"] > 0].sort_values("net_qty", ascending=False).head(20)

    def _rs_star(rs5):
        if rs5 >= 5:  return "[bold green]★★★[/]"
        if rs5 >= 2:  return "[green]★★ [/]"
        return "[cyan]★  [/]"

    tbl = Table(
        title="Top Broker Accumulators in High-RS Stocks",
        box=box.SIMPLE_HEAVY, show_lines=False,
        title_style="bold white"
    )
    tbl.add_column("Broker",    style="bold yellow", width=8)
    tbl.add_column("Symbol",    style="bold cyan",   width=10)
    tbl.add_column("Sector",    style="white",       width=22)
    tbl.add_column("RS (5D)",   justify="right",     width=10)
    tbl.add_column("RS",        width=6)
    tbl.add_column("Bought",    justify="right",     width=10)
    tbl.add_column("Sold",      justify="right",     width=10)
    tbl.add_column("Net",       justify="right",     width=10)
    tbl.add_column("Dom%",      justify="right",     width=8)

    for _, r in accum.iterrows():
        rs5 = r["rs5"]
        color = "green" if rs5 >= 0 else "red"
        sign  = "+" if rs5 >= 0 else ""
        tbl.add_row(
            str(r["broker"]),
            r["symbol"],
            r["sector"],
            f"[{color}]{sign}{rs5:.2f}%[/]",
            _rs_star(rs5),
            f"{int(r['buy_qty']):,}",
            f"[red]{int(r['sell_qty']):,}[/]",
            f"[{'green' if r['net_qty']>0 else 'red'}]{int(r['net_qty']):+,}[/]",
            f"{r['dominance']:.0f}%",
        )
    console.print(tbl)

    # ── Step 5: Broker conviction table ──────────────────────────────────────
    # Which brokers are buying MULTIPLE high-RS stocks (highest conviction)
    broker_summary = (
        rdf[rdf["net_qty"] > 0]
        .groupby("broker")
        .agg(
            stocks_accumulated=("symbol", "nunique"),
            total_net_qty=("net_qty", "sum"),
            avg_rs5=("rs5", "mean"),
            symbols=("symbol", lambda x: ", ".join(sorted(x.unique())))
        )
        .reset_index()
        .sort_values(["stocks_accumulated", "total_net_qty"], ascending=False)
        .head(10)
    )

    ctbl = Table(
        title="High-Conviction Brokers (Accumulating Multiple RS Leaders)",
        box=box.SIMPLE_HEAVY, show_lines=False,
        title_style="bold white"
    )
    ctbl.add_column("Broker",    style="bold yellow", width=8)
    ctbl.add_column("# Stocks",  justify="right",     width=9)
    ctbl.add_column("Total Net", justify="right",     width=12)
    ctbl.add_column("Avg RS",    justify="right",     width=10)
    ctbl.add_column("Symbols",   style="cyan",        width=45)

    for _, r in broker_summary.iterrows():
        avg = r["avg_rs5"]
        color = "green" if avg >= 0 else "red"
        ctbl.add_row(
            str(r["broker"]),
            str(int(r["stocks_accumulated"])),
            f"[green]{int(r['total_net_qty']):+,}[/]",
            f"[{color}]{'+' if avg>=0 else ''}{avg:.2f}%[/]",
            r["symbols"][:44],
        )
    console.print(ctbl)

    # ── Step 6: RS stocks with no broker accumulation (warning) ──────────────
    traded_syms = set(rdf["symbol"].unique())
    not_accumulated = [
        s for s in top_symbols
        if s not in traded_syms or rdf[(rdf["symbol"]==s) & (rdf["net_qty"]>0)].empty
    ]
    if not_accumulated:
        console.print(f"  [yellow]⚠ RS leaders with NO net broker buying:[/] {', '.join(sorted(not_accumulated))}")
        console.print("  [dim]Price outperformance without broker confirmation — treat with caution[/]\n")

    # Summary
    if not accum.empty:
        top_broker = broker_summary.iloc[0]
        console.print(
            f"  [bold green]Most active accumulator:[/] Broker {top_broker['broker']} "
            f"— buying {int(top_broker['stocks_accumulated'])} RS leaders "
            f"({top_broker['symbols'][:50]})"
        )



# ── 52-WEEK HIGH/LOW ALERTS ───────────────────────────────────────────────────

def analyze_week52(db_path="nepse_market_data.db"):
    """
    Find stocks near 52-week highs/lows.
    Cross-references with RS leaders for highest conviction setups.
    """
    import sqlite3, pandas as pd
    from rich.table import Table
    from rich import box

    console.rule("[bold cyan]52-Week High / Low Alerts[/]")
    console.print("[dim]Breakout candidates near highs · Recovery plays near lows · Cross-checked with RS[/]\n")

    conn = sqlite3.connect(db_path)

    # ── Pull 52-week range + current price for all equity stocks ─────────────
    df = pd.read_sql_query("""
        SELECT
            sp.symbol,
            c.sector,
            MAX(CASE WHEN sp.date >= date('now','-365 days') THEN sp.high END) as high52,
            MIN(CASE WHEN sp.date >= date('now','-365 days') THEN sp.low  END) as low52,
            MAX(CASE WHEN sp.date >= date('now','-10 days')  THEN sp.close END) as current,
            MAX(sp.date) as last_date
        FROM stock_prices sp
        JOIN companies c ON sp.symbol = c.symbol
        WHERE sp.date >= date('now','-365 days')
        GROUP BY sp.symbol
    """, conn)
    conn.close()

    if df.empty:
        console.print("[red]No price data available.[/]")
        return

    df = df.dropna(subset=["high52","low52","current"])
    df["range52"] = df["high52"] - df["low52"]
    df["pct_from_high"] = (df["current"] - df["high52"]) / df["high52"] * 100
    df["pct_from_low"]  = (df["current"] - df["low52"])  / df["low52"]  * 100
    df["range_pct"]     = df["range52"] / df["low52"] * 100

    # ── Get RS data for cross-reference ──────────────────────────────────────
    rs_data   = _calc_relative_strength()
    rs_lookup = {r["symbol"]: r["rs5"] for r in rs_data} if rs_data else {}

    df["rs5"] = df["symbol"].map(rs_lookup).fillna(0)

    # ── Near 52-week HIGH (within 5%) ────────────────────────────────────────
    near_high = df[df["pct_from_high"] >= -5].sort_values("pct_from_high", ascending=False)

    def _signal(row):
        at_high  = row["pct_from_high"] >= -1
        rs_good  = row["rs5"] > 1
        if at_high and rs_good:   return "[bold green]★★★ BREAKOUT[/]"
        if at_high:               return "[green]★★  At High[/]"
        if rs_good:               return "[cyan]★   RS+Near High[/]"
        return "[dim]—   Near High[/]"

    tbl_high = Table(
        title="Near 52-Week High — Breakout Watch",
        box=box.SIMPLE_HEAVY, show_lines=False,
        title_style="bold white"
    )
    tbl_high.add_column("#",            style="dim",        width=4)
    tbl_high.add_column("Symbol",       style="bold cyan",  width=10)
    tbl_high.add_column("Sector",       style="white",      width=22)
    tbl_high.add_column("Current",      justify="right",    width=10)
    tbl_high.add_column("52W High",     justify="right",    width=10)
    tbl_high.add_column("From High",    justify="right",    width=10)
    tbl_high.add_column("52W Low",      justify="right",    width=10)
    tbl_high.add_column("RS (5D)",      justify="right",    width=10)
    tbl_high.add_column("Signal",       width=20)

    for i, (_, row) in enumerate(near_high.head(20).iterrows(), 1):
        pfh  = row["pct_from_high"]
        rs5  = row["rs5"]
        rc   = "green" if pfh >= -1 else "yellow"
        rsc  = "green" if rs5 > 0 else "red"
        sign = "+" if rs5 >= 0 else ""
        tbl_high.add_row(
            str(i),
            row["symbol"],
            row["sector"],
            f"Rs {row['current']:,.1f}",
            f"Rs {row['high52']:,.1f}",
            f"[{rc}]{pfh:+.1f}%[/]",
            f"Rs {row['low52']:,.1f}",
            f"[{rsc}]{sign}{rs5:.1f}%[/]",
            _signal(row),
        )
    console.print(tbl_high)

    # ── Near 52-week LOW (within 10%) ─────────────────────────────────────────
    near_low = df[df["pct_from_low"] <= 10].sort_values("pct_from_low")

    tbl_low = Table(
        title="Near 52-Week Low — Avoid or Watch for Recovery",
        box=box.SIMPLE_HEAVY, show_lines=False,
        title_style="bold white"
    )
    tbl_low.add_column("#",           style="dim",       width=4)
    tbl_low.add_column("Symbol",      style="bold red",  width=10)
    tbl_low.add_column("Sector",      style="white",     width=22)
    tbl_low.add_column("Current",     justify="right",   width=10)
    tbl_low.add_column("52W Low",     justify="right",   width=10)
    tbl_low.add_column("From Low",    justify="right",   width=10)
    tbl_low.add_column("52W High",    justify="right",   width=10)
    tbl_low.add_column("RS (5D)",     justify="right",   width=10)
    tbl_low.add_column("Warning",     width=20)

    for i, (_, row) in enumerate(near_low.head(15).iterrows(), 1):
        pfl = row["pct_from_low"]
        rs5 = row["rs5"]
        rc  = "red" if pfl <= 3 else "yellow"
        rsc = "green" if rs5 > 0 else "red"
        sign = "+" if rs5 >= 0 else ""
        warning = "[bold red]AT LOW[/]" if pfl <= 1 else "[red]Danger Zone[/]" if pfl <= 5 else "[yellow]Watch[/]"
        tbl_low.add_row(
            str(i),
            row["symbol"],
            row["sector"],
            f"Rs {row['current']:,.1f}",
            f"Rs {row['low52']:,.1f}",
            f"[{rc}]+{pfl:.1f}%[/]",
            f"Rs {row['high52']:,.1f}",
            f"[{rsc}]{sign}{rs5:.1f}%[/]",
            warning,
        )
    console.print(tbl_low)

    # ── Sector summary ────────────────────────────────────────────────────────
    sec = df.groupby("sector").apply(lambda g: pd.Series({
        "near_high": (g["pct_from_high"] >= -5).sum(),
        "near_low":  (g["pct_from_low"]  <= 10).sum(),
        "total":     len(g),
        "avg_from_high": g["pct_from_high"].mean(),
    })).reset_index().sort_values("avg_from_high", ascending=False)

    stbl = Table(
        title="Sector 52-Week Position Summary",
        box=box.SIMPLE_HEAVY, show_lines=False,
        title_style="bold white"
    )
    stbl.add_column("Sector",        style="white",  width=26)
    stbl.add_column("Near High",     justify="right", width=12)
    stbl.add_column("Near Low",      justify="right", width=12)
    stbl.add_column("Avg From High", justify="right", width=14)
    stbl.add_column("Strength",      width=20)

    for _, row in sec.iterrows():
        afh = row["avg_from_high"]
        color = "green" if afh >= -10 else "yellow" if afh >= -25 else "red"
        bar_n = max(0, min(12, int((afh + 50) / 50 * 12)))
        bar = "█" * bar_n + "░" * (12 - bar_n)
        stbl.add_row(
            str(row["sector"]),
            f"[green]{int(row['near_high'])}/{int(row['total'])}[/]",
            f"[red]{int(row['near_low'])}/{int(row['total'])}[/]",
            f"[{color}]{afh:+.1f}%[/]",
            f"[{color}]{bar}[/]",
        )
    console.print(stbl)

    # ── Top conviction: near high + strong RS ────────────────────────────────
    conviction = df[
        (df["pct_from_high"] >= -5) & (df["rs5"] >= 2)
    ].sort_values(["pct_from_high", "rs5"], ascending=[False, False])

    if not conviction.empty:
        console.print("\n  [bold green]★★★ Highest conviction setups (Near 52W High + Strong RS):[/]")
        for _, row in conviction.head(5).iterrows():
            console.print(
                f"    [cyan]{row['symbol']}[/] ({row['sector']}) — "
                f"[green]{row['pct_from_high']:+.1f}%[/] from high, "
                f"RS [green]+{row['rs5']:.1f}%[/]"
            )
    else:
        console.print("\n  [yellow]No stocks currently near 52W high with strong RS — market may be extended or weak[/]")




# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  FUNDAMENTAL ANALYSIS BLOCK  (injected by inject_fundamentals.py)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

_SECTOR_ALIASES = {
    "Hydro Power": "Hydropower",
    "Hotels And Tourism": "Hotel & Tourism",
    "Tradings": "Trading",
    "Manufacturing And Processing": "Manufacturing and Processing",
}

def _norm_sector(s):
    return _SECTOR_ALIASES.get(str(s).strip(), str(s).strip())


# ── --fundamental SYMBOL ──────────────────────────────────────────────────────
def analyze_fundamental(symbol: str):
    import sqlite3
    from rich.table import Table
    from rich import box
    sym = symbol.upper().strip()
    console.rule(f"[bold cyan]Fundamental Snapshot — {sym}[/]")
    conn = sqlite3.connect("nepse_market_data.db")
    cur  = conn.cursor()
    cur.execute(
        "SELECT pe_ratio, pb_ratio, eps, book_value_per_share, roe,"
        " market_cap, shares_outstanding, sector, date"
        " FROM fundamentals WHERE symbol=? ORDER BY date DESC LIMIT 1",
        (sym,)
    )
    row = cur.fetchone()
    cur.execute(
        "SELECT fiscal_year, quarter, eps, net_profit, book_value, announcement_date"
        " FROM quarterly_earnings WHERE symbol=? ORDER BY announcement_date DESC LIMIT 8",
        (sym,)
    )
    q_rows = cur.fetchall()
    conn.close()
    if not row:
        console.print(f"[yellow]No fundamental data found for {sym}.[/]")
        return
    pe, pb, eps, bv, roe, mcap, shares, sector, fdate = row
    sector = _norm_sector(sector or '')
    ltp = high52 = low52 = pub_shares = pub_pct = promo_shares = promo_pct = None
    try:
        from nepse import Nepse
        import warnings; warnings.filterwarnings('ignore')
        n = Nepse(); n.setTLSVerification(False)
        d = n.getCompanyDetails(sym)
        if isinstance(d, dict):
            td = d.get('securityDailyTradeDto', {})
            ltp          = td.get('lastTradedPrice')
            high52       = td.get('fiftyTwoWeekHigh')
            low52        = td.get('fiftyTwoWeekLow')
            pub_shares   = d.get('publicShares')
            pub_pct      = d.get('publicPercentage')
            promo_shares = d.get('promoterShares')
            promo_pct    = d.get('promoterPercentage')
    except Exception:
        pass
    def _fmt(v, suffix='', prefix='', decimals=2):
        if v is None or v == 0: return '[dim]N/A[/]'
        return f'{prefix}{v:,.{decimals}f}{suffix}'
    def _crore(v):
        if v is None or v == 0: return '[dim]N/A[/]'
        return f'Rs {v/1e7:,.2f} Cr'
    t = Table(box=box.ROUNDED, border_style='cyan', show_header=False, padding=(0,1))
    t.add_column('Field',  style='dim',        width=26)
    t.add_column('Value',  style='bold white',  width=22)
    t.add_column('Field2', style='dim',         width=26)
    t.add_column('Value2', style='bold white',  width=22)
    pe_c  = 'green' if pe  and pe  < 20 else 'yellow' if pe  and pe  < 35 else 'red'
    pb_c  = 'green' if pb  and pb  < 1.5 else 'yellow' if pb  and pb  < 3  else 'red'
    roe_c = 'green' if roe and roe > 15 else 'yellow' if roe and roe > 8  else 'red'
    ltp_s = f'Rs {ltp:,.1f}' if ltp else 'N/A'
    t.add_row('Sector',            sector,                   'LTP',        ltp_s)
    t.add_row('Market Cap',        _crore(mcap),             '52W High',   _fmt(high52, prefix='Rs ', decimals=1))
    t.add_row('PE Ratio',          f'[{pe_c}]{_fmt(pe, suffix="x", decimals=1)}[/]',  '52W Low',    _fmt(low52, prefix='Rs ', decimals=1))
    t.add_row('PB Ratio',          f'[{pb_c}]{_fmt(pb, suffix="x", decimals=1)}[/]',  'EPS',        _fmt(eps, prefix='Rs '))
    t.add_row('ROE',               f'[{roe_c}]{_fmt(roe, suffix="%", decimals=1)}[/]','Book Value',  _fmt(bv, prefix='Rs '))
    t.add_row('Public Shares',     f'{pub_shares:,.0f}' if pub_shares else 'N/A',       'Public %',   f'{pub_pct:.1f}%' if pub_pct else 'N/A')
    t.add_row('Promoter Shares',   f'{promo_shares:,.0f}' if promo_shares else 'N/A',   'Promoter %', f'{promo_pct:.1f}%' if promo_pct else 'N/A')
    console.print(t)
    verdicts = []
    if pe and pb:
        if pe < 20 and pb < 1.5: verdicts.append('[bold green]Potentially UNDERVALUED — low PE + low PB[/]')
        elif pe > 40:            verdicts.append('[red]Expensive by PE[/]')
        elif pb > 4:             verdicts.append('[red]Expensive by PB[/]')
    if roe and roe > 15:         verdicts.append('[green]Strong ROE[/]')
    elif roe and roe < 5:        verdicts.append('[yellow]Weak ROE[/]')
    if ltp and bv and bv > 0 and ltp / bv < 1:
        verdicts.append(f'[bold green]Trading BELOW book value (PBV {ltp/bv:.2f}x)[/]')
    if verdicts:
        console.print()
        for v in verdicts: console.print(f'  {v}')
    if q_rows:
        console.print()
        qt = Table(title='Recent Quarterly Earnings', box=box.SIMPLE_HEAVY, border_style='dim', title_style='bold white')
        qt.add_column('FY',         width=10)
        qt.add_column('Q',          width=4,  justify='center')
        qt.add_column('EPS',        width=12, justify='right')
        qt.add_column('Net Profit', width=16, justify='right')
        qt.add_column('Book Val',   width=12, justify='right')
        qt.add_column('Announced',  width=14)
        for fy, q, q_eps, profit, q_bv, ann in q_rows:
            qt.add_row(
                str(fy or ''), str(q or ''),
                f'Rs {q_eps:.2f}' if q_eps else '[dim]N/A[/]',
                _crore(profit),
                f'Rs {q_bv:.2f}' if q_bv else '[dim]N/A[/]',
                str(ann or '')[:10],
            )
        console.print(qt)


# ── --earnings SYMBOL ─────────────────────────────────────────────────────────
def analyze_earnings(symbol: str):
    import sqlite3
    from rich.table import Table
    from rich import box
    sym = symbol.upper().strip()
    console.rule(f"[bold cyan]Earnings History — {sym}[/]")
    conn = sqlite3.connect("nepse_market_data.db")
    cur  = conn.cursor()
    cur.execute(
        "SELECT fiscal_year, quarter, eps, net_profit, revenue, book_value, announcement_date"
        " FROM quarterly_earnings WHERE symbol=? ORDER BY announcement_date DESC LIMIT 20",
        (sym,)
    )
    rows = cur.fetchall()
    conn.close()
    if not rows:
        console.print(f"[yellow]No earnings data for {sym}[/]")
        return
    t = Table(box=box.SIMPLE_HEAVY, border_style='dim', title_style='bold white', title=f'{sym} — Quarterly Earnings')
    t.add_column('FY',          width=10)
    t.add_column('Q',           width=4,  justify='center')
    t.add_column('EPS',         width=12, justify='right')
    t.add_column('Net Profit',  width=16, justify='right')
    t.add_column('Revenue',     width=14, justify='right')
    t.add_column('Book Value',  width=12, justify='right')
    t.add_column('Announced',   width=14)
    profits = []
    for fy, q, eps, profit, revenue, bv, ann in rows:
        if profit: profits.append(profit)
        t.add_row(
            str(fy or ''), str(q or ''),
            f'Rs {eps:.2f}'            if eps     else '[dim]N/A[/]',
            f'Rs {profit/1e7:,.2f}Cr'  if profit  else '[dim]N/A[/]',
            f'Rs {revenue/1e7:,.2f}Cr' if revenue else '[dim]N/A[/]',
            f'Rs {bv:.2f}'             if bv      else '[dim]N/A[/]',
            str(ann or '')[:10],
        )
    console.print(t)
    if len(profits) >= 2:
        trend = profits[0] - profits[1]
        if trend > 0:
            console.print(f'  [green]Profit UP vs last quarter (+Rs {trend/1e7:,.2f} Cr)[/]')
        else:
            console.print(f'  [red]Profit DOWN vs last quarter (Rs {trend/1e7:,.2f} Cr)[/]')



# ── --value  (peer comparison by sector) ─────────────────────────────────────
def analyze_value(filter_sector=None):
    import sqlite3, pandas as pd
    from rich.table import Table
    from rich import box
    from nepse import Nepse
    import warnings; warnings.filterwarnings('ignore')

    console.rule('[bold cyan]Sector Peer Value Screen[/]')
    console.print('[dim]Comparing Float%, Book Value, Market Price within each sector[/]')
    console.print('[dim]Lower PB vs peers = relatively undervalued[/]')
    console.print()

    conn = sqlite3.connect('nepse_market_data.db')

    # Get fundamentals
    df = pd.read_sql_query(
        'SELECT f.symbol, f.sector, f.book_value_per_share, f.pe_ratio, f.pb_ratio, f.roe, f.eps, f.shares_outstanding'
        ' FROM fundamentals f WHERE f.book_value_per_share > 0 ORDER BY f.sector, f.symbol',
        conn
    )

    # Get latest price from stock_prices
    prices = pd.read_sql_query(
        'SELECT sp.symbol, sp.close as ltp, sp.date'
        ' FROM stock_prices sp'
        ' INNER JOIN (SELECT symbol, MAX(date) as maxd FROM stock_prices GROUP BY symbol) mx'
        ' ON sp.symbol=mx.symbol AND sp.date=mx.maxd',
        conn
    )
    conn.close()

    if df.empty:
        console.print('[yellow]No fundamental data found.[/]')
        return

    # Merge price into fundamentals
    df = df.merge(prices[['symbol','ltp','date']], on='symbol', how='left')
    df['sector'] = df['sector'].apply(_norm_sector)

    # Recalculate PB from live price / book value
    df['pb_live'] = df.apply(lambda r: r['ltp']/r['book_value_per_share'] if r['ltp'] and r['book_value_per_share'] and r['book_value_per_share'] > 0 else None, axis=1)

    # Fetch float data from NEPSE API ? only for relevant sector if filtered
    console.print('[dim]Fetching float data from NEPSE API...[/]')
    n = Nepse(); n.setTLSVerification(False)
    float_cache = {}
    if filter_sector:
        fs_pre = filter_sector.lower()
        fetch_df = df[df['sector'].apply(_norm_sector).str.lower().str.contains(fs_pre)]
    else:
        fetch_df = df
    symbols = fetch_df['symbol'].tolist()
    for i, sym in enumerate(symbols):
        try:
            d = n.getCompanyDetails(sym)
            if isinstance(d, dict):
                float_cache[sym] = {
                    'pub_pct':    d.get('publicPercentage') or 0,
                    'pub_shares': d.get('publicShares') or 0,
                    'promo_pct':  d.get('promoterPercentage') or 0,
                    'promo_shares': d.get('promoterShares') or 0,
                }
            else:
                import pandas as pd
                df2 = pd.DataFrame(d) if not isinstance(d, pd.DataFrame) else d
                if 'publicPercentage' in df2.index:
                    float_cache[sym] = {
                        'pub_pct':    df2.loc['publicPercentage'].iloc[0] or 0,
                        'pub_shares': df2.loc['publicShares'].iloc[0] or 0,
                        'promo_pct':  df2.loc['promoterPercentage'].iloc[0] or 0,
                        'promo_shares': df2.loc['promoterShares'].iloc[0] or 0,
                    }
        except Exception:
            float_cache[sym] = {'pub_pct': None, 'pub_shares': None, 'promo_pct': None}
        if (i+1) % 20 == 0:
            console.print(f'[dim]  Fetched {i+1}/{len(symbols)}...[/]')

    # Load unlock status to correct float% for unlocked stocks
    import sqlite3 as _sq3f
    _fc = _sq3f.connect('nepse_market_data.db')
    _unlocked_set = set(r[0] for r in _fc.execute(
        "SELECT symbol FROM unlock_dates WHERE unlock_date < date('now')"
    ).fetchall())
    _lock_date_map = {r[0]: r[1] for r in _fc.execute(
        "SELECT symbol, unlock_date FROM unlock_dates WHERE unlock_date >= date('now')"
    ).fetchall()}
    _fc.close()

    def _fix_pub_pct(row):
        sym = row['symbol']
        sector = str(row.get('sector', '')).lower()
        lock_sectors = ['hydropower', 'hydro power', 'manufacturing', 'hotel', 'investment', 'others']
        in_lock_sector = any(s in sector for s in lock_sectors)
        if sym in _unlocked_set:
            return 100.0  # lock expired, all shares tradeable
        if in_lock_sector and sym not in _lock_date_map:
            return 100.0  # old company, no lock-in ever applied
        return float_cache.get(sym, {}).get('pub_pct')

    def _fix_pub_shares(row):
        sym = row['symbol']
        if sym in _unlocked_set:
            cd = float_cache.get(sym, {})
            pub = cd.get('pub_shares') or 0
            promo = cd.get('promo_shares') or 0
            total = pub + promo
            return total if total > 0 else pub
        return float_cache.get(sym, {}).get('pub_shares')

    df['pub_pct']    = df.apply(_fix_pub_pct, axis=1)
    df['pub_shares'] = df.apply(_fix_pub_shares, axis=1)
    df['promo_pct']  = df['symbol'].map(lambda s: 0.0 if s in _unlocked_set else float_cache.get(s, {}).get('promo_pct'))

    # Filter sector if requested
    sectors = df['sector'].unique()
    if filter_sector:
        fs = filter_sector.lower()
        sectors = [s for s in sectors if fs == s.lower()]
        if not sectors:
            console.print(f'[yellow]Sector "{filter_sector}" not found.[/]')
            console.print(f'[dim]Available: {list(df["sector"].unique())}[/]')
            return

    # ── Pre-load earnings growth map ─────────────────────────────────────────
    import sqlite3 as _sq3
    _eq_conn = _sq3.connect('nepse_market_data.db')
    _eq_rows = _eq_conn.execute(
        "SELECT symbol, net_profit, announcement_date FROM quarterly_earnings "
        "WHERE net_profit IS NOT NULL ORDER BY symbol, announcement_date DESC"
    ).fetchall()
    _eq_conn.close()
    from collections import defaultdict as _dd
    _eq_by_sym = _dd(list)
    for _s, _p, _d in _eq_rows:
        _eq_by_sym[_s].append(_p)
    earnings_map = {s: v[:4] for s, v in _eq_by_sym.items()}  # last 4 quarters

    all_scores = []  # collect for leaderboard

    for sec in sorted(sectors):
        sec_df = df[df['sector'] == sec].copy()
        if len(sec_df) < 2:
            continue

        # Sort will be by score after scoring — keep pb sort as initial
        sec_df = sec_df.sort_values('pb_live', ascending=True, na_position='last')

        # Sector stats
        med_pb  = sec_df['pb_live'].median()
        med_bv  = sec_df['book_value_per_share'].median()
        med_ltp = sec_df['ltp'].median()

        title = f'[bold white]{sec}[/]  [dim]({len(sec_df)} stocks  |  median PB:{med_pb:.1f}x  BV:Rs{med_bv:.0f}  Price:Rs{med_ltp:.0f})[/]' if med_pb else f'[bold white]{sec}[/]'

        t = Table(title=title, box=box.SIMPLE_HEAVY, border_style='cyan',
                  title_style='bold cyan', show_lines=False)
        t.add_column('Symbol',   width=10, style='bold white', no_wrap=True)
        t.add_column('Price',    width=11, justify='right', no_wrap=True)
        t.add_column('Book Val', width=10, justify='right', no_wrap=True)
        t.add_column('PB',       width=8,  justify='right', no_wrap=True)
        t.add_column('Float%',   width=9,  justify='right', no_wrap=True)
        t.add_column('ROE',      width=8,  justify='right', no_wrap=True)
        t.add_column('EG QoQ',   width=9,  justify='right', no_wrap=True)
        t.add_column('#',        width=5,  justify='right')
        t.add_column('Score',    width=8,  justify='right')
        t.add_column('Lock',     width=10, justify='right', no_wrap=True)
        t.add_column('Verdict',  width=28)

        if "score" in sec_df.columns:
            sec_df = sec_df.sort_values(by="score", ascending=False).reset_index(drop=True)
        for _rank_idx, (_row_i, r) in enumerate(sec_df.iterrows(), 1):
            ltp    = r['ltp']
            bv     = r['book_value_per_share']
            pb     = r['pb_live']
            roe    = r['roe']
            fpct   = r['pub_pct']
            ppct   = r['promo_pct']
            fshares= r['pub_shares']

            # ── Earnings growth score (QoQ) ─────────────────────────────
            eq = earnings_map.get(r['symbol'], [])
            if len(eq) >= 2 and eq[0] and eq[1] and eq[1] != 0:
                eq_growth = (eq[0] - eq[1]) / abs(eq[1]) * 100
            else:
                eq_growth = None

            # ── Value Score 0-100 ─────────────────────────────────────────
            score = 0
            # PB component (40 pts): below book=40, cheap vs peers=30, near median=15, expensive=0
            if pb is not None:
                if pb < 1.0:
                    score += 40
                elif med_pb and pb < med_pb * 0.7:
                    score += 32
                elif med_pb and pb < med_pb * 0.9:
                    score += 22
                elif med_pb and pb < med_pb:
                    score += 12
                elif med_pb and pb > med_pb * 1.3:
                    score += 0
                else:
                    score += 6
            # Float component (20 pts): low float = tight supply = price moves fast
            # If promoter lock expired, float% is 100% ? not a negative, treat as neutral (5pts)
            if fpct is not None:
                if r['symbol'] in _unlocked_set:
                    score += 5  # unlocked ? float is real but not a supply squeeze signal
                elif fpct < 20:
                    score += 20
                elif fpct < 30:
                    score += 15
                elif fpct < 40:
                    score += 10
                elif fpct < 55:
                    score += 5
            # ROE component (20 pts)
            if roe is not None:
                if roe > 20:
                    score += 20
                elif roe > 15:
                    score += 15
                elif roe > 10:
                    score += 10
                elif roe > 5:
                    score += 5
            # Earnings growth component (20 pts)
            if eq_growth is not None:
                if eq_growth > 20:
                    score += 20
                elif eq_growth > 10:
                    score += 15
                elif eq_growth > 0:
                    score += 10
                elif eq_growth > -10:
                    score += 4
                # negative growth = 0 pts
            # -- Reserves calc
            shares_out = r.get('shares_outstanding', 0) or 0
            reserve_cr = (bv - 100) * shares_out / 1e7 if bv and bv > 100 and shares_out else 0

            # Reserve bonus (up to 10 extra pts) -- strong reserves = financial cushion
            if reserve_cr > 500:
                score += 10
            elif reserve_cr > 100:
                score += 7
            elif reserve_cr > 50:
                score += 4
            elif reserve_cr > 10:
                score += 2

            all_scores.append({'symbol': r['symbol'], 'sector': sec, 'score': score,
                                'pb': pb, 'ltp': ltp, 'bv': bv, 'roe': roe, 'fpct': fpct, 'fshares': fshares, 'reserve_cr': reserve_cr})

            # ── Colors ────────────────────────────────────────────────────
            if pb is None:   pb_c = 'dim'
            elif pb < 1.0:   pb_c = 'bold green'
            elif med_pb and pb < med_pb * 0.8: pb_c = 'green'
            elif med_pb and pb < med_pb:       pb_c = 'yellow'
            else:            pb_c = 'white'

            if fpct is None:  f_c = 'dim'
            elif fpct < 25:   f_c = 'bold green'
            elif fpct < 40:   f_c = 'yellow'
            else:             f_c = 'white'

            roe_c = 'green' if roe and roe > 15 else 'yellow' if roe and roe > 8 else 'red' if roe and roe < 5 else 'white'

            if score >= 65:   sc_c = 'bold green'
            elif score >= 45: sc_c = 'green'
            elif score >= 30: sc_c = 'yellow'
            else:             sc_c = 'dim'

            # ── Verdict ───────────────────────────────────────────────────
            tags = []
            if pb is not None and pb < 1.0:
                tags.append('[bold green]BELOW BOOK[/]')
            elif med_pb and pb and pb < med_pb * 0.8:
                tags.append('[green]Cheap vs peers[/]')
            if fpct and fpct < 25:
                tags.append('[green]Low float[/]')
            if roe and roe > 15:
                tags.append('[green]Strong ROE[/]')
            if eq_growth is not None and eq_growth > 10:
                tags.append('[green]Profit growing[/]')
            elif eq_growth is not None and eq_growth < -10:
                tags.append('[red]Profit falling[/]')
            if reserve_cr > 100:
                tags.append('[cyan]Strong Reserve[/]')
            if ppct and ppct > 60:
                tags.append('[yellow]Hi-promoter[/]')
            if not tags:
                if med_pb and pb and pb > med_pb * 1.2:
                    tags.append('[dim]Expensive[/]')
                else:
                    tags.append('[dim]Average[/]')
            verdict = ' | '.join(tags)

            fshares_str = f'[{f_c}]{fpct:.1f}%[/]' if fpct is not None else '[dim]N/A[/]'
            ppct_str    = f'[red]{ppct:.1f}%[/]' if ppct and ppct > 60 else f'{ppct:.1f}%' if ppct else '[dim]N/A[/]'
            eg_str = (f'[green]+{eq_growth:.0f}%[/]' if eq_growth and eq_growth > 0
                      else f'[red]{eq_growth:.0f}%[/]' if eq_growth and eq_growth <= 0
                      else '[dim]N/A[/]')

            rank_num = _rank_idx

            # Lock days left
            _sym = r['symbol']
            if _sym in _lock_date_map:
                from datetime import date as _date
                _days = (datetime.strptime(_lock_date_map[_sym], '%Y-%m-%d').date() - _date.today()).days
                lock_cell = f'[yellow]{_days}d[/]'
            elif _sym in _unlocked_set:
                _promo = float_cache.get(_sym, {}).get('promo_pct', 0)
                _promo_str = f' {_promo:.0f}%P' if _promo else ''
                lock_cell = f'[red]Unlkd{_promo_str}[/]'
            else:
                lock_cell = '[dim]-[/]'

            t.add_row(
                r['symbol'],
                f'Rs {ltp:,.0f}'  if ltp else '[dim]N/A[/]',
                f'Rs {bv:,.0f}'   if bv  else '[dim]N/A[/]',
                f'[{pb_c}]{pb:.2f}x[/]' if pb else '[dim]N/A[/]',
                fshares_str,
                f'[{roe_c}]{roe:.1f}%[/]' if roe else '[dim]N/A[/]',
                eg_str,
                str(_rank_idx),
                f'[{sc_c}]{score}[/]',
                lock_cell,
                verdict,
            )
        console.print(t)

        # Top pick in sector by score
        scored = [x for x in all_scores if x['sector'] == sec and x['score'] > 0]
        if scored:
            top = max(scored, key=lambda x: x['score'])
            stars = '★★★' if top['score'] >= 65 else '★★' if top['score'] >= 45 else '★'
            sc_col = 'bold green' if top['score'] >= 65 else 'green' if top['score'] >= 45 else 'yellow'
            pb_str = f'PB {top["pb"]:.2f}x' if top['pb'] else ''
            roe_str = f'ROE {top["roe"]:.1f}%' if top['roe'] else ''
            console.print(f'  [{sc_col}]{stars} Best in {sec}: {top["symbol"]} — Score {top["score"]}/100  {pb_str}  {roe_str}[/]')
        console.print()

    # ── Cross-sector Top 10 leaderboard ──────────────────────────────────────
    if all_scores:
        top10 = sorted(all_scores, key=lambda x: x['score'], reverse=True)[:20]
        from rich.table import Table as _T
        from rich import box as _box
        lb = _T(title='[bold yellow]★ Top 10 Value Picks — All Sectors[/]',
                box=_box.SIMPLE_HEAVY, border_style='yellow', title_style='bold yellow')
        lb.add_column('#',      width=4,  justify='right')
        lb.add_column('Symbol', width=10, style='bold white', no_wrap=True)
        lb.add_column('Sector', width=20, no_wrap=True)
        lb.add_column('Score',  width=7,  justify='right')
        lb.add_column('Price',  width=10, justify='right', no_wrap=True)
        lb.add_column('BV',     width=9,  justify='right', no_wrap=True)
        lb.add_column('PB',     width=7,  justify='right', no_wrap=True)
        lb.add_column('Float%', width=8,  justify='right', no_wrap=True)
        lb.add_column('Shares', width=11, justify='right', no_wrap=True)
        lb.add_column('Resrv',  width=12, justify='right', no_wrap=True)
        lb.add_column('ROE',    width=7,  justify='right', no_wrap=True)
        lb.add_column('Lock',   width=8,  justify='right', no_wrap=True)
        for rank, x in enumerate(top10, 1):
            sc = x['score']
            sc_c = 'bold green' if sc >= 65 else 'green' if sc >= 45 else 'yellow'
            pb_v = x['pb']; ltp_v = x['ltp']; bv_v = x['bv']
            _sym2 = x['symbol']
            if _sym2 in _lock_date_map:
                from datetime import date as _date2
                _days2 = (datetime.strptime(_lock_date_map[_sym2], '%Y-%m-%d').date() - _date2.today()).days
                lb_lock = f'[yellow]{_days2}d[/]'
            elif _sym2 in _unlocked_set:
                _lb_promo = float_cache.get(_sym2, {}).get('promo_pct', 0)
                _lb_promo_str = f' {_lb_promo:.0f}%P' if _lb_promo else ''
                lb_lock = f'[red]Unlkd{_lb_promo_str}[/]'
            else:
                lb_lock = '[dim]-[/]'
            lb.add_row(
                str(rank),
                x['symbol'],
                x['sector'],
                f'[{sc_c}]{sc}[/]',
                f'Rs {ltp_v:,.0f}' if ltp_v else 'N/A',
                f'Rs {bv_v:,.0f}' if bv_v else 'N/A',
                f'[{sc_c}]{pb_v:.2f}x[/]' if pb_v else 'N/A',
                f'{x["fpct"]:.1f}%' if x['fpct'] is not None else 'N/A',
                f'{x["fshares"]/1e5:,.1f}L' if x.get('fshares') else 'N/A',
                f'Rs {x["reserve_cr"]:,.0f}Cr' if x.get('reserve_cr') and x['reserve_cr'] > 0 else 'N/A',
                f'{x["roe"]:.1f}%' if x['roe'] is not None else 'N/A',
                lb_lock,
            )
        console.print(lb)
        console.print()

    console.print('[dim]Score: PB 40pts + Float 20pts + ROE 20pts + Earnings Growth 20pts. Green â‰¥65, Yellow â‰¥45.[/]') # VALUE_SCORE_PATCHED

# ── --float SYMBOL ────────────────────────────────────────────────────────────
def analyze_float(symbol: str):
    from nepse import Nepse
    import warnings; warnings.filterwarnings('ignore')
    from rich.table import Table
    from rich import box
    sym = symbol.upper().strip()
    console.rule(f"[bold cyan]Float & Ownership — {sym}[/]")
    try:
        n = Nepse(); n.setTLSVerification(False)
        d = n.getCompanyDetails(sym)
    except Exception as e:
        console.print(f'[red]API error: {e}[/]')
        return
    if not isinstance(d, dict):
        console.print('[yellow]No data returned.[/]')
        return
    td           = d.get('securityDailyTradeDto', {})
    ltp          = td.get('lastTradedPrice', 0)
    high52       = td.get('fiftyTwoWeekHigh', 0)
    low52        = td.get('fiftyTwoWeekLow', 0)
    pub_shares   = d.get('publicShares', 0)
    pub_pct      = d.get('publicPercentage', 0)
    promo_shares = d.get('promoterShares', 0)
    promo_pct    = d.get('promoterPercentage', 0)
    mcap         = d.get('marketCapitalization', 0)
    float_mcap   = pub_shares * ltp if pub_shares and ltp else 0
    t = Table(box=box.ROUNDED, border_style='cyan', show_header=False, padding=(0,1))
    t.add_column('Field',  style='dim',        width=28)
    t.add_column('Value',  style='bold white',  width=24)
    t.add_column('Field2', style='dim',         width=28)
    t.add_column('Value2', style='bold white',  width=24)
    t.add_row('Last Traded Price',  f'Rs {ltp:,.1f}' if ltp else 'N/A',             '52W High', f'Rs {high52:,.1f}' if high52 else 'N/A')
    t.add_row('Public (Float)',     f'[green]{pub_shares:,.0f}[/]' if pub_shares else 'N/A',   'Float %',    f'[green]{pub_pct:.2f}%[/]' if pub_pct else 'N/A')
    t.add_row('Promoter (Locked)',  f'[red]{promo_shares:,.0f}[/]' if promo_shares else 'N/A', 'Promoter %', f'[red]{promo_pct:.2f}%[/]' if promo_pct else 'N/A')
    t.add_row('Float Market Cap',   f'Rs {float_mcap/1e7:,.2f} Cr' if float_mcap else 'N/A',  'Total MCap', f'Rs {mcap/1e7:,.2f} Cr' if mcap else 'N/A')
    t.add_row('52W Low',            f'Rs {low52:,.1f}' if low52 else 'N/A',                   '',           '')
    console.print(t)
    console.print()
    if pub_pct and pub_pct < 25:
        console.print('  [bold green]Low float (<25%) — small supply, price can move fast[/]')
    elif pub_pct and pub_pct < 40:
        console.print('  [yellow]Moderate float (25-40%) — normal liquidity[/]')
    else:
        console.print('  [dim]High float (>40%) — high supply, needs strong demand[/]')
    if promo_pct and promo_pct > 60:
        console.print('  [yellow]Promoter >60% — watch for unlock events[/]')


# ── --unlock ──────────────────────────────────────────────────────────────────
def _unlock_db():
    import sqlite3
    conn = sqlite3.connect("nepse_market_data.db")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS unlock_dates ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "symbol TEXT NOT NULL, unlock_date TEXT NOT NULL,"
        "note TEXT, added_at TEXT DEFAULT (date('now')))"
    )
    conn.commit()
    return conn

def analyze_unlock(args_unlock):
    import sqlite3
    from datetime import date, datetime
    from rich.table import Table
    from rich import box
    if not args_unlock:
        console.print('[yellow]Usage: --unlock list | --unlock upcoming | --unlock add SYMBOL DATE NOTE[/]')
        return
    cmd = args_unlock[0].lower()
    if cmd == 'add':
        if len(args_unlock) < 3:
            console.print('[red]Usage: --unlock add SYMBOL DATE note[/]')
            return
        sym   = args_unlock[1].upper()
        udate = args_unlock[2]
        note  = ' '.join(args_unlock[3:]) if len(args_unlock) > 3 else ''
        conn  = _unlock_db()
        conn.execute('INSERT INTO unlock_dates (symbol, unlock_date, note) VALUES (?,?,?)', (sym, udate, note))
        conn.commit(); conn.close()
        console.print(f'[green]Added unlock for {sym} on {udate}[/]')
        return
    if cmd == 'delete':
        if len(args_unlock) < 2:
            console.print('[red]Usage: --unlock delete ID[/]')
            return
        conn = _unlock_db()
        conn.execute('DELETE FROM unlock_dates WHERE id=?', (args_unlock[1],))
        conn.commit(); conn.close()
        console.print(f'[green]Deleted entry {args_unlock[1]}[/]')
        return
    conn  = _unlock_db()
    today = str(date.today())
    cur = conn.execute('SELECT id,symbol,unlock_date,note FROM unlock_dates ORDER BY unlock_date ASC')
    rows = cur.fetchall(); conn.close()
    console.rule('[bold cyan]Unlock / Lock-in Expiry Dates[/]')
    if not rows:
        console.print('[dim]No unlock dates recorded yet.[/]')
        console.print('[dim]Add: python nepse_scanner.py --unlock add NABIL 2026-08-15 Promoter_2M[/]')
        return

    upcoming = [(r,s,u,n) for r,s,u,n in rows if u >= today]
    expired  = [(r,s,u,n) for r,s,u,n in rows if u < today]

    if upcoming:
        t = Table(box=box.SIMPLE_HEAVY, border_style='yellow',
                  title=f'Upcoming Unlocks ({len(upcoming)})', title_style='bold yellow')
        t.add_column('ID',     width=5,  style='dim')
        t.add_column('Symbol', width=10, style='bold white')
        t.add_column('Date',   width=14)
        t.add_column('Days',   width=10, justify='right')
        t.add_column('Note',   width=40)
        for rid, sym, udate, note in upcoming:
            try:
                delta = (datetime.strptime(udate, '%Y-%m-%d').date() - date.today()).days
                day_s = f'[bold red]{delta}d[/]' if delta <= 7 else f'[yellow]{delta}d[/]' if delta <= 30 else f'[green]{delta}d[/]'
            except:
                day_s = '[dim]?[/]'
            t.add_row(str(rid), sym, udate, day_s, note or '')
        console.print(t)

    if expired:
        t2 = Table(box=box.SIMPLE_HEAVY, border_style='red',
                   title=f'Already Unlocked ({len(expired)}) ? Float may be higher than NEPSE shows',
                   title_style='bold red')
        t2.add_column('ID',     width=5,  style='dim')
        t2.add_column('Symbol', width=10, style='bold white')
        t2.add_column('Unlock Date', width=14)
        t2.add_column('Unlocked',    width=12, justify='right')
        t2.add_column('Note',        width=40)
        for rid, sym, udate, note in expired:
            try:
                delta = (date.today() - datetime.strptime(udate, '%Y-%m-%d').date()).days
                day_s = f'[dim]{delta}d ago[/]'
            except:
                day_s = '[dim]?[/]'
            t2.add_row(str(rid), sym, udate, day_s, note or '')
        console.print(t2)

    console.print('[dim]Delete: python nepse_scanner.py --unlock delete ID[/]')


# ── RELATIVE STRENGTH ─────────────────────────────────────────────────────────


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# WHY ENGINE — Broker Activity Logger + Story Generator + Why Block
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def _init_broker_activity_table(db_path="nepse_market_data.db"):
    """Create broker_activity table if it does not exist."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS broker_activity (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol       TEXT    NOT NULL,
            date         TEXT    NOT NULL,
            broker_id    TEXT    NOT NULL,
            broker_name  TEXT,
            buy_qty      REAL    DEFAULT 0,
            sell_qty     REAL    DEFAULT 0,
            net_qty      REAL    DEFAULT 0,
            buy_val      REAL    DEFAULT 0,
            sell_val     REAL    DEFAULT 0,
            net_val      REAL    DEFAULT 0,
            UNIQUE(symbol, date, broker_id)
        )
    """)
    conn.commit()
    conn.close()


def get_broker_story(symbol, fs_df, db_path="nepse_market_data.db"):
    import sqlite3
    empty = dict(
        dominant_broker_id=None, dominant_broker_name=None, dominant_pct=0,
        dominant_action="neutral", dominant_net_val=0, concentration="low",
        total_brokers=0, buy_brokers=0, sell_brokers=0,
        history_days=0, history_summary="", history_action="unknown",
        five_day_verdict="", ten_day_verdict="", twenty_day_verdict="",
    )
    try:
        if fs_df is None or fs_df.empty:
            return empty
        sym_fs = fs_df[fs_df["symbol"] == symbol] if "symbol" in fs_df.columns else fs_df
        if sym_fs.empty:
            return empty
        total_vol = sym_fs["quantity"].sum()
        if total_vol == 0:
            return empty
        buy_grp = sym_fs.groupby("buyer_broker").agg(
            bq=("quantity", "sum"), bv=("amount", "sum"), bname=("buyerBrokerName", "first")
        )
        sell_grp = sym_fs.groupby("seller_broker").agg(
            sq=("quantity", "sum"), sv=("amount", "sum"), sname=("sellerBrokerName", "first")
        )
        all_ids = set(buy_grp.index) | set(sell_grp.index)
        rows = []
        for bid in all_ids:
            bq = int(buy_grp.loc[bid, "bq"]) if bid in buy_grp.index else 0
            bv = float(buy_grp.loc[bid, "bv"]) if bid in buy_grp.index else 0.0
            sq = int(sell_grp.loc[bid, "sq"]) if bid in sell_grp.index else 0
            sv = float(sell_grp.loc[bid, "sv"]) if bid in sell_grp.index else 0.0
            name = str(buy_grp.loc[bid, "bname"] if bid in buy_grp.index else sell_grp.loc[bid, "sname"])
            vol = bq + sq
            rows.append(dict(bid=str(bid), name=name, bq=bq, bv=bv, sq=sq, sv=sv,
                net_val=bv-sv, net_qty=bq-sq, vol=vol))
        if not rows:
            return empty
        dom = max(rows, key=lambda r: r["vol"])
        dom_pct = dom["vol"] / (total_vol * 2) * 100
        conc = "high" if dom_pct >= 30 else ("medium" if dom_pct >= 15 else "low")
        action = "buying" if dom["net_val"] > 0 else ("selling" if dom["net_val"] < 0 else "neutral")
        buy_brokers = sum(1 for r in rows if r["net_val"] > 0)
        sell_brokers = sum(1 for r in rows if r["net_val"] < 0)
        history_days = 0
        history_summary = ""
        history_action = "unknown"
        five_day_verdict = ""
        ten_day_verdict = ""
        twenty_day_verdict = ""
        try:
            conn = sqlite3.connect(db_path)
            hist = conn.execute(
                "SELECT date, net_val FROM broker_activity WHERE symbol=? AND broker_id=?"
                " ORDER BY date DESC LIMIT 20",
                (symbol, dom["bid"])
            ).fetchall()
            conn.close()
            if len(hist) >= 2:
                history_days = len(hist)
                def _ws(days_slice):
                    if not days_slice: return None
                    n = len(days_slice)
                    b = sum(1 for _, nv in days_slice if nv > 0)
                    s = sum(1 for _, nv in days_slice if nv < 0)
                    net = sum(nv for _, nv in days_slice)
                    amt = ("Rs " + str(round(abs(net)/1e6, 1)) + "M") if abs(net) >= 1e6 else ("Rs " + str(round(abs(net)/1e3)) + "K")
                    if b > s: return str(b) + "/" + str(n) + "d bought (" + amt + " in)"
                    elif s > b: return str(s) + "/" + str(n) + "d sold (" + amt + " out)"
                    else: return str(n) + "d mixed"
                w5  = _ws(hist[:5])  if len(hist) >= 5  else None
                w10 = _ws(hist[:10]) if len(hist) >= 10 else None
                w20 = _ws(hist[:20]) if len(hist) >= 20 else None
                parts = []
                if w5:  parts.append("5d: " + w5)
                if w10: parts.append("10d: " + w10)
                if w20: parts.append("20d: " + w20)
                history_summary = "  |  ".join(parts) if parts else ""
                all_b = sum(1 for _, nv in hist if nv > 0)
                all_s = sum(1 for _, nv in hist if nv < 0)
                history_action = "accumulating" if all_b > all_s else ("distributing" if all_s > all_b else "mixed")
                # 5d verdict
                if len(hist) >= 5:
                    h5 = hist[:5]
                    b5 = sum(1 for _, nv in h5 if nv > 0)
                    s5 = sum(1 for _, nv in h5 if nv < 0)
                    n5 = sum(nv for _, nv in h5)
                    a5 = ("Rs " + str(round(abs(n5)/1e6, 1)) + "M") if abs(n5) >= 1e6 else ("Rs " + str(round(abs(n5)/1e3)) + "K")
                    if b5 >= 4:
                        five_day_verdict = "EARLY BUY SIGNAL — broker bought " + str(b5) + "/5 days (" + a5 + " in) — watch closely"
                    elif b5 == 3:
                        five_day_verdict = "MILD INTEREST — broker bought 3/5 days (" + a5 + " in) — not confirmed yet"
                    elif s5 >= 4:
                        five_day_verdict = "EARLY SELL SIGNAL — broker sold " + str(s5) + "/5 days (" + a5 + " out) — caution"
                    elif s5 == 3:
                        five_day_verdict = "MILD EXIT — broker sold 3/5 days (" + a5 + " out) — monitor"
                    else:
                        five_day_verdict = "NO SIGNAL — broker direction unclear over 5 days"
                # 10d verdict
                if len(hist) >= 10:
                    h10 = hist[:10]
                    b10 = sum(1 for _, nv in h10 if nv > 0)
                    s10 = sum(1 for _, nv in h10 if nv < 0)
                    n10 = sum(nv for _, nv in h10)
                    a10 = ("Rs " + str(round(abs(n10)/1e6, 1)) + "M") if abs(n10) >= 1e6 else ("Rs " + str(round(abs(n10)/1e3)) + "K")
                    if b10 >= 8:
                        ten_day_verdict = "STRONG BUY — broker bought " + str(b10) + "/10 days (" + a10 + " accumulated) — high conviction"
                    elif b10 >= 6:
                        ten_day_verdict = "MODERATE BUY — broker bought " + str(b10) + "/10 days (" + a10 + " in) — building position"
                    elif s10 >= 8:
                        ten_day_verdict = "STRONG AVOID — broker sold " + str(s10) + "/10 days (" + a10 + " distributed) — consistent exit"
                    elif s10 >= 6:
                        ten_day_verdict = "CAUTION — broker sold " + str(s10) + "/10 days (" + a10 + " out) — distribution ongoing"
                    else:
                        ten_day_verdict = "NO CONVICTION — broker mixed over 10 days (bought " + str(b10) + ", sold " + str(s10) + ")"
                # 20d verdict
                if len(hist) >= 20:
                    h20 = hist[:20]
                    b20 = sum(1 for _, nv in h20 if nv > 0)
                    s20 = sum(1 for _, nv in h20 if nv < 0)
                    n20 = sum(nv for _, nv in h20)
                    a20 = ("Rs " + str(round(abs(n20)/1e6, 1)) + "M") if abs(n20) >= 1e6 else ("Rs " + str(round(abs(n20)/1e3)) + "K")
                    if b20 >= 16:
                        twenty_day_verdict = "INSTITUTIONAL ACCUMULATION — broker bought " + str(b20) + "/20 days (" + a20 + " in) — very high conviction"
                    elif b20 >= 12:
                        twenty_day_verdict = "STRONG ACCUMULATION — broker bought " + str(b20) + "/20 days (" + a20 + " in) — sustained buying"
                    elif b20 >= 8:
                        twenty_day_verdict = "MODERATE ACCUMULATION — broker bought " + str(b20) + "/20 days (" + a20 + " in) — mild interest"
                    elif s20 >= 16:
                        twenty_day_verdict = "INSTITUTIONAL DISTRIBUTION — broker sold " + str(s20) + "/20 days (" + a20 + " out) — major exit"
                    elif s20 >= 12:
                        twenty_day_verdict = "STRONG DISTRIBUTION — broker sold " + str(s20) + "/20 days (" + a20 + " out) — sustained selling"
                    elif s20 >= 8:
                        twenty_day_verdict = "MODERATE DISTRIBUTION — broker sold " + str(s20) + "/20 days (" + a20 + " out) — mild exit"
                    else:
                        twenty_day_verdict = "NO TREND — no clear direction over 20 days (bought " + str(b20) + ", sold " + str(s20) + ")"
        except Exception:
            pass
        return dict(
            dominant_broker_id=dom["bid"],
            dominant_broker_name=dom["name"],
            dominant_pct=dom_pct,
            dominant_action=action,
            dominant_net_val=dom["net_val"],
            concentration=conc,
            total_brokers=len(rows),
            buy_brokers=buy_brokers,
            sell_brokers=sell_brokers,
            history_days=history_days,
            history_summary=history_summary,
            history_action=history_action,
            five_day_verdict=five_day_verdict,
            ten_day_verdict=ten_day_verdict,
            twenty_day_verdict=twenty_day_verdict,
        )
    except Exception:
        return empty


def _fmt_rs_val(val):
    """Format Rs value compactly."""
    if val is None:
        return ''
    a = abs(val)
    if a >= 1_000_000:
        return f"Rs {val/1_000_000:.1f}M"
    if a >= 1_000:
        return f"Rs {val/1_000:.0f}K"
    return f"Rs {val:.0f}"


def analyze_why(live_df, full_fs, rs_data=None, db_path="nepse_market_data.db"):
    """
    Print Why blocks for top bullish + bearish + neutral stocks.
    Add --why flag to any scan to trigger this.
    """
    from rich.rule import Rule

    console.print()
    console.rule("[bold yellow]Why These Stocks Were Flagged[/bold yellow]", style="yellow")
    console.print("[dim]Broker behavior + RS vs sector + 52W position + unlock dates[/dim]\n")

    # RS data
    if rs_data is None:
        rs_data = _calc_relative_strength(db_path)
    if not rs_data:
        console.print("[red]No RS data available.[/red]")
        return

    rdf = pd.DataFrame(rs_data)

    # Select stocks to explain
    bullish = rdf[rdf['rs5'] > 2].head(3).to_dict('records')
    bearish = rdf[rdf['rs5'] < -2].sort_values('rs5' if 'rs5' in rdf.columns else 'rs_score').head(3).to_dict('records')

    # Neutral = high turnover stocks with -2 < rs5 < 2
    neutral_syms = []
    if live_df is not None and not live_df.empty:
        try:
            vcols = [c for c in live_df.columns if any(x in c.lower() for x in ['turnover','volume','amount'])]
            if vcols:
                top_syms = live_df.nlargest(20, vcols[0])['symbol'].tolist()
                neutral_syms = [r for r in rs_data if r['symbol'] in top_syms and -2 <= r.get('rs5', 0) <= 2][:2]
        except Exception:
            pass

    # Unlock map
    unlock_map = {}
    try:
        import sqlite3
        _init_broker_activity_table(db_path)
        conn = sqlite3.connect(db_path)
        udf = pd.read_sql("""
            SELECT symbol, MIN(unlock_date) as next_unlock
            FROM unlock_dates WHERE unlock_date >= date('now')
            GROUP BY symbol
        """, conn)
        conn.close()
        unlock_map = dict(zip(udf['symbol'], udf['next_unlock']))
    except Exception:
        pass

    # ── WHY BLOCK ─────────────────────────────────────────────────────────────
    def _print_why(stock, tag):
        symbol = stock['symbol']
        sector = stock.get('sector', '')
        rs5    = stock.get('rs5', 0) or 0
        sec5   = stock.get('sec5', 0) or 0
        ret5   = stock.get('ret5', 0) or 0

        rs_rank  = sorted(rs_data, key=lambda x: x.get('rs_score', 0), reverse=True)
        rank     = next((i+1 for i, r in enumerate(rs_rank) if r['symbol'] == symbol), '?')
        total    = len(rs_rank)

        bstory   = get_broker_story(symbol, full_fs, db_path)
        unlock   = unlock_map.get(symbol)

        # 52W note from live_df
        w52_note = ''
        if live_df is not None and not live_df.empty:
            try:
                row = live_df[live_df['symbol'] == symbol]
                if not row.empty:
                    r    = row.iloc[0]
                    hcol = next((c for c in live_df.columns if '52' in c and 'high' in c.lower()), None)
                    lcol = next((c for c in live_df.columns if '52' in c and 'low'  in c.lower()), None)
                    pcol = next((c for c in live_df.columns if c.lower() in ('ltp','last_traded_price','close','lastTradedPrice')), None)
                    if hcol and pcol:
                        ltp  = float(r[pcol])
                        high = float(r[hcol])
                        pct_from_high = (ltp - high) / high * 100
                        if pct_from_high >= -5:
                            w52_note = f"Only {abs(pct_from_high):.1f}% from 52W high — breakout zone"
                        elif lcol:
                            low = float(r[lcol])
                            if low > 0:
                                pct_from_low = (ltp - low) / low * 100
                                if pct_from_low <= 5:
                                    w52_note = f"Only {pct_from_low:.1f}% above 52W low — danger zone"
                        if not w52_note:
                            w52_note = f"{abs(pct_from_high):.1f}% below 52W high"
            except Exception:
                pass

        # ── Build bullets ──────────────────────────────────────────────────
        # Bullet 1 — Broker
        bid   = bstory['dominant_broker_id']
        bname = bstory['dominant_broker_name'] or (f"Broker {bid}" if bid else None)
        if bid:
            conc  = {'high': f"dominant — {bstory['dominant_pct']:.0f}% of today's volume",
                     'medium': f"active — {bstory['dominant_pct']:.0f}% of today's volume",
                     'low':  f"present — {bstory['dominant_pct']:.0f}% of today's volume"}.get(bstory['concentration'], '')
            act   = {'buying': 'net BUYING', 'selling': 'net SELLING', 'neutral': 'market making'}.get(bstory['dominant_action'], '')
            nval  = _fmt_rs_val(abs(bstory['dominant_net_val'])) if bstory['dominant_net_val'] else ''
            nval_str = f" ({nval})" if nval else ""

            hist_note = ''
            if bstory['history_days'] > 1:
                hist_note = f"  [{bstory['history_summary']}]"
                if bstory['history_action'] == 'accumulating' and bstory['dominant_action'] == 'selling':
                    hist_note += "  FIRST SELL after accumulation (exit alert)"
                elif bstory['history_action'] == 'distributing' and bstory['dominant_action'] == 'buying':
                    hist_note += "  FIRST BUY after distribution (reversal alert)"
            if bstory.get('five_day_verdict'):
                hist_note += "\n      ðŸ“Š 5D:  " + bstory['five_day_verdict']
            if bstory.get('ten_day_verdict'):
                hist_note += "\n      â­ 10D: " + bstory['ten_day_verdict']
            if bstory.get('twenty_day_verdict'):
                hist_note += "\n      ðŸ† 20D: " + bstory['twenty_day_verdict']

            broad = ''
            if bstory['total_brokers'] > 0:
                bp = bstory['buy_brokers'] / bstory['total_brokers'] * 100
                if bp > 65:
                    broad = f"  |  {bstory['buy_brokers']}/{bstory['total_brokers']} brokers net buying (broad accumulation)"
                elif bp < 35:
                    broad = f"  |  {bstory['sell_brokers']}/{bstory['total_brokers']} brokers net selling (broad distribution)"

            b1 = f"Broker {bid} ({bname}) — {conc}, {act}{nval_str}{hist_note}{broad}"
        else:
            b1 = "Floorsheet not available (run with a scan that fetches floorsheet)"

        # Bullet 2 — Sector context
        if sec5 != 0:
            if rs5 > 0 and sec5 > 0:
                b2 = f"Sector ({sector}) also rising +{sec5:.1f}% 5D — stock outperforming by +{rs5:.1f}% (momentum confirmed)"
            elif rs5 < 0 and sec5 > 0:
                if rs5 >= -2:
                    b2 = f"Sector ({sector}) up +{sec5:.1f}% 5D — stock inline with sector ({rs5:+.1f}% RS)"
                else:
                    b2 = f"Sector ({sector}) up +{sec5:.1f}% but stock {ret5:+.1f}% — STOCK-SPECIFIC weakness, not sector"
            elif rs5 < 0 and sec5 < 0:
                b2 = f"Sector ({sector}) also weak {sec5:.1f}% — broad sector selling, not just this stock"
            else:
                b2 = f"Sector ({sector}) {sec5:+.1f}% / Stock {ret5:+.1f}% — RS {rs5:+.1f}%"
        else:
            b2 = f"Sector ({sector}) data unavailable for comparison"

        # Bullet 3 — RS rank
        if rs5 > 5:
            b3 = f"RS +{rs5:.2f}% vs sector — Rank #{rank}/{total} (top performer in market)"
        elif rs5 > 2:
            b3 = f"RS +{rs5:.2f}% vs sector — Rank #{rank}/{total} (outperforming sector)"
        elif rs5 >= -2:
            b3 = f"RS {rs5:+.2f}% vs sector — Rank #{rank}/{total} (inline with sector)"
        elif rs5 > -5:
            b3 = f"RS {rs5:.2f}% vs sector — Rank #{rank}/{total} (underperforming sector)"
        else:
            b3 = f"RS {rs5:.2f}% vs sector — Rank #{rank}/{total} (worst performers in market)"

        # Bullet 4 — 52W + unlock
        parts = []
        if w52_note:
            parts.append(w52_note)
        if unlock:
            from datetime import datetime, date
            try:
                unlock_dt = datetime.strptime(unlock, '%Y-%m-%d').date()
                days_away = (unlock_dt - date.today()).days
                if days_away <= 180:
                    parts.append(f"Lock-in expiry: {unlock} ({days_away} days away) — supply overhang risk")
                else:
                    parts.append(f"No near-term lock-in expiry (next: {unlock})")
            except Exception:
                parts.append(f"Lock-in expiry: {unlock} — supply overhang risk")
        else:
            parts.append("No lock-in expiry found")
        b4 = "  |  ".join(parts)

        # Verdict
        ha = bstory.get('history_action')
        da = bstory.get('dominant_action')
        if tag == 'bull':
            # Conflict: strong RS but dominant broker selling
            if da == 'selling' and bstory.get('concentration') in ('high', 'medium') and rs5 > 0:
                verdict = ('Strong RS but dominant broker net SELLING — '
                           'possible distribution at highs. '
                           'Wait for broker to stop selling before entry.')
            elif ha == 'accumulating' and rs5 > 5:
                verdict = "Sustained institutional accumulation + top RS. High conviction — buy on dips."
            elif da == 'buying' and bstory['concentration'] == 'high' and rs5 > 3:
                verdict = "Whale accumulating aggressively + strong RS. Watch for 52W high breakout."
            elif rs5 > 5:
                verdict = "Strongest momentum in market. Sector tailwind confirmed. Buy pullbacks."
            else:
                verdict = "Outperforming sector. Positive momentum — monitor for continuation."

        elif tag == 'bear':
            if ha == 'distributing' and rs5 < -5:
                verdict = "Sustained distribution + worst RS. No floor visible. Avoid entirely."
            elif da == 'selling' and sec5 > 0:
                buy_pct = (bstory.get('buy_brokers', 0) / bstory.get('total_brokers', 1)) * 100
                if buy_pct > 60:
                    verdict = ('One whale selling while 60%+ brokers buying — '
                               'possible shakeout before move up. Watch closely.')
                else:
                    verdict = 'Promoter/whale exit while sector rises. Stock-specific. Avoid until selling stops.'
            elif unlock:
                verdict = f"Lock-in expiry {unlock} creating supply. Wait for expiry to pass before entry."
            elif sec5 < 0:
                verdict = "Sector-wide weakness — not stock-specific. Wait for sector to stabilize first."
            else:
                verdict = "Underperforming sector. No catalyst visible. Avoid or cut losses."

        else:  # neutral
            if da == 'buying' and rs5 < 0:
                verdict = "Broker accumulating but RS still negative — early/risky entry. Wait for RS to turn positive."
            elif da == 'selling' and rs5 > 0:
                verdict = "RS positive but broker distributing — topping risk. Tighten stops if holding."
            elif unlock:
                verdict = f"Mixed signals + unlock on {unlock}. Wait for post-expiry clarity."
            else:
                verdict = "No strong signal. High turnover stock — monitor for breakout direction."

        # Print
        colors = {'bull': 'green', 'bear': 'red', 'neutral': 'yellow'}
        labels = {'bull': 'BULLISH', 'bear': 'BEARISH', 'neutral': 'NEUTRAL'}
        c = colors.get(tag, 'white')
        l = labels.get(tag, '')

        console.print(f"  [bold {c}]📌 {symbol}[/bold {c}] [{c}]— {l}[/{c}]")
        console.print(f"    [cyan]•[/cyan] {b1}")
        console.print(f"    [cyan]•[/cyan] {b2}")
        console.print(f"    [cyan]•[/cyan] {b3}")
        console.print(f"    [cyan]•[/cyan] {b4}")
        console.print(f"    [bold white]→ Verdict:[/bold white] {verdict}")
        # Top 4 broker holders from history
        holders = get_top_broker_holders(symbol, db_path, top_n=4)
        if holders:
            console.print(f"    \u2022 Top holders (cumulative net position):", style="dim")
            for h in holders:
                net = h['total_net']
                direction = 'NET LONG' if net >= 0 else 'NET SHORT'
                amt = ('Rs ' + str(round(abs(net)/1e6, 1)) + 'M') if abs(net) >= 1e6 else ('Rs ' + str(round(abs(net)/1e3)) + 'K')
                col = 'green' if net >= 0 else 'red'
                console.print(f"      Broker {h['broker_id']} ({h['broker_name']}) [{h['days_active']}d] — [{col}]{direction} {amt}[/{col}]", style="dim")
        console.print()

    # Print all sections
    if bullish:
        console.print("[bold green]── BULLISH — Accumulation Signals ──────────────────────────────[/bold green]")
        for s in bullish:
            _print_why(s, 'bull')

    if bearish:
        console.print("[bold red]── BEARISH — Distribution Signals ──────────────────────────────[/bold red]")
        for s in bearish:
            _print_why(s, 'bear')

    if neutral_syms:
        console.print("[bold yellow]── NEUTRAL — Watch for Direction ────────────────────────────────[/bold yellow]")
        for s in neutral_syms:
            _print_why(s, 'neutral')

    console.print(Rule(style="dim"))

def _ensure_broker_activity_table(db_path='nepse_market_data.db'):
    import sqlite3
    conn = sqlite3.connect(db_path)
    sql = (
        "CREATE TABLE IF NOT EXISTS broker_activity ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "symbol TEXT NOT NULL, date TEXT NOT NULL, broker_id TEXT NOT NULL, "
        "broker_name TEXT, buy_qty INTEGER DEFAULT 0, sell_qty INTEGER DEFAULT 0, "
        "net_qty INTEGER DEFAULT 0, buy_val REAL DEFAULT 0.0, sell_val REAL DEFAULT 0.0, "
        "net_val REAL DEFAULT 0.0, UNIQUE(symbol, date, broker_id))"
    )
    conn.execute(sql)
    conn.execute('CREATE INDEX IF NOT EXISTS idx_ba_symbol_date ON broker_activity(symbol, date)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_ba_date ON broker_activity(date)')
    conn.commit()
    conn.close()


def log_broker_activity(fs_df, db_path='nepse_market_data.db'):
    try:
        import sqlite3, pandas as pd
        from datetime import date, timedelta
        if fs_df is None or fs_df.empty:
            return
        _ensure_broker_activity_table(db_path)
        buy = (
            fs_df.groupby(['symbol', 'buyer_broker'])
            .agg(buy_qty=('quantity', 'sum'), buy_val=('amount', 'sum'), broker_name=('buyerBrokerName', 'first'))
            .reset_index().rename(columns={'buyer_broker': 'broker_id'})
        )
        sell = (
            fs_df.groupby(['symbol', 'seller_broker'])
            .agg(sell_qty=('quantity', 'sum'), sell_val=('amount', 'sum'), broker_name_s=('sellerBrokerName', 'first'))
            .reset_index().rename(columns={'seller_broker': 'broker_id'})
        )
        merged = pd.merge(buy, sell, on=['symbol', 'broker_id'], how='outer').fillna(0)
        if 'broker_name_s' in merged.columns:
            merged['broker_name'] = merged.apply(
                lambda r: r['broker_name'] if r['broker_name'] not in (0, '', None) else r['broker_name_s'], axis=1
            )
        trade_date = str(fs_df['businessDate'].iloc[0])[:10]
        records = []
        for _, row in merged.iterrows():
            bid_raw = str(row['broker_id']).replace('.0', '')
            bid = bid_raw if bid_raw.isdigit() else str(row['broker_id'])
            bq = int(row.get('buy_qty', 0) or 0)
            sq = int(row.get('sell_qty', 0) or 0)
            bv = float(row.get('buy_val', 0) or 0)
            sv = float(row.get('sell_val', 0) or 0)
            records.append((str(row['symbol']), trade_date, bid,
                str(row.get('broker_name', '') or ''), bq, sq, bq-sq, bv, sv, bv-sv))
        if not records:
            return
        conn = sqlite3.connect(db_path)
        upsert = (
            "INSERT INTO broker_activity "
            "(symbol,date,broker_id,broker_name,buy_qty,sell_qty,net_qty,buy_val,sell_val,net_val) "
            "VALUES (?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(symbol,date,broker_id) DO UPDATE SET "
            "broker_name=excluded.broker_name, buy_qty=excluded.buy_qty, sell_qty=excluded.sell_qty, "
            "net_qty=excluded.net_qty, buy_val=excluded.buy_val, sell_val=excluded.sell_val, "
            "net_val=excluded.net_val"
        )
        conn.executemany(upsert, records)
        cutoff = (date.today() - timedelta(days=3*365)).strftime('%Y-%m-%d')
        deleted = conn.execute('DELETE FROM broker_activity WHERE date < ?', (cutoff,)).rowcount
        conn.commit()
        total_rows = conn.execute('SELECT COUNT(*) FROM broker_activity').fetchone()[0]
        distinct_dates = conn.execute('SELECT COUNT(DISTINCT date) FROM broker_activity').fetchone()[0]
        conn.close()
        stocks_logged = len(merged['symbol'].unique())
        clean_msg = f'  (cleaned {deleted} old records)' if deleted > 0 else ''
        print(
            f'  Broker activity saved — {stocks_logged} stocks, {len(records)} broker rows '
            f'logged for {trade_date}{clean_msg}  '
            f'[{total_rows:,} total rows, {distinct_dates} trading days in history]'
        )
    except Exception as e:
        print(f'  [broker logger] Warning: {e}')


def get_top_broker_holders(symbol, db_path='nepse_market_data.db', top_n=15):
    """Return top broker holders for a symbol based on cumulative net buying from DB."""
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            'SELECT broker_id, '
            'SUM(buy_val) as total_buy, SUM(sell_val) as total_sell, '
            'SUM(net_val) as total_net, COUNT(DISTINCT date) as days_active, '
            'SUM(buy_qty) as total_buy_qty, SUM(sell_qty) as total_sell_qty '
            'FROM broker_activity WHERE symbol=? '
            'AND broker_id NOT LIKE "% %" '
            'AND broker_id GLOB "[0-9]*" '
            'GROUP BY broker_id '
            'ORDER BY total_net DESC',
            (symbol,)
        ).fetchall()
        conn.close()
        results = []
        for bid, tbuy, tsell, tnet, days, bqty, sqty in rows:
            tbuy = float(tbuy or 0)
            tsell = float(tsell or 0)
            bqty = int(bqty or 0)
            sqty = int(sqty or 0)
            avg_buy = round(tbuy / bqty, 2) if bqty > 0 else 0
            avg_sell = round(tsell / sqty, 2) if sqty > 0 else 0
            results.append(dict(
                broker_id=str(bid),
                broker_name=str(bid),
                total_buy=tbuy,
                total_sell=tsell,
                total_net=float(tnet or 0),
                days_active=int(days or 0),
                total_buy_qty=bqty,
                total_sell_qty=sqty,
                net_qty=bqty-sqty,
                avg_buy_price=avg_buy,
                avg_sell_price=avg_sell,
            ))
        return results[:top_n]
    except Exception as e:
        return []


def analyze_broker_holders(symbol=None, db_path='nepse_market_data.db'):
    """Menu option — show top 15 broker holders for any stock."""
    from rich.table import Table
    from rich.rule import Rule
    if not symbol:
        console.print()
        symbol = input('  Enter stock symbol (e.g. BUNGAL): ').strip().upper()
    if not symbol:
        console.print('  No symbol entered.', style='yellow')
        return
    holders = get_top_broker_holders(symbol, db_path, top_n=15)
    console.print()
    console.print(Rule(f'Top Broker Holders — {symbol}', style='cyan'))
    if not holders:
        console.print(f'  No broker history found for {symbol}.', style='yellow')
        console.print('  History builds automatically each trading day you run any scan.', style='dim')
        return
    t = Table(show_header=True, header_style='bold cyan', box=None, padding=(0, 2))
    t.add_column('#', style='dim', width=4)
    t.add_column('Broker ID', width=10)
    t.add_column('Net Position', width=14, justify='right')
    t.add_column('Net Shares', width=12, justify='right')
    t.add_column('Avg Buy', width=10, justify='right')
    t.add_column('Avg Sell', width=10, justify='right')
    t.add_column('Total Bought', width=14, justify='right')
    t.add_column('Total Sold', width=14, justify='right')
    t.add_column('Days', width=6, justify='right')
    def _fmt(val):
        if abs(val) >= 1e6:
            return ('Rs ' + str(round(abs(val)/1e6, 1)) + 'M')
        return ('Rs ' + str(round(abs(val)/1e3)) + 'K')
    for i, h in enumerate(holders, 1):
        net = h['total_net']
        net_str = ('+' if net >= 0 else '-') + _fmt(net)
        net_style = 'green' if net >= 0 else 'red'
        net_qty = h.get('net_qty', 0)
        nq_str = ('+' if net_qty >= 0 else '') + f'{net_qty:,}'
        nq_style = 'green' if net_qty >= 0 else 'red'
        avg_b = f"Rs {h.get('avg_buy_price',0):,.1f}" if h.get('avg_buy_price') else '-'
        avg_s = f"Rs {h.get('avg_sell_price',0):,.1f}" if h.get('avg_sell_price') else '-'
        t.add_row(
            str(i),
            h['broker_id'],
            f'[{net_style}]{net_str}[/{net_style}]',
            f'[{nq_style}]{nq_str}[/{nq_style}]',
            avg_b,
            avg_s,
            _fmt(h['total_buy']),
            _fmt(h['total_sell']),
            str(h['days_active']),
        )
    console.print(t)
    console.print()
    if holders:
        top = holders[0]
        console.print(f"  Top holder: Broker {top['broker_id']} — net {'+' if top['total_net']>=0 else ''}{round(top['total_net']/1e6,1)}M over {top['days_active']} days", style='bold')
        console.print()
        # Smart summary for top 3 holders
        console.print("  [bold cyan]── Smart Summary ──[/bold cyan]")
        for h in holders[:3]:
            net = h['total_net']
            net_qty = h.get('net_qty', 0)
            avg_b = h.get('avg_buy_price', 0)
            avg_s = h.get('avg_sell_price', 0)
            days = h['days_active']
            bid = h['broker_id']
            amt = ('Rs ' + str(round(abs(net)/1e6, 1)) + 'M') if abs(net) >= 1e6 else ('Rs ' + str(round(abs(net)/1e3)) + 'K')
            qty_str = f'{abs(net_qty):,}'
            if net > 0 and avg_b > 0 and avg_s > 0:
                if avg_b > avg_s:
                    msg = f"Broker {bid} bought avg Rs {avg_b:,.1f} and sold avg Rs {avg_s:,.1f} — buying HIGHER than selling, net accumulating {qty_str} shares worth {amt}"
                else:
                    msg = f"Broker {bid} bought avg Rs {avg_b:,.1f} and sold avg Rs {avg_s:,.1f} — selling HIGHER than buying, collecting profit while accumulating {qty_str} net shares ({amt})"
            elif net > 0 and avg_b > 0 and avg_s == 0:
                msg = f"Broker {bid} only BUYING — no sells, accumulating {qty_str} shares at avg Rs {avg_b:,.1f} ({amt} invested)"
            elif net < 0 and avg_b > 0 and avg_s > 0:
                if avg_s > avg_b:
                    msg = f"Broker {bid} bought avg Rs {avg_b:,.1f} and sold avg Rs {avg_s:,.1f} — selling HIGHER than buying, distributing {qty_str} shares at profit"
                else:
                    msg = f"Broker {bid} bought avg Rs {avg_b:,.1f} and sold avg Rs {avg_s:,.1f} — selling LOWER than buying, exiting position at loss ({amt} distributed)"
            elif net < 0 and avg_s > 0 and avg_b == 0:
                msg = f"Broker {bid} only SELLING — no buys, distributing {qty_str} shares at avg Rs {avg_s:,.1f} ({amt} out)"
            else:
                msg = f"Broker {bid} — net {'+' if net>=0 else ''}{amt} over {days} days"
            col = 'green' if net >= 0 else 'red'
            console.print(f"  [{col}]• {msg}[/{col}]")
    console.print()



def _get_dynamic_whales(days=30, top_n=10, db_path="nepse_market_data.db"):
    try:
        import sqlite3 as _sq3
        conn = _sq3.connect(db_path)
        dates = [d[0] for d in conn.execute("SELECT DISTINCT date FROM broker_activity ORDER BY date DESC LIMIT ?", (days,)).fetchall()]
        if not dates:
            conn.close(); return set(), set()
        ph = ",".join(["?"]*len(dates))
        rows = conn.execute(f"SELECT broker_id, SUM(CASE WHEN net_val>0 THEN net_val ELSE 0 END), SUM(CASE WHEN net_val<0 THEN ABS(net_val) ELSE 0 END), AVG(ABS(net_val)), COUNT(DISTINCT symbol) FROM broker_activity WHERE date IN ({ph}) GROUP BY broker_id", dates).fetchall()
        conn.close()
        scored = [(r[0], (r[3]/1000000)*(r[4]**0.5), r[1], r[2]) for r in rows]
        buyers = sorted([r for r in scored if r[2] > r[3]*1.2], key=lambda x: x[1], reverse=True)
        sellers = sorted([r for r in scored if r[3] > r[2]*1.2], key=lambda x: x[1], reverse=True)
        return set(r[0] for r in buyers[:top_n]), set(r[0] for r in sellers[:top_n])
    except:
        return set(), set()

def analyze_broker_trend(symbol=None, days=7, db_path="nepse_market_data.db"):
    import sqlite3
    from rich.table import Table
    if symbol: symbol = symbol.upper()
    if not symbol:
        console.print()
        symbol = input("  Enter stock symbol: ").strip().upper()
    if not symbol:
        console.print("  Missing symbol.", style="yellow"); return
    try:
        conn = sqlite3.connect(db_path)
        dates = conn.execute(
            "SELECT DISTINCT date FROM broker_activity WHERE symbol=? ORDER BY date DESC LIMIT ?",
            (symbol, days)
        ).fetchall()
        dates = [d[0] for d in dates]
        dates.reverse()
        if not dates:
            console.print(f"  No data for {symbol}.", style="yellow"); conn.close(); return
        console.print()
        console.rule(f"[bold cyan]Broker Trend — {symbol} (last {len(dates)} days)[/bold cyan]")
        console.print()
        t = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
        t.add_column("Date", width=12)
        t.add_column("Score", width=12, justify="center")
        t.add_column("Dominant Buyer", width=30)
        t.add_column("Dominant Seller", width=30)
        t.add_column("Net Flow", width=14, justify="center")
        score_history = []
        for date_str in dates:
            rows = conn.execute(
                "SELECT broker_id, net_val FROM broker_activity WHERE symbol=? AND date=? AND broker_id GLOB '[0-9]*' ORDER BY net_val DESC",
                (symbol, date_str)
            ).fetchall()
            if not rows: continue
            smb = [r for r in rows if r[1] > 0]
            sms = [r for r in rows if r[1] < 0]
            ssn = len(rows); snb = len(smb)
            sbp = snb / ssn * 100 if ssn else 0
            whale_buyers, whale_sellers = _get_dynamic_whales()
            ss = 50
            if sbp > 65: ss += 20
            elif sbp > 50: ss += 10
            else: ss -= 10
            for r2 in rows:
                if str(r2[0]) in whale_buyers: ss = min(100, ss + 8)
                elif str(r2[0]) in whale_sellers: ss = max(0, ss - 8)
            buyer_name = f"Broker {smb[0][0]} {_fmt_rs_val(abs(smb[0][1]))}" if smb else "—"
            seller_name = f"Broker {sms[0][0]} {_fmt_rs_val(abs(sms[0][1]))}" if sms else "—"
            ssv = "BULL" if ss >= 70 else "BEAR" if ss <= 30 else "MIX"
            ssc = "green" if ss >= 70 else "red" if ss <= 30 else "yellow"
            net_flow = sum(r[1] for r in rows if r[1] > 0)


            if net_flow > 100000: flow_str = f"[green]IN {_fmt_rs_val(abs(net_flow))}[/green]"
            elif net_flow < -100000: flow_str = f"[red]OUT {_fmt_rs_val(abs(net_flow))}[/red]"
            else: flow_str = f"[yellow]NEUTRAL {_fmt_rs_val(abs(net_flow))}[/yellow]"
            score_str = f"[{ssc}]{ss}  {ssv}[/{ssc}]"
            t.add_row(date_str, score_str, buyer_name, seller_name, flow_str)
            score_history.append(ss)
        console.print(t)
        console.print()
        if len(score_history) >= 2:
            console.print("[bold]Trend Insights:[/bold]")
            if score_history[-1] > score_history[0]:
                console.print("   [^] Smart money sentiment improving", style="green")
            elif score_history[-1] < score_history[0]:
                console.print("   [v] Smart money sentiment deteriorating", style="red")
            else:
                console.print("  [=] Sentiment flat over period", style="yellow")
            avg = sum(score_history) / len(score_history)
            console.print(f"  Avg score over {len(score_history)} days: {avg:.0f}/100")
        conn.close()
        console.print()
    except Exception as e:
        console.print(f"  Error: {e}", style="red")


def analyze_broker_impact(days=30, top_n=20, db_path="nepse_market_data.db"):
    import sqlite3
    from rich.table import Table
    console.print()
    console.rule("[bold cyan]Broker Impact Analysis[/bold cyan]")
    console.print()
    try:
        conn = sqlite3.connect(db_path)
        # Get date range
        dates = conn.execute("SELECT DISTINCT date FROM broker_activity ORDER BY date DESC LIMIT ?", (days,)).fetchall()
        dates = [d[0] for d in dates]
        if not dates:
            console.print("  No data found.", style="yellow"); conn.close(); return
        console.print(f"  Analysing {len(dates)} trading days ({dates[-1]} to {dates[0]})")
        console.print()
        # Aggregate per broker
        rows = conn.execute("""
            SELECT broker_id,
                COUNT(DISTINCT symbol) as stocks_traded,
                COUNT(*) as total_appearances,
                SUM(CASE WHEN net_val > 0 THEN 1 ELSE 0 END) as buy_days,
                SUM(CASE WHEN net_val < 0 THEN 1 ELSE 0 END) as sell_days,
                SUM(CASE WHEN net_val > 0 THEN net_val ELSE 0 END) as total_bought,
                SUM(CASE WHEN net_val < 0 THEN ABS(net_val) ELSE 0 END) as total_sold,
                AVG(ABS(net_val)) as avg_trade_size
            FROM broker_activity
            WHERE date IN ({})
            AND broker_id GLOB '[0-9]*'
            GROUP BY broker_id
            ORDER BY (total_bought + total_sold) DESC
        """.format(",".join(["?"]*len(dates))), dates).fetchall()
        if not rows:
            console.print("  No broker data found.", style="yellow"); return
        # Score each broker: avg_trade_size * stocks_traded * appearances
        scored = []
        for r in rows:
            bid, stocks, apps, bdays, sdays, tbought, tsold, avg_size = r
            impact = (avg_size / 1000000) * (stocks ** 0.5) * (apps ** 0.3)
            net = tbought - tsold
            bias = "BUYER" if tbought > tsold else "SELLER" if tsold > tbought else "NEUTRAL"
            scored.append((bid, stocks, apps, bdays, sdays, tbought, tsold, avg_size, impact, bias, net))
        scored.sort(key=lambda x: x[9], reverse=True)
        scored = scored[:top_n]
        t = Table(show_header=True, header_style="bold cyan", box=None, padding=(0,2))
        t.add_column("#", width=3, justify="right")
        t.add_column("Broker", width=6, justify="right")
        t.add_column("Stocks", width=7, justify="right")
        t.add_column("Appear", width=7, justify="right")
        t.add_column("Avg Size", width=12, justify="right")
        t.add_column("Total Bought", width=14, justify="right")
        t.add_column("Total Sold", width=14, justify="right")
        t.add_column("Bias", width=10, justify="center")
        for rank, r in enumerate(scored, 1):
            bid, stocks, apps, bdays, sdays, tbought, tsold, avg_size, impact, bias, net = r
            bc = "green" if bias == "BUYER" else "red" if bias == "SELLER" else "yellow"
            t.add_row(
                str(rank), str(bid),
                str(stocks), str(apps),
                _fmt_rs_val(avg_size),
                _fmt_rs_val(tbought),
                _fmt_rs_val(tsold),
                f"[{bc}]{bias}[/{bc}]"
            )
        console.print(t)
        console.print()
        # Query ALL brokers for net buyers/sellers (not just top 20 by volume)
        all_rows = conn.execute("""
            SELECT broker_id,
                COUNT(DISTINCT symbol) as stocks,
                COUNT(*) as apps,
                SUM(CASE WHEN net_val>0 THEN net_val ELSE 0 END) as tbought,
                SUM(CASE WHEN net_val<0 THEN ABS(net_val) ELSE 0 END) as tsold
            FROM broker_activity
            WHERE date IN ({})
            AND broker_id GLOB '[0-9]*'
            GROUP BY broker_id
        """.format(",".join(["?"]*len(dates))), dates).fetchall()
        all_buyers = sorted([r for r in all_rows if r[3] > r[4]], key=lambda x: x[3]-x[4], reverse=True)[:5]
        all_sellers = sorted([r for r in all_rows if r[4] > r[3]], key=lambda x: x[4]-x[3], reverse=True)[:5]
        console.print("[bold]Top 5 Net Buyers:[/bold]")
        for r in all_buyers:
            net = r[3] - r[4]
            console.print(f"  [green]Broker {r[0]} - net bought {_fmt_rs_val(net)} across {r[1]} stocks ({r[2]} trades)[/green]")
        console.print()
        console.print("[bold]Top 5 Net Sellers:[/bold]")
        for r in all_sellers:
            net = r[4] - r[3]
            console.print(f"  [red]Broker {r[0]} - net sold {_fmt_rs_val(net)} across {r[1]} stocks ({r[2]} trades)[/red]")
        conn.close()
        console.print()
    except Exception as e:
        console.print(f"  Error: {e}", style="red")


def analyze_momentum_hunter(days=7, top_n=15, min_days=2, db_path='nepse_market_data.db'):
    import sqlite3
    from rich.table import Table
    console.print()
    console.rule('[bold cyan]Momentum Hunter -- Early Accumulation Detector[/bold cyan]')
    console.print()
    try:
        conn = sqlite3.connect(db_path)
        dates = [d[0] for d in conn.execute('SELECT DISTINCT date FROM broker_activity ORDER BY date DESC LIMIT ?', (days,)).fetchall()]
        if len(dates) < 2:
            console.print('  Need at least 2 days of data. Run Full Scan daily.', style='yellow')
            conn.close()
            return
        dates_sorted = sorted(dates)
        console.print('  Scanning ' + str(len(dates)) + ' days (' + dates_sorted[0] + ' to ' + dates_sorted[-1] + ')')
        console.print()
        ph = ','.join(['?']*len(dates))
        symbols = [r[0] for r in conn.execute('SELECT DISTINCT symbol FROM broker_activity WHERE date IN (' + ph + ') ORDER BY symbol', dates).fetchall()]
        console.print('  Analysing ' + str(len(symbols)) + ' stocks...', style='dim')
        whale_buyers, whale_sellers = _get_dynamic_whales(days=days)
        candidates = []
        for symbol in symbols:
            daily = []
            for date_str in dates_sorted:
                rows = conn.execute('SELECT broker_id, net_val FROM broker_activity WHERE symbol=? AND date=?', (symbol, date_str)).fetchall()
                if not rows:
                    continue
                total_buy = sum(r[1] for r in rows if r[1] > 0)
                n_buyers = len([r for r in rows if r[1] > 0])
                n_total = len(rows)
                buyer_pct = n_buyers / n_total * 100 if n_total else 0
                whale_buy = sum(1 for r in rows if r[0] in whale_buyers and r[1] > 0)
                whale_sell = sum(1 for r in rows if r[0] in whale_sellers and r[1] < 0)
                ds = 50
                if buyer_pct > 65:
                    ds += 20
                elif buyer_pct > 50:
                    ds += 10
                else:
                    ds -= 10
                ds += whale_buy * 8
                ds -= whale_sell * 8
                ds = max(0, min(100, ds))
                daily.append({'date': date_str, 'score': ds, 'net': total_buy, 'buyers': n_buyers, 'total': n_total, 'wb': whale_buy})
            if len(daily) < min_days:
                continue
            consec = 0
            for d in reversed(daily):
                if d['score'] >= 55:
                    consec += 1
                else:
                    break
            if consec < min_days:
                continue
            recent = daily[-min_days:]
            avg_score = sum(d['score'] for d in recent) / len(recent)
            total_net = sum(d['net'] for d in recent)
            trend = daily[-1]['score'] - daily[0]['score'] if len(daily) > 1 else 0
            total_whale = sum(d['wb'] for d in recent)
            momentum = (avg_score * 0.4) + (min(consec, 5) * 8) + (min(total_whale, 5) * 4) + (min(trend, 30) * 0.3)
            momentum = max(0, min(100, momentum))
            candidates.append({'symbol': symbol, 'consec': consec, 'avg_score': avg_score, 'momentum': momentum, 'total_net': total_net, 'total_whale': total_whale, 'trend': trend, 'daily': daily})
        conn.close()
        if not candidates:
            console.print('  No momentum candidates found. Need more data days.', style='yellow')
            return
        candidates.sort(key=lambda x: x['momentum'], reverse=True)
        candidates = candidates[:top_n]
        t = Table(show_header=True, header_style='bold cyan', box=None, padding=(0, 2))
        t.add_column('Rank', width=5, justify='right')
        t.add_column('Symbol', width=10)
        t.add_column('Days', width=5, justify='center')
        t.add_column('Score', width=12, justify='center')
        t.add_column('Trend', width=10, justify='center')
        t.add_column('Net Flow', width=14, justify='right')
        t.add_column('Whales', width=7, justify='center')
        t.add_column('Signal', width=14, justify='center')
        for rank, c in enumerate(candidates, 1):
            sc = c['momentum']
            sc_col = 'green' if sc >= 70 else 'yellow' if sc >= 55 else 'white'
            tr = c['trend']
            if tr > 5:
                tr_str = '[green]+' + str(round(tr)) + '[/green]'
            elif tr < -5:
                tr_str = '[red]' + str(round(tr)) + '[/red]'
            else:
                tr_str = '[yellow]' + str(round(tr)) + '[/yellow]'
            if sc >= 75:
                sig = '[green]STRONG BUY[/green]'
            elif sc >= 60:
                sig = '[cyan]WATCH[/cyan]'
            else:
                sig = '[yellow]WEAK[/yellow]'
            t.add_row(str(rank), c['symbol'], str(c['consec']), '[' + sc_col + ']' + str(round(sc)) + '/100[/' + sc_col + ']', tr_str, _fmt_rs_val(c['total_net']), str(c['total_whale']), sig)
        console.print(t)
        console.print()
        console.print('[bold]Top 3 Detailed Breakdown:[/bold]')
        for c in candidates[:3]:
            sc = c['momentum']
            sc_col = 'green' if sc >= 70 else 'yellow'
            console.print('  [' + sc_col + ']' + c['symbol'] + '[/' + sc_col + '] - ' + str(c['consec']) + ' consecutive buy days, momentum ' + str(round(sc)) + '/100')
            for d in c['daily'][-3:]:
                dc = 'green' if d['score'] >= 60 else 'red' if d['score'] < 45 else 'yellow'
                console.print('    ' + d['date'] + ': [' + dc + ']' + str(d['score']) + '[/' + dc + '] | buyers ' + str(d['buyers']) + '/' + str(d['total']) + ' | net ' + _fmt_rs_val(d['net']))
        console.print()
        console.print('[dim]Best entries: STRONG BUY stocks near support (option 18). Confirm with 17c.[/dim]')
        console.print()
    except Exception as e:
        console.print('  Error: ' + str(e), style='red')
        import traceback
        traceback.print_exc()

def analyze_broker_date(symbol=None, date_str=None, db_path='nepse_market_data.db'):
    """Show broker activity for a specific stock on a specific date."""
    from rich.table import Table
    from rich.rule import Rule
    if not symbol:
        console.print()
        symbol = input('  Enter stock symbol (e.g. CHCL): ').strip().upper()
    symbol = symbol.upper()
    # Show available dates first, then ask for date
    try:
        import sqlite3 as _sq
        _conn = _sq.connect(db_path)
        _avail = _conn.execute(
            'SELECT DISTINCT date FROM broker_activity WHERE symbol=? ORDER BY date DESC LIMIT 30',
            (symbol,)
        ).fetchall()
        _conn.close()
        if _avail:
            console.print()
            console.print(f'  Available dates for [bold]{symbol}[/bold] in DB:')
            for _i, (_d,) in enumerate(_avail, 1):
                console.print(f'    {_i:>2}. {_d}')
            console.print()
        else:
            console.print(f'  No data found for {symbol} yet — run a scan first on a trading day.', style='yellow')
    except Exception:
        pass
    if not date_str or date_str.lower() == 'prompt':
        date_str = input('  Enter date from above (YYYY-MM-DD): ').strip()
    # Normalize date format
    try:
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts[2]) == 4:  # DD/MM/YYYY
                date_str = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
            else:  # MM/DD/YYYY
                date_str = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
    except Exception:
        pass
    if not symbol:
        console.print('  Missing symbol.', style='yellow')
        return
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        # Normalize date format
        try:
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts[2]) == 4:
                    date_str = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                else:
                    date_str = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
        except Exception:
            pass
        if not date_str:
            console.print('  No date entered.', style='yellow')
            conn.close()
            return
        rows = conn.execute(
            'SELECT broker_id, buy_qty, sell_qty, net_qty, buy_val, sell_val, net_val '
            'FROM broker_activity WHERE symbol=? AND date=? '
            'AND broker_id GLOB "[0-9]*" '
            'ORDER BY net_val DESC',
            (symbol, date_str)
        ).fetchall()
        conn.close()
    except Exception as e:
        console.print(f'  DB error: {e}', style='red')
        return
    console.print()
    console.print(Rule(f'Broker Activity — {symbol} on {date_str}', style='cyan'))
    if not rows:
        console.print(f'  No data found for {symbol} on {date_str}.', style='yellow')
        console.print('  Note: Only dates after you started running scans will have data.', style='dim')
        return
    def _fmt(val):
        if abs(val) >= 1e6:
            return ('Rs ' + str(round(abs(val)/1e6, 1)) + 'M')
        return ('Rs ' + str(round(abs(val)/1e3)) + 'K')
    t = Table(show_header=True, header_style='bold cyan', box=None, padding=(0, 2))
    t.add_column('#', style='dim', width=4)
    t.add_column('Broker ID', width=10)
    t.add_column('Net Position', width=14, justify='right')
    t.add_column('Net Shares', width=12, justify='right')
    t.add_column('Avg Price', width=12, justify='right')
    t.add_column('Total Bought', width=14, justify='right')
    t.add_column('Total Sold', width=14, justify='right')
    total_buy_val = 0
    total_sell_val = 0
    buyers = 0
    sellers = 0
    for i, (bid, bq, sq, nq, bv, sv, nv) in enumerate(rows, 1):
        net_style = 'green' if nv >= 0 else 'red'
        net_str = ('+' if nv >= 0 else '-') + _fmt(nv)
        nq_str = ('+' if nq >= 0 else '') + f'{nq:,}'
        total_vol = bq + sq
        avg_price = round((bv + sv) / total_vol, 1) if total_vol > 0 else 0
        avg_str = f'Rs {avg_price:,.1f}' if avg_price > 0 else '-'
        t.add_row(str(i), str(bid),
            f'[{net_style}]{net_str}[/{net_style}]',
            f'[{net_style}]{nq_str}[/{net_style}]',
            avg_str, _fmt(bv), _fmt(sv))
        total_buy_val += bv
        total_sell_val += sv
        if nv > 0: buyers += 1
        elif nv < 0: sellers += 1
    console.print(t)
    console.print()
    # Summary
    console.print(f'  Total brokers: {len(rows)}  |  Net buyers: [green]{buyers}[/green]  |  Net sellers: [red]{sellers}[/red]')
    console.print(f'  Total volume bought: {_fmt(total_buy_val)}  |  Total volume sold: {_fmt(total_sell_val)}')
    net_flow = total_buy_val - total_sell_val
    flow_col = 'green' if net_flow >= 0 else 'red'
    flow_dir = 'NET INFLOW' if net_flow >= 0 else 'NET OUTFLOW'

    # Smart Money Analysis
    console.print()
    console.rule('[bold cyan]Smart Money Analysis[/bold cyan]')
    # Detect market-wide net buyers and sellers from DB
    try:
        import sqlite3 as _sq2
        _conn2 = _sq2.connect(db_path)
        _all = _conn2.execute('''
            SELECT broker_id,
                SUM(CASE WHEN net_val>0 THEN net_val ELSE 0 END) as tb,
                SUM(CASE WHEN net_val<0 THEN ABS(net_val) ELSE 0 END) as ts
            FROM broker_activity
            WHERE broker_id GLOB '[0-9]*'
            GROUP BY broker_id
        ''').fetchall()
        _conn2.close()
        _net_buyers = set(str(r[0]) for r in sorted(_all, key=lambda x: x[1]-x[2], reverse=True)[:8] if r[1] > r[2])
        _net_sellers = set(str(r[0]) for r in sorted(_all, key=lambda x: x[2]-x[1], reverse=True)[:8] if r[2] > r[1])
        lw = {b: 'NET BUYER' for b in _net_buyers}
        lw.update({s: 'NET SELLER' for s in _net_sellers})
    except Exception:
        _net_buyers, _net_sellers = set(), set()
        lw = {}
    smb = [r for r in rows if r[6] > 0]
    sms = [r for r in rows if r[6] < 0]
    smtb = max(smb, key=lambda x: x[6]) if smb else None
    smts = min(sms, key=lambda x: x[6]) if sms else None
    smst = sum(abs(r[6]) for r in sms)
    ssn = len(rows); snb = len(smb); sns = len(sms)
    sbp = snb / ssn * 100 if ssn else 0
    console.print()
    console.print('  [bold yellow]Top Broker Activity:[/bold yellow]')
    # Show top 5 buyers
    for r in sorted(smb, key=lambda x: x[6], reverse=True)[:5]:
        bid = str(r[0])
        sv = _fmt_rs_val(r[6])
        tag = ' <- DOMINANT BUYER' if smtb and r[0] == smtb[0] else ''
        console.print(f'     [green]Broker {bid} - BUYING {sv}{tag}[/green]')
    # Show top 5 sellers
    for r in sorted(sms, key=lambda x: x[6])[:5]:
        bid = str(r[0])
        sv = _fmt_rs_val(abs(r[6]))
        tag = ' <- DOMINANT SELLER' if smts and r[0] == smts[0] else ''
        console.print(f'     [red]Broker {bid} - SELLING {sv}{tag}[/red]')
    ss = 50
    if sbp > 65: ss += 20
    elif sbp > 50: ss += 10
    else: ss -= 10
    if smts:
        sp2 = abs(smts[6]) / smst * 100 if smst else 0
        if sp2 > 60: ss -= 20
        elif sp2 > 40: ss -= 10
    # Boost score if dominant buyer is much larger than dominant seller
    if smtb and smts:
        if smtb[6] > abs(smts[6]) * 1.5:
            ss += 15
        elif abs(smts[6]) > smtb[6] * 1.5:
            ss -= 15
    ss = max(0, min(100, ss))
    ssv,ssc = ('BULLISH','green') if ss>=70 else ('MIXED','yellow') if ss>=50 else ('BEARISH','red')
    console.print()
    console.print(f'  [bold]Smart Money Score: [{ssc}]{ss}/100 ({ssv})[/{ssc}][/bold]')
    console.print(f'     + {snb} brokers buying ({sbp:.0f}% of participants)')
    console.print(f'     - {sns} brokers selling')
    if smts:
        sp2 = abs(smts[6]) / smst * 100 if smst else 0
        if sp2 > 40:
            sv4 = _fmt_rs_val(abs(smts[6]))
            bid4 = str(smts[0])
            console.print(f'     - 1 dominant seller (Broker {bid4}) - {sv4} ({sp2:.0f}% of all selling)')
    if net_flow > 10000: console.print(f'     + Net flow: [green]INFLOW {_fmt_rs_val(abs(net_flow))}[/green]')
    elif net_flow < -10000: console.print(f'     - Net flow: [red]OUTFLOW {_fmt_rs_val(abs(net_flow))}[/red]')
    else: console.print('     ~ Net flow: [yellow]NEUTRAL[/yellow]')
    console.print()
    if smts:
        sp2 = abs(smts[6]) / smst * 100 if smst else 0
        if sp2 > 50 and sbp > 60:
            bid5 = str(smts[0])
            console.print(f'  [bold yellow]WARNING:[/bold yellow] Large single seller (Broker {bid5}) offsetting all buying - possible distribution')
    if ss >= 70: console.print('  [bold green]SIGNAL:[/bold green] Strong smart money accumulation - watch for breakout')
    elif ss <= 30: console.print('  [bold red]SIGNAL:[/bold red] Smart money distributing - consider reducing exposure')
    console.print()
    console.print(f'  [{flow_col}]{flow_dir}: {_fmt(abs(net_flow))}[/{flow_col}]')
    console.print()

    # ── My Holders Watch ──
    try:
        import sqlite3 as _sq3
        _conn3 = _sq3.connect(db_path)
        # Get top 5 estimated holders from all broker_activity
        _holders = _conn3.execute(
            '''SELECT broker_id,
                SUM(buy_qty) - SUM(sell_qty) as net_held
            FROM broker_activity
            WHERE symbol=? AND broker_id GLOB "[0-9]*"
            GROUP BY broker_id
            HAVING net_held > 0
            ORDER BY net_held DESC LIMIT 5''',
            (symbol,)
        ).fetchall()
        _conn3.close()

        if _holders:
            _holder_ids = set(str(h[0]) for h in _holders)
            # Check which holders are buying or selling today
            _buying_holders  = [str(r[0]) for r in rows if str(r[0]) in _holder_ids and r[6] > 0]
            _selling_holders = [str(r[0]) for r in rows if str(r[0]) in _holder_ids and r[6] < 0]
            _inactive_holders = [str(h[0]) for h in _holders if str(h[0]) not in {str(r[0]) for r in rows}]

            console.rule('[bold cyan]Top Holder Watch[/bold cyan]')
            console.print()
            console.print(f'  [dim]Tracking your top 5 estimated holders for {symbol}:[/dim]')
            console.print()

            for h in _holders:
                hid = str(h[0])
                held = h[1]
                # Find today's activity for this holder
                today = next((r for r in rows if str(r[0]) == hid), None)
                if today:
                    nv = today[6]
                    nq = today[3]
                    if nv > 0:
                        status = f'[green]BUYING today  +{nq:,} shares (+{_fmt(nv)})[/green]  <- ACCUMULATING'
                    else:
                        status = f'[red]SELLING today {nq:,} shares (-{_fmt(abs(nv))})[/red]  <- WARNING'
                else:
                    status = '[dim]Not active today[/dim]'
                console.print(f'  Broker {hid:>3} (holds ~{held:,.0f} shares): {status}')

            console.print()

            # Check if market-wide net sellers are also selling this stock today
            import sqlite3 as _sq4
            _conn4 = _sq4.connect(db_path)
            _all2 = _conn4.execute('''
                SELECT broker_id,
                    SUM(CASE WHEN net_val>0 THEN net_val ELSE 0 END) as tb,
                    SUM(CASE WHEN net_val<0 THEN ABS(net_val) ELSE 0 END) as ts
                FROM broker_activity WHERE broker_id GLOB "[0-9]*"
                GROUP BY broker_id
            ''').fetchall()
            _conn4.close()
            _mkt_sellers = set(str(r[0]) for r in _all2 if r[2] > r[1])

            # Smart money sellers = market-wide net sellers selling this stock today, not in holders
            _smart_selling = [(str(r[0]), r[6]) for r in rows
                if str(r[0]) in _mkt_sellers and r[6] < 0 and str(r[0]) not in _holder_ids]
            _smart_selling.sort(key=lambda x: x[1])

            if _smart_selling:
                console.print('  [bold]Other net sellers active today:[/bold]')
                for bid, nv in _smart_selling[:5]:
                    console.print(f'    [red]Broker {bid} (net seller market-wide) selling Rs {abs(nv)/1e6:.2f}M today[/red]')
                total_smart_sell  = sum(abs(nv) for _, nv in _smart_selling)
                total_holder_buy  = sum(r[6] for r in rows if str(r[0]) in _holder_ids and r[6] > 0)
                net_smart = total_holder_buy - total_smart_sell
                net_col   = 'green' if net_smart > 0 else 'red'
                console.print()
                console.print(f'  Your holders buying:   [green]Rs {total_holder_buy/1e6:.2f}M[/green]')
                console.print(f'  Net sellers selling:   [red]Rs {total_smart_sell/1e6:.2f}M[/red]')
                console.print(f'  Net flow:              [{net_col}]Rs {net_smart/1e6:.2f}M[/{net_col}] {"(holders winning)" if net_smart > 0 else "(sellers winning)"}')
                console.print()

            # Final verdict
            _hbuy2  = sum(r[6] for r in rows if str(r[0]) in _holder_ids and r[6] > 0)
            _hsell2 = sum(abs(r[6]) for r in rows if str(r[0]) in _holder_ids and r[6] < 0)
            _sratio2 = _hsell2 / _hbuy2 if _hbuy2 > 0 else 1
            if _selling_holders and _sratio2 > 0.10:
                console.print(f'  [bold red]ALERT: Your holders selling — Broker {", ".join(_selling_holders)} flipping![/bold red]')
                console.print('  [red]-> Consider reducing position. Run 17d to check trend.[/red]')
            elif _smart_selling and _buying_holders:
                total_smart_sell = sum(abs(nv) for _, nv in _smart_selling)
                total_holder_buy = sum(r[6] for r in rows if str(r[0]) in _holder_ids and r[6] > 0)
                if total_smart_sell > total_holder_buy * 1.5:
                    console.print('  [bold yellow]CAUTION: Net sellers outweigh your holders buying[/bold yellow]')
                    console.print('  [yellow]-> Hold but tighten stop loss. Watch tomorrow.[/yellow]')
                else:
                    console.print('  [bold green]HOLD: Your holders accumulating despite net sellers[/bold green]')
                    console.print('  [green]-> Normal tug of war. Hold position, watch tomorrow.[/green]')
            elif _smart_selling and not _buying_holders:
                console.print('  [bold red]WARNING: Net sellers active, your holders inactive today[/bold red]')
                console.print('  [red]-> Watch tomorrow. If holders stay inactive 2+ days, consider reducing.[/red]')
            elif _buying_holders:
                console.print(f'  [bold green]GOOD: Your holders accumulating — Broker {", ".join(_buying_holders)}[/bold green]')
                console.print('  [green]-> Hold position. Institutions still confident.[/green]')
            else:
                console.print('  [yellow]Top holders not active today — neutral signal.[/yellow]')
                console.print('  [dim]-> Watch tomorrow.[/dim]')
            console.print()
    except Exception as _e:
        pass

    # Final analysis summary
    console.rule('[bold cyan]Analysis Summary[/bold cyan]')
    console.print()
    lines_out = []

    # Dominant buyer
    if smtb:
        bv = _fmt_rs_val(smtb[6])
        bid_b = str(smtb[0])
        tag = ' [NET BUYER market-wide]' if bid_b in _net_buyers else ''
        lines_out.append(f'[green]+ Broker {bid_b}{tag} is the top buyer at {bv}[/green]')

    # Dominant seller
    if smts:
        sv = _fmt_rs_val(abs(smts[6]))
        bid_s = str(smts[0])
        tag_s = ' [NET SELLER market-wide]' if bid_s in _net_sellers else ''
        lines_out.append(f'[red]- Broker {bid_s}{tag_s} is the dominant seller at {sv}[/red]')

    # Buyer vs seller count
    if sbp > 60:
        lines_out.append(f'[green]+ More brokers buying ({snb}) than selling ({sns}) — buying pressure[/green]')
    elif sbp < 40:
        lines_out.append(f'[red]- More brokers selling ({sns}) than buying ({snb}) — selling pressure[/red]')
    else:
        lines_out.append(f'[yellow]~ Buyers ({snb}) and sellers ({sns}) roughly balanced — tug of war[/yellow]')

    # Known net buyers active in this stock today
    active_net_buyers = [str(r[0]) for r in rows if str(r[0]) in _net_buyers and r[6] > 0]
    active_net_sellers = [str(r[0]) for r in rows if str(r[0]) in _net_sellers and r[6] < 0]
    if active_net_buyers:
        lines_out.append(f'[green]+ Known market-wide NET BUYERS active here: Broker {", ".join(active_net_buyers)} — STRONG signal[/green]')
    if active_net_sellers:
        lines_out.append(f'[red]- Known market-wide NET SELLERS active here: Broker {", ".join(active_net_sellers)} — CAUTION[/red]')

    # Verdict - consider buyer count and known net buyers too
    strong_buyers_active = len(active_net_buyers) >= 3
    buyer_majority = sbp >= 65
    if ss >= 70 or (strong_buyers_active and buyer_majority):
        verdict = '[bold green]STRONG BUY / ACCUMULATE — Multiple institutional buyers active. Watch for breakout.[/bold green]'
    elif ss >= 50 or (strong_buyers_active and ss >= 35):
        verdict = '[bold green]HOLD / ACCUMULATE — Known net buyers accumulating. Institutional interest strong.[/bold green]'
    elif buyer_majority and ss >= 35:
        verdict = '[bold yellow]HOLD — Broad buying but dominant seller present. Watch if seller exits.[/bold yellow]'
    elif ss >= 35:
        verdict = '[bold yellow]CAUTION — More selling than buying. Consider reducing if in profit.[/bold yellow]'
    else:
        verdict = '[bold red]CONSIDER SELLING — Smart money distributing. High selling pressure.[/bold red]'

    for l in lines_out:
        console.print(f'  {l}')
    console.print()
    console.print(f'  Verdict: {verdict}')
    console.print()
    # === NEPALI FY QUARTERLY (Shrawan-based) ===
    console.print()
    console.rule('[bold]Nepali FY Quarterly Seasonality (Shrawan-based)[/bold]')
    console.print()
    console.print('  [dim]FYQ1=Shrawan-Ashwin  FYQ2=Kartik-Poush  FYQ3=Magh-Chaitra  FYQ4=Baisakh-Ashadh[/dim]')
    console.print()

    # Map BS months to FY quarters
    fy_q_map = {4:'FYQ1',5:'FYQ1',6:'FYQ1',
                7:'FYQ2',8:'FYQ2',9:'FYQ2',
                10:'FYQ3',11:'FYQ3',12:'FYQ3',
                1:'FYQ4',2:'FYQ4',3:'FYQ4'}
    fy_q_labels = {
        'FYQ1':'Shrawan-Bhadra-Ashwin (Jul-Oct)',
        'FYQ2':'Kartik-Mangsir-Poush  (Oct-Jan)',
        'FYQ3':'Magh-Falgun-Chaitra   (Jan-Apr)',
        'FYQ4':'Baisakh-Jestha-Ashadh (Apr-Jul)',
    }

    def _fy_label(bs_yr, bs_m):
        if bs_m in (4,5,6,7,8,9,10,11,12): return bs_yr
        else: return bs_yr - 1

    # Build FY quarterly data from monthly data
    from collections import defaultdict as _dd2
    from datetime import date as _dt_fyq2
    _bs_start_fyq = {
        2077:(2020,4,13),2078:(2021,4,14),2079:(2022,4,14),
        2080:(2023,4,14),2081:(2024,4,13),2082:(2025,4,14),2083:(2026,4,14),
    }
    _bs_mdays_fyq = {
        2077:[31,31,31,32,31,31,30,29,30,29,30,30],
        2078:[31,31,32,31,31,31,30,29,30,29,30,30],
        2079:[31,32,31,32,31,30,30,29,30,29,30,30],
        2080:[31,31,31,32,31,31,30,29,30,29,30,30],
        2081:[31,31,32,31,31,31,30,29,30,29,30,30],
        2082:[31,32,31,32,31,30,30,29,30,29,30,30],
        2083:[31,31,31,32,31,31,30,29,30,29,30,30],
    }
    def _to_bs_fyq(d):
        for yr in sorted(_bs_start_fyq.keys(), reverse=True):
            g = _bs_start_fyq[yr]
            s = _dt_fyq2(g[0],g[1],g[2])
            if d >= s:
                days = (d-s).days
                for mi,md in enumerate(_bs_mdays_fyq.get(yr,[])):
                    if days < md: return yr, mi+1
                    days -= md
                return yr+1,1
        return None,None
    by_fyq      = _dd2(list)
    by_fyq_hl   = _dd2(list)
    _fyq_raw = _dd2(list)
    _fyq_hl_raw = _dd2(list)

    # Load raw trading days grouped by FY quarter
    conn2 = sqlite3.connect(db_path)
    conn2.row_factory = sqlite3.Row
    rows2 = conn2.execute(
        "SELECT date, close, high, low FROM stock_prices "
        "WHERE symbol=? AND close>0 ORDER BY date", (symbol,)
    ).fetchall()
    conn2.close()

    for r in rows2:
        try:
            d = _dt_fyq2.fromisoformat(r['date'])
            bs_yr2, bs_m2 = _to_bs_fyq(d)
            if bs_yr2 and bs_m2:
                fyq  = fy_q_map[bs_m2]
                fy   = _fy_label(bs_yr2, bs_m2)
                key  = (fy, fyq)
                _fyq_raw[key].append((r['close'], r['high'], r['low']))
        except: pass

    # DB first and current FY quarter to skip
    from datetime import date as _dt_fyq
    _today_bs2 = _to_bs_fyq(_dt_fyq2.today())
    _curr_fyq_key = (_fy_label(_today_bs2[0], _today_bs2[1]), fy_q_map[_today_bs2[1]])
    _first_bs2 = _to_bs_fyq(_dt_fyq2(2021,5,25))
    _first_fyq_key = (_fy_label(_first_bs2[0], _first_bs2[1]), fy_q_map[_first_bs2[1]])

    for key, entries in sorted(_fyq_raw.items()):
        if len(entries) < 10: continue
        if key == _curr_fyq_key: continue
        if key == _first_fyq_key: continue
        fy, fyq = key
        oc = entries[0][0]; cc = entries[-1][0]
        hh = max(e[1] for e in entries)
        ll = min(e[2] for e in entries if e[2]>0)
        ret   = (cc-oc)/oc*100
        swing = (hh-ll)/ll*100
        up    = (hh-oc)/oc*100
        dn    = (oc-ll)/oc*100
        by_fyq[fyq].append((fy, ret))
        by_fyq_hl[fyq].append((fy, swing, up, dn))

    # Current and next FY quarter
    curr_fyq = fy_q_map[_today_bs2[1]]
    fyq_order = ['FYQ1','FYQ2','FYQ3','FYQ4']
    curr_fyq_idx = fyq_order.index(curr_fyq)
    next_fyq = fyq_order[(curr_fyq_idx+1) % 4]

    fyqtable = Table(show_header=True, header_style='bold cyan', box=None, padding=(0,1))
    fyqtable.add_column('Quarter',      width=22)
    fyqtable.add_column('Avg Ret',      justify='right', width=8)
    fyqtable.add_column('W/T',          justify='center', width=5)
    fyqtable.add_column('Best',         justify='right', width=7)
    fyqtable.add_column('Worst',        justify='right', width=7)
    fyqtable.add_column('Signal',       width=8)
    fyqtable.add_column('Swing(rng)',   justify='center', width=14)
    fyqtable.add_column('Up',           justify='right', width=6)
    fyqtable.add_column('Dn',           justify='right', width=6)

    for fyq in fyq_order:
        rets = by_fyq[fyq]
        if not rets: continue
        avg   = sum(r for _,r in rets)/len(rets)
        wins  = sum(1 for _,r in rets if r>0)
        best  = max(r for _,r in rets)
        worst = min(r for _,r in rets)
        rng   = by_fyq_hl[fyq]
        avg_sw = sum(r[1] for r in rng)/len(rng) if rng else 0
        min_sw = min(r[1] for r in rng) if rng else 0
        max_sw = max(r[1] for r in rng) if rng else 0
        avg_up = sum(r[2] for r in rng)/len(rng) if rng else 0
        avg_dn = sum(r[3] for r in rng)/len(rng) if rng else 0
        col    = 'green' if avg>=2 else 'yellow' if avg>=-1 else 'red'
        sig    = 'STR.BUY' if avg>=5 else 'BUY' if avg>=2 else 'NTRL' if avg>=-1 else 'AVOID' if avg>=-4 else 'STR.AVD'
        marker = ' <-NOW' if fyq==curr_fyq else (' <-NXT' if fyq==next_fyq else '')
        sw_str = f'{avg_sw:.0f}%({min_sw:.0f}-{max_sw:.0f})'
        lim_tag = ' [dim](limited)[/dim]' if len(rets) < 3 else ''
        fyqtable.add_row(
            f'[bold]{fyq}{marker}[/bold]{lim_tag}',
            f'[{col}]{avg:+.1f}%[/{col}]',
            f'[{col}]{wins}/{len(rets)}[/{col}]',
            f'[green]{best:+.1f}%[/green]',
            f'[red]{worst:+.1f}%[/red]',
            f'[{col}]{sig}[/{col}]',
            f'[yellow]{sw_str}[/yellow]',
            f'[green]+{avg_up:.1f}%[/green]',
            f'[red]-{avg_dn:.1f}%[/red]',
        )

    console.print(fyqtable)
    console.print()

    # FYQ Trading Guide
    console.rule('[bold]Nepali FY Quarter Trading Guide[/bold]')
    console.print()
    for fyq in fyq_order:
        rets = by_fyq[fyq]
        if not rets: continue
        avg   = sum(r for _,r in rets)/len(rets)
        wins  = sum(1 for _,r in rets if r>0)
        rng   = by_fyq_hl[fyq]
        avg_up = round(sum(r[2] for r in rng)/len(rng),1) if rng else 0
        avg_dn = round(sum(r[3] for r in rng)/len(rng),1) if rng else 0
        avg_sw = round(sum(r[1] for r in rng)/len(rng),1) if rng else 0
        marker = ' <-- NOW' if fyq==curr_fyq else (' <- NEXT' if fyq==next_fyq else '')
        col    = 'green' if avg>=2 else 'yellow' if avg>=-1 else 'red'
        if avg_up > abs(avg_dn)*2 and avg>=3:
            char = f'Strong rally — up {avg_up:.1f}% dominates'
        elif avg_up > abs(avg_dn)*2 and avg<3:
            char = f'Rally then fade — up {avg_up:.1f}% given back'
        elif abs(avg_dn) > avg_up*1.5:
            char = f'Downside dominated — drops {avg_dn:.1f}%'
        elif avg_sw > 25:
            char = f'Extreme volatility — {avg_sw:.0f}% swing'
        else:
            char = f'Mixed — up {avg_up:.1f}% / dn {avg_dn:.1f}%'
        if avg>=5:   action = f'Deploy capital — strong tailwind +{avg_up:.1f}%'
        elif avg>=2: action = f'Lean bullish. Dip {avg_dn:.1f}% then rally {avg_up:.1f}%.'
        elif avg>=-1:action = f'Neutral — selective only. Up {avg_up:.1f}% vs dn {avg_dn:.1f}%.'
        elif avg>=-4:action = f'Avoid longs. Drops {avg_dn:.1f}%, recovers {avg_up:.1f}%.'
        else:        action = f'Stay cash. Heavy selling {avg_dn:.1f}% down.'
        console.print(f'  [{col}][bold]{fyq}{marker}[/bold]  ({fy_q_labels[fyq]})  avg={avg:+.1f}%  ({wins}/{len(rets)} up)[/{col}]')
        console.print(f'    Character : {char}')
        console.print(f'    Action    : [{col}]{action}[/{col}]')
        console.print()

    console.print('  [dim]Research only. Not financial advice. Paper trade first.[/dim]')
    console.print()


if __name__ == "__main__":
    main()

