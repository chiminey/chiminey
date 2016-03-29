#!/bin/sh

PROC_DESTINATION=$1

cd $PROC_DESTINATION
bin/hadoop jar hadoop-mapreduce-examples-2.7.2.jar grep input output 'dfs[a-z.]+'
