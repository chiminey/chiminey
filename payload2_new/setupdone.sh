#!/bin/sh
# version 2.0
PSD_PACKAGE="PSDCode"
HRMC_PACKAGE="HRMC2"

command -v f95 >/dev/null 2>&1 || { echo >&2 "f95 not installed Aborting."; exit 1; }
command -v g77 >/dev/null 2>&1 || { echo >&2 "g77 not installed Aborting."; exit 1; }
command -v dos2unix >/dev/null 2>&1 || { echo >&2 "dos2unix not installed Aborting."; exit 1; }
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
echo Deployment Completed
