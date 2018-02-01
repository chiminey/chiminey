#!/bin/sh

INPUT_DIR=$1

cp run.sh $INPUT_DIR/run.sh

RUN_DIR=`cd "$(dirname "$0")" && pwd`

echo $RUN_DIR > mainsh.output

sh $RUN_DIR/run.sh $@

# --- EOF ---
