#!/bin/bash

INPUT_DIR=$1
OUTPUT_DIR=$2
HADOOP_HOME="$3"
HADOOP_INPUT=$4
HADOOP_OUTPUT=$5
OPTS_ARGS=$6

$HADOOP_HOME/bin/hdfs dfs -rm -r -f $HADOOP_INPUT
$HADOOP_HOME/bin/hdfs dfs -mkdir -p $HADOOP_INPUT
$HADOOP_HOME/bin/hdfs dfs -put $INPUT_DIR/*   $HADOOP_INPUT

$HADOOP_HOME/bin/hdfs dfs -rm -r -f $HADOOP_OUTPUT
$HADOOP_HOME/bin/hadoop jar hadoop-mapreduce-examples-2.7.2.jar grep  $HADOOP_INPUT  $HADOOP_OUTPUT  $OPTS_ARGS

$HADOOP_HOME/bin/hdfs dfs -get $HADOOP_OUTPUT $OUTPUT_DIR

