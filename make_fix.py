with open('fix_unlock_clean.py', 'w', encoding='utf-8') as f:
    f.write("""
with open('nepse_scanner.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = "            unlock_str = f\\"{e['days_left']}d\\" if e['days_left'] >= 0 else 'REG'\\n            unlock_color = 'green' if e['days_left'] > 365 else 'yellow' if e['days_left'] > 90 else 'red'"

new = \"\"\"            if e['days_left'] >= 0:
                unlock_str = f"{e['days_left']}d"
                unlock_color = 'green' if e['days_left'] > 365 else 'yellow' if e['days_left'] > 90 else 'red'
            else:
                unlock_str = 'UNLOCKED'
                unlock_color = 'dim'\"\"\"

if old in content:
    content = content.replace(old, new, 1)
    print("OK")
else:
    print("NOT FOUND")
    # show context
    idx = content.find('unlock_str')
    print(repr(content[idx-20:idx+200]))

with open('nepse_scanner.py', 'w', encoding='utf-8') as f:
    f.write(content)
""")
