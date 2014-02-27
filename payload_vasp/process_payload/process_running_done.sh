#!/bin/sh

cd ./vasp

ID=`sed 's/\..*$//' <run.pid`

nqstat > nqstat.out
RUNNING=`grep "^${ID} R" nqstat.out`
SUSPENDED=`grep "^${ID} S" nqstat.out`
QUEUED=`grep "^${ID} Q" nqstat.out`

echo $RUNNING
if [ "$RUNNING" ]
then
  echo  running stillrunning
  exit 
fi
echo $SUSPENDED
if [ "$SUSPENDED" ]
then
  echo suspended stillrunning
  exit
fi
echo $QUEUED
if [ "$QUEUED" ]
then
  echo queued stillrunning
  exit 
fi

OUTPUT=`ls | grep "o${ID}" | wc -l`
if [[ "$OUTPUT" == 0 ]]; then
  echo stillrunning
else
  echo stopped
fi

echo $OUTPUT


