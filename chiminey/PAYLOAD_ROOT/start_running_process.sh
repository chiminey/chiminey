exec_start_time=`date +"%Y-%m-%d %H:%M:%S"`
sed -i "s/EXEC_START_TIME/$exec_start_time/" ./timedata.txt
bash main.sh $@ &  echo "$!" > "run.pid"
