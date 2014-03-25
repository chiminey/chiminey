#!/bin/sh
# Starts the processes of making separate execution environments for all
# processes that will run on this VM.  Normally, this code should not need to be
# changed.

PAYLOAD_NAME=$1
IDS=$2

while read line
do
    mkdir -p $line
    cp -r $PAYLOAD_NAME/*  $line
    cd $line
    make start_process_schedule PAYLOAD_NAME=$PAYLOAD_NAME IDS=$IDS
    cd ..
done < $IDS
