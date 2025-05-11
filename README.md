# insert-OptROM-into-BIOS
This Python code insert a Option ROM into a empty space into the BIOS ROM

The Script was initial designed to implement the XTIDE ROM into a Bondwell B310 BIOS ROM. This works well. For other BIOS ROMs, you must change the three offset values in the script.

This code implementing the XTIDE ROM into a BIOS ROM. This code is for a tow BIOS ROM chip (HI and LO).
To run you need the following files:
  * the script him self in the directory
  * BIOS_HI.BIN file with the dump of the HI or Even part of the BIOS
  * BIOS_LO.BIN file with the dump of the LO or Odd  part of the BIOS
  * XTIDE.BIN with a configured XTIDE ROM image


With all these files in one directory you must only execute the script and you get a patches new BIOS file ("BIOS+XTIDE.BIN") and the HI and LO part for the EPROMs ("BIOS+XTIDE_HI.BIN" and "BIOS+XTIDE_LO.BIN").

The idea, the solution and the code is from Sebastian-gthb

ToDo's:
  * calculating the jumpdestinations insted hard coded <-- solved!
  * searching for free space in original BIOS ROM
  * placing the XTIDE ROM and the subfunction automaticly into free space in the BIOS ROM
  * error handling if files ar missing 
