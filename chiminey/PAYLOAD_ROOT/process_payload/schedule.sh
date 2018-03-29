#!/bin/sh

INPUT_DIR=$1
OUTPUT_DIR=$2

end_time=`date +"%Y-%m-%d %H:%M:%S.%3N"`
sed -i "s/SCHED_END_TIME/$end_time/" ./timedata.txt
cp ./timedata.txt $OUTPUT_DIR/timedata.txt
