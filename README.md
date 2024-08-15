# Assumptions
- There is a shared NFS storage, such that the main `rdma-from-gpu` folder (or at least the experiment folder) is shared among all nodes involved in the tests
- You have passwordless `sudo` and a public key for login to these nodes
- You have `nvidia_peermem` and correct rdma-core setup.
  In most cases, running the `setup.yml` playbook should prepare the environment well-enough:
    ```
    ansible-playbook -i ./inventory/t4.yml ./setup.yml
    ```

# How to

In general, one just want to run `bash run_*.sh`, and then check the results in `results/*`.
Here there will a folder test name, and for each a time-stamped folder that contains all output and logs for each run

# Post processing and plotting

The files in `post-processing` will parse thee outputs and build a Hickle dataframe for each test.
These will then be read by other scripts to generate the plots for each different experiment.


# Dependencies

Tests are run with ansible, and a standard deployment where you can run `sudo` without password and you can login with ssh keys should be enough.

To generate the plots, some Python packages are needed.
For these it should be enough to create a new environment with Conda starting from `requirements.txt`.
Note this cannot be done with `virtualenv` due to Pandas dependency on PyTables, which is somewhat limiting when installed via plain pip.

# The process

In general, one should run the `run_{test_name}.sh` scripts (that call ansible) to run the tests.

These will produce plain text results in `results/{test_name}`, which are then collected by running `plotters/collect_{test_name}.py`.
This will create an individual `results.h5` file for each run, and then read them back and aggregate the results in a single `results.h5` test for all results.

When using the `_multi` versions of the scripts (e.g. for the generator), the scripts will read a wildcard (e.g. `generator_pktsize_{a100,l40,cpu}`), and place the global results in `generator_pktsize/results.h5`).

These `results.h5` files are then read by `plot_{testname}.py` which would generate the plots as pdfs (typically).


When there is a `multi.py` version of the plot scripts, this is intended to be used to collect, and plot, results for multiple _similar_ folders.
For instance, running `./run_generator_pktsize_a100.sh` and `./run_generator_pktsize_l40.sh` would create two folders `./results/generator_pktsize_{a100,l40}`, each with its own result set.
The `collect_generator_pktsize_multi.py` script would produce a `./results/generator_pktsize/results.h5` file with all results, which will be then read by `plot_generator_pktsize_multi.py` to generate the plots.

So, in practice, you want to run the following commands (for the generator plots):

```
./run_generator_pktsize_cpu.sh 
./run_generator_pktsize_l40.sh 
./run_generator_pktsize_a100.sh 
# Repeat the above for how many "runs" you want
cd plotters
python3 ./collect_generator_pktsize_multi.py --multi 
python3 ./plot_generator_pktsize.py
```


## Disclaimer

The original plots published in the EdgeSys 24 paper where obtained with a more complex and hack-ish setup based on NPF.
The tests contained in this folder aim to replicate the same plots with a leaner and more standardized software stack, but there is no willing to re-create the exact same plots as in the paper (e.g. proportions, labels, axis, ...).
So you can expect these plots to appear somewhat different than the published figures.

Also note the hardware setup changed after the original paper, so some results (especially CPU-related) could be slightly different, or instable w.r.t. the original ones. However, further tweaking of parameters (e.g. batch sizes and sleep intervals) should fix these differences.
