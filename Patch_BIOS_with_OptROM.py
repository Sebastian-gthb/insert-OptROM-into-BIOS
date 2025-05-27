# This code implementing the option ROM (like XTIDE) into a BIOS ROM.

# To run you need the following files:
#   * the script him self in the directory
#   * BIOS_HI.BIN and BIOS_LO.BIN file with the dump of the HI (Even) and LO (Odd) part of the BIOS
#   * or BIOS.BIN file with the dump of the BIOS from a one chip ROM
#   * OptROM.BIN with a option ROM image like a configured XTIDE ROM image
#
# With all these files in one directory you must only execute the script and you get a patches new BIOS file ("BIOS+OPT.BIN") and the HI and LO part for the EPROMs ("BIOS+OPT_HI.BIN" and "BIOS+OPT_LO.BIN").
#
# The idea, the solution and the code is from Sebastian-gthb.
#
#
# ToDo's:
#   * calculating the jumpdestinations insted hard coded <-- solved!
#   * searching for free space in original BIOS ROM <-- solved!
#   * placing the option ROM automaticly into free space in the BIOS ROM  <-- solved!
#   * handle HI and LO or one-chip-BIOS <-- solved!
#   * error handling if files are missing <-- solved!
#   * automaticly found the BIOS sub function to SearchOptionRomAndCall and read the offset of this call <-- solved!
#   * placing the subfunction automaticly into free space in the BIOS ROM <-- solved!
#   * set the right checksum of the ROM <-- solved!
#   * third serach for empty space market as 0xCF for Vedem BIOS types <-- solved!

#   * check if the Option ROM is already insert in the BIOS



# code for the SubFunc to call the Option ROM with blanced call destinations. The destinations are calculated and set in this script.
byte_content_SubFunc = bytearray(b'\x60\x9C\x9A\x03\x00\x00\x00\x9D\x61\xE8\x00\x00\xC3\x00')
#                                                       ^^^^^^^             ^^^^^^^     ^^^
#                                             Segment of OptROM             |||||||     used for changing the checksum
#                                                                           |||||||
#                                                               distance to the orig. SubFunction
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

def readFileContent(filename):                              # function to read a file with error handling
    try:
        file1 = open(filename, "rb")
        byte_content=bytearray(file1.read(-1))
        file1.close()
    except FileNotFoundError:
        print("ERROR: FileNotFound", filename)
        input("Abort!")
        sys.exit()
    return byte_content


def searchForFreeSpace(byte_content_BIOS, freeSpaceSize):      # function to search for free space and return a list of offsets
    blocksize = 32            # minimum block size of free space (must be a multible of 16)
    freeSpaceList = []        # generate a empty list
    
    # search for free space marked as 0x00
    i = 0
    countFreeROM = 0
    startblock = 0
    


    while i < len(byte_content_BIOS):
        if byte_content_BIOS[i]==0x00:
            if startblock==0: startblock = i
            countFreeROM += 1
            i += 1
        else:
       
            if countFreeROM >= blocksize:
                print("   free space (0x00) found at offset", hex(startblock), "with size", countFreeROM)
                if countFreeROM >= freeSpaceSize:
                    #print("   space size found at offset", hex(startblock))
                    freeSpaceList.append(startblock)
            countFreeROM = 0
            startblock = 0
            i >>= 5     #unset the lower 4 bits
            i <<= 5
            i += blocksize

    # search again for empty space marked as 0xFF
    i = 0
    countFreeROM = 0
    startblock = 0

    while i < len(byte_content_BIOS):
        if byte_content_BIOS[i]==0xFF:
            if startblock==0: startblock = i
            countFreeROM += 1
            i += 1
        else:
       
            if countFreeROM >= blocksize:
                print("   free space (0xFF) found at offset", hex(startblock), "with size", countFreeROM)
                if countFreeROM >= freeSpaceSize:
                    #print("   space size found at offset", hex(startblock))
                    freeSpaceList.append(startblock)
            countFreeROM = 0
            startblock = 0
            i >>= 5     #unset the lower 4 bits
            i <<= 5
            i += blocksize


    # search again for empty space marked as 0xCF (Vadem BIOS types)
    i = 0
    countFreeROM = 0
    startblock = 0

    while i < len(byte_content_BIOS):
        if byte_content_BIOS[i]==0xCF:
            if startblock==0: startblock = i
            countFreeROM += 1
            i += 1
        else:
       
            if countFreeROM >= blocksize:
                print("   free space (0xCF) found at offset", hex(startblock), "with size", countFreeROM)
                if countFreeROM >= freeSpaceSize:
                    #print("   space size found at offset", hex(startblock))
                    freeSpaceList.append(startblock)
            countFreeROM = 0
            startblock = 0
            i >>= 5     #unset the lower 4 bits
            i <<= 5
            i += blocksize

    freeSpaceList.sort()
    print("   Found", len(freeSpaceList), "free space blocks to place", freeSpaceSize, "bytes at", list(map(hex, freeSpaceList)))
    return freeSpaceList


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
    print("Loding BIOS as one chip file...")
    byte_content_BIOS = readFileContent("BIOS.BIN")

    twoChipBios = False   # flag for spliting BIOS in HI and LO part

