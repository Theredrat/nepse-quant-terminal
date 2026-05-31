# Just print the raw lines to see exact format
sample = """64


Sun Securities...
22,53,123Rs. 63.84 Cr51,97,305Rs. 1.73 ArabRs. 332.938,3685.4729,44,182Rs. 1.09 ArabRs. 370.884,2633.143.351,33,4694,80,18,915.7182
58


Naasa Securiti...
18,04,274Rs. 40.67 Cr1,18,31,119Rs. 3.89 ArabRs. 329.0321,44512.441,00,26,845Rs. 3.48 ArabRs. 347.6717,97310.5415.2513,04,27145,65,50,066.81,876"""

for i, line in enumerate(sample.splitlines()):
    print(f"{i:3} | repr: {repr(line)}")
