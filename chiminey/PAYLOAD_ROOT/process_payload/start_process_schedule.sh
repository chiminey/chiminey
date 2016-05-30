#!/bin/bash

sh schedule.sh $@ & echo "$!" > "setup.pid"
