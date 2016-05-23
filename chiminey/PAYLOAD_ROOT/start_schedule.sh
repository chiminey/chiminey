#!/bin/bash

PAYLOAD_NAME=$1
IDS=$2
PROC_DESTINATION=$3

while read line
do
    mkdir -p $line/$PROC_DESTINATION
    cp -r $PAYLOAD_NAME/*  $line
    cd $line
    make start_process_schedule $PROC_DESTINATION
    cd ..
done < $IDS
