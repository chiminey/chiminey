#!/bin/sh

sh setup.sh $1 & echo "$!" > "setup.pid"