# STEP 2 ------------------------------------------------
print("Loding option ROM...")

byte_content_OptROM  = readFileContent("OptROM.BIN")


# STEP 3 ------------------------------------------------
print("Search for the SearchForOptionRom call in the BIOS...")

searchpattern = [bytearray(b'\xBB\x00\xC8\xBA\x00\xE0\xE8'),         "Award",      #search pattern 0 for Award BIOS (Bondewell B310)
                 bytearray(b'\xB8\x00\xC0\xBA\x80\xC7\xB7\x02\xE8'), "Pegasus",    #search pattern 1 for Pegasus BIOS (Olivetti)
                 bytearray(b'\x32\xD2\xBE\x00\xC8\xB9\x00\xE0\xE8'), "Phoenix",    #search pattern 2 for Phoenix BIOS (Sharp PC5541)
                 bytearray(b'\xBB\x00\xC8\xBF\x00\xF0\xE8'),         "Vadem",      #search pattern 3 for Vadem BIOS (Sharp PC4521)
                 bytearray(b'\xE6\x80\xBB\x00\xC8\xE8'),             "AMI",        #search pattern 4 for AMI BIOS some (386 BIOS ROMs)
                 bytearray(b'\xBB\x00\xC8\xB9\x00\x00\xC1\xE9\x04\x81\xC1\x00\x28\xBF\x55\xAA\xE8'), "Chips and Technologie" ]    #search pattern 5 for Chips and Technologies

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
            #print(hex(searchpattern[patternNumber][patternpossition])," ", end='')
            patternpossition += 1
            if patternpossition == patternlength:
                print("   Call found with pattern for", searchpattern[patternNumber+1], "BIOS at", hex(i))
                offsetCall = i
                patternFound += 1
                patternpossition = 0
        else:
            if patternpossition != 0:
                #print(" ")
                patternpossition = 0
        i += 1
    
    patternNumber += 2

if patternFound == 0:
    print("No known pattern found for a call in BIOS. Manual disassembling and search required!")
    print("You can send the BIOS file to the developer to improve this script.")
    input("Abort!")
    sys.exit()
    
if patternFound > 1:
    print("Found too many hits for a call in BIOS. Manual disassembling and search required!")
    print("You can send the BIOS file to the developer to improve this script.")
    input("Abort!")
    sys.exit()



# STEP 4 ------------------------------------------------
print("Search for free space in the BIOS ROM to place the option ROM...")

freeSpaceList = searchForFreeSpace(byte_content_BIOS, len(byte_content_OptROM))

if len(freeSpaceList) == 0:
    print("ERROR: not enough empty space found in BIOS ROM to insert the option ROM")
    input("Abort!")
    sys.exit()

offsetOptROM = freeSpaceList[0]       # use the first free space block to insert the option ROM



# STEP 5 ------------------------------------------------
print("Insert option ROM into BIOS...")

# now we need "offsetOptROM"
i = 0
warnung = 0
position = offsetOptROM
FirstSameByte = byte_content_BIOS[position]
print("   inserting", len(byte_content_OptROM), "byte code in", len(byte_content_BIOS), "byte of BIOS ROM, at position", hex(offsetOptROM))

