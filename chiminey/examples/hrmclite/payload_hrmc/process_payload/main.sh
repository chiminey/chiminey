#!/bin/sh

INPUT_DIR=$1
OUTPUT_DIR=$2


cp HRMC $INPUT_DIR/HRMC; cd $INPUT_DIR; ./HRMC >& ../$OUTPUT_DIR/output
