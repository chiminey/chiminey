#!/bin/bash

PID=`cat run.pid`

if [ `ps -p $PID | wc -l` -gt 1 ]
then
  # program is still running
  echo stillrunning

else
    echo stopped
fi
