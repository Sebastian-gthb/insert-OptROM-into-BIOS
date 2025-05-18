# This code implementing the option ROM (like XTIDE) into a BIOS ROM. This code is for a tow BIOS ROM chip (HI and LO).
# To run you need the following files:
#   * the script him self in the directory
#   * BIOS_HI.BIN and BIOS_LO.BIN file with the dump of the HI (Even) and LO (Odd) part of the BIOS
#   * or BIOS.BIN file with the dump of the BIOS from a one chip ROM
#   * OptROM.BIN with a option ROM image like a configured XTIDE ROM image
#
# With all these files in one directory you must only execute the script and you get a patches new BIOS file ("BIOS+OPT.BIN") and the HI and LO part for the EPROMs ("BIOS+OPT_HI.BIN" and "BIOS+OPT_LO.BIN").
#
# The idea, the solution and the code is from Sebastian Berger.
#
#
# ToDo's:
#   * calculating the jumpdestinations insted hard coded <-- solved!
#   * searching for free space in original BIOS ROM <-- solved!
#   * placing the option ROM automaticly into free space in the BIOS ROM  <-- solved!
#   * handle HI and LO or one-chip-BIOS <-- solved!
#   * error handling if files are missing <-- partly solved

#   * placing the subfunction automaticly into free space in the BIOS ROM
#      - option one: find a call that called only one time an place the subfunction there <- current state
#      - option tow: simulating an option ROM to an other option ROM location and put the subfunction there. The BIOS will search the option ROM and call it. pro: we must noch find the option-ROM-search-function in the BIOS (it's hard to do in a script). contra: we lost aviable memory of an empty option ROM 
#   * set the right checksum of the ROM
#   * check if the Option ROM is already insert in the BIOS


offsetCall    = 0x8B4F   # Position des Call zu einer Subfunction, an der wir die Zieladresse austauschen um die eingefüghte Subfunction aufzurufen (8B4F). Achtung Sprungmarken im Code sind aktuell nox fix und damit schlecht änderbar!
offsetSubFunc = 0xDC50   # Position an der der Code für die SubFunction in das BIOS ROM eingefüght werden soll



import os
import sys

def readFileContent(filename):
    try:
        file1 = open(filename, "rb")
        byte_content=bytearray(file1.read(-1))
        file1.close()
    except FileNotFoundError:
        print("ERROR: FileNotFound", filename)
        input("Abort!")
        sys.exit()
    return byte_content


workdir = os.path.dirname(os.path.realpath(__file__))
os.chdir(workdir)
print("Working directory =", workdir)


# STEP 1 ------------------------------------------------
# loading BIOS ROM (as HI+LO or as single chip file)

if os.path.isfile("BIOS_LO.BIN"):
    print("Loding BIOS HI and LO and merge both parts...")
    byte_content_BIOS_LO = readFileContent("BIOS_LO.BIN")
    byte_content_BIOS_HI = readFileContent("BIOS_HI.BIN")

    byte_content_BIOS = bytearray()
    i = 0
    while i < len(byte_content_BIOS_LO):
        byte_content_BIOS.append(byte_content_BIOS_LO[i])
        byte_content_BIOS.append(byte_content_BIOS_HI[i])
        i += 1
    
    twoChipBios = True   # flag for spliting BIOS in HI and LO part
    
    # we can save the merged original BIOS if needed
    file4 = open('BIOS.BIN', "wb")
    file4.write(bytes(byte_content_BIOS))
    file4.close()

else:
    print("Loding BIOS one chip file...")
    byte_content_BIOS = readFileContent("BIOS.BIN")

    twoChipBios = False   # flag for spliting BIOS in HI and LO part

# STEP 2 ------------------------------------------------
print("Loding option ROM...")

byte_content_OptROM  = readFileContent("OptROM.BIN")


# STEP 3 ------------------------------------------------
print("Search for free space in the BIOS ROM...")

# search for empty space marked as 0x00
blocksize = 32
i = 0
countFreeROM = 0
startblock = 0
optROMsize = len(byte_content_OptROM)
offsetOptROM  = 0xFFFFF   # init variable to find out that we have found a place for the option ROM

while i < len(byte_content_BIOS):
    if byte_content_BIOS[i]==0x00:
        if startblock==0: startblock = i
        countFreeROM += 1
        i += 1
    else:
       
        if countFreeROM >= blocksize:
            print("free space (0x00) found at offset", hex(startblock), "with size", countFreeROM)
            if countFreeROM >= optROMsize:
                print("space for option ROM found at offset", hex(startblock))
                offsetOptROM = startblock
        countFreeROM = 0
        startblock = 0
        i >>= 5     #unset the lower 4 bits
        i <<= 5
        i += blocksize

# if nothing found search again for empty space marked as 0xFF
if offsetOptROM == 0xFFFFF:
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
                print("free space (0xFF) found at offset", hex(startblock), "with size", countFreeROM)
                if countFreeROM >= optROMsize:
                    print("space for option ROM found at offset", hex(startblock))
                    offsetOptROM = startblock
            countFreeROM = 0
            startblock = 0
            i >>= 5     #unset the lower 4 bits
            i <<= 5
            i += blocksize

if offsetOptROM == 0xFFFFF:
    print("ERROR: not enough empty space found in BIOS ROM to insert the option ROM")
    input("Abort!")
    sys.exit()


