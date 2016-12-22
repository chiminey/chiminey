#!/bin/sh
# version 2.0

INPUT_DIR=$1
OUTPUT_DIR=$2

JAVA_HOME=/opt/jdk1.8.0_101

cp roughness-analysis-cli.jar $INPUT_DIR/roughness-analysis-cli.jar
cp run-rac.py $INPUT_DIR/run-rac.py
cd $INPUT_DIR

python run-rac.py -v values -o ../$OUTPUT_DIR -j $JAVA_HOME

# --- EOF ---
