#!/bin/sh

python -c 'import random;  print random.random()'  >& chiminey/output
python -c 'import random;  print random.random()'  >> chiminey/output
