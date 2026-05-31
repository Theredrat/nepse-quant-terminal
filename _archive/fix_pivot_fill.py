content = open('nepse_scanner.py', encoding='utf-8').read()

# Fix: fill price gaps before computing returns so more stocks contribute
old = '''        sec_piv  = pivot[[s for s in syms if s in pivot.columns]].dropna(how="all")
        if sec_piv.empty:
            continue'''

new = '''        sec_piv  = pivot[[s for s in syms if s in pivot.columns]].dropna(how="all")
        sec_piv  = sec_piv.ffill().bfill()  # fill gaps so more stocks contribute
        if sec_piv.empty:
            continue'''

if old in content:
    content = content.replace(old, new)
    print('Fix applied: added ffill/bfill to sector pivot')
    open('nepse_scanner.py', 'w', encoding='utf-8').write(content)
else:
    print('ERROR: target not found - no changes made')
