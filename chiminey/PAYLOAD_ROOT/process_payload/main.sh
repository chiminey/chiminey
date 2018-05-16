#!/bin/bash

INPUT_DIR=$1
OUTPUT_DIR=$2

exec_end_time=`date +"%Y-%m-%d %H:%M:%S.%3N"`
sed -i "s/EXEC_END_TIME/$exec_end_time/" ./timedata.txt
cp ./timedata.txt $OUTPUT_DIR/timedata.txt
