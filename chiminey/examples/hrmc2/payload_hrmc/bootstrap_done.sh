#!/bin/sh
# version 2.0

command -v f95 >/dev/null 2>&1 || { echo >&2 "f95 not installed Aborting."; exit 1; }
# g77 is obsolete and not included in centos 7, but gfortran should work in compatibility mode
#command -v g77 >/dev/null 2>&1 || { echo >&2 "g77 not installed Aborting."; exit 1; }
command -v gfortran >/dev/null 2>&1 || { echo >&2 "gfortran not installed Aborting."; exit 1; }
command -v dos2unix >/dev/null 2>&1 || { echo >&2 "dos2unix not installed Aborting."; exit 1; }

echo Environment Setup Completed

