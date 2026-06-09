"""
auto_daily.py — NEPSE Auto Daily Scanner
Runs every trading day at 4 PM via Windows Task Scheduler

Sequence:
  1. Sync latest data (_sync_data.py)
  2. Run --quickpick       (option 4)
  3. Run --smartpick       (option 5)
  4. Run --momentum-hunter (option 17f)
  5. Run --deployment-planner (option 41, Sundays only)
  6. Update signal_tracker results
  7. Save log to logs/auto_daily.log
"""

import subprocess
import sys
import os
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
PYTHON    = sys.executable
SCANNER   = os.path.join(BASE_DIR, 'nepse_scanner.py')
SYNC      = os.path.join(BASE_DIR, '_sync_data.py')
TRACKER   = os.path.join(BASE_DIR, 'signal_tracker.py')
LOG_DIR   = os.path.join(BASE_DIR, 'logs')
LOG_FILE  = os.path.join(LOG_DIR, 'auto_daily.log')

os.makedirs(LOG_DIR, exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────
def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

# ── Run a command silently, return (success, output) ─────────────────────────
def run(label, args, timeout=120):
    log(f"START  {label}")
    try:
        r = subprocess.run(
            [PYTHON] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=BASE_DIR,
            encoding='utf-8',
            errors='replace'
        )
        # Log last 3 lines of output as summary
        out_lines = [l for l in (r.stdout + r.stderr).encode('ascii', errors='replace').decode('ascii').splitlines() if l.strip()]
        summary = ' | '.join(out_lines[-3:]) if out_lines else '(no output)'
        if r.returncode == 0:
            log(f"OK     {label} — {summary}")
            return True
        else:
            log(f"FAIL   {label} — returncode={r.returncode} — {summary}")
            return False
    except subprocess.TimeoutExpired:
        log(f"TIMEOUT {label} after {timeout}s")
        return False
    except Exception as e:
        log(f"ERROR  {label} — {e}")
        return False

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    now      = datetime.now()
    weekday  = now.weekday()  # 0=Mon, 6=Sun
    is_sunday = weekday == 6

    log("=" * 55)
    log(f"NEPSE Auto Daily — {now.strftime('%A %Y-%m-%d %H:%M')}")
    log("=" * 55)

    # NEPSE trading days: Sun-Thu (weekday 6,0,1,2,3)
    trading_days = {0, 1, 2, 3, 6}
    if weekday not in trading_days:
        log("Not a trading day (Friday/Saturday) — skipping.")
        return

    # Step 1: Sync data
    ok = run("Sync data", [SYNC])
    if not ok:
        log("WARNING: Sync failed — continuing with existing data")

    # Step 0: Backup DB to OneDrive
    import shutil as _sh, datetime as _dt
    _bk_dir = os.path.join(r"C:\Users\HP User\OneDrive", "NEPSE_Backup")
    os.makedirs(_bk_dir, exist_ok=True)
    _bk_file = os.path.join(_bk_dir, "nepse_market_data_" + _dt.date.today().isoformat() + ".db")
    try:
        _sh.copy2(os.path.join(BASE_DIR, "nepse_market_data.db"), _bk_file)
        log("Backup OK -> " + _bk_file)
    except Exception as _e:
        log("Backup WARN: " + str(_e))

    # Step 1a: Fetch fresh prices from Merolagani into data DB
    import subprocess as _sp, os as _os
    _ing_env = _os.environ.copy()
    _ing_env["PYTHONPATH"] = BASE_DIR
    _ing = _sp.run(
        [PYTHON, _os.path.join(BASE_DIR, "scripts", "ingestion", "deterministic_daily_ingestion.py"),
         "--source", "db", "--backfill-days", "7", "--max-staleness-days", "3"],
        capture_output=True, text=True, timeout=1800,
        cwd=BASE_DIR, env=_ing_env, encoding="utf-8", errors="replace"
    )
    log("Price ingestion: " + ("OK" if _ing.returncode == 0 else "FAIL") + " rc=" + str(_ing.returncode))
    if _ing.stdout: log(_ing.stdout.strip()[-300:])
    if _ing.stderr and _ing.returncode != 0: log(_ing.stderr.strip()[-300:])

    # Step 1b: Sync data DB to root DB
    DBSYNC = os.path.join(BASE_DIR, "db_sync.py")
    run("DB Sync (data -> root)", [DBSYNC])


    # Step 2: Quick Pick (option 4)
    run("Quick Pick (option 4)", [SCANNER, '--quickpick', '--offline'])

    # Step 3: Smart Pick (option 5)
    run("Smart Pick (option 5)", [SCANNER, '--smartpick', '--offline'])

    # Step 4: Momentum Hunter (option 17f)
    run("Momentum Hunter (option 17f)", [SCANNER, '--momentum-hunter'])

    # Step 4b: Broker RS (option 7b) — updates watchlist with confirmed setups
    run("Broker RS (option 7b)", [SCANNER, "--broker-rs"])

    # Step 5: Deployment Planner (option 41) — Sundays only
    if is_sunday:
        run("Deployment Planner (option 41) [Sunday]", [SCANNER, '--deployment-planner', '--offline'])
    else:
        log("SKIP   Deployment Planner (runs Sundays only)")

    # Step 6: Update signal tracker results
    run("Signal tracker update", [TRACKER, '--update'])

    log("=" * 55)
    log("Auto daily complete.")
    log("=" * 55)

if __name__ == '__main__':
    main()

