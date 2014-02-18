#!/bin/sh
PSD_PACKAGE=PSDCode
HRMC_PACKAGE="HRMC2"

rm -f $(PSD_PACKAGE)/run.pid
cd $HRMC_PACKAGE ; ./HRMC >& output &  echo "$!" > "run.pid"

