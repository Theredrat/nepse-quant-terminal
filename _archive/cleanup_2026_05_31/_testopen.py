from nepse import Nepse
n = Nepse()
n.setTLSVerification(False)
try:
    status = n.getMarketStatus()
    print(chr(77)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(32)+chr(115)+chr(116)+chr(97)+chr(116)+chr(117)+chr(115)+chr(58), status)
except Exception as e:
    print(chr(103)+chr(101)+chr(116)+chr(77)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(83)+chr(116)+chr(97)+chr(116)+chr(117)+chr(115)+chr(32)+chr(101)+chr(114)+chr(114)+chr(111)+chr(114)+chr(58), e)
try:
    isopen = n.isNepseOpen()
    print(chr(105)+chr(115)+chr(78)+chr(101)+chr(112)+chr(115)+chr(101)+chr(79)+chr(112)+chr(101)+chr(110)+chr(58), isopen)
except Exception as e:
    print(chr(105)+chr(115)+chr(78)+chr(101)+chr(112)+chr(115)+chr(101)+chr(79)+chr(112)+chr(101)+chr(110)+chr(32)+chr(101)+chr(114)+chr(114)+chr(111)+chr(114)+chr(58), e)
