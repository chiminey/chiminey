#!/bin/sh

PID=`cat AEAO_v1_1/run.pid`
echo $PID
if [ `ps -p $PID | wc -l` -gt 1 ]
then
  echo stillrunning
else
  echo stopped
fi