
import os, shutil, datetime

bak_dir = '_backups'
os.makedirs(bak_dir, exist_ok=True)
today = datetime.datetime.now().strftime('%Y-%m-%d')

files = [
    ('nepse_market_data.db', f'db_{today}.db'),
    ('signal_log.json', f'signal_log_{today}.json'),
    ('nepse_scanner.py', f'nepse_scanner_{today}.py'),
    ('launch_nepse.bat', f'launch_{today}.bat'),
    ('dashboard_tui.py', f'dashboard_tui_{today}.py'),
    ('nepse_alerts.py', f'nepse_alerts_{today}.py'),
    ('signal_tracker.py', f'signal_tracker_{today}.py'),
]

for src, dst_name in files:
    if not os.path.exists(src):
        continue
    dst = os.path.join(bak_dir, dst_name)
    if os.path.exists(dst):
        continue
    shutil.copy2(src, dst)

db_baks = sorted([f for f in os.listdir(bak_dir) if f.startswith('db_') and f.endswith('.db')], reverse=True)
for old in db_baks[7:]:
    os.remove(os.path.join(bak_dir, old))
