#!/bin/bash

set -x
TESTNAME="generator_pktsize_l40"
mkdir -p results/$TESTNAME/

export TS=$(date --iso-8601=seconds)
mkdir -p ./tmp/${TS}
#rm -rf ./tmp/${TS}/*

ansible-playbook -i ./inventory/l40.yml ./generator_pktsize.yml \
  --extra-vars '{"MODES":["gpu"], "BATCH":512, "GPU_BATCH":4096}' $@

for f in tmp/${TS}/*; do
  cp generator_pktsize.yml $f
  # This is used as a sentinel to find results (beside being useful for debug)
  cp run_generator_pktsize_l40.sh $f/test.sh
done

mv tmp/${TS}/* results/$TESTNAME/
rm -rf tmp/${TS}


cd plotters
python3 collect_generator_pktsize.py --path ../results/generator_pktsize_l40

#python3 plot_generator_pktsize.py --input ../results/generator_pktsize_l40/results.h5 --output ../results/generator_pktsize_l40/plots
