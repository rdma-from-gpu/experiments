#!/bin/bash

set -x
TESTNAME="generator_pktsize"
mkdir -p results/$TESTNAME/

export TS=$(date --iso-8601=seconds)
mkdir -p ./tmp/${TS}
#rm -rf ./tmp/${TS}/*

ansible-playbook -i ./inventory/t4.yml ./generator_pktsize.yml $@

for f in tmp/${TS}/*; do
  cp generator_pktsize.yml $f
  # This is used as a sentinel to find results (beside being useful for debug)
  cp run_generator_pktsize.sh $f/test.sh
done

mv tmp/${TS}/* results/$TESTNAME/
rm -rf tmp/${TS}

python3 collect_generator_pktsize.py --path ../results/generator_pktsize
python3 plot_generator_pktsize.py --input ../results/generator_pktsize/results.h5 --output ../results/generator_pktsize/plots
