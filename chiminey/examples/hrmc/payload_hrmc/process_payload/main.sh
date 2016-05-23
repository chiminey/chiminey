#!/bin/sh
# version 2.0

INPUT_DIR=$1
OUTPUT_DIR=$2

cp HRMC $INPUT_DIR/HRMC
cd $INPUT_DIR
./HRMC >& ../$OUTPUT_DIR/hrmc_output
cp input_bo.dat ../$OUTPUT_DIR/input_bo.dat
cp input_gr.dat ../$OUTPUT_DIR/input_gr.dat
cp input_sq.dat ../$OUTPUT_DIR/input_sq.dat
cp xyz_final.xyz  ../$OUTPUT_DIR/xyz_final.xyz
cp HRMC.inp_template ../$OUTPUT_DIR/HRMC.inp_template

cp -f xyz_final.xyz ../PSDCode/xyz_final.xyz
cd ../PSDCode; ./PSD >&  ../$OUTPUT_DIR/psd_output
cp PSD_exp.dat ../$OUTPUT_DIR/
cp psd.dat ../$OUTPUT_DIR/
