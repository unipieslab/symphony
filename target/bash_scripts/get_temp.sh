#!/bin/bash
printf "Temp(celsius): PMD=%d, SoC=%d, DIMM=%d\n" $cnt $(i2cget -y 1 0x2f 0x13 w) $(i2cget -y 1 0x2f 0x11 w) $(i2cget -y 1 0x2f 0x12 w) #>> ${file}
	