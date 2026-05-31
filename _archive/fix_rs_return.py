import shutil
shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_rs_return_fix.py')
print('Backup saved')

lines = open('nepse_scanner.py', encoding='utf-8').readlines()

old = '    rdf["rs_score"] = rdf["rs5"]*0.50 + rdf["rs10"].fillna(0)*0.30 + rdf["rs20"].fillna(0)*0.20\n'
new = ('    rdf["rs_score"] = rdf["rs5"]*0.50 + rdf["rs10"].fillna(0)*0.30 + rdf["rs20"].fillna(0)*0.20\n'
       '\n'
       '    return rdf.sort_values("rs_score", ascending=False).to_dict("records")\n')

fixed = 0
out = []
for i, l in enumerate(lines, 1):
    if l == old and fixed == 0:
        out.append(new)
        fixed += 1
        print(f'Fixed line {i}: added return statement')
    else:
        out.append(l)

if fixed == 0:
    print('ERROR: target line not found - no changes made')
else:
    open('nepse_scanner.py', 'w', encoding='utf-8').write(''.join(out))
    print('Done. Only 1 line added.')
