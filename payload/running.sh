#!/bin/sh

PID=`cat AEAO_v1_1/run.pid`
echo $PID
if [ `ps -p $PID | wc -l` -gt 1 ]
then
  echo stillrunning
elif [ -e "PSDCode/run.pid" ]
then
    POST_PID=`cat PSDCode/run.pid`
    if [ `ps -p $POST_PID | wc -l` -gt 1 ]
    then
        echo stillrunning

    else
        mkdir AEAO_v1_1/PSD_output
        cp PSDCode/psd_output AEAO_v1_1/PSD_output/
        cp PSDCode/PSD_exp.dat AEAO_v1_1/PSD_output/
        cp PSDCode/psd.dat AEAO_v1_1/PSD_output/
        echo stopped

    fi

else
  make run_psd

fi