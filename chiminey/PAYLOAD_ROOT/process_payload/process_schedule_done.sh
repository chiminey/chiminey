#!/bin/bash

PID=`cat setup.pid`

if [ `ps -p $PID | wc -l` -gt 1 ]
then
  # program is still running
  echo stillrunning

else
    echo Process Setup Completed
fi
