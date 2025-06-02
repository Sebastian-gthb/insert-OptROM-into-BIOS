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


def calcChecksum(byte_content_BIOS):
    i = 0
    checksum = 0
    while i < len(byte_content_BIOS):
        checksum += byte_content_BIOS[i]
        i += 1
    return checksum & 0xFF


def searchForFreeSpace(byte_content_BIOS, freeSpaceSize):      # function to search for free space and return a list of offsets
    blocksize = 32            # minimum block size of free space (must be a multible of 16)
    freeSpaceList = []        # generate a empty list
    
    newRow = False
    colNumers = 3    # save lines of output with list in coloumns
    colCount = 1
    searchpattern = [0x00, 0xFF, 0xCF]      #search for blocks of contiguous bytes of these values
    patternNumber = 0

    while patternNumber < len(searchpattern):
        i = 0
        countFreeROM = 0
        startblock = 0

        while i < len(byte_content_BIOS):
            if byte_content_BIOS[i]==searchpattern[patternNumber]:
                if startblock==0: startblock = i
                countFreeROM += 1
                i += 1
            else:
       
                if countFreeROM >= blocksize:
                    print("   ", format(countFreeROM, '>6'), "byte of", format(searchpattern[patternNumber], '#04X'), "at", format(startblock, '#7x'), end='')
                    if colCount == colNumers:
                        print("\n", end='')
                        newRow = False
                        colCount = 1
                    else:
                        print("\t", end='')
                        newRow = True
                        colCount += 1
                    if countFreeROM >= freeSpaceSize:
                        #print("   space size found at offset", hex(startblock))
                        freeSpaceList.append(startblock)
                countFreeROM = 0
                startblock = 0
                i >>= 5     #unset the lower 4 bits
                i <<= 5
                i += blocksize
        patternNumber += 1


    if newRow: print("\n", end='')
    freeSpaceList.sort()
    if len(freeSpaceList) == 0:
        outputcolor = txtcolor.ERROR
    else:
        outputcolor = txtcolor.GOOD
    print(outputcolor + "   Found", len(freeSpaceList), "free space blocks to place", freeSpaceSize, "bytes at" , list(map(hex, freeSpaceList)), "" + txtcolor.normal)
    #print("   Found", len(freeSpaceList), "free space blocks to place", freeSpaceSize, "bytes at" , list(map(hex, freeSpaceList)))
    return freeSpaceList


def searchForBiosCall(byte_content_BIOS, exitOnError):
    searchpattern = [bytearray(b'\xBB\x00\xC8\xBA\x00\xE0\xE8'),         "Award",           #search pattern for Award BIOS (Bondewell B310)
                     bytearray(b'\xB8\x00\xC0\xBA\x80\xC7\xB7\x02\xE8'), "Pegasus",         #search pattern for Pegasus BIOS (Olivetti)
                     bytearray(b'\xBE\x00\xC8\xB9\x00\xE0\xB2\x00\xE8'), "Phoenix 1987",    #search pattern for Phoenix BIOS
                     bytearray(b'\x32\xD2\xBE\x00\xC8\xB9\x00\xE0\xE8'), "Phoenix 1988",    #search pattern for Phoenix BIOS (Sharp PC5541)
                     bytearray(b'\xBB\x00\xC8\xBF\x00\xF0\xE8'),         "Vadem",           #search pattern for Vadem BIOS (Sharp PC4521)
                     bytearray(b'\xE6\x80\xBB\x00\xC8\xE8'),             "AMI",             #search pattern for AMI BIOS some (386 BIOS ROMs)
                     bytearray(b'\xBB\x00\xC8\xB9\x00\x00\xC1\xE9\x04\x81\xC1\x00\x28\xBF\x55\xAA\xE8'), "Chips and Technologie",    #search pattern for Chips and Technologies
                     bytearray(b'\xBB\x00\xC8\xB9\x00\x30\xA0\x8F\x00\x50\xE8'), "Quadtel",         #search pattern for Quadtel BIOS
                     bytearray(b'\xE6\x80\xBB\x00\xC8\xB9\x30\x00\xB4\x00\xE8'), "Zenith" ]         #search pattern for Zenith BIOS

    patternFound = 0
    patternNumber = 0
    offsetCall = 0

    while patternNumber < len(searchpattern):
        i = 0
        patternpossition = 0
        patternlength = len(searchpattern[patternNumber])
        #print("   search with pattern for", searchpattern[patternNumber+1], "BIOS")

        while i < len(byte_content_BIOS) - patternlength:
            if byte_content_BIOS[i] == searchpattern[patternNumber][patternpossition]:
                patternpossition += 1
                if patternpossition == patternlength:
                    print(txtcolor.GOOD + "   Call found with pattern for", searchpattern[patternNumber+1], "BIOS at", hex(i), "" + txtcolor.normal)
                    offsetCall = i
                    patternFound += 1
                    patternpossition = 0
            else:
                patternpossition = 0
            i += 1
    
        patternNumber += 2

    if patternFound == 0:
        print(txtcolor.ERROR + "   No known pattern found for a call in BIOS. Manual disassembling and search required!" + txtcolor.normal)
        if exitOnError:
            print("   You can send the BIOS file to the developer to improve this script.")
            input("   Abort!")
            sys.exit()
    
    if patternFound > 1:
        print(txtcolor.ERROR + "   Found too many hits for a call in BIOS. Manual disassembling and search required!" + txtcolor.normal)
        if exitOnError:
            print("   You can send the BIOS file to the developer to improve this script.")
            input("   Abort!")
            sys.exit()
        
    return offsetCall


def analyseRomImage(filename):

    file1 = open(filename, "rb")
    byte_content_BIOS   = bytearray(file1.read(-1))    # -1 = read the whole file
    file1.close()


    # calculating checksum of the original BIOS ROM
    i = 0
    checksum = 0
    while i < len(byte_content_BIOS):
        checksum += byte_content_BIOS[i]
        i += 1
    checksumOrg = checksum & 0xFF
    print("   BIOS ROM size =", len(byte_content_BIOS), "byte. \t checksum =", hex(checksumOrg))


    freeSpaceList = searchForFreeSpace(byte_content_BIOS, 5000)

    offsetCall = searchForBiosCall(byte_content_BIOS, False)   # second parameter is for exitOnError

    return


#----------------------start code here--------------------------------------

workdir = os.path.dirname(os.path.realpath(__file__))
os.chdir(workdir)
os.system("")     # to activate colored output
print("Working directory =", workdir)


for fileList in os.listdir():
    if fileList.endswith((".bin",".BIN")):
        # Prints only .bin file present in My Folder
        print(fileList,"---------------------------------------------")
        analyseRomImage(fileList)


input("finished!")
