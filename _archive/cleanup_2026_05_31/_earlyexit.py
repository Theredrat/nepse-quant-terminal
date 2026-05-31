import ast, shutil
shutil.copy2(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121),chr(95)+chr(98)+chr(97)+chr(99)+chr(107)+chr(117)+chr(112)+chr(115)+chr(47)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(95)+chr(112)+chr(114)+chr(101)+chr(95)+chr(101)+chr(97)+chr(114)+chr(108)+chr(121)+chr(101)+chr(120)+chr(105)+chr(116)+chr(46)+chr(112)+chr(121))
lns=open(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).read().splitlines()
# Find insertion point - after earnings early exit, before console.print NEPSE Scanner Starting
ins_idx=None
for i,l in enumerate(lns):
    if chr(103)+chr(101)+chr(116)+chr(97)+chr(116)+chr(116)+chr(114) in l and chr(101)+chr(97)+chr(114)+chr(110)+chr(105)+chr(110)+chr(103)+chr(115) in l:
        for j in range(i,min(len(lns),i+4)):
            if lns[j].strip()==chr(114)+chr(101)+chr(116)+chr(117)+chr(114)+chr(110):
                ins_idx=j+1
                break
        break
if ins_idx is None:
    print(chr(69)+chr(82)+chr(82)+chr(79)+chr(82)+chr(58)+chr(32)+chr(99)+chr(111)+chr(117)+chr(108)+chr(100)+chr(32)+chr(110)+chr(111)+chr(116)+chr(32)+chr(102)+chr(105)+chr(110)+chr(100)+chr(32)+chr(105)+chr(110)+chr(115)+chr(101)+chr(114)+chr(116)+chr(105)+chr(111)+chr(110)+chr(32)+chr(112)+chr(111)+chr(105)+chr(110)+chr(116))
    exit(1)
