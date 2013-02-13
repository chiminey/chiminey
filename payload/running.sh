#!/bin/sh

PID=`cat AEAO_v1_1/run.pid`
PSD_PACKAGE="PSDCode"

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
        mkdir -p AEAO_v1_1/PSD_output
        cp PSDCode/psd_output AEAO_v1_1/PSD_output/
        cp PSDCode/PSD_exp.dat AEAO_v1_1/PSD_output/
        cp PSDCode/psd.dat AEAO_v1_1/PSD_output/
        echo stopped

    fi

else
  	cp -f AEAO_v1_1/hrmc[0-9]* $PSD_PACKAGE/
  	rm -f $PSD_PACKAGE/hrmc*.out
  	cp -f $PSD_PACKAGE/hrmc*.xyz $PSD_PACKAGE/hrmc01.xyz
  	cd $PSD_PACKAGE; ./PSD >& psd_output &  echo "$!" > "run.pid"
  	echo stillrunning

fi