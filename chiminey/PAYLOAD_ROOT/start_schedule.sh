#!/bin/bash

PAYLOAD_NAME=$1
IDS=$2
OUTPUT_DIR=$3
INPUT_DIR=$4

while read line
do
    start_time=`date +"%Y-%m-%d %H:%M:%S.%3N"`
    mkdir -p $line/$OUTPUT_DIR
    mkdir -p $line/$INPUT_DIR
    cp -r $PAYLOAD_NAME/*  $line
    cd $line
    echo "$line" > task.id
    make start_process_schedule $INPUT_DIR $OUTPUT_DIR
    cd ..
    sed -i "s/SCHED_START_TIME/$start_time/" $line/timedata.txt
done < $IDS
