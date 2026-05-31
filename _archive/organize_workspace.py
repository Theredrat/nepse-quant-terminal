"""
organize_workspace.py
Moves files into subfolders — NOTHING IS DELETED.
If anything breaks, just move files back from the subfolder.

Run from: C:\Users\HP User\nepse-quant-terminal
"""
import shutil
from pathlib import Path

here = Path('.')

# ── Define exactly what goes where ─────────────────────────────────────

# These stay in root — your working system
KEEP_IN_ROOT = {
    'nepse_scanner.py',          # main scanner
    'launch_nepse.bat',          # menu
    'nepse_market_data.db',      # main database
    'nepse_market_data',         # 0-byte marker file (referenced in scanner)
    'nepse_alerts.py',           # alerts system (referenced in scanner)
    'nepse_alerts.log',          # alerts log
    'signal_tracker.py',         # signal tracker (referenced in scanner)
    'signal_log.json',           # signal log data
    'auto_refresh_sectors.py',   # referenced in scanner
    'dashboard_tui.py',          # dashboard (referenced in scanner)
    'dashboard_tui.tcss',        # dashboard styles
    'dashboard_tui_raw.py',      # dashboard raw version
    'requirements.txt',          # pip install list
    'README.md',                 # documentation
    'Makefile',                  # build commands
    '.env',                      # environment config
    '.env.example',              # env template
    '.gitignore',                # git config
}

# Move to _backups/ — old scanner versions (safe, never needed unless scanner breaks)
TO_BACKUPS = {
    'nepse_scanner_backup_clean.py',
    'nepse_scanner_pre_fix4.py',
    'nepse_scanner_pre_momentum.py',
    'nepse_scanner_pre_rs.py',
    'nepse_scanner_pre_rs_return_fix.py',
    'nepse_scanner_pre_sector_fix.py',
    'nepse_scanner_pre_trend_fix.py',
    'nepse_scanner_pre_validfix.py',
    'nepse_scanner_pre_why.py',
    'nepse_scanner_pre_why_fix.py',
    'nepse_scanner_pre_why_v2.py',
}

# Move to _data/ — CSV, JSON, data files
TO_DATA = {
    'backtest_nav.csv',
    'backtest_trades.csv',
    'signals_cache_2026-05-27.json',
    'signals_cache_2026-05-28.json',
    'signals_cache_2026-05-29.json',
    'nepse_market_data_backup.db',
    'nepse_alerts_ci.py',        # CI version of alerts — not used daily
}

# Move to _archive/ — all one-off dev/debug/fix scripts (safe to never see again)
TO_ARCHIVE = {
    # audit scripts
    'audit_functions.py', 'audit_main.py', 'full_audit.py',
    # check scripts
    'check2.py', 'check3.py', 'check_analyze_rs.py', 'check_broker_tables.py',
    'check_calc_rs_full.py', 'check_calc_rs_infile.py', 'check_end.py',
    'check_end2.py', 'check_floorsheet_structure.py', 'check_fs_live.py',
    'check_line.py', 'check_loadlog.py', 'check_menu.py', 'check_scanner.py',
    'check_sector_names.py', 'check_sector_returns_body.py',
    'check_sector_values.py', 'check_tables.py', 'check_trend_keys.py',
    # debug scripts
    'debug_output.txt', 'debug_rs.py', 'debug_rs_full.py', 'debug_sector.py',
    # find scripts
    'find_menu.py', 'find_rs.py', 'find_rs_arg.py',
    # fix scripts
    'fix4_inline_wording.py', 'fix_blocks.py', 'fix_debug.py',
    'fix_dupcalls.py', 'fix_dupcalls2.py', 'fix_elif.py', 'fix_log.py',
    'fix_pivot_fill.py', 'fix_rs_return.py', 'fix_scanner.py',
    'fix_sector_names.py', 'fix_trend_display.py', 'fix_why_arg.py',
    'fix_why_floor.py', 'fix_why_verdicts.py', 'fix_why_verdicts2.py',
    'revert_valid.py', 'safe_fix.py',
    # inject scripts (already applied to scanner)
    'inject_peer_value.py', 'inject_portfolio.py', 'inject_relative_strength.py',
    'inject_sector_momentum.py', 'inject_value_score.py', 'inject_week52.py',
    # build scripts (already applied)
    'build_why_engine.py',
    # test/verify scripts
    'test_calc_rs.py', 'test_rs_inmodule.py', 'test_sector_returns.py',
    'verify_rs.py',
}

# ── Preview what will happen ────────────────────────────────────────────
print('=' * 65)
print('ORGANIZE WORKSPACE — preview (nothing moved yet)')
print('=' * 65)

all_files = {f.name for f in here.iterdir() if f.is_file()}
accounted = KEEP_IN_ROOT | TO_BACKUPS | TO_DATA | TO_ARCHIVE
unaccounted = all_files - accounted - {'organize_workspace.py'}

print(f'\n ROOT (stays):    {len(KEEP_IN_ROOT & all_files)} files')
print(f' _backups/:       {len(TO_BACKUPS & all_files)} scanner backup versions')
print(f' _data/:          {len(TO_DATA & all_files)} data/csv/json files')
print(f' _archive/:       {len(TO_ARCHIVE & all_files)} dev scripts (safe to archive)')

if unaccounted:
    print(f'\n UNACCOUNTED ({len(unaccounted)} files — will NOT be touched):')
    for name in sorted(unaccounted):
        print(f'   {name}')

print()
print('Root will contain:')
for name in sorted(KEEP_IN_ROOT):
    if (here / name).exists():
        print(f'  {name}')

print()
confirm = input('Type YES to organize, anything else to cancel: ').strip()

if confirm != 'YES':
    print('Cancelled — nothing moved.')
    raise SystemExit

# ── Create folders and move ─────────────────────────────────────────────
moved = {'_backups': 0, '_data': 0, '_archive': 0}
errors = []

for folder, fileset in [('_backups', TO_BACKUPS), ('_data', TO_DATA), ('_archive', TO_ARCHIVE)]:
    dest_dir = here / folder
    dest_dir.mkdir(exist_ok=True)
    for name in fileset:
        src = here / name
        if src.exists():
            try:
                shutil.move(str(src), str(dest_dir / name))
                moved[folder] += 1
            except Exception as e:
                errors.append(f'{name}: {e}')

print(f'\nMoved to _backups/:  {moved["_backups"]} files')
print(f'Moved to _data/:     {moved["_data"]} files')
print(f'Moved to _archive/:  {moved["_archive"]} files')

if errors:
    print('\nErrors:')
    for e in errors:
        print(f'  {e}')

print('\nDone. Your root folder now contains only essential files.')
print('All moved files are safe in subfolders — nothing deleted.')
print()
print('To restore any file:  copy _archive\\filename.py .')
print('To restore scanner:   copy _backups\\nepse_scanner_pre_fix4.py nepse_scanner.py')
