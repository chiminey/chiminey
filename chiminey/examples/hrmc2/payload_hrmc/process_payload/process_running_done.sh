#!/bin/sh
# version 2.0

PSD_PACKAGE="PSDCode"
HRMC_PACKAGE="HRMC2"
PSD_OUTPUT=$HRMC_PACKAGE"/PSD_output"

PID=`cat $HRMC_PACKAGE/run.pid`
echo $PID
if [ `ps -p $PID | wc -l` -gt 1 ]
then
  # hrmc is still running
  echo stillrunning
elif [ -e "$PSD_PACKAGE/run.pid" ]
then
    # hrmc as stopped
    POST_PID=`cat $PSD_PACKAGE/run.pid`
    if [ `ps -p $POST_PID | wc -l` -gt 1 ]
    then
        # psd still running
        echo stillrunning
    else
        # psd has finished
        mkdir -p $PSD_OUTPUT
        cp $PSD_PACKAGE/psd_output $PSD_OUTPUT/
        cp $PSD_PACKAGE/PSD_exp.dat $PSD_OUTPUT/
        cp $PSD_PACKAGE/psd.dat $PSD_OUTPUT/
        echo stopped
    fi
else
    # hrmc has just finished, need to start psd
    #rm -f $PSD_PACKAGE/xyz_final.xyz
    rm -f $PSD_PACKAGE/psd.dat
    rm -f $PSD_PACKAGE/psd_output
    cp -f $HRMC_PACKAGE/xyz_final.xyz $PSD_PACKAGE/
    cd $PSD_PACKAGE; ./PSD >& psd_output &  echo "$!" > "run.pid"
    echo stillrunning

fi