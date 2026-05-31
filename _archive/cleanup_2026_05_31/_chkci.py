import urllib.request, json
url=chr(104)+chr(116)+chr(116)+chr(112)+chr(115)+chr(58)+chr(47)+chr(47)+chr(114)+chr(97)+chr(119)+chr(46)+chr(103)+chr(105)+chr(116)+chr(104)+chr(117)+chr(98)+chr(117)+chr(115)+chr(101)+chr(114)+chr(99)+chr(111)+chr(110)+chr(116)+chr(101)+chr(110)+chr(116)+chr(46)+chr(99)+chr(111)+chr(109)+chr(47)+chr(84)+chr(104)+chr(101)+chr(114)+chr(101)+chr(100)+chr(114)+chr(97)+chr(116)+chr(47)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(45)+chr(113)+chr(117)+chr(97)+chr(110)+chr(116)+chr(45)+chr(116)+chr(101)+chr(114)+chr(109)+chr(105)+chr(110)+chr(97)+chr(108)+chr(47)+chr(109)+chr(97)+chr(105)+chr(110)+chr(47)+chr(110)+chr(101)+chr(112)+chr(115)+chr(101)+chr(95)+chr(97)+chr(108)+chr(101)+chr(114)+chr(116)+chr(115)+chr(95)+chr(99)+chr(105)+chr(46)+chr(112)+chr(121)
try:
    content=urllib.request.urlopen(url).read().decode()
    print(content[:3000])
except Exception as e:
    print(chr(69)+chr(114)+chr(114)+chr(111)+chr(114)+chr(58),e)
