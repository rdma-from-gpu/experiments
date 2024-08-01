import pandas as pd
import glob
import os
from pathlib import Path
import argparse
import re
from utils import *
import matplotlib.pyplot as plt

if __name__ != "__main__":
    exit(0)

file_path = os.path.dirname(__file__)
results_path = os.path.abspath(Path(file_path)/ ".." / "results"/"generator_pktsize")
results_path_h5 = os.path.abspath(Path(file_path)/ ".." / "results"/"generator_pktsize" / "results.h5")
output_path  = os.path.abspath(Path(file_path)/ ".." / "results"/"generator_pktsize" / "plots")

parser = argparse.ArgumentParser(

                description='Generate plots')
parser.add_argument("--input", default=str(results_path_h5),
                    help="results.h5 output to load")
parser.add_argument("--output", default=str(output_path),
                    help="Where to place plots")
args = parser.parse_args()
print(args)

with pd.HDFStore(args.input,"r") as store:
    results = store.get("results")
    keys= list(store.get("keys"))
    kind_results = {k: store.get(k) for k in keys}


if not os.path.exists(output_path):
    os.makedirs(output_path)

# Global matplotlib settings
plt.rcParams["figure.figsize"] = (10,3.5)
plt.rcParams["figure.dpi"] = (180)
plt.rcParams["font.size"] = (15)
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42



time_results = kind_results["TIME"]

fig, ax = errorbar_plotter(time_results, X="WRITE_SIZE", Y="TX_BPS_worker", SERIES="MODE")
fig.savefig(output_path + "/generator_pktsize_mode_tx_bps.pdf")

fig, ax = errorbar_plotter(time_results, X="WRITE_SIZE", Y="CPU_CORES_worker", SERIES="MODE")
fig.savefig(output_path + "/generator_pktsize_mode_cpu_cores.pdf")
