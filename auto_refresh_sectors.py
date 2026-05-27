"""
Auto-refresh companies table and sector map.
- Runs silently on every launch_nepse.bat startup
- Only hits NEPSE API if data is older than 7 days
- Auto-regenerates sectors.py if new companies are found
- Prints a one-line status message only
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

DB_PATH     = "nepse_market_data.db"
SECTORS_PY  = "backend/quant_pro/sectors.py"
SCANNER_PY  = "nepse_scanner.py"
REFRESH_DAYS = 7  # refresh once per week

def get_last_refresh(conn):
    """Get the last time companies table was refreshed."""
    cur = conn.cursor()
    try:
        cur.execute("SELECT MAX(rowid) FROM companies")
        # Use a metadata table if available
        cur.execute("""
            CREATE TABLE IF NOT EXISTS refresh_log (
                table_name TEXT PRIMARY KEY,
                last_refresh TEXT
            )
        """)
        cur.execute("SELECT last_refresh FROM refresh_log WHERE table_name='companies'")
        row = cur.fetchone()
        if row and row[0]:
            return datetime.fromisoformat(row[0])
    except Exception:
        pass
    return None

def set_last_refresh(conn):
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO refresh_log (table_name, last_refresh)
        VALUES ('companies', ?)
    """, (datetime.now().isoformat(),))
    conn.commit()

def fetch_companies():
    """Fetch active equity companies from NEPSE."""
    from nepse import Nepse
    client = Nepse()
    client.setTLSVerification(False)
    companies = client.getCompanyList()
    return [c for c in companies
            if c.get('instrumentType') == 'Equity'
            and c.get('status') == 'A']

