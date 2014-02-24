#!/bin/sh
# version 2.0

command -v f95 >/dev/null 2>&1 || { echo >&2 "f95 not installed Aborting."; exit 1; }
command -v g77 >/dev/null 2>&1 || { echo >&2 "g77 not installed Aborting."; exit 1; }
command -v dos2unix >/dev/null 2>&1 || { echo >&2 "dos2unix not installed Aborting."; exit 1; }

echo Environment Setup Completed

