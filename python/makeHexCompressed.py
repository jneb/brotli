#!python3
"""Make a file that is decompressed as a "listing" consisting of
three groups of eight hex chars per line, each line ending in CR/LF.
This file when decompressed, will not be compressed (yet) by
the brotli compressor to its potential.
The best way to do this (after the first line) appears to make two literal codes:
- 0-f
- 0-f+space
The first code is for after the space/new line, the other for "in the middle"
Newlines are handled by copying: distance is always 28, length is always 2.
"""

source = '''
0 0                  #WSIZE, LAST
00 0000000000011011  #length = 28
1 000                #uncompressed
ascii ascii  ascii ascii  ascii ascii  ascii ascii
00100000
ascii ascii  ascii ascii  ascii ascii  ascii ascii
00100000
ascii ascii  ascii ascii  ascii ascii  ascii ascii
00001101 00001010    #\r\n

1 0                  #LAST, not empty
00 length            #length
0                    #1 literal block type
0                    #1 insert&copy block type
0001                 #distance block types
01 00                #BTD is simple, 1 code word
01                   #+1
01 01                #BCD is simple, 2 code words
00000                #BCxx: 1-4
11000                #[13*x]: BC8433-16624
00 0                 #first block count is 1

000000               #POSTFIX=DIST=0
01                   #context mode MSB6
0001                 #2 literal trees

1 0100               #RLEMAX = 5
01 10                #simple, 3 code words
110 011 101          #0:1 10:xxx+8 11:xxxxx+32
01 100 0 11 10011    #12 zeroes, 1, 51 zeros
1                    #with IMTF

0001                 #2 distance prefix tree
0                    #no run length encoding
01 01                #simple, 2 code words
0 1                  #0 and 1
0000 1111            #the context map
0                    #no IMTF

11                   #literal prefix tree 0
0111 00 00 0111      #4:1 (0) 0:unused 5:unused 0xxx:1 (1)
1 100 1 101          #3+4=7,43+5=48 unused
0000000000           #digits: 4 bits
1 011 1 100          #3+3,6,35+4=39 unused
000000               #abcdef: 4 bits

11                   #literal prefix tree 1
0111 00 011 011      #4:1 (0) 0:unused 5:2 (01) 0xxx:2 (11)
11 010 11 101        #3+2,27+5=32 unused
0                    #space: 4 bits
11 000 11 100        #0+3,11+4=15 unused
0000000000           #digits: 4 bits
11 011 11 100        #3+3,6,35+4=39 unused
0000 01 01           #abcd: 4 bits; ef: 5 bits

#insert&copy
01 00                #simple, 1 code word
0100011000           #insert26+xxx, copy 2

#distance code 0 and 1
01 00                #simple, 1 code word
010101               #distance: 11xxx-3 (011 gives 24)
01 00                #simple, 1 code word
000000               #last

#metablock
000                  #literal 26, copy 2
L0                   #a, L0
L1 L1 L1 L1 L1 L1 L1
0000                 #spatie
L0                   #0, L0
L1 L1 L1 L1 L1 L1 L1
0000
L0                   #9, L0
L1 L1 L1 L1 L1 L1 L1
111                  #distance: 28
#you see, it is 96bits + 3+4+4+3+2.5 bits = 112.5 bits

000                  #literal 26, copy 2
L0                   #5, L0
L1 L1 L1 L1 L1 L1 L1
0000                 #spatie
L0                   #4, L0
L1 L1 L1 L1 L1 L1 L1
0000
L0                   #8, L0
L1 L1 L1 L1 L1 L1 L1
1 1111111111111      #block switch. Length: enough

#from now on, it is 96bits + 3+4+4+3+1+2.5 bits = 110.5 bits
'''

L0 = {'0':'0000', '1':'1000', '2':'0100', '3':'1100',
      '4':'0010', '5':'1010', '6':'0110', '7':'1110',
      '8':'0001', '9':'1001', 'a':'0101', 'b':'1101',
      'c':'0011', 'd':'1011', 'e':'0111', 'f':'1111',
      }
L1 = {'0':'1000', '1':'0100', '2':'1100', '3':'0010',
      '4':'1010', '5':'0110', '6':'1110', '7':'0001',
      '8':'1001', '9':'0101', 'a':'1101', 'b':'0011',
      'c':'1011', 'd':'0111', 'e':'01111', 'f':'11111',
      ' ':'0000' }
ascii = {'0':'00110000', '1':'00110001', '2':'00110010', '3':'00110011',
         '4':'00110100', '5':'00110101', '6':'00110110', '7':'00110111',
         '8':'00111000', '9':'00111001', 'a':'01100001', 'b':'01100010',
         'c':'01100011', 'd':'01100100', 'e':'01100101', 'f':'01100110',
         }

#this length (in lines) gives about 10000 compressed bytes
length = 725
import random
def processLine(line):
    global outputNum, outputLen
    #chop of comments
    try: line = line[:line.index('#')]
    except ValueError: pass
    for bits in line.split():
        if bits in ('L0', 'L1', 'ascii', 'length'):
            if bits=='length':
                bits = '{:16b}'.format(length*28-1)
            else:
                char = '{:x}'.format(random.randrange(16))
                bits = globals()[bits][char]
        outputNum = outputNum|int(bits,2)<<outputLen
        outputLen += len(bits)
        #write every time we happen to have a multiple of 8
        if outputLen&7==0:
            outfile.write(outputNum.to_bytes(outputLen>>3, 'little'))
            outputNum = outputLen = 0

#write intermediate output as a number with given length
outputNum = outputLen = 0
outfile = open('hex.txt.manual','wb')
for line in source.splitlines():
    processLine(line)

L17 = 'L1 '*7
space = L1[' ']
for i in range(length-2):
    processLine('000 L0 '+L17+space+' L0 '+L17+space+' L0 '+L17)
outfile.write(outputNum.to_bytes(outputLen+7>>3, 'little'))
outfile.close()
