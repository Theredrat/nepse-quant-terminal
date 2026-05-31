with open('dashboard_tui.py', encoding='utf-8') as f:
    src = f.read()

old = '                open("sig_debug.txt","w").write(str(list(sigs[0].keys())) + "\\n" + str(sigs[0]))\n                '
new = '                '

if old in src:
    src = src.replace(old, new)
    open('dashboard_tui.py', 'w', encoding='utf-8').write(src)
    print('Cleaned!')
else:
    print('Pattern not found')
