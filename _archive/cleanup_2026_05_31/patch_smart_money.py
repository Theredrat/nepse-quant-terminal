import shutil, ast, types
shutil.copy(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121), chr(95)+chr(98)+chr(97)+chr(99)+chr(107)+chr(117)+chr(112)+chr(115)+chr(47)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(95)+chr(112)+chr(114)+chr(101)+chr(95)+chr(115)+chr(109)+chr(97)+chr(114)+chr(116)+chr(109)+chr(111)+chr(110)+chr(101)+chr(121)+chr(46)+chr(112)+chr(121))
src = open(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121), encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).read()
lines = src.splitlines()
ins = None
for i,l in enumerate(lines):
    if (chr(78)+chr(69)+chr(84)+chr(32)+chr(73)+chr(78)+chr(70)+chr(76)+chr(79)+chr(87)) in l or (chr(78)+chr(69)+chr(84)+chr(32)+chr(79)+chr(85)+chr(84)+chr(70)+chr(76)+chr(79)+chr(87)) in l:
        if chr(102)+chr(108)+chr(111)+chr(119)+chr(95)+chr(100)+chr(105)+chr(114) in l or chr(102)+chr(108)+chr(111)+chr(119)+chr(95)+chr(99)+chr(111)+chr(108) in l:
            ins = i
            break
print(chr(65)+chr(110)+chr(99)+chr(104)+chr(111)+chr(114)+chr(32)+chr(97)+chr(116)+chr(32)+chr(108)+chr(105)+chr(110)+chr(101)+chr(58), ins)
print(chr(79)+chr(75))
