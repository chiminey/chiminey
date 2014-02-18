#!/bin/sh

IDS=$1

while read line
do
    cd $line
    make startrun
    cd ..
done < $IDS