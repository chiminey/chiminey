#!/bin/bash

sh setup.sh $@ & echo "$!" > "setup.pid"
