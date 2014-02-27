#!/bin/sh

IDS=$1
completed=0
completed_procs=""
procs=0

while read line
do
    cd $line
    procs=`expr $procs + 1 `
    msg=`make process_schedule_done IDS=$IDS`
    if [[ "$msg" ==  *"Process Setup Completed"* ]];
    then
            completed=`expr $completed + 1 `
            completed_procs=`echo  $completed_procs " $line,"`
    fi
    cd ..
done < $IDS

if [ $completed == $procs ];
then
        echo "All processes are scheduled"
else
        echo "$completed of $procs processes scheduled"
        echo  $completed_procs
fi