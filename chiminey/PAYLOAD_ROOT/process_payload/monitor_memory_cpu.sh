#!/bin/bash

parent=$1
OUTPUT_DIR=$2
WATCH_INTERVAL=$3
re='^[0-9]+([.][0-9]+)?$'
memory_usage=0.0
cpu_usage=0.0
avg_memory_usage=0.0
avg_cpu_usage=0.0
sum_memory_usage=0.0
sum_cpu_usage=0.0
cpu_usage_count=0
memory_usage_count=0

global_procs_list=""
global_usage_data=""

get_children() {
    PID_local=$1
    child_list=$PID_local
    seperator=' '
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
}

get_usage() {
    proc_id=$1
    option=$2
    local_usage_data=0.0
    procs=`get_children $proc_id`
    if [ ! -z "$procs" ]
    then
        local_usage_data=`ps --no-headers -o $option $procs | xargs`
    fi
    global_procs_list="$procs"
    global_usage_data="$local_usage_data"
}

status=`ps -p $parent | wc -l`
PID=$parent
echo "Monitoring resourse usage"
echo "Parent Process : $PID"
echo "================================="
while [ $status -gt 1 ]
do
    get_usage $PID pmem
    memory_usage=`echo $global_usage_data| xargs | sed -e 's/ /+/g' | bc`
    echo "Process(es) monitored : $global_procs_list"
    echo "Memory usage : $global_usage_data"
    if [[ $memory_usage =~ $re ]]
    then
        if (( $(bc -l<<<"$memory_usage>0.0") ))
        then
            memory_usage_count=`expr $memory_usage_count + 1`
            sum_memory_usage=$(bc<<<"scale=2;$sum_memory_usage + $memory_usage")
            avg_memory_usage=$(bc<<<"scale=2;$sum_memory_usage / $memory_usage_count")
        fi
    fi

    get_usage $PID pcpu
    cpu_usage=`echo $global_usage_data| xargs | sed -e 's/ /+/g' | bc`
    echo "Process(es) monitored : $global_procs_list"
    echo "Cpu usage : $global_usage_data"
    if [[ $memory_usage =~ $re ]]
    then
        if (( $(bc -l<<<"$cpu_usage>0.0") ))
        then
            cpu_usage_count=`expr $cpu_usage_count + 1`
            sum_cpu_usage=$(bc<<<"scale=2;$sum_cpu_usage + $cpu_usage")
            avg_cpu_usage=$(bc<<<"scale=2;$sum_cpu_usage / $cpu_usage_count")
        fi
    fi

    sleep $WATCH_INTERVAL
    echo "---------------------------------"
    status=`ps -p $parent | wc -l`
done
echo "==============DONE==============="

sed -i "s/AVG_MEMORY_USAGE/$avg_memory_usage/" ./timedata.txt
sed -i "s/AVG_CPU_USAGE/$avg_cpu_usage/" ./timedata.txt
cp ./timedata.txt $OUTPUT_DIR/timedata.txt
