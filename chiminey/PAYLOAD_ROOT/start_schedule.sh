#!/bin/bash
START_TIME=$SECONDS

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

END_TIME=$SECONDS
ELAPSED_TIME=$(($END_TIME - $START_TIME))

echo "START_SCHEDULE START_TIME=$START_TIME END_TIME=$END_TIME ELAPSED_TIME=$ELAPSED_TIME"
