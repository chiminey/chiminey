#!/bin/sh
# version 2.0
PSD_PACKAGE="PSDCode"
HRMC_PACKAGE="HRMC2"

if [ ! -f $HRMC_PACKAGE/HRMC ];
then
    echo "HRMC File not found!"
    exit 1;
fi
if [ ! -f $PSD_PACKAGE/PSD ];
then
    echo "PSD File not found!"
    exit 1;
fi

echo Process Setup Completed
