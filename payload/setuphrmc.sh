#!/bin/sh
yum -y install unzip dos2unix gcc-gfortran compat-gcc-34-g77.x86_64
tar --extract --gunzip --verbose --file=aeao_v1_1_package.tar.gz
g77 AEAO_v1_1/HRMC.f -o AEAO_v1_1/HRMC
rm -rf PSDCode
unzip -o PSDCode.zip
cd PSDCode; g77 PSD.f -o PSD
