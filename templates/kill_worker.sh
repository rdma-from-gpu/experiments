#!/bin/bash

# Look into the process tree with pid PARENT and kill all CMD processes
# This won't work if the processes changes their name!

PARENT=${PARENT:-1}
CMD=${CMD:-worker}
CHILD=$(ps --ppid $PARENT -o pid,cmd | grep $CMD | tr -s " " | cut -f1 --delimiter=" " )
if [  "${CHILD}" ]; then
  echo $CHILD | xargs kill -2
else
  echo "No $CMD child of $PARENT to kill!"
fi
