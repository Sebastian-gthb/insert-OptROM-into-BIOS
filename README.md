# insert-OptROM-into-BIOS
This Python code insert a Option ROM into a empty space into the BIOS ROM

The Script was initial designed to implement the XTIDE ROM into a Bondwell B310 BIOS ROM. This works well. For other BIOS ROMs, you must change tow offset values in the script.

This code is for a tow BIOS ROM chip (HI and LO).

To run you need the following files:
  * the script him self in the directory
  * BIOS_HI.BIN file with the dump of the HI or Even part of the BIOS
  * BIOS_LO.BIN file with the dump of the LO or Odd  part of the BIOS
  * OptROM.BIN with a option ROM image like a configured XTIDE ROM image


With all these files in one directory you must only execute the script and you get a patches new BIOS file ("BIOS+OPT.BIN") and the HI and LO part for the EPROMs ("BIOS+OPT_HI.BIN" and "BIOS+OPT_LO.BIN").

The idea, the solution and the code is from Sebastian-gthb

ToDo's:
   * calculating the jumpdestinations insted hard coded <-- solved!
   * searching for free space in original BIOS ROM <-- partly solved
   * placing the XTIDE ROM and the subfunction automaticly into free space in the BIOS ROM  <-- partly solved
   * set the right checksum of the ROM
   * error handling if files ar missing 
   * check if the Option ROM is already insert in the BIOS
