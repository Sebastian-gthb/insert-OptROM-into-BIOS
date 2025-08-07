# This code implementing the option ROM (like XTIDE) into a BIOS ROM.

# To run you need the following files:
#   * the script him self in the directory
#   * BIOS_HI.BIN and BIOS_LO.BIN file with the dump of the HI (Odd) and LO (Even) part of the BIOS
#   * or BIOS.BIN file with the dump of the BIOS from a one chip ROM
#   * OptROM.BIN with a option ROM image like a configured XTIDE ROM image
#
# With all these files in one directory you must only execute the script and you get a patches new BIOS file ("BIOS+OPT.BIN") and the HI and LO part for the EPROMs ("BIOS+OPT_HI.BIN" and "BIOS+OPT_LO.BIN").
#
# The idea, the solution and the code is from Sebastian-gthb.



# code for the SubFunc to call the Option ROM with blanced call destinations. The destinations are calculated and set in this script.
byte_content_SubFunc = bytearray(b'\x60\x9C\x9A\x03\x00\x00\x00\x9D\x61\xE8\x00\x00\xC3\x00')
#                                                       ^^^^^^^             ^^^^^^^     ^^^
#                                             Segment of OptROM             |||||||     used for changing the checksum
#                                                                           |||||||
#                                                               distance to the org. SubFunction
#example:
#f000:dc50    60            pusha
#f000:dc51    9C            pushf
#f000:dc52    9A030000f2    call far f200:0003
#f000:dc57    9D            popf
#f000:dc58    61            popa
#f000:dc59    E8CCB1        call near f000:8E28
#f000:dc5C    C3            ret

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
        print("   search with pattern for", searchpattern[patternNumber+1], "BIOS")

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


def insertArrayIntoArray(byte_content_BIOS, byte_content_injection, position):
    i = 0
    warning = False
    FirstSameByte = byte_content_BIOS[position]
    print("   inserting", len(byte_content_injection), "byte code in", len(byte_content_BIOS), "byte of BIOS ROM, at position", hex(position))

    if position + len(byte_content_injection) > len(byte_content_BIOS):
        print(txtcolor.ERROR + "   ERROR: offset + option ROM length to long for BIOS" + txtcolor.normal)
        input("   Abort!")
        sys.exit()

    while i < len(byte_content_injection):

        if byte_content_BIOS[position] != FirstSameByte:
            if not warning:
                print(txtcolor.WARNING + "   WARNING: found content at: ", end='')
                warning = True
            print(position, " ", end='')

        byte_content_BIOS[position] = byte_content_injection[i]

        i += 1
        position += 1

    if warning: print(" " + txtcolor.normal)    # if a warning was printed make a new line at the end
    
    return byte_content_BIOS


#----------------------start code here--------------------------------------

os.system("")     # to activate colored output
workdir = os.path.dirname(os.path.realpath(__file__))
os.chdir(workdir)
print("Working directory =", workdir)


# STEP 1 ------------------------------------------------
# loading BIOS ROM (as HI+LO or as single chip file)

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
    
    twoChipBios = True   # flag for spliting BIOS in HI and LO part
    
    # we save the merged original BIOS if
    file4 = open('BIOS.BIN', "wb")
    file4.write(bytes(byte_content_BIOS))
    file4.close()

else:
    print("Loading BIOS as one chip file...")
    byte_content_BIOS = readFileContent("BIOS.BIN")

    twoChipBios = False   # flag for spliting BIOS in HI and LO part

# calculating checksum and print some information of the original BIOS ROM
checksumOrg = calcChecksum(byte_content_BIOS)
print("   BIOS ROM size =", len(byte_content_BIOS), "byte. \t checksum =", hex(checksumOrg))


# STEP 2 ------------------------------------------------
print("Loading option ROM...")

byte_content_OptROM  = readFileContent("OptROM.BIN")


# STEP 3 ------------------------------------------------
print("Search for the SearchForOptionRom call in the BIOS...")

offsetCall = searchForBiosCall(byte_content_BIOS, True)


# STEP 4 ------------------------------------------------
print("Search for free space in the BIOS ROM to place the option ROM...")

