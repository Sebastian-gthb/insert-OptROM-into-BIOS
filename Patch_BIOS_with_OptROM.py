# This code implementing the XTIDE ROM into a BIOS ROM. This code is for a tow BIOS ROM chip (HI and LO).
# To run you need the following files:
#   * the script him self in the directory
#   * BIOS_HI.BIN file with the dump of the HI or Even part of the BIOS
#   * BIOS_LO.BIN file with the dump of the LO or Odd  part of the BIOS
#   * XTIDE.BIN with a configured XTIDE ROM image

#
# With all these files in one directory you must only execute the script and you get a patches new BIOS file ("BIOS+XTIDE.BIN") and the HI and LO part for the EPROMs ("BIOS+XTIDE_HI.BIN" and "BIOS+XTIDE_LO.BIN").
#
# The idea, the solution and the code is from Sebastian Berger.
#
#
# ToDo's:
#   * calculating the jumpdestinations insted hard coded <-- solved!
#   * searching for free space in original BIOS ROM
#   * placing the XTIDE ROM and the subfunction automaticly into free space in the BIOS ROM
#   * set the right checksum of the ROM
#   * error handling if files ar missing 


offsetOptROM  = 0x2000   # Possition an der der XTIDE Code in das BIOS ROM eingefüght werden soll. (Größe 8kB!) It must be a multiple of 16!
offsetSubFunc = 0xDC50   # Possition an der der Code für die SubFunction in das BIOS ROM eingefüght werden soll
offsetCall    = 0x8B4F   # Position des Call zu einer Subfunction, an der wir die Zieladresse austauschen um die eingefüghte Subfunction aufzurufen (8B4F). Achtung Sprungmarken im Code sind aktuell nox fix und damit schlecht änderbar!


import os
import sys
workdir = os.path.dirname(os.path.realpath(__file__))
os.chdir(workdir)

print("Working directory =", workdir)

# STEP 0 ------------------------------------------------
print("Checking options...")

#check if the offsetOptROM is a multiple of 16 (Segment adress is divided by 16)
offsetOptROMtest = offsetOptROM >> 4
offsetOptROMtest <<= 4
if offsetOptROM - offsetOptROMtest != 0:
    print("ERROR: offset for the Option ROM (", hex(offsetOptROM), ") is not a multiple of 16!")
    input("Abort!")
    sys.exit()



# STEP 1 ------------------------------------------------
print("Loding BIOS HI and LO part...")

#File 1 = Lo oder OD Chip
file1 = open('BIOS_LO.BIN', "rb")
#File 2 = Hi oder Ev Chip
file2 = open('BIOS_HI.BIN', "rb")
byte_content_BIOS_LO = bytearray(file1.read(-1))
byte_content_BIOS_HI = bytearray(file2.read(-1))
file1.close()
file2.close()


# STEP 2 ------------------------------------------------
print("Merge the BIOS HI and LO part...")

byte_content_BIOS = bytearray()

i = 0
while i < len(byte_content_BIOS_LO):
    byte_content_BIOS.append(byte_content_BIOS_LO[i])
    byte_content_BIOS.append(byte_content_BIOS_HI[i])
    i += 1

# we can save the merged BIOS if needed
#file3 = open('BIOS.BIN', "wb")
#file3.write(bytes(byte_content_BIOS))
#file3.close()




print("---------------Sprungberechnungen-------------")
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

input("-------Sprungberechnung-fertig----------------")



# STEP 3 ------------------------------------------------
print("Insert XTIDE ROM into BIOS...")

# now we need "offsetOptROM"

#File 4 = XTIDE ROM Code
file4 = open('XTIDE.BIN', "rb")
byte_content_XTIDE = bytearray(file4.read(-1))
file4.close()


i = 0
warnung = 0
position = offsetOptROM
FirstSameByte = byte_content_BIOS[position]
print("   inserting", len(byte_content_XTIDE), "byte code in", len(byte_content_BIOS), "byte of BIOS code, at position", hex(offsetOptROM))

if offsetOptROM + len(byte_content_XTIDE) > len(byte_content_BIOS):
    print("ERROR: offset + XTIDE-ROM length to long for BIOS")
    input("Abort!")
    sys.exit()


while i < len(byte_content_XTIDE):

    if byte_content_BIOS[position] != FirstSameByte:
        if warnung == 0:
            print("WARNING: found content at: ", end='')
            warnung = 1
        print(position, " ", end='')


    byte_content_BIOS[position] = byte_content_XTIDE[i]

    i += 1
    position += 1

if warnung != 0: print(" ")


# STEP 4 ------------------------------------------------
print("Insert subfunction to call XTIDE ROM...")

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


# STEP 6 ------------------------------------------------
print("Save patched BIOS to file...")

file6 = open('BIOS+XTIDE.BIN', "wb")
file6.write(bytes(byte_content_BIOS))
file6.close()


# STEP 7 ------------------------------------------------
print("Split BIOS in to HI an LO file...")

byte_content_BIOS_LO_new = bytearray()
byte_content_BIOS_HI_new = bytearray()

i = 0
while i < len(byte_content_BIOS):
    byte_content_BIOS_LO_new.append(byte_content_BIOS[i])
    i += 1
    byte_content_BIOS_HI_new.append(byte_content_BIOS[i])
    i += 1


#File 7 = Lo oder OD Chip
file7 = open('BIOS+XTIDE_LO.BIN', "wb")
#File 8 = Hi oder Ev Chip
file8 = open('BIOS+XTIDE_HI.BIN', "wb")
file7.write(bytes(byte_content_BIOS_LO_new))
file8.write(bytes(byte_content_BIOS_HI_new))
file7.close()
file8.close()



input("finished!")