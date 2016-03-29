#!/bin/sh
# version 2.0
# Specify packages that are needed to run your program
#   If your program is going to run on Centos VM and your program requires dos2unix,
#   yum -y install dos2unix
# NB: Notice the '-y' flag.
yum -y install compat-libf2c-34 gcc-gfortran compat-gcc-44-gfortran compat-libgfortran-41 dos2unix
#yum -y install dos2unix gcc-gfortran compat-libgfortran-41 compat-gcc-34-g77.x86_64
