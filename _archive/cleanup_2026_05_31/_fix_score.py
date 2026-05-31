import ast
src=open(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).read()
old=chr(32)*8+chr(123)+chr(34)+chr(107)+chr(105)+chr(110)+chr(100)+chr(34)+chr(58)+chr(32)+chr(34)+chr(115)+chr(116)+chr(111)+chr(99)+chr(107)+chr(34)+chr(44)+chr(32)+chr(34)+chr(107)+chr(101)+chr(121)+chr(34)+chr(58)+chr(32)+chr(102)+chr(34)+chr(115)+chr(116)+chr(111)+chr(99)+chr(107)+chr(58)+chr(123)+chr(115)+chr(121)+chr(109)+chr(125)+chr(34)+chr(44)+chr(32)+chr(34)+chr(108)+chr(97)+chr(98)+chr(101)+chr(108)+chr(34)+chr(58)+chr(32)+chr(115)+chr(121)+chr(109)+chr(44)+chr(32)+chr(34)+chr(115)+chr(121)+chr(109)+chr(98)+chr(111)+chr(108)+chr(34)+chr(58)+chr(32)+chr(115)+chr(121)+chr(109)+chr(125)
new=old[:-1]+chr(44)+chr(32)+chr(34)+chr(115)+chr(99)+chr(111)+chr(114)+chr(101)+chr(34)+chr(58)+chr(32)+chr(115)+chr(99)+chr(111)+chr(114)+chr(101)+chr(115)+chr(46)+chr(103)+chr(101)+chr(116)+chr(40)+chr(115)+chr(121)+chr(109)+chr(44)+chr(32)+chr(48)+chr(41)+chr(125)
if old in src:
    src=src.replace(old,new)
    try:
        ast.parse(src)
        open(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121),chr(119),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).write(src)
        print(chr(70)+chr(105)+chr(120)+chr(101)+chr(100))
    except SyntaxError as e:
        print(chr(69)+chr(82)+chr(82)+chr(79)+chr(82),e)
else:
    print(chr(78)+chr(79)+chr(84)+chr(32)+chr(70)+chr(79)+chr(85)+chr(78)+chr(68))
    lns=src.splitlines()
    print(repr(lns[349]))
