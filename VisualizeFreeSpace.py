#!/usr/bin/env python3


import os
import sys


#-------------classes--------------------------------------------

class txtcolor:                  #class for text color
    black   = '\033[30m'
    red     = '\033[31m'
    green   = '\033[32m'
    yellow  = '\033[33m'
    blue    = '\033[34m'
    magenta = '\033[35m'
    cyan    = '\033[36m'
    white   = '\033[37m'      #standard
    gray    = '\033[90m'
    brightred     = '\033[91m'
    brightgreen   = '\033[92m'
    brightyellow  = '\033[93m'
    brightblue    = '\033[94m'
    brightmagenta = '\033[95m'
    brightcyan    = '\033[96m'
    brightwhite   = '\033[97m'
    normal   = '\033[0m'
    WARNING  = brightyellow   #defined colors for messages
    ERROR    = brightred
    GOOD     = green
    VERYGOOD = brightgreen

class bgcolor:
    black   = '\033[40m'      #standard
    red     = '\033[41m'
    green   = '\033[42m'
    yellow  = '\033[43m'
    blue    = '\033[44m'
    magenta = '\033[45m'
    cyan    = '\033[46m'
    white   = '\033[47m'
    gray    = '\033[100m'
    brightred     = '\033[101m'
    brightgreen   = '\033[102m'
    brightyellow  = '\033[103m'
    brightblue    = '\033[104m'
    brightmagenta = '\033[105m'
    brightcyan    = '\033[106m'
    brightwhite   = '\033[107m'
    normal   = '\033[0m'

#-------------functions-------------------------------------------------

def readFileContent(filename):                              # function to read a file with error handling
    try:
        file1 = open(filename, "rb")
        byte_content=bytearray(file1.read(-1))
        file1.close()
    except FileNotFoundError:
        print(txtcolor.ERROR + "ERROR: FileNotFound", filename, "" + txtcolor.normal)
        input("Abort!")
        sys.exit()
    return byte_content


def visualizeFreeSpace(byte_content_BIOS):      # function to search for and visualize free space
    blocksize = 16            # minimum block size of free space (must be a multible of 16)
    
    searchpattern = [0x00, 0xFF, 0xCF]      #search for blocks of contiguous bytes of these values
    i = 0

    while i < len(byte_content_BIOS):
        
        blockconsistent = True
        blockfirstbyte = byte_content_BIOS[i]
        for offset in range(1,blocksize-1):
            if byte_content_BIOS[i+offset]!=blockfirstbyte:
                blockconsistent=False
                offset=blocksize                         #stop the for loop

        color='\033[44m'
        symbol = 67
        
        if blockconsistent:
            if blockfirstbyte == 0x00:
                symbol = 185
                color='\033[42m'
            if blockfirstbyte == 0xFF:
                symbol = 178
                color='\033[42m'
            if blockfirstbyte == 0xCF:
                symbol = 179
                color='\033[42m'

        block=color+chr(symbol)
        print(block,end='')

        i += blocksize

    print(bgcolor.normal,"\n", end='')
    return


#----------------------start code here--------------------------------------

workdir = os.path.dirname(os.path.realpath(__file__))
os.chdir(workdir)
os.system("")     # to activate colored output
#print("Working directory =", workdir)


if os.path.isfile("BIOS_LO.BIN"):
    print("Loding BIOS as HI and LO chip and merge both parts...")
    byte_content_BIOS_LO = readFileContent("BIOS_LO.BIN")
    byte_content_BIOS_HI = readFileContent("BIOS_HI.BIN")

    byte_content_BIOS = bytearray()
    i = 0
    while i < len(byte_content_BIOS_LO):
        byte_content_BIOS.append(byte_content_BIOS_LO[i])
        byte_content_BIOS.append(byte_content_BIOS_HI[i])
        i += 1
else:
    print("Loading BIOS as one chip file...")
    byte_content_BIOS = readFileContent("BIOS.BIN")


visualizeFreeSpace(byte_content_BIOS)

print(" ")
print("blocksize = 16 byte")
print("\033[44mC\033[0m = code block")
print("\033[42m¹\033[0m = free block of 0x00")
print("\033[42m²\033[0m = free block of 0xFF")
print("\033[42m³\033[0m = free block of 0xCF")


input("finished!")
