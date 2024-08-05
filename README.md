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
