lns=open(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).read().splitlines()
hits=[l.strip() for l in lns if chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(97)+chr(108)+chr(112)+chr(104)+chr(97) in l.lower() or chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(115)+chr(116)+chr(111)+chr(99)+chr(107) in l.lower() or chr(100)+chr(101)+chr(102)+chr(32)+chr(105)+chr(110)+chr(105)+chr(116) in l]
for h in hits[:20]: print(h)