freeSpaceList = searchForFreeSpace(byte_content_BIOS, len(byte_content_OptROM))

if len(freeSpaceList) == 0:
    print("   ERROR: not enough empty space found in BIOS ROM to insert the option ROM")
    input("   Abort!")
    sys.exit()

offsetOptROM = freeSpaceList[0]       # use the first free space block to insert the option ROM



# STEP 5 ------------------------------------------------
print("Insert option ROM into BIOS...")

# now we need "offsetOptROM"

# parameter:
#     * target binary array = byte_content_BIOS
#     * source binary array = byte_content_OptROM
#     * position to insert  = offsetOptROM
#
# return:
#     * byte_content_BIOS

byte_content_BIOS = insertArrayIntoArray(byte_content_BIOS, byte_content_OptROM, offsetOptROM)



# STEP 6 ------------------------------------------------
print("Search for free space in the BIOS ROM to place the new subfunction...")

freeSpaceList = searchForFreeSpace(byte_content_BIOS, len(byte_content_SubFunc))

if len(freeSpaceList) == 0:
    print("   ERROR: not enough empty space found in BIOS ROM to insert the new subfunction")
    input("   Abort!")
    sys.exit()

if len(freeSpaceList) == 1:
    offsetSubFunc = freeSpaceList[0]          # have we only one free space so use this space
else:
    print("   Search the closest free space...")
    print("      offsetCall =", hex(offsetCall))

    i = 0
    for x in freeSpaceList:
        if x > offsetCall:
            break
        i += 1
    
    if i == 0:
        offsetSubFunc = freeSpaceList[0]        # if the 1st space position greater the offsetCall use the first space
    else:
        if i == len(freeSpaceList) -1:          # if all spaces lower than the offsetCall use the last space
            offsetSubFunc = freeSpaceList[len(freeSpaceList) -1]
        else:                                   # if we have a space before and after calculte the distance
            distanceToCallDown = offsetCall - freeSpaceList[i -1]
            distanceToCallUp   = freeSpaceList[i] - offsetCall
            if distanceToCallDown < distanceToCallUp:
                offsetSubFunc = freeSpaceList[i -1]       # if the distance to the lower space closer use the lower space
            else:
                offsetSubFunc = freeSpaceList[i]          # if the distance to the higher space closer or equal use the higher space
                
print("      closest space at", hex(offsetSubFunc))

print("   Check it's in range of a near call...")

distanceToCall = offsetCall - offsetSubFunc 
if distanceToCall < 0: distanceToCall = -distanceToCall      # change a negative distance to positive

print("      Distance =", distanceToCall, "and may not be greater than", 0x7FFF)

if distanceToCall > 0x7FFF:
    print("   ERROR: no free space found in a range of a near call.")
    input("   Abort!")
    sys.exit()


# STEP 7 ------------------------------------------------
print("calculating all the call destinations...")


# calculating the segment adress of the Option ROM and implementing it in the new SubFunction
FarCallSegmentAdress = 0x100000 - len(byte_content_BIOS) + offsetOptROM
FarCallSegmentAdress >>= 4
print("   Segment adress for OptROM =", hex(FarCallSegmentAdress))
byte_content_SubFunc[5] = FarCallSegmentAdress & 0xFF
print("      low  byte =", hex(FarCallSegmentAdress & 0xFF))
FarCallSegmentAdress >>= 8
byte_content_SubFunc[6] = FarCallSegmentAdress & 0xFF
print("      high byte =", hex(FarCallSegmentAdress & 0xFF))

# calculating the offset and distance of the original SubFunction and implementing it in the new SubFunction
offsetOrgSubFunc = byte_content_BIOS[offsetCall+1]            #low byte
offsetOrgSubFunc += byte_content_BIOS[offsetCall+2] << 8      #high byte

if offsetOrgSubFunc & 0x8000 > 0:                 # if the call destination negative...
    offsetOrgSubFunc &= 0x7FFF                    # take only the 15bit with the distance
    offsetOrgSubFunc = -offsetOrgSubFunc          # set the value to negative

