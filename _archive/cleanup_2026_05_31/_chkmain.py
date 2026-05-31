lns=open(chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(115)+chr(99)+chr(97)+chr(110)+chr(110)+chr(101)+chr(114)+chr(46)+chr(112)+chr(121),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)).read().splitlines()
for i,l in enumerate(lns):
    if chr(110)+chr(97)+chr(109)+chr(101) in l and chr(109)+chr(97)+chr(105)+chr(110) in l:
        for j in range(i,min(len(lns),i+30)):
            print(j,lns[j])
        break
