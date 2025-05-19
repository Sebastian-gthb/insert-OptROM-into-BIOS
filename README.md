# insert-OptROM-into-BIOS
This Python code insert a Option ROM into a empty space into the BIOS ROM

The Script was initial designed to implement the XTIDE ROM into a Bondwell B310 BIOS ROM. This works well. For other BIOS ROMs, you must change one offset values in the script.
The Script supporting automaticly search for the BIOS call to the function "SearchOptionRomAndCall". I't supports Award, Phoenix, Pegasus and Vadem BIOS types. 

To run you need the following files:
  * the script him self in the directory
  * BIOS_HI.BIN and BIOS_LO.BIN file with the dump of the HI (Even) and LO (Odd) part of the BIOS
  * or BIOS.BIN file with the dump of the BIOS from a one chip ROM
  * OptROM.BIN with a option ROM image like a configured XTIDE ROM image


With all these files in one directory you must only execute the script and you get a patches new BIOS file ("BIOS+OPT.BIN") and if you start with a splited HI+LO ROM you get the HI and LO part for the EPROMs ("BIOS+OPT_HI.BIN" and "BIOS+OPT_LO.BIN").

The idea, the solution and the code is from Sebastian-gthb

ToDo's:
   * placing the subfunction automaticly into free space in the BIOS ROM
   * set the right checksum of the ROM
   * check if the Option ROM is already insert in the BIOS

Changes:
   * calculating the jump destinations insted hard coded <-- solved!
   * searching for free space in original BIOS ROM <-- solved!
   * placing the option ROM automaticly into free space in the BIOS ROM  <-- solved!
   * handle HI and LO or one-chip-BIOS <-- solved!
   * error handling if files ar missing <-- solved!
   * automaticly found the BIOS call to the sub function "SearchOptionRomAndCall" <-- solved!
