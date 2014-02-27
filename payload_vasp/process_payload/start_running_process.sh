#!/bin/sh

cd ./vasp

qsub vasp_sub > run.pid

#e.g. python -c 'import random;  print random.random()'  >& output &  echo "$!" > "run.pid"


