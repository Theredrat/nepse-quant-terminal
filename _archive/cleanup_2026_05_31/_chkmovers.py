lns=open(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).read().splitlines()
for i,l in enumerate(lns):
    if chr(77)+chr(79)+chr(86)+chr(69)+chr(82)+chr(83) in l or chr(87)+chr(65)+chr(84)+chr(67)+chr(72)+chr(76)+chr(73)+chr(83)+chr(84) in l:
        if chr(103)+chr(111)+chr(116)+chr(111) in l:
            print(i,l)
