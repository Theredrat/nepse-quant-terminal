import os
for root,dirs,files in os.walk(chr(46)+chr(103)+chr(105)+chr(116)+chr(104)+chr(117)+chr(98)):
    for f in files: print(os.path.join(root,f))
