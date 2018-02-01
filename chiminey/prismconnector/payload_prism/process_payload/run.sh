#!/bin/sh

INPUT_DIR=$1
OUTPUT_DIR=$2

java_exe=$(whereis java 2>&1 | awk '/java/ {print $2}')
java_path=$(dirname $java_exe)

prism_exe=$(whereis prism 2>&1 | awk '/prism/ {print $2}')
prism_path=$(dirname $prism_exe)

export PATH=$java_path:$prism_path:$PATH

cd $INPUT_DIR

prism $(cat cli_parameters.txt) &> runlog.txt

cp ./*.txt ../$OUTPUT_DIR

# --- EOF ---
