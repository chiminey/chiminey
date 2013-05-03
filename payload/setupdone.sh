#!/bin/sh
command -v g77 >/dev/null 2>&1 || { echo >&2 "g77 not installed Aborting."; exit 1; }
command -v unzip >/dev/null 2>&1 || { echo >&2 "unzip not installed Aborting."; exit 1; }
command -v dos2unix >/dev/null 2>&1 || { echo >&2 "dos2unix not installed Aborting."; exit 1; }
if [ ! -f AEAO_v1_1/HRMC ];
then
    echo "HRMC File not found!"
    exit 1;
fi
if [ ! -f PSDCode/PSD ];
then
    echo "PSD File not found!"
    exit 1;
fi
echo Deployment Completed
