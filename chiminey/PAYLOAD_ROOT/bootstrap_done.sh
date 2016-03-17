#!/bin/sh

PID=`cat bootstrap.pid`

if [ `ps -p $PID | wc -l` -gt 1 ]
then
  # program is still running
  echo stillrunning

else
    echo Environment Setup Completed
fi


