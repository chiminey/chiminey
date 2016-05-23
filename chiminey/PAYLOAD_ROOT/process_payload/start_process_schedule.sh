#!/bin/sh

sh schedule.sh $@ & echo "$!" > "setup.pid"
