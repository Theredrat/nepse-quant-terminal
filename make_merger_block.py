with open('fix_merger_block.py', 'w', encoding='utf-8') as f:
    f.write(
'with open(\'nepse_scanner.py\', \'r\', encoding=\'utf-8\') as f:\n'
'    content = f.read()\n'
'\n'
'old = \'    # Filter non-equity\n    equity = []\n    for r in stocks:\n        sym = r[0]\'\n'
'new = \'    # Merger-formed companies — not genuine IPOs\n    MERGER_EXCLUDE = {\n        \'\'\'MATRI\'\'\', \'\'\'SMPDA\'\'\', \'\'\'RBCL\'\'\', \'\'\'SICL\'\'\', \'\'\'NLG\'\'\', \'\'\'CORBL\'\'\'\n    }\n\n    # Filter non-equity\n    equity = []\n    for r in stocks:\n        sym = r[0]\n        if sym in MERGER_EXCLUDE: continue\'\n'
'\n'
'if old in content:\n'
'    content = content.replace(old, new, 1)\n'
'    print("OK")\n'
'else:\n'
'    print("NOT FOUND")\n'
'    idx = content.find("Filter non-equity")\n'
'    print(repr(content[idx-20:idx+100]))\n'
'\n'
'with open(\'nepse_scanner.py\', \'w\', encoding=\'utf-8\') as f:\n'
'    f.write(content)\n'
)
