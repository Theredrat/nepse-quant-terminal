import os
gi=chr(46)+chr(103)+chr(105)+chr(116)+chr(105)+chr(103)+chr(110)+chr(111)+chr(114)+chr(101)
txt=open(gi,encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).read() if os.path.exists(gi) else chr(32)
if chr(95)+chr(105)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116)+chr(95)+chr(108)+chr(111)+chr(103) in txt:
    print(chr(65)+chr(108)+chr(114)+chr(101)+chr(97)+chr(100)+chr(121)+chr(32)+chr(105)+chr(110)+chr(32)+chr(103)+chr(105)+chr(116)+chr(105)+chr(103)+chr(110)+chr(111)+chr(114)+chr(101))
else:
    open(gi,chr(97),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).write(chr(10)+chr(95)+chr(105)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116)+chr(95)+chr(108)+chr(111)+chr(103)+chr(46)+chr(106)+chr(115)+chr(111)+chr(110)+chr(10))
    print(chr(65)+chr(100)+chr(100)+chr(101)+chr(100)+chr(32)+chr(116)+chr(111)+chr(32)+chr(103)+chr(105)+chr(116)+chr(105)+chr(103)+chr(110)+chr(111)+chr(114)+chr(101))
