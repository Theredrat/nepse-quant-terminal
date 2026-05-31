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
    sym = symbol.upper()
    if sym in NON_EQUITY_SYMBOLS:
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

def auto_update_watchlist(rs_data, full_fs, db_path, top_n=15):
    """Score every stock on RS + broker accumulation + volume spike, keep top N."""
    import json, sqlite3
    from pathlib import Path

    WATCHLIST_PATH = Path("data/runtime/accounts/account_1/watchlist.json")
    if not WATCHLIST_PATH.exists():
        return

    scores = {}

    # ── Score 1: RS score (normalised 0-40) ──────────────────────────────────
    if rs_data:
        rs_sorted = sorted(rs_data, key=lambda x: x.get("rs_score", 0) or 0, reverse=True)
        total = len(rs_sorted)
        for rank, row in enumerate(rs_sorted, 1):
            sym = row.get("symbol", "")
            if not sym:
                continue
            # top rank = 40 pts, bottom = 0
            scores.setdefault(sym, 0)
            scores[sym] += int((1 - (rank - 1) / max(total, 1)) * 40)

    # ── Score 2: Broker accumulation from today floorsheet (0-40) ────────────
    if full_fs is not None and not full_fs.empty:
        try:
            for sym, grp in full_fs.groupby("symbol"):
                buy_val  = grp[grp["buyerMemberId"].notna()]["contractAmount"].sum()
                sell_val = grp[grp["sellerMemberId"].notna()]["contractAmount"].sum()
                total_val = buy_val + sell_val
                if total_val > 0:
                    net_ratio = (buy_val - sell_val) / total_val  # -1 to +1
                    scores.setdefault(sym, 0)
                    if net_ratio > 0:
                        scores[sym] += int(net_ratio * 40)
        except Exception:
            pass

    # ── Score 3: Volume spike vs DB average (0-20) ───────────────────────────
    if full_fs is not None and not full_fs.empty and db_path and Path(db_path).exists():
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cur  = conn.cursor()
            # today volume per symbol from floorsheet
            today_vol = full_fs.groupby("symbol")["contractQuantity"].sum().to_dict()
            for sym, vol in today_vol.items():
                try:
                    cur.execute(
                        "SELECT AVG(v) FROM (SELECT SUM(quantity) as v FROM broker_activity "
                        "WHERE symbol=? GROUP BY date ORDER BY date DESC LIMIT 20)",
                        (sym,)
                    )
                    row = cur.fetchone()
                    avg_vol = row[0] if row and row[0] else 0
                    if avg_vol > 0 and vol > avg_vol * 1.5:
                        spike_score = min(int(((vol / avg_vol) - 1) * 10), 20)
                        scores.setdefault(sym, 0)
                        scores[sym] += spike_score
                except Exception:
                    pass
            conn.close()
        except Exception:
            pass

    # ── Pick top N ────────────────────────────────────────────────────────────
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top    = [sym for sym, sc in ranked if sc > 0][:top_n]

    if not top:
        return

    # ── Write watchlist ───────────────────────────────────────────────────────
    watchlist = [
        {"kind": "stock", "key": f"stock:{sym}", "label": sym, "symbol": sym}
        for sym in top
    ]
    WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    json.dump(watchlist, open(WATCHLIST_PATH, "w", encoding="utf-8"), indent=2)
    print(f"Watchlist auto-updated — top {len(top)} stocks by RS + accumulation + volume")
    if top:
        print(f"  Top picks: {', '.join(top[:5])}{'...' if len(top) > 5 else ''}")


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
        return "Strong uptrend  ↑↑", "bold green"
    elif avg > 0.5:
        return "Heating up      ↑",  "green"
    elif avg > -0.5:
        return "Neutral         →",  "dim white"
    elif avg > -2.0:
        return "Cooling down    ↓",  "red"
    else:
        return "Strong downtrend ↓↓","bold red"


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
    console.print()
    console.print(Rule("[bold green]Watchlist[/bold green]", style="green"))
    console.print()

    if live_df is None or live_df.empty:
        console.print("[red]No live data.[/red]")
        return

    t = Table(title="Your Watchlist — Live Status", box=box.ROUNDED, border_style="green", header_style="bold green")
    t.add_column("Symbol",   width=10, style="bold white")
    t.add_column("LTP",      width=13, justify="right", no_wrap=True)
    t.add_column("Change",   width=10, justify="right", no_wrap=True)
    t.add_column("Volume",   width=10, justify="right")
    t.add_column("Turnover", width=14, justify="right", style="yellow")
    t.add_column("52W High", width=12, justify="right", style="dim")
    t.add_column("52W Low",  width=11, justify="right", style="dim")
    t.add_column("Status",   width=25)

    # Fetch 52W high/low from DB for watchlist symbols
    import sqlite3 as _sq
    _conn = _sq.connect('nepse_market_data.db')
    _w52 = {}
    for _sym in WATCHLIST:
        try:
            _cur = _conn.execute(
                "SELECT MAX(high), MIN(low) FROM stock_prices WHERE symbol=? AND date >= date('now','-365 days')",
                (_sym,)
            )
            _row = _cur.fetchone()
            _w52[_sym] = {'high': _row[0] or 0, 'low': _row[1] or 0}
        except:
            _w52[_sym] = {'high': 0, 'low': 0}
    _conn.close()

    for sym in WATCHLIST:
        row = live_df[live_df['symbol'].str.upper() == sym.upper()]
        if row.empty:
            t.add_row(
                str(rank),
                str(rank + 1),sym, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "[dim]Not trading[/dim]")
            continue
        r       = row.iloc[0]
        ltp     = r.get('ltp', 0)
        chg     = r.get('change_pct', 0)
        high52  = _w52.get(sym, {}).get('high', 0)
        low52   = _w52.get(sym, {}).get('low', 0)

        status = "[dim]Normal[/dim]"
        if pd.notna(high52) and high52 > 0 and pd.notna(ltp):
            dist_high = (high52 - ltp) / high52 * 100
            dist_low  = (ltp - low52) / low52 * 100 if pd.notna(low52) and low52 > 0 else 100
            if dist_high <= 3:   status = "[green]Near 52W High[/green]"
            elif dist_low <= 5 and chg > 0: status = "[cyan]Bouncing off Low[/cyan]"
            elif chg >= 5:       status = "[green]Strong Gainer[/green]"
            elif chg <= -3:      status = "[red]Dropping — check floor[/red]"

        t.add_row(
            sym,
            f"Rs {ltp:,.2f}" if pd.notna(ltp) else "N/A",
            color_change(chg),
            fmt_vol(r.get('volume',0)),
            fmt_rs(r.get('turnover',0)),
            f"Rs {high52:,.0f}" if pd.notna(high52) and high52 else "N/A",
            f"Rs {low52:,.0f}"  if pd.notna(low52)  and low52  else "N/A",
            status,
        )
    console.print(t)
    console.print("[dim]Edit WATCHLIST at the top of nepse_scanner.py to add/remove stocks[/dim]")

