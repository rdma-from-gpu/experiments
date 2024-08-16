[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.13332403.svg)](https://doi.org/10.5281/zenodo.13332403)




This folder provides some scripts and tools to reproduce the figures and measurements of our paper.
These are based on Ansible, and requires some machines running Ubuntu, with NVIDIA GPUs and NVIDIA Mellanox NICs.




# Assumptions
- There is a shared NFS (or equivalent) storage, such that the main `rdma-from-gpu` folder (or at least the experiment folder) is shared among all nodes involved in the tests
- You have passwordless `sudo` and a public key for login to these nodes
- You have `nvidia_peermem` and correct rdma-core setup.
  In most cases, running the `setup.yml` playbook should prepare the environment well-enough:
    ```
    ansible-playbook -i ./inventory/t4.yml ./setup.yml
    ```

- The `inventory/*` files would map to your actual setup of clients and servers. You'd need at least a machine with 2 sockets and 2 independent NICs on different NUMAs to replicate most of the experiments, although these have been done with two separate machines to avoid any conflict.
- The experiments (and the whole programs compilations) have been tested under Ubuntu 22.04 LTS, with standard libraries obtained from the usual sources.


# Dependencies

Tests are run with ansible, and a standard deployment where you can run `sudo` without password and you can login with ssh keys should be enough.

To generate the plots, some Python packages are needed.
For these it should be enough to create a new environment with Conda starting from `requirements.txt`.
Note this cannot be done with `virtualenv` due to Pandas dependency on PyTables, which is somewhat limiting when installed via plain pip.

# How to

In general, one just want to run `bash run_*.sh`, and then check the results in `results/*`.
Here there will a folder test name, and for each a time-stamped folder that contains all output and logs for each run

The files in `plotters` will parse thee outputs and build a Hickle dataframe for each test.
These will then be read by other scripts to generate the plots for each different experiment.


# The process with more details

In general, one should run the `run_{test_name}.sh` scripts (that call ansible) to run the tests.

These will produce plain text results in `results/{test_name}`, which are then collected by running `plotters/collect_{test_name}.py`.
This will create an individual `results.h5` file for each run, and then read them back and aggregate the results in a single `results.h5` test for all results.

These `results.h5` files are then read by `plot_{testname}.py` which would generate the plots as pdfs (typically).

For instance, running `./run_generator_pktsize_a100.sh` and `./run_generator_pktsize_l40.sh` would create two folders `./results/generator_pktsize_{a100,l40}`, each with its own result set.
The `collect_generator_pktsize.py` script would produce a `./results/generator_pktsize/results.h5` file with all results, which will be then read by `plot_generator_pktsize.py` to generate the plots.
The `--multi` flags needs to be specified in the collect scripts so that it would collect with a wildcard (e.g. for all matching folders)

So, in practice, you want to run the following commands (e.g. for the generator plots):

```
./run_generator_pktsize_cpu.sh 
./run_generator_pktsize_l40.sh 
./run_generator_pktsize_a100.sh 
# Repeat the above for how many "runs" you want
cd plotters
python3 ./collect_generator_pktsize.py --multi --force
python3 ./plot_generator_pktsize.py
```




# Caveat Emptor

The original plots published in the EdgeSys 24 paper where obtained with a more complex and hack-ish setup based on NPF.
The tests contained in this folder aim to replicate the same plots with a leaner and more standardized software stack, but there is no willing to re-create the exact same plots as in the paper (e.g. proportions, labels, axis, ...).
So you can expect these plots to appear somewhat different than the published figures.

However, the code published in this repositories is the exact same code used when running the experiments reported in the EdgeSys paper, with only minor modifications to reshape the code in a more re-usable way.
No relevant performance differences addressable to these changes have been measured between the original and the released versions.

Also note the hardware setup changed after the original paper, so some results (especially CPU-related) could be slightly different, or instable w.r.t. the original ones. However, further tweaking of parameters (e.g. batch sizes and sleep intervals) should fix these differences.

# Reproduce paper's figures

The paper figures can be reproduced with the following commands:

## Figure 2: inference time distribution vs concurrency
![Figure 2](results/profiler_concurrency/plots/profiler_concurrency_cdf_a100_squeezenet_tuned.pdf)

```
bash ./run_profiler_concurrency.sh
cd plotters
python3 ./collect_profiler_concurrency.py --multi
python3 ./plot_profiler_concurrency.py
```


## Figure 4 & 5: Throughput and post time vs packet size
![Figure 4](results/generator_pktsize/plots/generator_pktsize_mode_rx_bps.pdf)
![Figure 5](results/generator_pktsize/plots/generator_pktsize_mode_avg_send.pdf)

```
bash ./run_generator_pktsize_a100.sh
bash ./run_generator_pktsize_l40.sh
bash ./run_generator_pktsize_cpu.sh

cd plotters
python3 ./collect_generator_pktsize.py --multi
python3 ./plot_generator_pktsize.py
```

## Figure 6: GPU vs CPU stacked latencies
![Figure 6](results/worker_modes/plots/worker_stacked_latencies.pdf)

```
bash ./run_worker_modes.sh
cd plotters
python3 ./collect_worker_modes.py --multi
python3 ./plot_worker_modes.py
```

## Figure 7: CPU usage vs polling mechanism
![Figure 7](results/worker_poll/plots/worker_cpu_poll.pdf)

```
bash ./run_worker_poll.sh
cd plotters
python3 ./collect_worker_poll.py --multi
python3 ./plot_worker_poll.py
```

# LICENSE

(C) 2024 Massimo Girondi  girondi@kth.se GNU GPL v3

See [LICENSE](LICENSE).
