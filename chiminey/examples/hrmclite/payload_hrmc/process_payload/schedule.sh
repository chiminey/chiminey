#!/bin/sh

INPUT_DIR=$1
OUTPUT_DIR=$2


tar --extract --gunzip --verbose --file=HRMC2.tar.gz
f95 HRMC2/hrmc.f90 -fno-align-commons -o HRMC
