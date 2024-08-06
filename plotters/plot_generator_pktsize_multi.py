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
results_path = os.path.abspath(Path(file_path)/ ".." / "results" / "generator_pktsize")
results_path_h5 = os.path.abspath(Path(file_path)/ ".." / "results"/"generator_pktsize" / "results.h5")
output_path  = os.path.abspath(Path(file_path)/ ".." / "results"/"generator_pktsize" / "plots")

parser = argparse.ArgumentParser(

                description='Generate plots')
parser.add_argument("--input", default=str(results_path_h5),
                    help="results.h5 output to load")
parser.add_argument("--output", default=str(output_path),
                    help="Where to place plots")
args = parser.parse_args()
output_path = args.output

with pd.HDFStore(args.input,"r") as store:
    results = store.get("results")
    keys= list(store.get("keys"))
    kind_results = {k: store.get(k) for k in keys}


if not os.path.exists(output_path):
    os.makedirs(output_path)

# Global matplotlib settings
plt.rcParams["figure.figsize"] = (10,5.5)
plt.rcParams["figure.dpi"] = (180)
plt.rcParams["font.size"] = (15)
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42


time_results = kind_results["TIME"]




# Remove edges and bad points (note threshold 0 means anything is good bw-wise)
if "RX_BPS_worker" in time_results:
    time_results = time_cutter(time_results, "RX_BPS_worker", 1e9, 1, 0)

# Remove bad runs. This should not be needed
if "AVG_SEND" in results.columns:
    results = results[results["AVG_SEND"] < 10000000]


fig, ax = plt.subplots()
for g, gdata in time_results.groupby("run"):
    rtime = gdata["TIME"] - gdata["TIME"].iloc[0]
    ax.plot(rtime, gdata["RX_BPS_worker"])

fig.savefig(output_path + "/debug-bw_time.pdf")


#  We reset index to be able to add a MODE2 column which would also cover the testname (this is needed for l40/a100 cases)
time_results = time_results.reset_index()
time_results["MODE2"] = time_results["MODE"] + "-" +  time_results["testname"]
results = results.reset_index()
results["MODE2"] = results["MODE"] + "-" +  results["testname"]



# This should not be needed.
# However, we have instabilities in our tests due to a (bad) rate limiter in the CPU cases
# So... we need to drop some points whre the write_size is high-ish but the throughput drops
time_results["WRITE_SIZE"] = pd.to_numeric( time_results["WRITE_SIZE"])
time_results = time_results[(time_results["WRITE_SIZE"] < 21001) | (time_results["RX_BPS_worker"] > 90e9)]


fig, ax = errorbar_plotter(time_results, X="WRITE_SIZE", Y="TX_BPS_worker", SERIES="MODE2", medians=False)
format_bw_plot(ax)
format_pktsize_plot(ax)
fig.tight_layout()
fig.savefig(output_path + "/generator_pktsize_mode_tx_bps.pdf")

fig, ax = errorbar_plotter(time_results, X="WRITE_SIZE", Y="RX_BPS_worker", SERIES="MODE2", medians=False, point_labels=False)
format_bw_plot(ax)
format_pktsize_plot(ax)
fig.tight_layout()
ax.set_xlim(0,80e3)
fig.savefig(output_path + "/generator_pktsize_mode_rx_bps.pdf")




fig, ax = errorbar_plotter(results, X="WRITE_SIZE", Y="AVG_SEND", SERIES="MODE2", medians=False)
format_time_plot(ax, ylabel="Application time to post a verb", div=1, log=True, stop=4e3, start=1)
format_pktsize_plot(ax)
ax.set_xlim(0,80e3)
fig.tight_layout()
fig.savefig(output_path + "/generator_pktsize_mode_avg_send.pdf")


# fig, ax = errorbar_plotter(results, X="WRITE_SIZE", Y="RUNTIME", SERIES="MODE", medians=False)
# # format_bw_plot(ax)
# fig.savefig(output_path + "/generator_pktsize_mode_runtime.pdf")


# results["RUNTIME2"] = results["STOPTIME"] - results["STARTTIME"]
# fig, ax = errorbar_plotter(results, X="WRITE_SIZE", Y="RUNTIME2", SERIES="MODE", medians=False)
# fig.savefig(output_path + "/generator_pktsize_mode_runtime2.pdf")

