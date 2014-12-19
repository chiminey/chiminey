#!/bin/sh
# version 2.0
tar --extract --gunzip --verbose --file=HRMC2.tar.gz
f95 HRMC2/hrmc.f90 -fno-align-commons -o HRMC2/HRMC
tar --extract --gunzip --verbose --file=PSDCode.tar.gz
#g77 is obsolete in centos 7, but gfortran should work in compatiblity mode
#g77 PSDCode/PSD.f -o PSDCode/PSD
gfortran PSDCode/PSD.f -o PSDCode/PSD
