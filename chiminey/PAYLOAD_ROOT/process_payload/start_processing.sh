#!/bin/bash

sh main.sh $@ &  echo "$!" > "run.pid"

PID=`cat run.pid`
OUTPUT_DIR=$2
WATCH_INTERVAL=3
sh monitor_memory_cpu.sh $PID $OUTPUT_DIR $WATCH_INTERVAL &> memory_cpu_usage.log &
sh monitor_io.sh $PID $OUTPUT_DIR $WATCH_INTERVAL &
