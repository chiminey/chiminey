#!/bin/bash

PAYLOAD_NAME=$1
IDS=$2
OUTPUT_DIR=$3
INPUT_DIR=$4

while read line
do
    mkdir -p $line/$OUTPUT_DIR
    mkdir -p $line/$INPUT_DIR
    cp -r $PAYLOAD_NAME/*  $line
    cd $line
    make start_process_schedule $INPUT_DIR $OUTPUT_DIR
    cd ..
done < $IDS
