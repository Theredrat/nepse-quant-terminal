"""
smart_scraper.py - Smart parallel quarterly earnings scraper for NEPSE.
- Filters equity stocks only (excludes debentures/bonds)
- Skips stocks already up to date for current quarter
- Parallel scraping (5 threads) for speed
- Shows live progress
"""
import re, sqlite3, sys, os, logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from earnings_scraper import (
    scrape_symbol_earnings, upsert_quarterly_earnings,
    upsert_fundamentals_snapshots, create_quarterly_earnings_table,
    create_fundamentals_table, _load_sharesansar_company_map,
    _new_session, _get_db_path,
)

DEBENTURE_PATTERN = re.compile(r'(D\d{2,}|\d{2,}$|LD\d|BD\d|PO$)', re.IGNORECASE)

def is_equity(symbol):
    if DEBENTURE_PATTERN.search(symbol): return False
    if re.search(r'\d+P$', symbol): return False
    return True

def get_equity_symbols(db_path):
    conn = sqlite3.connect(db_path)
    latest = conn.execute("SELECT MAX(date) FROM stock_prices").fetchone()[0]
    rows = conn.execute("SELECT DISTINCT symbol FROM stock_prices WHERE date=? ORDER BY symbol", (latest,)).fetchall()
    conn.close()
    all_syms = [r[0] for r in rows]
    equity = [s for s in all_syms if is_equity(s)]
    print(f"  Total: {len(all_syms)} | Equity: {len(equity)} | Filtered: {len(all_syms)-len(equity)}")
    return equity

def get_latest_quarter(db_path):
    """Get latest valid quarter (1-4 only) and fiscal year."""
    conn = sqlite3.connect(db_path)
    row = conn.execute("""
        SELECT fiscal_year, MAX(quarter) 
        FROM quarterly_earnings 
        WHERE eps IS NOT NULL 
        AND quarter BETWEEN 1 AND 4
        AND fiscal_year = (
            SELECT fiscal_year FROM quarterly_earnings 
            WHERE eps IS NOT NULL AND quarter BETWEEN 1 AND 4
            ORDER BY fiscal_year DESC LIMIT 1
        )
    """).fetchone()
    conn.close()
    return (row[0], row[1]) if row else ("082-083", 3)

def get_symbols_needing_update(db_path, symbols, fy, q):
    conn = sqlite3.connect(db_path)
    existing = set(r[0] for r in conn.execute(
        "SELECT DISTINCT symbol FROM quarterly_earnings WHERE fiscal_year=? AND quarter=? AND eps IS NOT NULL",
        (fy, q)
    ).fetchall())
    conn.close()
    return [s for s in symbols if s not in existing]

def scrape_worker(args):
    symbol, db_path = args
    try:
        session = _new_session()
        rows = scrape_symbol_earnings(symbol, session=session, db_path=db_path)
        if rows:
            inserted = upsert_quarterly_earnings(db_path, rows)
            upsert_fundamentals_snapshots(db_path, rows)
            return symbol, inserted, None
        return symbol, 0, None
    except Exception as e:
        return symbol, 0, str(e)

def main():
    db_path = _get_db_path()
    create_quarterly_earnings_table(db_path)
    create_fundamentals_table(db_path)

    print("\n╔══════════════════════════════════════╗")
    print("║  NEPSE Smart Quarterly Scraper        ║")
    print("╚══════════════════════════════════════╝\n")

    print("► Loading equity symbols...")
    symbols = get_equity_symbols(db_path)

    print("► Checking current quarter...")
    fy, q = get_latest_quarter(db_path)
    print(f"  Latest valid quarter in DB: FY {fy} Q{q}")

    print("► Finding symbols needing update...")
    to_scrape = get_symbols_needing_update(db_path, symbols, fy, q)
    print(f"  Up to date: {len(symbols)-len(to_scrape)} | Need scraping: {len(to_scrape)}")

    if not to_scrape:
        print(f"\n✅ All stocks up to date for FY {fy} Q{q}!\n")
        return

    est = max(1, len(to_scrape) * 2 // 5)
    print(f"\n► Scraping {len(to_scrape)} symbols with 5 threads (~{est} min)...\n")

    stats = {"scraped": 0, "rows": 0, "errors": 0, "empty": 0}
    errors = []
    done = 0

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scrape_worker, (sym, db_path)): sym for sym in to_scrape}
        for future in as_completed(futures):
            symbol, rows, error = future.result()
            done += 1
            pct = int(done / len(to_scrape) * 100)
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            if error:
                stats["errors"] += 1
                errors.append(f"{symbol}: {error}")
                status = "✗ ERROR"
            elif rows > 0:
                stats["scraped"] += 1
                stats["rows"] += rows
                status = f"✓ {rows} rows"
            else:
                stats["empty"] += 1
                status = "- no data"
            print(f"  [{bar}] {pct:3d}% | {done:3d}/{len(to_scrape)} | {symbol:<12} {status}")

    print(f"\n╔══════════════════════════════════════╗")
    print(f"║  ✓ Scraped:     {stats['scraped']:<22}║")
    print(f"║  - No data:     {stats['empty']:<22}║")
    print(f"║  ✗ Errors:      {stats['errors']:<22}║")
    print(f"║  📊 Rows added: {stats['rows']:<22}║")
    print(f"╚══════════════════════════════════════╝\n")

    if errors:
        print("Errors:")
        for e in errors[:10]:
            print(f"  {e}")

if __name__ == "__main__":
    main()
