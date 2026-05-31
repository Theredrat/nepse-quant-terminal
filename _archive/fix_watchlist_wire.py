"""
fix_watchlist_wire.py - wires auto_update_watchlist after broker logger print
"""
import ast, shutil
from pathlib import Path

SCANNER = Path("nepse_scanner.py")
BACKUP  = Path("nepse_scanner_pre_watchlist_wire.py")

OLD = "            f'[{total_rows:,} total rows, {distinct_dates} trading days in history]'\n        )"

NEW = "            f'[{total_rows:,} total rows, {distinct_dates} trading days in history]'\n        )\n        auto_update_watchlist(rs_data if 'rs_data' in locals() else [], full_fs, db_path)"

def patch():
    src = SCANNER.read_text(encoding="utf-8")

    if OLD not in src:
        print("ERROR: exact anchor not found — no changes made")
        return

    if src.count(OLD) > 1:
        print("ERROR: anchor appears more than once — unsafe, aborting")
        return

    if "auto_update_watchlist" not in src:
        print("ERROR: auto_update_watchlist function missing — run patch_auto_watchlist.py first")
        return

    # Check wire not already there
    if "auto_update_watchlist(rs_data" in src:
        print("Already wired — nothing to do")
        return

    new_src = src.replace(OLD, NEW)

    try:
        ast.parse(new_src)
    except SyntaxError as e:
        print(f"SYNTAX ERROR: {e} — aborting, no changes made")
        return

    shutil.copy(SCANNER, BACKUP)
    print(f"Backup created -> {BACKUP.name}")
    SCANNER.write_text(new_src, encoding="utf-8")
    print("Wire connected safely")
    print("Syntax OK — all existing functions untouched")
    print()
    print("Every scan now auto-updates watchlist with top 15 stocks.")

if __name__ == "__main__":
    patch()
