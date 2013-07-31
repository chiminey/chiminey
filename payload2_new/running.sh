#!/bin/sh

IDS=$1
completed=0
completed_procs=""
procs=0

while read line
do
    cd $line
    procs=`expr $procs + 1 `
    msg=`make running IDS=$IDS`
    if [[ "$msg" ==  *"stopped"* ]];
    then
            completed=`expr $completed + 1 `
            completed_procs=`echo  $completed_procs " $line,"`
    fi
    cd ..
done < $IDS

if [ $procs == 0 ]
then
        echo "The process ID file is empty "
        exit
fi


#if [ $completed == $procs ] && [ $completed != 0 ];

if [ $completed == $procs ];
then
        echo "All processes completed execution"
else
        echo "$completed of $procs processes completed execution"
        echo  $completed_procs
fi