#!/bin/sh
# version 2.0
#-----------------------------------------------------
job_dir=`pwd`
#job_dir=~ec2-user/$job_id/chiminey_payload_copy
host_ip=`hostname -I | awk '{ print $1}'`
pids_collections_file=`find $job_dir -name PIDs_collections`
job_id=`echo $pids_collections_file | sed 's/\// /g' | sed  's/[^0-9]/ /g' | sed 's/^ *//g' | sed 's/ *$//g' | tr -s ' ' | sed 's/ /\n/g' | tail -1`
pid_list=`cat $pids_collections_file | xargs`
#-----------------------------------------------------
log_name="yum_install_disk_usage_log.txt"
echo "Checking yum update history ... .. ."
if [ -e $log_name ]; then rm $log_name; fi
id=`yum history list | awk -F'[^0-9]*' '{print $2}'| xargs`
for i in $id
do
   if [ $i != "1" ]
   then
       yum history info $i >> ./$log_name
   fi
done
yum_update_size_h=`grep "Total download size" $job_dir/bootstrap.output | awk '{ print $4 }'`
yum_update_HS=`grep "Total download size" $job_dir/bootstrap.output | awk '{ print $5 }'`
if [ $yum_update_HS == "K" ]
then
    yum_update_size=$((yum_update_size_h * 1024))
elif [ $yum_update_HS == "M" ]
then
    yum_update_size=$((yum_update_size_h * 1024 *1024))
elif [ $yum_update_HS == "G" ]
then
    yum_update_size=$((yum_update_size_h * 1024 *1024 * 1024))
else
    yum_update_size= yum_update_size_h
fi
printf "BootstrapStage\tVM: $host_ip\tjob_id: $job_id\tyum_install_size: $yum_update_size\n" >> ./$log_name
#-----------------------------------------------------
log_name="other_install_disk_usage_log.txt"
echo "Checking 3rd party software installed at /opt ... .. ."
find  /opt -type f -printf "BootstrapStage\tVM: $host_ip\tjob_id: $job_id\tsize: %s\tfilename: %f\tlocation: %h\n" > ./$log_name
find  /opt -maxdepth 1 -type f  -printf "BootstrapStage\tVM: $host_ip\tjob_id: $job_id\tsize: %s\tfilename: %f\tlocation: %h\n" >> ./$log_name
opt_dir_list=`du -d 1  /opt | awk '{ print $2}'`
for adir in $opt_dir_list
do 
    dir_size=`du -s -B1 $adir | awk '{ print $1}'` 
    printf "BootstrapStage\tVM: $host_ip\tjob_id: $job_id\tsize: $dir_size\tfilename: $adir\tlocation: $adir\n" >> ./$log_name
done
#-----------------------------------------------------
log_name="job_level_disk_usage_log.txt"
echo "Checking contents of job directory: $job_dir"
find  $job_dir -maxdepth 1 -type f -printf "Execute_and_WaitStage\tVM: $host_ip\tjob_id: $job_id\ttask_id: 0\tsize: %s \tfilename: %f \t\tlocation: %h\n" > ./$log_name
process_payload_dir=$job_dir/process_payload
find  $process_payload_dir -type f  -printf "Execute_and_WaitStage\tVM: $host_ip\tjob_id: $job_id\ttask_id: 0\tsize: %s\tfilename: %f\tlocation: %h\n" >> ./$log_name

for j in $pid_list
do
    process_dir=$job_dir/$j
    echo "Checking contents of process directory: $process_dir ... .. ."
    find  $process_dir -maxdepth 1 -type f -printf "Execute_and_WaitStage\tVM: $host_ip\tjob_id: $job_id\ttask_id: $j\tsize: %s \tfilename: %f \t\tlocation: %h\n" >> ./$log_name

    input_dir=$job_dir/$j/smart_connector_input
    find  $input_dir -type f -printf "Execute_and_WaitStage\tVM: $host_ip\tjob_id: $job_id\ttask_id: $j\tsize: %s \tfilename: %f \t\tlocation: %h\n" >> ./$log_name

    output_dir=$job_dir/$j/chiminey_output
    find  $output_dir -type f -printf "Execute_and_WaitStage\tVM: $host_ip\tjob_id: $job_id\ttask_id: $j\tsize: %s \tfilename: %f \t\tlocation: %h\n" >> ./$log_name
done
echo "Disk usage checking done"
