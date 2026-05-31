lns=open(chr(108)+chr(97)+chr(117)+chr(110)+chr(99)+chr(104)+chr(95)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(46)+chr(98)+chr(97)+chr(116),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).read().splitlines()
for i,l in enumerate(lns):
    if chr(82)+chr(85)+chr(78)+chr(95)+chr(77)+chr(79)+chr(86)+chr(69)+chr(82)+chr(83) in l or chr(82)+chr(85)+chr(78)+chr(95)+chr(87)+chr(65)+chr(84)+chr(67)+chr(72) in l:
        for j in range(i,min(len(lns),i+6)): print(j,lns[j])
        print()