# STEP 4 ------------------------------------------------
print("Search for the SearchForOptionRom call in the BIOS...")
searchpattern1 = bytearray(b'\xBB\x00\xC8\xBA\x00\xE0\xE8')            #search pattern for Award   BIOS Bondewell
searchpattern2 = bytearray(b'\xB8\x00\xC0\xBA\x80\xC7\xB7\x02\xE8')    #search pattern for Pegasus BIOS Olivetti
searchpattern3 = bytearray(b'\x32\xD2\xBE\x00\xC8\xB9\x00\xE0\xE8')    #search pattern for Phoenix BIOS Sharp PC4521

i = 0
patternpossition = 0
patternNotFound = True
patternlength = len(searchpattern1)

while i < len(byte_content_BIOS) - patternlength:
    if byte_content_BIOS[i] == searchpattern1[patternpossition]:
        #print(hex(searchpattern1[patternpossition])," ", end='')
        patternpossition += 1
        if patternpossition == patternlength:
            print("   Call found at", hex(i))
            patternNotFound = False
            patternpossition = 0
    else:
        if patternpossition != 0:
            #print(" ")
            patternpossition = 0
    i += 1

if patternNotFound:
    print("No known pattern for a call fount in BIOS. Manual disassembling and search required!")
    print("You can send the BIOS file to the developer to improve this script.")
    input("Abort!")
    sys.exit()

# STEP 4 ------------------------------------------------
print("calculating all the call destinations...")

# code for the SubFunc to call the Option ROM with blanced call destinations
byte_content_SubFunc = bytearray(b'\x60\x9C\x9A\x03\x00\x00\x00\x9D\x61\xE8\x00\x00\xC3')
#                                                       ^^^^^^^             ^^^^^^^
#                                             Segment of OptROM             distance to the orig. SubFunction
#example:
#f000:dc50    60            pusha
#f000:dc51    9C            pushf
#f000:dc52    9A030000f2    call far f200:0003
#f000:dc57    9D            popf
#f000:dc58    61            popa
#f000:dc59    E8CCB1        call near f000:8E28
#f000:dc5C    C3            ret

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
offsetOrgSubFunc = byte_content_BIOS[offsetCall+1]            #low byte                  Achtung! Wass, wenn hier ein negativer Wert drin steht?!!!!!!!!!!!
offsetOrgSubFunc += byte_content_BIOS[offsetCall+2] << 8      #high byte
offsetOrgSubFunc += offsetCall + 3
callDistanceToOrgSubFunc = offsetOrgSubFunc - (offsetSubFunc + 12)
print("   calculated distance for the call in the new SubFunc from", hex(offsetSubFunc+12), "to original SubFunc", hex(offsetOrgSubFunc),"=", callDistanceToOrgSubFunc, hex(callDistanceToOrgSubFunc))
byte_content_SubFunc[10] = callDistanceToOrgSubFunc & 0xFF
print("      low  byte =", hex(callDistanceToOrgSubFunc & 0xFF))
callDistanceToOrgSubFunc >>= 8
byte_content_SubFunc[11] = callDistanceToOrgSubFunc & 0xFF
print("      high byte =", hex(callDistanceToOrgSubFunc & 0xFF))

# calculating the distance to the new SubFunction and implementing it in the BIOS code
callDistanceToNewSubFunc = offsetSubFunc - (offsetCall + 3)
print("   calculated distance for the call from", hex(offsetCall), "to SubFunc", hex(offsetSubFunc),"=", callDistanceToNewSubFunc, hex(callDistanceToNewSubFunc))
byte_content_BIOS[offsetCall+1] = callDistanceToNewSubFunc & 0xFF
print("      low  byte =", hex(callDistanceToNewSubFunc & 0xFF))
callDistanceToNewSubFunc >>= 8
byte_content_BIOS[offsetCall+2] = callDistanceToNewSubFunc & 0xFF
print("      high byte =", hex(callDistanceToNewSubFunc & 0xFF))



# STEP 5 ------------------------------------------------
print("Insert option ROM into BIOS...")

# now we need "offsetOptROM"
i = 0
warnung = 0
position = offsetOptROM
FirstSameByte = byte_content_BIOS[position]
print("   inserting", len(byte_content_OptROM), "byte code in", len(byte_content_BIOS), "byte of BIOS code, at position", hex(offsetOptROM))

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
print("Insert subfunction to call option ROM...")

# now we need "offsetSubFunc"


# theoretisches vorgehen:
#   insert SubFunction
#   suche im BIOS nach der Stelle welche die SubFuncion "SearchFromBXtoDXforOptionRomAndCall" für BX=C800 und DX=E000 aufruft
#   lies die Zieladresse des Calls dort aus und berechne wo die routine liegt --> Ziel2
#   berechne von dort aus die Sprungentfernung zur neuen SubFunction --> Ziel1
#   ersetze diesen Aufruf mit dem Aufruf der neuen SubFunction (Ziel1)
#   ersetze in der neuen SubFunction den call zu Ziel1 


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


# STEP 7 ------------------------------------------------
print("Callculating check sum...")

i = 0
checksum = 0

while i < len(byte_content_BIOS):
    checksum += byte_content_BIOS[i]
    i += 1
    
print("Checksum =", hex(checksum & 0xFF))


# STEP 8 ------------------------------------------------
print("Save patched BIOS to file...")

file6 = open('BIOS+OPT.BIN', "wb")
file6.write(bytes(byte_content_BIOS))
file6.close()


# STEP 9 ------------------------------------------------
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