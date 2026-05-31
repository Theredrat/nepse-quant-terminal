"""
patch_auto_watchlist.py
Injects auto_update_watchlist() into nepse_scanner.py and wires it
to run at the end of every scan (--rs, full scan, smart pick, etc.)

Criteria:
  1. High RS score (outperforming sector)
  2. Broker accumulation detected (dominant broker net buying)
  3. Strong volume spike

Top 15 stocks selected. Replaces watchlist fully each run.
"""

import re, shutil, ast
from pathlib import Path
from datetime import datetime

SCANNER = Path("nepse_scanner.py")
BACKUP  = Path(f"nepse_scanner_pre_auto_watchlist.py")

# ── The function to inject ────────────────────────────────────────────────────
NEW_FUNC = '''
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

'''

# ── Wire point: call auto_update_watchlist after broker logger ────────────────
WIRE_ANCHOR = "Broker activity saved"
WIRE_CALL   = "\n    # Auto-update watchlist with top RS + accumulation + volume stocks\n    auto_update_watchlist(rs_data if 'rs_data' in dir() else [], full_fs, db_path)\n"

def patch():
    src = SCANNER.read_text(encoding="utf-8")

    # backup
    shutil.copy(SCANNER, BACKUP)
    print(f"Backup created → {BACKUP.name}")

    # check not already patched
    if "auto_update_watchlist" in src:
        print("Already patched — skipping")
        return

    # inject function before 'def analyze_rs' or similar anchor
    anchor = "\ndef analyze_"
    idx = src.find(anchor)
    if idx == -1:
        anchor = "\ndef _print_why"
        idx = src.find(anchor)
    if idx == -1:
        print("ERROR: injection anchor not found")
        return

    src = src[:idx] + NEW_FUNC + src[idx:]
    print("auto_update_watchlist() function injected")

    # wire call — find log_broker_activity call site and add after it
    # look for the print line that contains "Broker activity saved"
    wire_idx = src.find('"Broker activity saved')
    if wire_idx == -1:
        wire_idx = src.find("'Broker activity saved")
    if wire_idx != -1:
        # find end of that print statement line
        line_end = src.find("\n", wire_idx)
        src = src[:line_end] + "\n    auto_update_watchlist(rs_data if 'rs_data' in locals() else [], full_fs, db_path)" + src[line_end:]
        print("Wire call inserted after broker logger")
    else:
        print("WARNING: wire anchor not found — function exists but not auto-called")
        print("  You can call auto_update_watchlist() manually after any scan")

    # syntax check
    try:
        ast.parse(src)
        print("Syntax OK")
    except SyntaxError as e:
        print(f"SYNTAX ERROR: {e} — restoring backup")
        shutil.copy(BACKUP, SCANNER)
        return

    SCANNER.write_text(src, encoding="utf-8")
    print("patch_auto_watchlist.py — DONE")
    print()
    print("From now on, every scan automatically updates your watchlist with")
    print("Top 15 stocks ranked by: RS score + broker accumulation + volume spike")

if __name__ == "__main__":
    patch()
