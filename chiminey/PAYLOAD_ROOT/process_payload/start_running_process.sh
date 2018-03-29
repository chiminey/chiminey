#!/bin/bash

#exec_start_time=`date +"%Y-%m-%d %H:%M:%S.%3N"`
#sed -i "s/EXEC_START_TIME/$exec_start_time/" ./timedata.txt

sh main.sh $@ &  echo "$!" > "run.pid"
