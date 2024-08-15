#!/bin/bash

set -x
MODEL=${MODEL:-a100_superresolution_tuned}
MODEL2=${MODEL//_/-}
echo $MODEL2

TESTNAME="worker_modes_${MODEL2}"
mkdir -p results/$TESTNAME/

export TS=$(date --iso-8601=seconds)
mkdir -p ./tmp/${TS}
#rm -rf ./tmp/${TS}/*

ansible-playbook -i ./inventory/client-worker.yml ./worker.yml \
  --extra-vars '{"MODES":["cpu-cpu", "gpu-gpu"], "MODEL":"'${MODEL}'"}' $@
  #--extra-vars '{"MODES":["cpu-cpu", "gpu-gpu", "cpu-gpu"], "MODEL":"'${MODEL}'"}' $@

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
