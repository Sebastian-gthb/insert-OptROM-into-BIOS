# insert-OptROM-into-BIOS
This Python code insert a Option ROM into a empty space in a BIOS ROM (for the era of 286 and 386 CPUs).

Status = finished and need to be tested with different types of BIOS

The Script was initial designed to implement the XTIDE ROM into a Bondwell B310 BIOS ROM. This works well. For other BIOS ROMs the script should automaticly search and check all conditions to place an option ROM in to the BIOS ROM.
The Script supporting automaticly search for the BIOS call to the function "SearchOptionRomAndCall". So we use this call to implement a new SubFunction that call the option ROM. This call came to the exact right time in the boot process to load option ROMs. The script supports Award, AMI, Phoenix, Pegasus, Vadem, Quadtel, Zenith and "Chips and Technologies" BIOS types. If you have found an unsupportet BIOS (error message = No known pattern found for a call in BIOS. Manual disassembling and search required!) feel free to contact me and i try to implement this.

To run you need the following files:
  * the script him self in the directory
  * BIOS_HI.BIN and BIOS_LO.BIN file with the dump of the HI (Odd) and LO (Even) part of the BIOS
  * or BIOS.BIN file with the dump of the BIOS from a one chip ROM
  * OptROM.BIN with a option ROM image like a configured XTIDE ROM image

With all these files in one directory you must only execute the script and you get a patches new BIOS file ("BIOS+OPT.BIN") and if you start with a splited HI+LO ROM you get the HI and LO part for the EPROMs ("BIOS+OPT_HI.BIN" and "BIOS+OPT_LO.BIN").

Patch_BIOS_with_OptROM.py is the script to insert the option ROM into the BIOS ROM image.

Analyse_many_BIOS_Files.py is a script to check all *.bin files in the same directory for the conditions to insert a option ROM. 

WARNING: Use this script at your own risk. It is currently not well tested. Have a working backup of your original BIOS ROMs or keep the original ROMs and test the result with spare ROMs.

The idea, the solution and the code is from Sebastian-gthb.

ToDo's:
   * creating a library to use the same functions in both scripts
   * check if the Option ROM is already insert in the BIOS

Changes:
   * calculating the jump destinations insted hard coded <-- solved!
   * searching for free space in original BIOS ROM <-- solved!
   * placing the option ROM automaticly into free space in the BIOS ROM  <-- solved!
   * handle HI and LO or one-chip-BIOS <-- solved!
   * error handling if files ar missing <-- solved!
   * automaticly found the BIOS call to the sub function "SearchOptionRomAndCall" <-- solved!
   * placing the subfunction automaticly into free space in the BIOS ROM <-- solved!
   * set the right checksum of the ROM <-- solved!
   * third serach for empty space market as 0xCF for Vedem BIOS types <-- solved!
   * adding more BIOS search pattern... have found some ROMs with unknown pattern <-- solved!
   * recreating the original checksum of the BIOS ROM insted of a checksum of 0 <-- solved!


### Example output of the script is:
```
Working directory = C:\Users\user\Documents\B310
Loding BIOS as HI and LO chip and merge both parts...
   BIOS ROM size = 65536 byte.   checksum = 0x1e
Loding option ROM...
Search for the SearchForOptionRom call in the BIOS...
   search with pattern for Award BIOS
   Call found with pattern for Award BIOS at 0x8b4f
   search with pattern for Pegasus BIOS
   search with pattern for Phoenix 1987 BIOS
   search with pattern for Phoenix 1988 BIOS
   search with pattern for Vadem BIOS
   search with pattern for AMI BIOS
   search with pattern for Chips and Technologie BIOS
   search with pattern for Quadtel BIOS
   search with pattern for Zenith BIOS
Search for free space in the BIOS ROM to place the option ROM...
     25120 byte of 0X00 at   0xde0             224 byte of 0X00 at  0x7020              32 byte of 0X00 at  0x72e0
       128 byte of 0X00 at  0x7380             227 byte of 0X00 at  0x7420            2656 byte of 0X00 at  0x75a0
       960 byte of 0X00 at  0xdc40             113 byte of 0X00 at  0xe680              35 byte of 0X00 at  0xfec0
   Found 1 free space blocks to place 8192 bytes at ['0xde0']
Insert option ROM into BIOS...
   inserting 8192 byte code in 65536 byte of BIOS ROM, at position 0xde0
Search for free space in the BIOS ROM to place the new subfunction...
      1565 byte of 0X00 at  0x27c0           16928 byte of 0X00 at  0x2de0             224 byte of 0X00 at  0x7020
        32 byte of 0X00 at  0x72e0             128 byte of 0X00 at  0x7380             227 byte of 0X00 at  0x7420
      2656 byte of 0X00 at  0x75a0             960 byte of 0X00 at  0xdc40             113 byte of 0X00 at  0xe680
        35 byte of 0X00 at  0xfec0
   Found 10 free space blocks to place 14 bytes at ['0x27c0', '0x2de0', '0x7020', '0x72e0', '0x7380', '0x7420', '0x75a0', '0xdc40', '0xe680', '0xfec0']
   Search the closest free space...
      offsetCall = 0x8b4f
      closest space at 0x75a0
   Check it's in range of a near call...
      Distance = 5551 and may not be greater than 32767
calculating all the call destinations...
   Segment adress for OptROM = 0xf0de
      low  byte = 0xde
      high byte = 0xf0
   readed distance from BIOS call to original SubFunc is 726   The offset of the original SubFunction is 0x8e28
   calculated distance for the call in the new SubFunc from 0x75ac to original SubFunc 0x8e28 = 6268 0x187c
      low  byte = 0x7c
      high byte = 0x18
   calculated distance for the call from 0x8b4f to SubFunc 0x75a0 = -5554 0xea4e
      low  byte = 0x4e
      high byte = 0xea
Insert subfunction to call the option ROM...
   inserting 14 byte code in 65536 byte of BIOS ROM, at position 0x75a0
Callculating checksum and correcting to the original checksum...
   Current checksum is 0x22 and now adding 0xfc to be 0x1e
   New corrected checksum is now 0x1e
Save patched BIOS to file...
Split BIOS in to HI an LO file...
finished!
```
