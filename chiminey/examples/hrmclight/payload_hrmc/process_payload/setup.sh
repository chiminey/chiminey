#!/bin/sh
# version 2.0

PROC_DESTINATION=$1

tar --extract --gunzip --verbose --file=HRMC2.tar.gz
f95 HRMC2/hrmc.f90 -fno-align-commons -o $PROC_DESTINATION/HRMC