#!/bin/bash

set -x
TESTNAME="generator_pktsize"
mkdir -p results/$TESTNAME/

mkdir -p ./tmp
rm -rf ./tmp/*

ansible-playbook -i ./inventory/t4.yml ./generator_pktsize.yml $@

for f in tmp/*; do
  cp generator_pktsize.yml $f
  # This is used as a sentinel to find results (beside being useful for debug)
  cp run_generator_pktsize.sh $f/test.sh
done

mv tmp/* results/$TESTNAME/
