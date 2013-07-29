#!/bin/sh

ID=`sed 's/\..*$//' <run.pid`

nqstat > nqstat.out 
RUNNING=`grep "^${ID} R" nqstat.out`
SUSPENDED=`grep "^${ID} S" nqstat.out`
QUEUED=`grep "^${ID} Q" nqstat.out`

echo $VAR
if [ "$RUNNING" ]
then
  echo stillrunning 
fi
if [ "$SUSPENDED" ]
then
  echo stillrunning 
fi
if [ "$QUEUED" ]
then
  echo stillrunning 
fi

