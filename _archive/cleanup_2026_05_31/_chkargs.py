lns=open(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).read().splitlines()
args=[l for l in lns if chr(97)+chr(100)+chr(100)+chr(95)+chr(97)+chr(114)+chr(103)+chr(117)+chr(109)+chr(101)+chr(110)+chr(116) in l]
for l in args: print(l)
