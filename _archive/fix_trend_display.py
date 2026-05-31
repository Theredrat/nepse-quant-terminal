import shutil
shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_trend_fix.py')
print('Backup saved')

content = open('nepse_scanner.py', encoding='utf-8').read()

# Fix 1: sector trend table - add show_header=True and fix column separator
# The table is missing the Sector column header row separator
# Change box=box.ROUNDED to box=box.SIMPLE_HEAD so column headers show properly
old1 = '''    t = Table(
        title="Sector Momentum (Equal-Weighted)",
        box=box.ROUNDED, border_style="cyan", header_style="bold cyan",
    )
    t.add_column("Sector",   min_width=22, style="bold white")'''

new1 = '''    t = Table(
        title="Sector Momentum (Equal-Weighted)",
        box=box.SIMPLE_HEAVY, border_style="cyan", header_style="bold cyan",
        show_header=True,
    )
    t.add_column("Sector",   min_width=22, no_wrap=True, style="bold white")'''

if old1 in content:
    content = content.replace(old1, new1)
    print('Fix 1 applied: table style and no_wrap')
else:
    print('Fix 1: target not found - skipping')

# Fix 2: Hydropower/Hotel/Manufacturing N/A - reduce valid stock minimum from 2 to 1
old2 = '            if valid.sum() < 2:'
new2 = '            if valid.sum() < 1:'

if old2 in content:
    content = content.replace(old2, new2)
    print('Fix 2 applied: valid stock minimum 2->1')
else:
    print('Fix 2: target not found - skipping')

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)
print('Done.')