def save_companies(conn, equity):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            symbol    TEXT PRIMARY KEY,
            name      TEXT,
            sector    TEXT,
            status    TEXT,
            regulator TEXT
        )
    """)
    new_count = 0
    for c in equity:
        sym = c.get('symbol')
        if not sym:
            continue
        cur.execute("SELECT symbol FROM companies WHERE symbol=?", (sym,))
        exists = cur.fetchone()
        cur.execute("INSERT OR REPLACE INTO companies VALUES (?,?,?,?,?)", (
            sym,
            c.get('companyName'),
            c.get('sectorName') or 'Unknown',
            c.get('status'),
            c.get('regulatoryBody'),
        ))
        if not exists:
            new_count += 1
    conn.commit()
    return new_count

def regenerate_sectors_py(conn):
    """Regenerate backend/quant_pro/sectors.py from DB."""
    cur = conn.cursor()
    cur.execute("SELECT symbol, sector FROM companies ORDER BY sector, symbol")
    rows = cur.fetchall()

    NAME_MAP = {
        "Hydro Power":                  "Hydropower",
        "Commercial Banks":             "Commercial Banks",
        "Development Banks":            "Development Banks",
        "Finance":                      "Finance",
        "Microfinance":                 "Microfinance",
        "Life Insurance":               "Life Insurance",
        "Non Life Insurance":           "Non-Life Insurance",
        "Manufacturing And Processing": "Manufacturing & Processing",
        "Hotels And Tourism":           "Hotels & Tourism",
        "Investment":                   "Investment",
        "Tradings":                     "Trading",
        "Others":                       "Others",
    }

    groups = defaultdict(list)
    for symbol, sector in rows:
        code_name = NAME_MAP.get(sector, sector)
        groups[code_name].append(symbol)

    cur.execute("SELECT sector, COUNT(*) FROM companies GROUP BY sector")
    listed_counts = {r[0]: r[1] for r in cur.fetchall()}
    listed_by_code = {NAME_MAP.get(k, k): v for k, v in listed_counts.items()}

    sector_order = [
        "Commercial Banks", "Development Banks", "Finance", "Hydropower",
        "Life Insurance", "Non-Life Insurance", "Microfinance",
        "Manufacturing & Processing", "Hotels & Tourism",
        "Investment", "Trading", "Others",
    ]

    lines = [
        '"""\n',
        f'Sector group mappings — auto-generated {datetime.now().strftime("%Y-%m-%d")}.\n',
        '"""\n',
        'SECTOR_GROUPS = {\n',
    ]
    for sector in sector_order:
        syms = sorted(groups.get(sector, []))
        if not syms:
            continue
        lines.append(f'    "{sector}": {{\n')
        for i in range(0, len(syms), 8):
            chunk = syms[i:i+8]
            lines.append('        ' + ', '.join(f'"{s}"' for s in chunk) + ',\n')
        lines.append('    },\n')
    lines += [
        '}\n',
        'SECTOR_LOOKUP = {\n',
        '    symbol: sector\n',
        '    for sector, members in SECTOR_GROUPS.items()\n',
        '    for symbol in members\n',
        '}\n',
        '__all__ = ["SECTOR_GROUPS", "SECTOR_LOOKUP"]\n',
    ]

    with open(SECTORS_PY, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return groups, listed_by_code

def patch_scanner_sector_map(groups, listed_by_code, non_equity):
    """Update SECTOR_MAP and SECTOR_LISTED in nepse_scanner.py."""
    import re

    sector_order = [
        "Commercial Banks", "Development Banks", "Finance", "Hydropower",
        "Life Insurance", "Non-Life Insurance", "Microfinance", "Manufacturing",
        "Hotels", "Investment", "Trading", "Others",
    ]

    # Scanner uses shorter names — map from sectors.py names
    short_map = {
        "Manufacturing & Processing": "Manufacturing",
        "Hotels & Tourism":           "Hotels",
    }

    lines = []
    lines.append("# ── SECTOR MAP (auto-generated from nepse_market_data.db) ───────────────────\n")
    lines.append("SECTOR_MAP = {\n")
    for sector in sector_order:
        full = {v: k for k, v in short_map.items()}.get(sector, sector)
        syms = sorted(groups.get(full, groups.get(sector, [])))
        if not syms:
            continue
        lines.append(f'    "{sector}": [\n')
        for i in range(0, len(syms), 8):
            chunk = syms[i:i+8]
            lines.append('        ' + ', '.join(f'"{s}"' for s in chunk) + ',\n')
        lines.append('    ],\n')
    lines.append('}\n\n')

    lines.append("# Total listed equity stocks per sector\n")
    lines.append("SECTOR_LISTED = {\n")
    for sector in sector_order:
        full = {v: k for k, v in short_map.items()}.get(sector, sector)
        count = listed_by_code.get(full, listed_by_code.get(sector, 0))
        if count:
            lines.append(f'    "{sector}": {count},\n')
    lines.append('}\n\n')

    ne_sorted = sorted(non_equity)
    lines.append("# Non-equity symbols to exclude from sector rotation\n")
    lines.append("NON_EQUITY_SYMBOLS = {\n")
    for i in range(0, len(ne_sorted), 6):
        chunk = ne_sorted[i:i+6]
        lines.append('    ' + ', '.join(f'"{s}"' for s in chunk) + ',\n')
    lines.append('}\n\n')

    lines.append("def get_sector(symbol):\n")
    lines.append('    """Return sector for a symbol, or None if non-equity."""\n')
    lines.append("    sym = symbol.upper()\n")
    lines.append("    if sym in NON_EQUITY_SYMBOLS:\n")
    lines.append("        return None\n")
    lines.append("    for sector, symbols in SECTOR_MAP.items():\n")
    lines.append("        if sym in symbols:\n")
    lines.append("            return sector\n")
    lines.append('    return "Others"\n\n')

    new_block = "".join(lines)

    with open(SCANNER_PY, encoding='utf-8') as f:
        content = f.read()

    old_block = re.search(
        r"# ── SECTOR MAP.*?def get_sector\(symbol\):.*?return \"Others\"\n",
        content, re.DOTALL
    )
    if old_block:
        content = content[:old_block.start()] + new_block + content[old_block.end():]
        with open(SCANNER_PY, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    conn = sqlite3.connect(DB_PATH)

    last = get_last_refresh(conn)
    now  = datetime.now()

    if last and (now - last) < timedelta(days=REFRESH_DAYS):
        days_ago = (now - last).days
        print(f"  [sectors] Up to date (last refresh: {days_ago}d ago)")
        conn.close()
        return

    # Needs refresh
    print("  [sectors] Refreshing company list from NEPSE...", end=" ", flush=True)
    try:
        equity = fetch_companies()
    except Exception as e:
        print(f"FAILED ({e}) — using cached data")
        conn.close()
        return

    old_count_cur = conn.cursor()
    old_count_cur.execute("SELECT COUNT(*) FROM companies")
    old_count = old_count_cur.fetchone()[0]

    new_count = save_companies(conn, equity)
    total     = len(equity)

    # Get non-equity symbols
    cur = conn.cursor()
    cur.execute("SELECT symbol FROM non_equity_securities")
    non_equity = {r[0] for r in cur.fetchall()}

    # Regenerate sectors.py
    groups, listed_by_code = regenerate_sectors_py(conn)

    # Patch nepse_scanner.py
    patch_scanner_sector_map(groups, listed_by_code, non_equity)

    set_last_refresh(conn)
    conn.close()

    if new_count > 0:
        print(f"UPDATED — {new_count} new stocks added ({total} total)")
    else:
        print(f"OK — {total} companies, no changes")

if __name__ == "__main__":
    # Change to project root if needed
    script_dir = Path(__file__).parent
    if (script_dir / "nepse_market_data.db").exists():
        os.chdir(script_dir)
    main()