print("   readed distance from BIOS call to original SubFunc is", offsetOrgSubFunc, "  The offset of the original SubFunction is", hex(offsetOrgSubFunc + offsetCall + 3))

offsetOrgSubFunc += offsetCall + 3
callDistanceToOrgSubFunc = offsetOrgSubFunc - (offsetSubFunc + 12)
print("   calculated distance for the call in the new SubFunc from", hex(offsetSubFunc+12), "to original SubFunc", hex(offsetOrgSubFunc),"=", callDistanceToOrgSubFunc, hex(callDistanceToOrgSubFunc &0xFFFF))
byte_content_SubFunc[10] = callDistanceToOrgSubFunc & 0xFF
print("      low  byte =", hex(callDistanceToOrgSubFunc & 0xFF))
callDistanceToOrgSubFunc >>= 8
byte_content_SubFunc[11] = callDistanceToOrgSubFunc & 0xFF
print("      high byte =", hex(callDistanceToOrgSubFunc & 0xFF))

# calculating the distance to the new SubFunction and implementing it in the BIOS code
callDistanceToNewSubFunc = offsetSubFunc - (offsetCall + 3)
print("   calculated distance for the call from", hex(offsetCall), "to SubFunc", hex(offsetSubFunc),"=", callDistanceToNewSubFunc, hex(callDistanceToNewSubFunc &0xFFFF))
byte_content_BIOS[offsetCall+1] = callDistanceToNewSubFunc & 0xFF
print("      low  byte =", hex(callDistanceToNewSubFunc & 0xFF))
callDistanceToNewSubFunc >>= 8
byte_content_BIOS[offsetCall+2] = callDistanceToNewSubFunc & 0xFF
print("      high byte =", hex(callDistanceToNewSubFunc & 0xFF))



# STEP 8 ------------------------------------------------
print("Insert subfunction to call the option ROM...")

# parameter:
#     * target binary array = byte_content_BIOS
#     * source binary array = byte_content_SubFunc
#     * position to insert  = offsetSubFunc
#
# return:
#     * byte_content_BIOS

byte_content_BIOS = insertArrayIntoArray(byte_content_BIOS, byte_content_SubFunc, offsetSubFunc)


# STEP 9 ------------------------------------------------
print("Callculating checksum and correcting to the original checksum...")


checksum = calcChecksum(byte_content_BIOS)
checksumaddon = checksumOrg - (checksum & 0xFF)
print("   Current checksum is", hex(checksum & 0xFF), "and now adding", hex(checksumaddon & 0xFF), "to be", hex(checksumOrg))

# patching the checksum
byte_content_BIOS[offsetSubFunc + 13] = checksumaddon & 0xFF

# check new checksum
checksum = calcChecksum(byte_content_BIOS)
if checksum == checksumOrg:
    outputcolor = txtcolor.GOOD
else:
    outputcolor = txtcolor.WARNING
print(outputcolor + "   New corrected checksum is now", hex(checksum & 0xFF),"" + txtcolor.normal)



# STEP 10 ------------------------------------------------
print("Save patched BIOS to file...")

file6 = open('BIOS+OPT.BIN', "wb")
file6.write(bytes(byte_content_BIOS))
file6.close()


# STEP 11 ------------------------------------------------
if twoChipBios:
    print("Split BIOS into HI an LO file...")

    byte_content_BIOS_LO_new = bytearray()
    byte_content_BIOS_HI_new = bytearray()

    i = 0
    while i < len(byte_content_BIOS):
        byte_content_BIOS_LO_new.append(byte_content_BIOS[i])
        i += 1
        byte_content_BIOS_HI_new.append(byte_content_BIOS[i])
        i += 1

    file7 = open('BIOS+OPT_LO.BIN', "wb")   # Low  or Even Chip
    file8 = open('BIOS+OPT_HI.BIN', "wb")   # High or Odd  Chip
    file7.write(bytes(byte_content_BIOS_LO_new))
    file8.write(bytes(byte_content_BIOS_HI_new))
    file7.close()
    file8.close()



input(txtcolor.GOOD + "finished!" + txtcolor.normal)