print(chr(73)+chr(110)+chr(115)+chr(101)+chr(114)+chr(116)+chr(105)+chr(110)+chr(103)+chr(32)+chr(97)+chr(116)+chr(32)+chr(108)+chr(105)+chr(110)+chr(101),ins_idx)
block=[
    chr(32)*4+chr(105)+chr(102)+chr(32)+chr(103)+chr(101)+chr(116)+chr(97)+chr(116)+chr(116)+chr(114)+chr(40)+chr(97)+chr(114)+chr(103)+chr(115)+chr(44)+chr(32)+chr(39)+chr(109)+chr(111)+chr(109)+chr(101)+chr(110)+chr(116)+chr(117)+chr(109)+chr(95)+chr(104)+chr(117)+chr(110)+chr(116)+chr(101)+chr(114)+chr(39)+chr(44)+chr(32)+chr(70)+chr(97)+chr(108)+chr(115)+chr(101)+chr(41)+chr(58),
    chr(32)*8+chr(97)+chr(110)+chr(97)+chr(108)+chr(121)+chr(122)+chr(101)+chr(95)+chr(109)+chr(111)+chr(109)+chr(101)+chr(110)+chr(116)+chr(117)+chr(109)+chr(95)+chr(104)+chr(117)+chr(110)+chr(116)+chr(101)+chr(114)+chr(40)+chr(41),
    chr(32)*8+chr(114)+chr(101)+chr(116)+chr(117)+chr(114)+chr(110),
    chr(32)*4+chr(105)+chr(102)+chr(32)+chr(103)+chr(101)+chr(116)+chr(97)+chr(116)+chr(116)+chr(114)+chr(40)+chr(97)+chr(114)+chr(103)+chr(115)+chr(44)+chr(32)+chr(39)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(105)+chr(109)+chr(112)+chr(97)+chr(99)+chr(116)+chr(39)+chr(44)+chr(32)+chr(70)+chr(97)+chr(108)+chr(115)+chr(101)+chr(41)+chr(58),
    chr(32)*8+chr(97)+chr(110)+chr(97)+chr(108)+chr(121)+chr(122)+chr(101)+chr(95)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(105)+chr(109)+chr(112)+chr(97)+chr(99)+chr(116)+chr(40)+chr(41),
    chr(32)*8+chr(114)+chr(101)+chr(116)+chr(117)+chr(114)+chr(110),
    chr(32)*4+chr(105)+chr(102)+chr(32)+chr(103)+chr(101)+chr(116)+chr(97)+chr(116)+chr(116)+chr(114)+chr(40)+chr(97)+chr(114)+chr(103)+chr(115)+chr(44)+chr(32)+chr(39)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(116)+chr(114)+chr(101)+chr(110)+chr(100)+chr(39)+chr(44)+chr(32)+chr(78)+chr(111)+chr(110)+chr(101)+chr(41)+chr(58),
    chr(32)*8+chr(97)+chr(110)+chr(97)+chr(108)+chr(121)+chr(122)+chr(101)+chr(95)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(116)+chr(114)+chr(101)+chr(110)+chr(100)+chr(40)+chr(97)+chr(114)+chr(103)+chr(115)+chr(46)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(116)+chr(114)+chr(101)+chr(110)+chr(100)+chr(41),
    chr(32)*8+chr(114)+chr(101)+chr(116)+chr(117)+chr(114)+chr(110),
    chr(32)*4+chr(105)+chr(102)+chr(32)+chr(103)+chr(101)+chr(116)+chr(97)+chr(116)+chr(116)+chr(114)+chr(40)+chr(97)+chr(114)+chr(103)+chr(115)+chr(44)+chr(32)+chr(39)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(100)+chr(97)+chr(116)+chr(101)+chr(39)+chr(44)+chr(32)+chr(78)+chr(111)+chr(110)+chr(101)+chr(41)+chr(58),
    chr(32)*8+chr(97)+chr(110)+chr(97)+chr(108)+chr(121)+chr(122)+chr(101)+chr(95)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(100)+chr(97)+chr(116)+chr(101)+chr(40)+chr(97)+chr(114)+chr(103)+chr(115)+chr(46)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(100)+chr(97)+chr(116)+chr(101)+chr(91)+chr(48)+chr(93)+chr(44)+chr(97)+chr(114)+chr(103)+chr(115)+chr(46)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(100)+chr(97)+chr(116)+chr(101)+chr(91)+chr(49)+chr(93)+chr(41),
    chr(32)*8+chr(114)+chr(101)+chr(116)+chr(117)+chr(114)+chr(110),
    chr(32)*4+chr(105)+chr(102)+chr(32)+chr(103)+chr(101)+chr(116)+chr(97)+chr(116)+chr(116)+chr(114)+chr(40)+chr(97)+chr(114)+chr(103)+chr(115)+chr(44)+chr(32)+chr(39)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(104)+chr(111)+chr(108)+chr(100)+chr(101)+chr(114)+chr(115)+chr(39)+chr(44)+chr(32)+chr(78)+chr(111)+chr(110)+chr(101)+chr(41)+chr(58),
    chr(32)*8+chr(97)+chr(110)+chr(97)+chr(108)+chr(121)+chr(122)+chr(101)+chr(95)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(104)+chr(111)+chr(108)+chr(100)+chr(101)+chr(114)+chr(115)+chr(40)+chr(97)+chr(114)+chr(103)+chr(115)+chr(46)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(104)+chr(111)+chr(108)+chr(100)+chr(101)+chr(114)+chr(115)+chr(41),
    chr(32)*8+chr(114)+chr(101)+chr(116)+chr(117)+chr(114)+chr(110),
]
lns=lns[:ins_idx]+block+lns[ins_idx:]
ns=chr(10).join(lns)
try:
    ast.parse(ns)
    open(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121),chr(119),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).write(ns)
    print(chr(83)+chr(85)+chr(67)+chr(67)+chr(69)+chr(83)+chr(83)+chr(32)+chr(45)+chr(32)+chr(101)+chr(97)+chr(114)+chr(108)+chr(121)+chr(32)+chr(101)+chr(120)+chr(105)+chr(116)+chr(115)+chr(32)+chr(97)+chr(100)+chr(100)+chr(101)+chr(100))
except SyntaxError as e:
    print(chr(83)+chr(89)+chr(78)+chr(84)+chr(65)+chr(88)+chr(32)+chr(69)+chr(82)+chr(82)+chr(79)+chr(82)+chr(32)+chr(45)+chr(32)+chr(110)+chr(111)+chr(32)+chr(99)+chr(104)+chr(97)+chr(110)+chr(103)+chr(101)+chr(115)+chr(58),e)
