lns=open(chr(108)+chr(97)+chr(117)+chr(110)+chr(99)+chr(104)+chr(95)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(46)+chr(98)+chr(97)+chr(116),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).read().splitlines()
for i,l in enumerate(lns):
    if chr(58)+chr(77)+chr(79)+chr(86)+chr(69)+chr(82)+chr(83) in l or chr(58)+chr(87)+chr(65)+chr(84)+chr(67)+chr(72) in l or chr(109)+chr(111)+chr(118)+chr(101)+chr(114)+chr(115) in l.lower() or chr(119)+chr(97)+chr(116)+chr(99)+chr(104) in l.lower():
        print(i,l)
