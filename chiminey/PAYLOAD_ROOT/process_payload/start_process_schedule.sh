#!/bin/sh

sh setup.sh $@ & echo "$!" > "setup.pid"