# ── DAILY REPORT ──────────────────────────────────────────────────────────────

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
        for item in turnover_list[:8]:
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
        bdf = pd.DataFrame(bdata).sort_values('net_qty', ascending=False)

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

def analyze_quick_pick(live_df, top_n=10):
    console.print()
    console.print(Rule("[bold green]Quick Stock Pick[/bold green]", style="green"))
    console.print("[dim]Best stocks for 10%+ gain in 7 days to 1 month — signals only[/dim]\n")

    if live_df is None or live_df.empty:
        console.print("[red]No live data.[/red]")
        return []

    df = live_df.copy()
    df = df[df['ltp'].notna() & df['volume'].notna() & (df['ltp'] > 0)].copy()

    scores = []
    vol_median   = df['volume'].median()
    turn_median  = df['turnover'].median() if 'turnover' in df.columns else 0

    for _, row in df.iterrows():
        sym    = row.get('symbol','')
        ltp    = row.get('ltp', 0)
        chg    = row.get('change_pct', 0) or 0
        vol    = row.get('volume', 0) or 0
        turn   = row.get('turnover', 0) or 0
        h52    = row.get('week52_high', 0) or 0
        l52    = row.get('week52_low', 0) or 0
        high   = row.get('high', 0) or 0
        low    = row.get('low', 0) or 0

        score  = 0
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

        # 2. Volume surge (max 25 pts)
        if vol_median > 0:
            vol_ratio = vol / vol_median
            if vol_ratio >= 5:
                score += 25; reasons.append(f"Vol {vol_ratio:.1f}x surge")
            elif vol_ratio >= 3:
                score += 20; reasons.append(f"Vol {vol_ratio:.1f}x high")
            elif vol_ratio >= 2:
                score += 12; reasons.append(f"Vol {vol_ratio:.1f}x above avg")

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
                score -= 5  # deep discount, risky

        # 4. Liquidity (max 15 pts)
        if turn_median > 0:
            turn_ratio = turn / turn_median
            if turn_ratio >= 3:
                score += 15; reasons.append("Very liquid")
            elif turn_ratio >= 1.5:
                score += 10; reasons.append("Good liquidity")
            elif turn_ratio < 0.3:
                score -= 10; reasons.append("Low liquidity")

        # 5. Day range tightness = consolidation (max 15 pts)
        if high > 0 and low > 0 and ltp > 0:
            rng_pct = (high - low) / ltp * 100
            if rng_pct <= 1.5 and chg > 0:
                score += 15; reasons.append("Tight range breakout")
            elif rng_pct <= 3 and chg > 0:
                score += 8; reasons.append("Controlled move")

        # Filter: must have positive momentum and decent score
        if chg <= 0 or score < 30:
            continue

        # Estimate gain potential
        if h52 > 0 and ltp > 0:
            upside = (h52 - ltp) / ltp * 100
        else:
            upside = chg * 4  # rough estimate

        scores.append({
            'symbol':   sym,
            'score':    min(score, 100),
            'ltp':      ltp,
            'change':   chg,
            'volume':   vol,
            'upside':   round(upside, 1),
            'reasons':  ' | '.join(reasons[:3]),
        })

    if not scores:
        console.print("[yellow]No quick pick candidates today.[/yellow]")
        return []

    scores = sorted(scores, key=lambda x: x['score'], reverse=True)

    t = Table(title="Quick Pick — Top Candidates (10%+ Potential)",
              box=box.ROUNDED, border_style="green", header_style="bold green")
    t.add_column("#",        width=3,  justify="right", style="dim")
    t.add_column("Symbol",   width=10, style="bold white")
    t.add_column("LTP",      width=13, justify="right", no_wrap=True)
    t.add_column("Today",    width=10, justify="right", no_wrap=True)
    t.add_column("Upside",   width=10, justify="right", style="cyan")
    t.add_column("Score",    width=8,  justify="right", style="magenta")
    t.add_column("Confidence", width=14)
    t.add_column("Why",      min_width=30, style="dim white")

    for i, r in enumerate(scores[:top_n], 1):
        sc = r['score']
        if sc >= 80:
            conf = "[green]HIGH[/green]"
        elif sc >= 60:
            conf = "[yellow]MODERATE[/yellow]"
        else:
            conf = "[dim]LOW[/dim]"

        upside_s = f"[green]+{r['upside']:.1f}%[/green]" if r['upside'] >= 10 else f"[yellow]+{r['upside']:.1f}%[/yellow]"

        t.add_row(
            str(i),
            r['symbol'],
            f"Rs {r['ltp']:,.2f}",
            color_change(r['change']),
            upside_s,
            f"{sc}/100",
            conf,
            r['reasons'],
        )

    console.print(t)
    console.print(Panel(
        "[dim]Upside = distance to 52W high. Score = combined technical strength.\n"
        "HIGH confidence = multiple signals aligning. Always verify before trading.[/dim]",
        border_style="dim"
    ))
    return scores


