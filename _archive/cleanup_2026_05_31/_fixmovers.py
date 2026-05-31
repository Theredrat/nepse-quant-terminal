import shutil
shutil.copy2(chr(108)+chr(97)+chr(117)+chr(110)+chr(99)+chr(104)+chr(95)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(46)+chr(98)+chr(97)+chr(116),chr(95)+chr(98)+chr(97)+chr(99)+chr(107)+chr(117)+chr(112)+chr(115)+chr(47)+chr(108)+chr(97)+chr(117)+chr(110)+chr(99)+chr(104)+chr(95)+chr(112)+chr(114)+chr(101)+chr(95)+chr(102)+chr(105)+chr(120)+chr(109)+chr(111)+chr(118)+chr(101)+chr(114)+chr(115)+chr(46)+chr(98)+chr(97)+chr(116))
lns=open(chr(108)+chr(97)+chr(117)+chr(110)+chr(99)+chr(104)+chr(95)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(46)+chr(98)+chr(97)+chr(116),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).read().splitlines()
for i,l in enumerate(lns):
    if chr(99)+chr(104)+chr(111)+chr(105)+chr(99)+chr(101)+chr(37)+chr(34)+chr(61)+chr(61)+chr(34)+chr(50)+chr(34) in l and chr(109)+chr(111)+chr(118)+chr(101)+chr(114)+chr(115)+chr(45)+chr(111)+chr(110)+chr(108)+chr(121) in l:
        lns[i]=chr(105)+chr(102)+chr(32)+chr(34)+chr(37)+chr(99)+chr(104)+chr(111)+chr(105)+chr(99)+chr(101)+chr(37)+chr(34)+chr(61)+chr(61)+chr(34)+chr(50)+chr(34)+chr(32)+chr(103)+chr(111)+chr(116)+chr(111)+chr(32)+chr(82)+chr(85)+chr(78)+chr(95)+chr(77)+chr(79)+chr(86)+chr(69)+chr(82)+chr(83)
        print(chr(70)+chr(105)+chr(120)+chr(101)+chr(100)+chr(32)+chr(111)+chr(112)+chr(116)+chr(105)+chr(111)+chr(110)+chr(32)+chr(50))
    if chr(99)+chr(104)+chr(111)+chr(105)+chr(99)+chr(101)+chr(37)+chr(34)+chr(61)+chr(61)+chr(34)+chr(51)+chr(34) in l and chr(119)+chr(97)+chr(116)+chr(99)+chr(104)+chr(108)+chr(105)+chr(115)+chr(116) in l:
        lns[i]=chr(105)+chr(102)+chr(32)+chr(34)+chr(37)+chr(99)+chr(104)+chr(111)+chr(105)+chr(99)+chr(101)+chr(37)+chr(34)+chr(61)+chr(61)+chr(34)+chr(51)+chr(34)+chr(32)+chr(103)+chr(111)+chr(116)+chr(111)+chr(32)+chr(82)+chr(85)+chr(78)+chr(95)+chr(87)+chr(65)+chr(84)+chr(67)+chr(72)+chr(76)+chr(73)+chr(83)+chr(84)
        print(chr(70)+chr(105)+chr(120)+chr(101)+chr(100)+chr(32)+chr(111)+chr(112)+chr(116)+chr(105)+chr(111)+chr(110)+chr(32)+chr(51))
# Add blocks before AGAIN
for i,l in enumerate(lns):
    if chr(58)+chr(65)+chr(71)+chr(65)+chr(73)+chr(78) in l.strip():
        block=[
            chr(58)+chr(82)+chr(85)+chr(78)+chr(95)+chr(77)+chr(79)+chr(86)+chr(69)+chr(82)+chr(83),
            chr(112)+chr(121)+chr(116)+chr(104)+chr(111)+chr(110)+chr(32)+chr(95)+chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(99)+chr(104)+chr(101)+chr(99)+chr(107)+chr(46)+chr(112)+chr(121),
            chr(105)+chr(102)+chr(32)+chr(101)+chr(114)+chr(114)+chr(111)+chr(114)+chr(108)+chr(101)+chr(118)+chr(101)+chr(108)+chr(32)+chr(110)+chr(101)+chr(113)+chr(32)+chr(48)+chr(32)+chr(103)+chr(111)+chr(116)+chr(111)+chr(32)+chr(65)+chr(71)+chr(65)+chr(73)+chr(78),
            chr(112)+chr(121)+chr(116)+chr(104)+chr(111)+chr(110)+chr(32)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121)+chr(32)+chr(45)+chr(45)+chr(109)+chr(111)+chr(118)+chr(101)+chr(114)+chr(115)+chr(45)+chr(111)+chr(110)+chr(108)+chr(121),
            chr(103)+chr(111)+chr(116)+chr(111)+chr(32)+chr(65)+chr(71)+chr(65)+chr(73)+chr(78),
            chr(58)+chr(82)+chr(85)+chr(78)+chr(95)+chr(87)+chr(65)+chr(84)+chr(67)+chr(72)+chr(76)+chr(73)+chr(83)+chr(84),
            chr(112)+chr(121)+chr(116)+chr(104)+chr(111)+chr(110)+chr(32)+chr(95)+chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(99)+chr(104)+chr(101)+chr(99)+chr(107)+chr(46)+chr(112)+chr(121),
            chr(105)+chr(102)+chr(32)+chr(101)+chr(114)+chr(114)+chr(111)+chr(114)+chr(108)+chr(101)+chr(118)+chr(101)+chr(108)+chr(32)+chr(110)+chr(101)+chr(113)+chr(32)+chr(48)+chr(32)+chr(103)+chr(111)+chr(116)+chr(111)+chr(32)+chr(65)+chr(71)+chr(65)+chr(73)+chr(78),
            chr(112)+chr(121)+chr(116)+chr(104)+chr(111)+chr(110)+chr(32)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121)+chr(32)+chr(45)+chr(45)+chr(119)+chr(97)+chr(116)+chr(99)+chr(104)+chr(108)+chr(105)+chr(115)+chr(116),
            chr(103)+chr(111)+chr(116)+chr(111)+chr(32)+chr(65)+chr(71)+chr(65)+chr(73)+chr(78),
        ]
        lns=lns[:i]+block+lns[i:]
        print(chr(65)+chr(100)+chr(100)+chr(101)+chr(100)+chr(32)+chr(98)+chr(108)+chr(111)+chr(99)+chr(107)+chr(115))
        break
open(chr(108)+chr(97)+chr(117)+chr(110)+chr(99)+chr(104)+chr(95)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(46)+chr(98)+chr(97)+chr(116),chr(119),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).write(chr(10).join(lns))
print(chr(68)+chr(111)+chr(110)+chr(101))
