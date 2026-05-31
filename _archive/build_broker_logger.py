"""
build_broker_logger.py
Adds broker activity logging to nepse_scanner.py:
  - Creates broker_activity table in DB (if not exists)
  - Adds log_broker_activity() function to scanner
  - Auto-calls it after every floorsheet fetch
  - Keeps 3 years of history, then auto-cleans older records
  - Shows brief confirmation after saving
Run from: C:\Users\HP User\nepse-quant-terminal
"""
import shutil, ast
from pathlib import Path

# ── Backup ──────────────────────────────────────────────────────────────
shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_broker_logger.py')
print('Backup saved: nepse_scanner_pre_broker_logger.py')

content = open('nepse_scanner.py', encoding='utf-8').read()

# ── Step 1: The log_broker_activity() function to append ────────────────
NEW_FUNCTION = '''

# ═══════════════════════════════════════════════════════════════════════
# BROKER ACTIVITY LOGGER
# Saves daily broker-level summary for every stock to DB.
# Keeps 3 years of history. Called automatically after floorsheet fetch.
# ═══════════════════════════════════════════════════════════════════════

def _ensure_broker_activity_table(db_path="nepse_market_data.db"):
    """Create broker_activity table if it does not exist."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS broker_activity (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol        TEXT    NOT NULL,
            date          TEXT    NOT NULL,
            broker_id     TEXT    NOT NULL,
            broker_name   TEXT,
            buy_qty       INTEGER DEFAULT 0,
            sell_qty      INTEGER DEFAULT 0,
            net_qty       INTEGER DEFAULT 0,
            buy_val       REAL    DEFAULT 0.0,
            sell_val      REAL    DEFAULT 0.0,
            net_val       REAL    DEFAULT 0.0,
            UNIQUE(symbol, date, broker_id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ba_symbol_date ON broker_activity(symbol, date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ba_date       ON broker_activity(date)")
    conn.commit()
    conn.close()


def log_broker_activity(fs_df, db_path="nepse_market_data.db"):
    """
    Given today's full floorsheet DataFrame, compute per-stock per-broker
    buy/sell summary and save to broker_activity table.
    Keeps 3 years of history (auto-deletes records older than 3 years).
    Shows brief confirmation after saving.
    """
    try:
        import sqlite3, pandas as pd
        from datetime import date, timedelta

        if fs_df is None or fs_df.empty:
            return

        _ensure_broker_activity_table(db_path)

        # ── Compute per-symbol per-broker summary ──────────────────────
        records = []

        # Buyer side
        buy = fs_df.groupby(['symbol', 'buyer_broker']).agg(
            buy_qty=('quantity', 'sum'),
            buy_val=('amount',   'sum'),
            broker_name=('buyerBrokerName', 'first')
        ).reset_index().rename(columns={'buyer_broker': 'broker_id'})

        # Seller side
        sell = fs_df.groupby(['symbol', 'seller_broker']).agg(
            sell_qty=('quantity', 'sum'),
            sell_val=('amount',   'sum'),
            broker_name_s=('sellerBrokerName', 'first')
        ).reset_index().rename(columns={'seller_broker': 'broker_id'})

        # Merge buy + sell on symbol + broker_id
        merged = pd.merge(
            buy, sell,
            on=['symbol', 'broker_id'],
            how='outer'
        ).fillna(0)

        # Resolve broker name (prefer buy side name, fallback to sell side)
        if 'broker_name' not in merged.columns:
            merged['broker_name'] = ''
        if 'broker_name_s' in merged.columns:
            merged['broker_name'] = merged.apply(
                lambda r: r['broker_name'] if r['broker_name'] not in (0, '', None)
                          else r['broker_name_s'], axis=1
            )

        # Get trading date from floorsheet
        trade_date = str(fs_df['businessDate'].iloc[0])[:10]

        for _, row in merged.iterrows():
            records.append((
                str(row['symbol']),
                trade_date,
                str(int(row['broker_id'])) if str(row['broker_id']).replace('.0','').isdigit()
                    else str(row['broker_id']),
                str(row.get('broker_name', '')) or '',
                int(row.get('buy_qty',  0) or 0),
                int(row.get('sell_qty', 0) or 0),
                int(row.get('buy_qty',  0) or 0) - int(row.get('sell_qty', 0) or 0),
                float(row.get('buy_val',  0) or 0),
                float(row.get('sell_val', 0) or 0),
                float(row.get('buy_val',  0) or 0) - float(row.get('sell_val', 0) or 0),
            ))

        if not records:
            return

        # ── Save to DB ──────────────────────────────────────────────────
        conn = sqlite3.connect(db_path)

        conn.executemany("""
            INSERT INTO broker_activity
                (symbol, date, broker_id, broker_name,
                 buy_qty, sell_qty, net_qty,
                 buy_val, sell_val, net_val)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(symbol, date, broker_id) DO UPDATE SET
                broker_name = excluded.broker_name,
                buy_qty     = excluded.buy_qty,
                sell_qty    = excluded.sell_qty,
                net_qty     = excluded.net_qty,
                buy_val     = excluded.buy_val,
                sell_val    = excluded.sell_val,
                net_val     = excluded.net_val
        """, records)

        # ── Auto-clean records older than 3 years ───────────────────────
        cutoff = (date.today() - timedelta(days=3*365)).strftime('%Y-%m-%d')
        deleted = conn.execute(
            "DELETE FROM broker_activity WHERE date < ?", (cutoff,)
        ).rowcount

        conn.commit()

        # ── Count stats for confirmation message ────────────────────────
        total_rows = conn.execute("SELECT COUNT(*) FROM broker_activity").fetchone()[0]
        distinct_dates = conn.execute(
            "SELECT COUNT(DISTINCT date) FROM broker_activity"
        ).fetchone()[0]
        conn.close()

        stocks_logged = len(merged['symbol'].unique())
        clean_msg = f"  (cleaned {deleted} old records)" if deleted > 0 else ""
        print(f"  Broker activity saved — {stocks_logged} stocks, "
              f"{len(records)} broker rows logged for {trade_date}"
              f"{clean_msg}  [{total_rows:,} total rows, {distinct_dates} trading days in history]")

    except Exception as e:
        # Never crash the scanner due to logging failure
        print(f"  [broker logger] Warning: {e}")
'''

