import shutil
from pathlib import Path

here = Path('.')

# Files to move to _archive (patch/fix/check scripts)
TO_ARCHIVE = [
    'build_broker_logger.py',
    'check_data.py',
    'fix_broker_logger.py',
    'fix_broker_story_dict.py',
    'fix_verdict_wire.py',
    'fix_watchlist_wire.py',
    'health_check.py',
    'patch_all_verdicts.py',
    'patch_auto_watchlist.py',
    'patch_broker_history_timeframes.py',
    'patch_broker_story.py',
    'patch_tui_news.py',
]

# Files to move to _backups (scanner backups)
TO_BACKUPS = [
    'nepse_scanner_pre_all_verdicts.py',
    'nepse_scanner_pre_auto_watchlist.py',
    'nepse_scanner_pre_broker_logger.py',
    'nepse_scanner_pre_broker_story.py',
    'nepse_scanner_pre_story_dict.py',
    'nepse_scanner_pre_timeframes.py',
    'nepse_scanner_pre_wire.py',
]

# Files to move to _data
TO_DATA = [
    'signals_cache_2026-05-29.json',
]

for folder, files in [('_archive', TO_ARCHIVE), ('_backups', TO_BACKUPS), ('_data', TO_DATA)]:
    d = here / folder
    d.mkdir(exist_ok=True)
    for name in files:
        src = here / name
        if src.exists():
            shutil.move(str(src), str(d / name))
            print(f'  {folder}/  {name}')

print()
print('=== ROOT FILES REMAINING ===')
for f in sorted(here.iterdir()):
    if f.is_file():
        print(f'  {f.name}')
print()
for folder in ['_backups', '_data', '_archive']:
    p = here / folder
    if p.exists():
        print(f'  {folder}/  ({len(list(p.iterdir()))} files)')
