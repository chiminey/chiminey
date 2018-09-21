#!/bin/bash

parent=$1
OUTPUT_DIR=$2
WATCH_INTERVAL=$3
export LANG=en_AU.UTF-8

get_children() {
    PID_local=$1
    child_list=$PID_local
    seperator=","
    status_local=`ps -p $PID_local | wc -l`
    if [ $status_local -gt 1 ]
    then
        line_count=`ps --ppid $PID_local | wc -l`
        while [ $line_count -gt 1 ]
        do
            PID_local=`ps --ppid $PID_local | tail -1| awk '{ print $1}'`
            child_list=$child_list$seperator$PID_local
            line_count=`ps --ppid $PID_local | wc -l`
        done
        echo $child_list
    fi
    #child_list="2672,2696,2734,2737"
    #echo $child_list
}
get_usage() {
    sum_usage=0.00
    kb_write=0.00
    kb_read=0.00
    proc_id=$1
    procs=`get_children $proc_id`
    process_list=`echo $procs | sed -e 's/,/ /g'` 
    echo "IO Monitoring for processes" > io_statistics.log
    echo $process_list >> io_statistics.log
    echo "====================================" >> io_statistics.log
    if [ ! -z "$procs" ]
    then
        SECONDS=0
        pidstat -d $WATCH_INTERVAL -p $procs &> io_usage.log 
        ELAPSED_TIME=$SECONDS
        for i in $process_list; do
             kb_read_temp1=`grep $i io_usage.log | awk '{ print $4 }' | xargs | sed -e 's/ /+/g' | bc`
             kb_read_temp1=$(bc<<<"scale=2;$kb_read_temp1 * $WATCH_INTERVAL")
             kb_read=$(bc<<<"scale=2;$kb_read + $kb_read_temp1")

             kb_write_temp1=`grep $i io_usage.log | awk '{ print $5 }' | xargs | sed -e 's/ \+/ /g' | sed -e 's/ /+/g' | bc`
             kb_write_temp1=$(bc<<<"scale=2;$kb_write_temp1 * $WATCH_INTERVAL")
             kb_write=$(bc<<<"scale=2;$kb_write + $kb_write_temp1")

             echo "------------------------------------" >> io_statistics.log
             echo "IO Monitor for process: $i" >> io_statistics.log
             echo "KB_Read: $kb_read_temp1" >> io_statistics.log 
             echo "KB_Write: $kb_write_temp1">> io_statistics.log
        done
        if [ "$ELAPSED_TIME" -ne 0 ]
        then
            kb_read_psec=$(bc<<<"scale=2;$kb_read / $ELAPSED_TIME")
            kb_write_psec=$(bc<<<"scale=2;$kb_write / $ELAPSED_TIME")
        else
            kb_read_psec=$kb_read
            kb_write_psec=$kb_write
        fi
        echo "------------------------------------" >> io_statistics.log
        echo "Total KB_Read : $kb_read" >> io_statistics.log 
        echo "Total KB_Write : $kb_write" >> io_statistics.log 
        echo "Elapsed time : $ELAPSED_TIME" >> io_statistics.log 
        echo "Average KB_Read/sec : $kb_read_psec" >> io_statistics.log 
        echo "Average KB_Write/sec :$kb_write_psec">> io_statistics.log

        sed -i "s/AVG_IOREAD/$kb_read_psec/" ./timedata.txt
        sed -i "s/AVG_IOWRITE/$kb_write_psec/" ./timedata.txt
        cp ./timedata.txt $OUTPUT_DIR/timedata.txt
    else
        echo "Empty list. No processses monitored"
    fi
    echo "===============DONE=================" >> io_statistics.log
}

status=`ps -p $parent | wc -l`
if [ $status -gt 1 ]
then
    sleep 1
    get_usage $parent
fi
#get_usage $parent
