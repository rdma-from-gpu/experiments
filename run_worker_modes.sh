#!/bin/bash

set -x
TESTNAME="worker_modes"
mkdir -p results/$TESTNAME/

export TS=$(date --iso-8601=seconds)
mkdir -p ./tmp/${TS}
#rm -rf ./tmp/${TS}/*

ansible-playbook -i ./inventory/client-worker.yml ./worker.yml \
  --extra-vars '{"MODES":["cpu-cpu"]}' $@
  #--extra-vars '{"MODES":["cpu-cpu","gpu-gpu","cpu-gpu"]}' $@

for f in tmp/${TS}/*; do
  cp worker_modes.yml $f
  # This is used as a sentinel to find results (beside being useful for debug)
  cp run_worker_modes.sh $f/test.sh
done

mv tmp/${TS}/* results/$TESTNAME/
rm -rf tmp/${TS}


# cd plotters
# python3 collect_generator_pktsize.py --path ../results/generator_pktsize_a100
# python3 plot_generator_pktsize.py --input ../results/generator_pktsize_a100/results.h5 --output ../results/generator_pktsize_a100/plots
