#!/bin/sh

PROC_DESTINATION=$1
INPUT_DIR=$2
OUTPUT_DIR=$3
cd $PROC_DESTINATION


HADOOP_HOME=/home/ec2-user/hadoop-2.7.2
$HADOOP_HOME/bin/hdfs dfs -mkdir -p   $INPUT_DIR
$HADOOP_HOME/bin/hdfs dfs -put $HADOOP_HOME/etc/hadoop/*   $INPUT_DIR
$HADOOP_HOME/bin/hadoop jar $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.2.jar grep  $INPUT_DIR  $OUTPUT_DIR  'dfs[a-z.]+'

$HADOOP_HOME/bin/hdfs dfs -get $OUTPUT_DIR .

