import ast
import shutil
shutil.copy2(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121), chr(95)+chr(98)+chr(97)+chr(99)+chr(107)+chr(117)+chr(112)+chr(115)+chr(47)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(95)+chr(112)+chr(114)+chr(101)+chr(95)+chr(119)+chr(105)+chr(114)+chr(101)+chr(49)+chr(55)+chr(102)+chr(46)+chr(112)+chr(121))
print(chr(66)+chr(97)+chr(99)+chr(107)+chr(117)+chr(112)+chr(32)+chr(111)+chr(107))

# Wire bat
bat=open(chr(108)+chr(97)+chr(117)+chr(110)+chr(99)+chr(104)+chr(95)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(46)+chr(98)+chr(97)+chr(116),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).read()
bat=bat.replace(chr(101)+chr(99)+chr(104)+chr(111)+chr(32)+chr(32)+chr(32)+chr(49)+chr(55)+chr(101)+chr(46)+chr(32)+chr(66)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(32)+chr(73)+chr(109)+chr(112)+chr(97)+chr(99)+chr(116)+chr(32)+chr(32)+chr(40)+chr(105)+chr(110)+chr(115)+chr(116)+chr(105)+chr(116)+chr(117)+chr(116)+chr(105)+chr(111)+chr(110)+chr(97)+chr(108)+chr(32)+chr(114)+chr(97)+chr(110)+chr(107)+chr(105)+chr(110)+chr(103)+chr(41), chr(101)+chr(99)+chr(104)+chr(111)+chr(32)+chr(32)+chr(32)+chr(49)+chr(55)+chr(101)+chr(46)+chr(32)+chr(66)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(32)+chr(73)+chr(109)+chr(112)+chr(97)+chr(99)+chr(116)+chr(32)+chr(32)+chr(40)+chr(105)+chr(110)+chr(115)+chr(116)+chr(105)+chr(116)+chr(117)+chr(116)+chr(105)+chr(111)+chr(110)+chr(97)+chr(108)+chr(32)+chr(114)+chr(97)+chr(110)+chr(107)+chr(105)+chr(110)+chr(103)+chr(41)+chr(10)+chr(101)+chr(99)+chr(104)+chr(111)+chr(32)+chr(32)+chr(32)+chr(49)+chr(55)+chr(102)+chr(46)+chr(32)+chr(77)+chr(111)+chr(109)+chr(101)+chr(110)+chr(116)+chr(117)+chr(109)+chr(32)+chr(72)+chr(117)+chr(110)+chr(116)+chr(101)+chr(114)+chr(32)+chr(40)+chr(101)+chr(97)+chr(114)+chr(108)+chr(121)+chr(32)+chr(97)+chr(99)+chr(99)+chr(117)+chr(109)+chr(117)+chr(108)+chr(97)+chr(116)+chr(105)+chr(111)+chr(110)+chr(41))
print(chr(77)+chr(101)+chr(110)+chr(117)+chr(32)+chr(108)+chr(105)+chr(110)+chr(101)+chr(32)+chr(97)+chr(100)+chr(100)+chr(101)+chr(100))

# Find and insert MOMENTUM_HUNTER block after BROKER_IMPAAT goto AGAIN
lns=bat.splitlines()
done=False
for i,l in enumerate(lns):
    if chr(66)+chr(82)+chr(79)+chr(75)+chr(69)+chr(82)+chr(95)+chr(73)+chr(77)+chr(80)+chr(65)+chr(65)+chr(84) in l and l.strip().startswith(chr(58)):
        for j in range(i+1,min(len(lns),i+10)):
            if chr(103)+chr(111)+chr(116)+chr(111)+chr(32)+chr(65)+chr(71)+chr(65)+chr(73)+chr(78) in lns[j]:
                lns=lns[:j+1]+[chr(32)]+[chr(58)+chr(77)+chr(79)+chr(77)+chr(69)+chr(78)+chr(84)+chr(85)+chr(77)+chr(95)+chr(72)+chr(85)+chr(78)+chr(84)+chr(69)+chr(82)]+[chr(112)+chr(121)+chr(116)+chr(104)+chr(111)+chr(110)+chr(32)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121)+chr(32)+chr(45)+chr(45)+chr(109)+chr(111)+chr(109)+chr(101)+chr(110)+chr(116)+chr(117)+chr(109)+chr(45)+chr(104)+chr(117)+chr(110)+chr(116)+chr(101)+chr(114)]+[chr(103)+chr(111)+chr(116)+chr(111)+chr(32)+chr(65)+chr(71)+chr(65)+chr(73)+chr(78)]+lns[j+1:]
                done=True
                print(chr(66)+chr(108)+chr(111)+chr(99)+chr(107)+chr(32)+chr(97)+chr(100)+chr(100)+chr(101)+chr(100))
                break
        break

