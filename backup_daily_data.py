import os, shutil
from datetime import datetime

src = 'daily_data'
backup_dir = 'backups/daily_data'
os.makedirs(backup_dir, exist_ok=True)

# Copy all JSON files
copied = 0
for f in os.listdir(src):
    if f.endswith('.json'):
        src_path = os.path.join(src, f)
        dst_path = os.path.join(backup_dir, f)
        if not os.path.exists(dst_path):
            shutil.copy2(src_path, dst_path)
            copied += 1
        
print(f'Backed up {copied} new files to {backup_dir}')
print(f'Total files in backup: {len(os.listdir(backup_dir))}')
