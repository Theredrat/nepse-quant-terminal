import shutil
shutil.copy2(chr(108)+chr(97)+chr(117)+chr(110)+chr(99)+chr(104)+chr(95)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(46)+chr(98)+chr(97)+chr(116),chr(95)+chr(98)+chr(97)+chr(99)+chr(107)+chr(117)+chr(112)+chr(115)+chr(47)+chr(108)+chr(97)+chr(117)+chr(110)+chr(99)+chr(104)+chr(95)+chr(112)+chr(114)+chr(101)+chr(95)+chr(115)+chr(121)+chr(110)+chr(99)+chr(46)+chr(98)+chr(97)+chr(116))
lns=open(chr(108)+chr(97)+chr(117)+chr(110)+chr(99)+chr(104)+chr(95)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(46)+chr(98)+chr(97)+chr(116),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).read().splitlines()
for i,l in enumerate(lns):
    if chr(112)+chr(121)+chr(116)+chr(104)+chr(111)+chr(110)+chr(32)+chr(95)+chr(98)+chr(97)+chr(99)+chr(107)+chr(117)+chr(112)+chr(46)+chr(112)+chr(121) in l:
        ins=[chr(58)+chr(58)+chr(32)+chr(83)+chr(89)+chr(78)+chr(67)+chr(32)+chr(45)+chr(32)+chr(112)+chr(117)+chr(108)+chr(108)+chr(32)+chr(108)+chr(97)+chr(116)+chr(101)+chr(115)+chr(116)+chr(32)+chr(74)+chr(83)+chr(79)+chr(78)+chr(32)+chr(102)+chr(114)+chr(111)+chr(109)+chr(32)+chr(71)+chr(105)+chr(116)+chr(72)+chr(117)+chr(98), chr(101)+chr(99)+chr(104)+chr(111)+chr(32)+chr(83)+chr(121)+chr(110)+chr(99)+chr(105)+chr(110)+chr(103)+chr(32)+chr(100)+chr(97)+chr(116)+chr(97)+chr(46)+chr(46)+chr(46), chr(112)+chr(121)+chr(116)+chr(104)+chr(111)+chr(110)+chr(32)+chr(95)+chr(115)+chr(121)+chr(110)+chr(99)+chr(95)+chr(100)+chr(97)+chr(116)+chr(97)+chr(46)+chr(112)+chr(121), chr(101)+chr(99)+chr(104)+chr(111)+chr(46)]
        lns=lns[:i+1]+ins+lns[i+1:]
        print(chr(83)+chr(121)+chr(110)+chr(99)+chr(32)+chr(97)+chr(100)+chr(100)+chr(101)+chr(100))
        break
open(chr(108)+chr(97)+chr(117)+chr(110)+chr(99)+chr(104)+chr(95)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(46)+chr(98)+chr(97)+chr(116),chr(119),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).write(chr(10).join(lns))
print(chr(68)+chr(111)+chr(110)+chr(101))