# Also add choice routing
bat2=chr(10).join(lns)
old17e=chr(105)+chr(102)+chr(32)+chr(34)+chr(37)+chr(99)+chr(104)+chr(111)+chr(105)+chr(99)+chr(101)+chr(37)+chr(34)+chr(61)+chr(61)+chr(34)+chr(49)+chr(55)+chr(101)+chr(34)+chr(32)+chr(103)+chr(111)+chr(116)+chr(111)+chr(32)+chr(66)+chr(82)+chr(79)+chr(75)+chr(69)+chr(82)+chr(95)+chr(73)+chr(77)+chr(80)+chr(65)+chr(65)+chr(84)
new17e=old17e+chr(10)+chr(105)+chr(102)+chr(32)+chr(34)+chr(37)+chr(99)+chr(104)+chr(111)+chr(105)+chr(99)+chr(101)+chr(37)+chr(34)+chr(61)+chr(61)+chr(34)+chr(49)+chr(55)+chr(102)+chr(34)+chr(32)+chr(103)+chr(111)+chr(116)+chr(111)+chr(32)+chr(77)+chr(79)+chr(77)+chr(69)+chr(78)+chr(84)+chr(85)+chr(77)+chr(95)+chr(72)+chr(85)+chr(78)+chr(84)+chr(69)+chr(82)
bat2=bat2.replace(old17e,new17e)
open(chr(108)+chr(97)+chr(117)+chr(110)+chr(99)+chr(104)+chr(95)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(46)+chr(98)+chr(97)+chr(116),chr(119),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).write(bat2)
print(chr(66)+chr(97)+chr(116)+chr(32)+chr(100)+chr(111)+chr(110)+chr(101))

# Wire scanner CLI arg
lns=open(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).read().splitlines()
arg=chr(32)+chr(32)+chr(32)+chr(32)+chr(112)+chr(46)+chr(97)+chr(100)+chr(100)+chr(95)+chr(97)+chr(114)+chr(103)+chr(117)+chr(109)+chr(101)+chr(110)+chr(116)+chr(40)+chr(39)+chr(45)+chr(45)+chr(109)+chr(111)+chr(109)+chr(101)+chr(110)+chr(116)+chr(117)+chr(109)+chr(45)+chr(104)+chr(117)+chr(110)+chr(116)+chr(101)+chr(114)+chr(39)+chr(44)+chr(97)+chr(99)+chr(116)+chr(105)+chr(111)+chr(110)+chr(61)+chr(39)+chr(115)+chr(116)+chr(111)+chr(114)+chr(101)+chr(95)+chr(116)+chr(114)+chr(117)+chr(101)+chr(39)+chr(44)+chr(100)+chr(101)+chr(102)+chr(97)+chr(117)+chr(108)+chr(116)+chr(61)+chr(70)+chr(97)+chr(108)+chr(115)+chr(101)+chr(44)+chr(104)+chr(101)+chr(108)+chr(112)+chr(61)+chr(39)+chr(77)+chr(111)+chr(109)+chr(101)+chr(110)+chr(116)+chr(117)+chr(109)+chr(32)+chr(104)+chr(117)+chr(110)+chr(116)+chr(101)+chr(114)+chr(39)+chr(41)
for i,l in enumerate(lns):
    if chr(45)+chr(45)+chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(45)+chr(105)+chr(109)+chr(112)+chr(97)+chr(99)+chr(116) in l and chr(97)+chr(100)+chr(100)+chr(95)+chr(97)+chr(114)+chr(103)+chr(117)+chr(109)+chr(101)+chr(110)+chr(116) in l:
        lns.insert(i+1,arg)
        print(chr(65)+chr(114)+chr(103)+chr(32)+chr(97)+chr(100)+chr(100)+chr(101)+chr(100))
        break
for i,l in enumerate(lns):
    if chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114)+chr(95)+chr(105)+chr(109)+chr(112)+chr(97)+chr(99)+chr(116) in l and chr(103)+chr(101)+chr(116)+chr(97)+chr(116)+chr(116)+chr(114) in l:
        for j in range(i,min(len(lns),i+6)):
            if lns[j].strip()==chr(114)+chr(101)+chr(116)+chr(117)+chr(114)+chr(110):
                lns.insert(j+1,chr(32)+chr(32)+chr(32)+chr(32)+chr(105)+chr(102)+chr(32)+chr(103)+chr(101)+chr(116)+chr(97)+chr(116)+chr(116)+chr(114)+chr(40)+chr(97)+chr(114)+chr(103)+chr(115)+chr(44)+chr(32)+chr(34)+chr(109)+chr(111)+chr(109)+chr(101)+chr(110)+chr(116)+chr(117)+chr(109)+chr(95)+chr(104)+chr(117)+chr(110)+chr(116)+chr(101)+chr(114)+chr(34)+chr(44)+chr(32)+chr(70)+chr(97)+chr(108)+chr(115)+chr(101)+chr(41)+chr(58))
                lns.insert(j+2,chr(32)+chr(32)+chr(32)+chr(32)+chr(32)+chr(32)+chr(32)+chr(32)+chr(97)+chr(110)+chr(97)+chr(108)+chr(121)+chr(122)+chr(101)+chr(95)+chr(109)+chr(111)+chr(109)+chr(101)+chr(110)+chr(116)+chr(117)+chr(109)+chr(95)+chr(104)+chr(117)+chr(110)+chr(116)+chr(101)+chr(114)+chr(40)+chr(41))
                lns.insert(j+3,chr(32)+chr(32)+chr(32)+chr(32)+chr(32)+chr(32)+chr(32)+chr(32)+chr(114)+chr(101)+chr(116)+chr(117)+chr(114)+chr(110))
                print(chr(72)+chr(97)+chr(110)+chr(100)+chr(108)+chr(101)+chr(114)+chr(32)+chr(97)+chr(100)+chr(100)+chr(101)+chr(100))
                break
        break
ns=chr(10).join(lns)
try:
    ast.parse(ns)
    open(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121),chr(119),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).write(ns)
    print(chr(83)+chr(85)+chr(67)+chr(67)+chr(69)+chr(83)+chr(83))
except SyntaxError as e:
    print(chr(69)+chr(82)+chr(82)+chr(79)+chr(82),e)