# ── Step 2: Append the function before the main() / if __name__ block ──
insert_marker = '\nif __name__'
if insert_marker in content:
    idx = content.rfind(insert_marker)
    content = content[:idx] + NEW_FUNCTION + content[idx:]
    print('Step 1: log_broker_activity() function appended')
else:
    content = content + NEW_FUNCTION
    print('Step 1: log_broker_activity() function appended (at end)')

# ── Step 3: Wire log_broker_activity() after floorsheet fetch ───────────
# Find where full_fs is assigned from get_full_floorsheet
# Pattern: full_fs = get_full_floorsheet(...)  or similar
import re

# Find the line that calls get_full_floorsheet and assigns to full_fs / live_df
patterns = [
    'full_fs = get_full_floorsheet(',
    'live_df = get_full_floorsheet(',
    'fs = get_full_floorsheet(',
]

wired = False
for pat in patterns:
    idx = content.find(pat)
    if idx != -1:
        # Find end of that statement (next newline)
        line_end = content.find('\n', idx)
        varname  = pat.split('=')[0].strip()   # full_fs / live_df / fs
        inject   = f'\n    log_broker_activity({varname})  # auto-log broker data'
        content  = content[:line_end] + inject + content[line_end:]
        print(f'Step 2: log_broker_activity({varname}) wired after floorsheet fetch')
        wired = True
        break

if not wired:
    # Search more broadly
    matches = [(m.start(), m.group()) for m in
               re.finditer(r'(\w+)\s*=\s*get_full_floorsheet\(', content)]
    if matches:
        idx, match = matches[0]
        varname = match.split('=')[0].strip()
        line_end = content.find('\n', idx)
        inject   = f'\n    log_broker_activity({varname})  # auto-log broker data'
        content  = content[:line_end] + inject + content[line_end:]
        print(f'Step 2: log_broker_activity({varname}) wired (broad match)')
        wired = True

if not wired:
    print('Step 2 WARNING: could not auto-wire — add manually:')
    print('  After the line that calls get_full_floorsheet(), add:')
    print('  log_broker_activity(full_fs)')

# ── Step 4: Save ────────────────────────────────────────────────────────
open('nepse_scanner.py', 'w', encoding='utf-8').write(content)
print('Step 3: nepse_scanner.py saved')

# ── Step 5: Syntax check ────────────────────────────────────────────────
try:
    ast.parse(content)
    print('Step 4: Syntax OK')
except SyntaxError as e:
    print(f'Step 4: SYNTAX ERROR — {e}')
    shutil.copy('nepse_scanner_pre_broker_logger.py', 'nepse_scanner.py')
    print('Backup restored — no changes applied')
    raise SystemExit(1)

# ── Step 6: Create the DB table now so it exists before first run ───────
try:
    import sys
    sys.path.insert(0, '.')
    import types
    src2 = open('nepse_scanner.py', encoding='utf-8').read()
    mod  = types.ModuleType('t')
    exec(compile(src2[:src2.rfind('\nif __name__')],
                 'nepse_scanner.py', 'exec'), mod.__dict__)
    mod._ensure_broker_activity_table()
    print('Step 5: broker_activity table created in DB')
except Exception as e:
    print(f'Step 5 WARNING: table creation: {e}')

print()
print('=' * 60)
print('DONE. Broker activity logger installed.')
print()
print('How it works:')
print('  Every time you run any scan that fetches the floorsheet')
print('  (options 5,6,7,8,9,10,13, or --why), it will automatically')
print('  save broker data for all 270+ stocks silently.')
print()
print('  After saving you will see:')
print('  Broker activity saved — 270 stocks, 2847 broker rows')
print('  logged for 2026-06-03  [2847 total rows, 1 trading days]')
print()
print('  After 5 trading days the Why block will show:')
print('  Broker 34 bought 4 of last 5 days (Rs 127M total)')
print('  TODAY: continuing to buy Rs 18M — no sign of exit')
print()
print('  History: 3 years kept, older records auto-deleted.')
print('=' * 60)
