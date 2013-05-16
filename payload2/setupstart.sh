#!/bin/sh
# version 2.0
yum -y install dos2unix gcc-gfortran compat-libgfortran-41 compat-gcc-34-g77.x86_64
tar --extract --gunzip --verbose --file=HRMC2.tar.gz
f95 HRMC2/hrmc.f90 -fno-align-commons -o HRMC2/HRMC
tar --extract --gunzip --verbose --file=PSDCode.tar.gz
g77 PSDCode/PSD.f -o PSDCode/PSD