if offsetOptROM + len(byte_content_OptROM) > len(byte_content_BIOS):
    print("ERROR: offset + option ROM length to long for BIOS")
    input("Abort!")
    sys.exit()


while i < len(byte_content_OptROM):

    if byte_content_BIOS[position] != FirstSameByte:
        if warnung == 0:
            print("WARNING: found content at: ", end='')
            warnung = 1
        print(position, " ", end='')


    byte_content_BIOS[position] = byte_content_OptROM[i]

    i += 1
    position += 1

if warnung != 0: print(" ")



# STEP 6 ------------------------------------------------
print("Search for free space in the BIOS ROM to place the new subfunction...")

freeSpaceList = searchForFreeSpace(byte_content_BIOS, len(byte_content_SubFunc))

if len(freeSpaceList) == 0:
    print("ERROR: not enough empty space found in BIOS ROM to insert the new subfunction")
    input("Abort!")
    sys.exit()

if len(freeSpaceList) == 1:
    offsetSubFunc = freeSpaceList[0]          # have we only one free space so use this space
else:
    print("   Search the closest free space...")
    print("      offsetCall =", hex(offsetCall))

    i = 0
    for x in freeSpaceList:
        #print(hex(x))
        if x > offsetCall:
            break
        i += 1

    #print("      ListNumber =", i)
    
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
    print("ERROR: no free space found in a range of a near call.")
    input("Abort!")
    sys.exit()


# STEP 7 ------------------------------------------------
print("calculating all the call destinations...")


# calculating the segment adress of the Option ROM and implementing it in the new SubFunction
print("   BIOS ROM size =", len(byte_content_BIOS), "byte")
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
print("Insert subfunction to call option ROM...")

# now we need "offsetSubFunc"

i = 0
warnung = 0
position = offsetSubFunc
FirstSameByte = byte_content_BIOS[position]
print("   inserting", len(byte_content_SubFunc), "byte code in", len(byte_content_BIOS), "byte of BIOS code, at position", hex(offsetSubFunc))

if offsetSubFunc + len(byte_content_SubFunc) > len(byte_content_BIOS):
    print("ERROR: offset + SubFunc length to long for BIOS")
    input("Abort!")
    sys.exit()

while i < len(byte_content_SubFunc):

    if byte_content_BIOS[position] != FirstSameByte:
        if warnung == 0:
            print("WARNING: found content at: ", end='')
            warnung = 1
        print(position, " ", end='')


    byte_content_BIOS[position] = byte_content_SubFunc[i]

    i += 1
    position += 1

if warnung != 0: print(" ")


# STEP 9 ------------------------------------------------
print("Callculating checksum...")

i = 0
checksum = 0

while i < len(byte_content_BIOS):
    checksum += byte_content_BIOS[i]
    i += 1

checksumaddon = 256 - (checksum & 0xFF)

print("   Current checksum is", hex(checksum & 0xFF), "and now adding", hex(checksumaddon), "to be 0x00")

byte_content_BIOS[offsetSubFunc + 13] = checksumaddon & 0xFF

# check new checksum
i = 0
checksum = 0

while i < len(byte_content_BIOS):
    checksum += byte_content_BIOS[i]
    i += 1

print("   New corrected checksum is now", hex(checksum & 0xFF))



# STEP 10 ------------------------------------------------
print("Save patched BIOS to file...")

file6 = open('BIOS+OPT.BIN', "wb")
file6.write(bytes(byte_content_BIOS))
file6.close()


# STEP 11 ------------------------------------------------
if twoChipBios:
    print("Split BIOS in to HI an LO file...")

    byte_content_BIOS_LO_new = bytearray()
    byte_content_BIOS_HI_new = bytearray()

    i = 0
    while i < len(byte_content_BIOS):
        byte_content_BIOS_LO_new.append(byte_content_BIOS[i])
        i += 1
        byte_content_BIOS_HI_new.append(byte_content_BIOS[i])
        i += 1

    file7 = open('BIOS+OPT_LO.BIN', "wb")   # Lo oder OD Chip
    file8 = open('BIOS+OPT_HI.BIN', "wb")   # Hi oder Ev Chip
    file7.write(bytes(byte_content_BIOS_LO_new))
    file8.write(bytes(byte_content_BIOS_HI_new))
    file7.close()
    file8.close()



input("finished!")