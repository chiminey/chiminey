#!/bin/sh

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
