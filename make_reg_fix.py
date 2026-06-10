with open('fix_reg_class.py', 'w', encoding='utf-8') as f:
    f.write(
'with open(\'nepse_scanner.py\', \'r\', encoding=\'utf-8\') as f:\n'
'    content = f.read()\n'
'\n'
'old = \'        # Skip unlocked non-regulated sectors\\n        is_unlocked = days_left < 0 and sector not in REGULATED_SECTORS\'\n'
'new = \'        # Non-regulated past 3yr go to Section E; regulated stay in Section A\\n        is_unlocked = days_left < 0 and sector not in REGULATED_SECTORS\'\n'
'\n'
'if old in content:\n'
'    content = content.replace(old, new, 1)\n'
'    print("OK")\n'
'else:\n'
'    print("NOT FOUND")\n'
'    idx = content.find("is_unlocked")\n'
'    print(repr(content[idx-50:idx+150]))\n'
'\n'
'with open(\'nepse_scanner.py\', \'w\', encoding=\'utf-8\') as f:\n'
'    f.write(content)\n'
)
