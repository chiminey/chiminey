#!/bin/sh

python -c 'import random;  print random.random()'  >& output 
python -c 'import random;  print random.random()'  >> output &  echo "$!" > "run.pid"