# ── SMART PICK ────────────────────────────────────────────────────────────────

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
    p.add_argument('--movers-only', action='store_true')
    p.add_argument('--legend',      action='store_true')
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
    p.add_argument('--broker-holders', metavar='SYMBOL', default=None, help='Top 15 broker holders for a stock')
    return p.parse_args()



# ════════════════════════════════════════════════════════════════════════════
#  PHASE 5 — PORTFOLIO INTELLIGENCE
# ════════════════════════════════════════════════════════════════════════════

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
    console.print("  [red]🔴 Red  > 0.85[/red]  — Move together always    → Avoid holding both, no diversification")
    console.print("  [yellow]🟡 Yellow 0.60-0.85[/yellow] — Move together usually  → Partial diversification, acceptable")
    console.print("  [green]🟢 Green < 0.60[/green]  — Move independently    → Best diversification, hold both")
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
        console.print("  [green]✅ Best pairs to hold together (independent):[/green]")
        for v, p in pairs_green[:5]:
            console.print(f"     {p}  ({v:.2f})")
    else:
        console.print("  [yellow]⚠️  No green pairs in NEPSE — all sectors are correlated[/yellow]")
        console.print("  [yellow]   Best available pairs (lowest correlation):[/yellow]")
        for v, p in pairs_yellow[:5]:
            console.print(f"     [green]{p}  ({v:.2f})[/green]")
    console.print()
    console.print("  [red]❌ Avoid holding together (move in sync):[/red]")
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

    t.add_row("1% Risk / 2×ATR stop",
              str(shares_1pct), f"Rs {cost_1pct:,.0f}", f"{cost_1pct/capital*100:.1f}%")
    t.add_row("2% Risk / 2×ATR stop",
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

def main():
    args = parse_args()

    if args.legend:
        print_legend()
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
    if gainers or losers or turnover:
        print_market_movers(gainers, losers, turnover)
        console.print()

    if args.movers_only:
        return

    # Decide what to fetch
    need_live  = not (args.floor or args.brokers) or any([args.watchlist, args.powersell, args.sector, args.report, args.sr, args.quickpick, args.smartpick])
    need_floor = any([args.floor, args.brokers, args.powersell, args.sector, args.whale, args.sr, args.broker, args.smartpick, getattr(args, 'why', False)])

    live_df = None
    if need_live:
        with console.status("[cyan]Fetching live market data...[/cyan]"):
            live_df = get_live_market(n)
        if live_df is not None:
            console.print(f"[dim]Loaded {len(live_df)} securities.[/dim]\n")

    full_fs = None
    if need_floor:
        full_fs = get_full_floorsheet(n)
        try:
            log_broker_activity(full_fs)
        except Exception:
            pass

    # Run requested features
    if args.watchlist:
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
        analyze_quick_pick(live_df)
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
        if rs5 >= -1:  return "[dim]–   Inline[/]"
        return "[red]▼   Lagging[/]"

    tbl = Table(
        title="Top Outperformers (Stock Return − Sector Avg)",
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
    # Prefer broker names over IDs
    if 'buyerBrokerName' in df.columns:
        df['buyer_broker'] = df['buyerBrokerName'].fillna(df.get('buyerMemberId', 'Unknown')).fillna('Unknown')
    elif 'buyerMemberId' in df.columns:
        df['buyer_broker'] = df['buyerMemberId'].fillna('Unknown')
    if 'sellerBrokerName' in df.columns:
        df['seller_broker'] = df['sellerBrokerName'].fillna(df.get('sellerMemberId', 'Unknown')).fillna('Unknown')
    elif 'sellerMemberId' in df.columns:
        df['seller_broker'] = df['sellerMemberId'].fillna('Unknown')
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
        return "[dim]–   Near High[/]"

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




# ══════════════════════════════════════════════════════════════════════════════
#  FUNDAMENTAL ANALYSIS BLOCK  (injected by inject_fundamentals.py)
# ══════════════════════════════════════════════════════════════════════════════

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

    console.print('[dim]Score: PB 40pts + Float 20pts + ROE 20pts + Earnings Growth 20pts. Green ≥65, Yellow ≥45.[/]') # VALUE_SCORE_PATCHED

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


# ══════════════════════════════════════════════════════════════════════════════
# WHY ENGINE — Broker Activity Logger + Story Generator + Why Block
# ══════════════════════════════════════════════════════════════════════════════

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
                    hist_note += " ← FIRST SELL after accumulation (exit alert)"
                elif bstory['history_action'] == 'distributing' and bstory['dominant_action'] == 'buying':
                    hist_note += " ← FIRST BUY after distribution (reversal alert)"
            if bstory.get('five_day_verdict'):
                hist_note += "\n      📊 5D:  " + bstory['five_day_verdict']
            if bstory.get('ten_day_verdict'):
                hist_note += "\n      ⭐ 10D: " + bstory['ten_day_verdict']
            if bstory.get('twenty_day_verdict'):
                hist_note += "\n      🏆 20D: " + bstory['twenty_day_verdict']

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
            'SELECT broker_id, broker_name, '
            'SUM(buy_val) as total_buy, SUM(sell_val) as total_sell, '
            'SUM(net_val) as total_net, COUNT(DISTINCT date) as days_active, '
            'SUM(buy_qty) as total_buy_qty, SUM(sell_qty) as total_sell_qty '
            'FROM broker_activity WHERE symbol=? '
            'GROUP BY broker_id, broker_name '
            'ORDER BY total_net DESC',
            (symbol,)
        ).fetchall()
        conn.close()
        results = []
        for bid, bname, tbuy, tsell, tnet, days, bqty, sqty in rows:
            tbuy = float(tbuy or 0)
            tsell = float(tsell or 0)
            bqty = int(bqty or 0)
            sqty = int(sqty or 0)
            avg_buy = round(tbuy / bqty, 2) if bqty > 0 else 0
            avg_sell = round(tsell / sqty, 2) if sqty > 0 else 0
            results.append(dict(
                broker_id=str(bid),
                broker_name=str(bname or ''),
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
    t.add_column('Broker Name', width=32)
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
            h['broker_name'],
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
        console.print(f"  Top holder: Broker {top['broker_id']} ({top['broker_name']}) — net {'+' if top['total_net']>=0 else ''}{round(top['total_net']/1e6,1)}M over {top['days_active']} days", style='bold')
        console.print()
        # Smart summary for top 3 holders
        console.print("  [bold cyan]── Smart Summary ──[/bold cyan]")
        for h in holders[:3]:
            net = h['total_net']
            net_qty = h.get('net_qty', 0)
            avg_b = h.get('avg_buy_price', 0)
            avg_s = h.get('avg_sell_price', 0)
            days = h['days_active']
            name = h['broker_name']
            bid = h['broker_id']
            amt = ('Rs ' + str(round(abs(net)/1e6, 1)) + 'M') if abs(net) >= 1e6 else ('Rs ' + str(round(abs(net)/1e3)) + 'K')
            qty_str = f'{abs(net_qty):,}'
            if net > 0 and avg_b > 0 and avg_s > 0:
                if avg_b > avg_s:
                    msg = f"Broker {bid} ({name}) bought avg Rs {avg_b:,.1f} and sold avg Rs {avg_s:,.1f} — buying HIGHER than selling, net accumulating {qty_str} shares worth {amt}"
                else:
                    msg = f"Broker {bid} ({name}) bought avg Rs {avg_b:,.1f} and sold avg Rs {avg_s:,.1f} — selling HIGHER than buying, collecting profit while accumulating {qty_str} net shares ({amt})"
            elif net > 0 and avg_b > 0 and avg_s == 0:
                msg = f"Broker {bid} ({name}) only BUYING — no sells, accumulating {qty_str} shares at avg Rs {avg_b:,.1f} ({amt} invested)"
            elif net < 0 and avg_b > 0 and avg_s > 0:
                if avg_s > avg_b:
                    msg = f"Broker {bid} ({name}) bought avg Rs {avg_b:,.1f} and sold avg Rs {avg_s:,.1f} — selling HIGHER than buying, distributing {qty_str} shares at profit"
                else:
                    msg = f"Broker {bid} ({name}) bought avg Rs {avg_b:,.1f} and sold avg Rs {avg_s:,.1f} — selling LOWER than buying, exiting position at loss ({amt} distributed)"
            elif net < 0 and avg_s > 0 and avg_b == 0:
                msg = f"Broker {bid} ({name}) only SELLING — no buys, distributing {qty_str} shares at avg Rs {avg_s:,.1f} ({amt} out)"
            else:
                msg = f"Broker {bid} ({name}) — net {'+' if net>=0 else ''}{amt} over {days} days"
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
                "SELECT broker_id, broker_name, net_val FROM broker_activity WHERE symbol=? AND date=? ORDER BY net_val DESC",
                (symbol, date_str)
            ).fetchall()
            if not rows: continue
            smb = [r for r in rows if r[2] > 0]
            sms = [r for r in rows if r[2] < 0]
            ssn = len(rows); snb = len(smb)
            sbp = snb / ssn * 100 if ssn else 0
            whale_buyers, whale_sellers = _get_dynamic_whales()
            ss = 50
            if sbp > 65: ss += 20
            elif sbp > 50: ss += 10
            else: ss -= 10
            for r2 in rows:
                if r2[0] in whale_buyers: ss = min(100, ss + 8)
                elif r2[0] in whale_sellers: ss = max(0, ss - 8)
            buyer_name = f"{smb[0][0]} {smb[0][1][:18]} {_fmt_rs_val(abs(smb[0][2]))}" if smb else "—"
            seller_name = f"{sms[0][0]} {sms[0][1][:18]} {_fmt_rs_val(abs(sms[0][2]))}" if sms else "—"
            ssv = "BULL" if ss >= 70 else "BEAR" if ss <= 30 else "MIX"
            ssc = "green" if ss >= 70 else "red" if ss <= 30 else "yellow"
            net_flow = sum(r[2] for r in rows if r[2] > 0)


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
                console.print("  ↗ Smart money sentiment improving", style="green")
            elif score_history[-1] < score_history[0]:
                console.print("  ↘ Smart money sentiment deteriorating", style="red")
            else:
                console.print("  → Sentiment flat over period", style="yellow")
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
            SELECT broker_id, broker_name,
                COUNT(DISTINCT symbol) as stocks_traded,
                COUNT(*) as total_appearances,
                SUM(CASE WHEN net_val > 0 THEN 1 ELSE 0 END) as buy_days,
                SUM(CASE WHEN net_val < 0 THEN 1 ELSE 0 END) as sell_days,
                SUM(CASE WHEN net_val > 0 THEN net_val ELSE 0 END) as total_bought,
                SUM(CASE WHEN net_val < 0 THEN ABS(net_val) ELSE 0 END) as total_sold,
                AVG(ABS(net_val)) as avg_trade_size
            FROM broker_activity
            WHERE date IN ({})
            GROUP BY broker_id, broker_name
            ORDER BY avg_trade_size DESC
        """.format(",".join(["?"]*len(dates))), dates).fetchall()
        conn.close()
        if not rows:
            console.print("  No broker data found.", style="yellow"); return
        # Score each broker: avg_trade_size * stocks_traded * appearances
        scored = []
        for r in rows:
            bid, bname, stocks, apps, bdays, sdays, tbought, tsold, avg_size = r
            impact = (avg_size / 1000000) * (stocks ** 0.5) * (apps ** 0.3)
            net = tbought - tsold
            bias = "BUYER" if tbought > tsold * 1.2 else "SELLER" if tsold > tbought * 1.2 else "NEUTRAL"
            scored.append((bid, bname, stocks, apps, bdays, sdays, tbought, tsold, avg_size, impact, bias, net))
        scored.sort(key=lambda x: x[9], reverse=True)
        scored = scored[:top_n]
        t = Table(show_header=True, header_style="bold cyan", box=None, padding=(0,2))
        t.add_column("#", width=3, justify="right")
        t.add_column("Broker", width=6, justify="right")
        t.add_column("Name", width=28)
        t.add_column("Stocks", width=7, justify="right")
        t.add_column("Appear", width=7, justify="right")
        t.add_column("Avg Size", width=12, justify="right")
        t.add_column("Total Bought", width=14, justify="right")
        t.add_column("Total Sold", width=14, justify="right")
        t.add_column("Bias", width=10, justify="center")
        for rank, r in enumerate(scored, 1):
            bid, bname, stocks, apps, bdays, sdays, tbought, tsold, avg_size, impact, bias, net = r
            bc = "green" if bias == "BUYER" else "red" if bias == "SELLER" else "yellow"
            t.add_row(
                str(rank), str(bid), bname[:28],
                str(stocks), str(apps),
                _fmt_rs_val(avg_size),
                _fmt_rs_val(tbought),
                _fmt_rs_val(tsold),
                f"[{bc}]{bias}[/{bc}]"
            )
        console.print(t)
        console.print()
        console.print("[bold]Top 5 Institutional Buyers:[/bold]")
        buyers = [r for r in scored if r[10] == "BUYER"][:5]
        for r in buyers:
            console.print(f"  [green]Broker {r[0]} ({r[1][:25]}) - avg {_fmt_rs_val(r[8])} per trade, {r[2]} stocks[/green]")
        console.print()
        console.print("[bold]Top 5 Institutional Sellers:[/bold]")
        sellers = [r for r in scored if r[10] == "SELLER"][:5]
        for r in sellers:
            console.print(f"  [red]Broker {r[0]} ({r[1][:25]}) - avg {_fmt_rs_val(r[8])} per trade, {r[2]} stocks[/red]")
        console.print()
    except Exception as e:
        console.print(f"  Error: {e}", style="red")

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
            'SELECT broker_id, broker_name, buy_qty, sell_qty, net_qty, buy_val, sell_val, net_val '
            'FROM broker_activity WHERE symbol=? AND date=? '
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
    t.add_column('Broker Name', width=35)
    t.add_column('Net Position', width=14, justify='right')
    t.add_column('Net Shares', width=12, justify='right')
    t.add_column('Avg Price', width=12, justify='right')
    t.add_column('Total Bought', width=14, justify='right')
    t.add_column('Total Sold', width=14, justify='right')
    total_buy_val = 0
    total_sell_val = 0
    buyers = 0
    sellers = 0
    for i, (bid, bname, bq, sq, nq, bv, sv, nv) in enumerate(rows, 1):
        net_style = 'green' if nv >= 0 else 'red'
        net_str = ('+' if nv >= 0 else '-') + _fmt(nv)
        nq_str = ('+' if nq >= 0 else '') + f'{nq:,}'
        total_vol = bq + sq
        avg_price = round((bv + sv) / total_vol, 1) if total_vol > 0 else 0
        avg_str = f'Rs {avg_price:,.1f}' if avg_price > 0 else '-'
        t.add_row(str(i), str(bid), str(bname or ''),
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
    lw = {'34':'Vision Sec','41':'Linch Stock','52':'Sundhara Sec','58':'Naasa Sec'}
    smb = [r for r in rows if r[7] > 0]
    sms = [r for r in rows if r[7] < 0]
    smtb = max(smb, key=lambda x: x[7]) if smb else None
    smts = min(sms, key=lambda x: x[7]) if sms else None
    smst = sum(abs(r[7]) for r in sms)
    ssn = len(rows); snb = len(smb); sns = len(sms)
    sbp = snb / ssn * 100 if ssn else 0
    console.print()
    console.print('  [bold yellow]Whale Activity:[/bold yellow]')
    swf = False
    for r in rows:
        bid = str(r[0])
        if bid in lw:
            swf = True
            sa = 'BUYING' if r[7] > 0 else 'SELLING'
            sc2 = 'green' if r[7] > 0 else 'red'
            sv = _fmt_rs_val(abs(r[7]))
            sd = ' <- DOMINANT SELLER' if smts and r[0] == smts[0] and r[7] < 0 else ''
            console.print(f'     [{sc2}]Broker {bid} ({lw[bid]}) - {sa} {sv}{sd}[/{sc2}]')
    if smts and str(smts[0]) not in lw:
        sv2 = _fmt_rs_val(abs(smts[7]))
        bid2 = str(smts[0]); bnm2 = smts[1]
        console.print(f'     [red]Broker {bid2} ({bnm2}) - SELLING {sv2} <- DOMINANT SELLER[/red]')
    if smtb and str(smtb[0]) not in lw:
        sv3 = _fmt_rs_val(smtb[7])
        bid3 = str(smtb[0]); bnm3 = smtb[1]
        console.print(f'     [green]Broker {bid3} ({bnm3}) - BUYING {sv3} <- DOMINANT BUYER[/green]')
    if not swf: console.print('     [dim]No tracked whales active today[/dim]')
    ss = 50
    if sbp > 65: ss += 20
    elif sbp > 50: ss += 10
    else: ss -= 10
    if smts:
        sp2 = abs(smts[7]) / smst * 100 if smst else 0
        if sp2 > 60: ss -= 20
        elif sp2 > 40: ss -= 10
    for r in rows:
        if str(r[0]) in lw:
            ss += 10 if r[7] > 0 else -10
    ss = max(0, min(100, ss))
    ssv,ssc = ('BULLISH','green') if ss>=70 else ('MIXED','yellow') if ss>=50 else ('BEARISH','red')
    console.print()
    console.print(f'  [bold]Smart Money Score: [{ssc}]{ss}/100 ({ssv})[/{ssc}][/bold]')
    console.print(f'     + {snb} brokers buying ({sbp:.0f}% of participants)')
    console.print(f'     - {sns} brokers selling')
    if smts:
        sp2 = abs(smts[7]) / smst * 100 if smst else 0
        if sp2 > 40:
            sv4 = _fmt_rs_val(abs(smts[7]))
            bid4 = str(smts[0])
            console.print(f'     - 1 dominant seller (Broker {bid4}) - {sv4} ({sp2:.0f}% of all selling)')
    if net_flow > 10000: console.print(f'     + Net flow: [green]INFLOW {_fmt_rs_val(abs(net_flow))}[/green]')
    elif net_flow < -10000: console.print(f'     - Net flow: [red]OUTFLOW {_fmt_rs_val(abs(net_flow))}[/red]')
    else: console.print('     ~ Net flow: [yellow]NEUTRAL[/yellow]')
    console.print()
    if smts:
        sp2 = abs(smts[7]) / smst * 100 if smst else 0
        if sp2 > 50 and sbp > 60:
            bid5 = str(smts[0])
            console.print(f'  [bold yellow]WARNING:[/bold yellow] Large single seller (Broker {bid5}) offsetting all buying - possible distribution')
    if ss >= 70: console.print('  [bold green]SIGNAL:[/bold green] Strong smart money accumulation - watch for breakout')
    elif ss <= 30: console.print('  [bold red]SIGNAL:[/bold red] Smart money distributing - consider reducing exposure')
    console.print()
    if smts:
        sp2 = abs(smts[7]) / smst * 100 if smst else 0
        if sp2 > 50 and sbp > 60:
            bid5 = str(smts[0])
            console.print(f'  [bold yellow]WARNING:[/bold yellow] Large single seller (Broker {bid5}) offsetting all buying - possible distribution')
    if ss >= 70: console.print('  [bold green]SIGNAL:[/bold green] Strong smart money accumulation - watch for breakout')
    elif ss <= 30: console.print('  [bold red]SIGNAL:[/bold red] Smart money distributing - consider reducing exposure')
    console.print()
    console.print(f'  [{flow_col}]{flow_dir}: {_fmt(abs(net_flow))}[/{flow_col}]')
    console.print()


if __name__ == "__main__":
    main()