import os
import sys
workdir = os.path.dirname(os.path.realpath(__file__))
os.chdir(workdir)
print("Working directory =", workdir)


def searchForFreeSpace(byte_content_BIOS, freeSpaceSize):      # function to search for free space and return a list of offsets
    blocksize = 32            # minimum block size of free space (must be a multible of 16)
    freeSpaceList = []        # generate a empty list
    
    newRow = False    # save lines of output with list in 2 coloumns
    rowNumers = 3
    rowCount = 1
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
                    if rowCount == rowNumers:
                        print("\n", end='')
                        newRow = False
                        rowCount = 1
                    else:
                        print("\t", end='')
                        newRow = True
                        rowCount += 1
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
    print("   Found", len(freeSpaceList), "free space blocks to place", freeSpaceSize, "bytes at", list(map(hex, freeSpaceList)))
    return freeSpaceList


def searchForBiosCall(byte_content_BIOS):
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
                    print("   Call found with pattern for", searchpattern[patternNumber+1], "BIOS at", hex(i))
                    offsetCall = i
                    patternFound += 1
                    patternpossition = 0
            else:
                patternpossition = 0
            i += 1
    
        patternNumber += 2

    if patternFound == 0:
        print("   No known pattern found for a call in BIOS. Manual disassembling and search required!")
        #print("   You can send the BIOS file to the developer to improve this script.")
        #input("   Abort!")
        #sys.exit()
    
    if patternFound > 1:
        print("   Found too many hits for a call in BIOS. Manual disassembling and search required!")
        #print("   You can send the BIOS file to the developer to improve this script.")
        #input("   Abort!")
        #sys.exit()
        
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

    offsetCall = searchForBiosCall(byte_content_BIOS)



    return




for fileList in os.listdir():
    if fileList.endswith((".bin",".BIN")):
        # Prints only .bin file present in My Folder
        print(fileList,"---------------------------------------------")
        analyseRomImage(fileList)


input("fertig!")
