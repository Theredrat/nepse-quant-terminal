with open('fix_reg_section.py', 'w', encoding='utf-8') as f:
    f.write(
'with open(\'nepse_scanner.py\', \'r\', encoding=\'utf-8\') as f:\n'
'    content = f.read()\n'
'\n'
'old = \'        # Non-regulated past 3yr go to Section E; regulated stay in Section A\\n        is_unlocked = days_left < 0 and sector not in REGULATED_SECTORS\'\n'
'new = \'        # All unlocked stocks go to Section E regardless of sector\\n        is_unlocked = days_left < 0\'\n'
'\n'
'if old in content:\n'
'    content = content.replace(old, new, 1)\n'
'    print("OK")\n'
'else:\n'
'    print("NOT FOUND")\n'
'\n'
'with open(\'nepse_scanner.py\', \'w\', encoding=\'utf-8\') as f:\n'
'    f.write(content)\n'
)
