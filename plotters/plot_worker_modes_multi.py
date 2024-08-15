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
results_path = os.path.abspath(Path(file_path)/ ".." / "results" / "worker_modes")
results_path_h5 = os.path.abspath(Path(file_path)/ ".." / "results"/"worker_modes" / "results.h5")
output_path  = os.path.abspath(Path(file_path)/ ".." / "results"/"worker_modes" / "plots")

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
    os.makedirs(output_path) # Global matplotlib settings
plt.rcParams["figure.figsize"] = (10,5.5)
plt.rcParams["figure.dpi"] = (180)
plt.rcParams["font.size"] = (15)
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42


time_results = kind_results["TIME"]
gpu_results = kind_results["GPU"]

print(time_results.columns)


# Remove bad runs
gpu_results = gpu_results[gpu_results["GPU_COPY_INPUT_AVG"] < 1e8]
gpu_results = gpu_results[gpu_results["GPU_COPY_OUTPUT_AVG"] < 1e8]
gpu_results = gpu_results[gpu_results["GPU_RUN_AVG"] < 10e9]

# # Remove edges and bad points (note threshold 0 means anything is good bw-wise)
# if "RX_BPS_worker" in time_results:
#     time_results = time_cutter(time_results, "RX_BPS_worker", 10e8, 1, 0)

# # # Remove bad runs. This should not be needed
# # if "AVG_SEND" in results.columns:
# #     results = results[results["AVG_SEND"] < 100000]


# fig, ax = plt.subplots()
# for g, gdata in time_results.groupby("run"):
#     rtime = gdata["TIME"] - gdata["TIME"].iloc[0]
#     ax.plot(rtime, gdata["RX_BPS_worker"])

# fig.savefig(output_path + "/debug-bw_time.pdf")



elements=["GPU_RUN_AVG", "GPU_SEND_AVG", "GPU_WAIT_AVG","GPU_COPY_OUTPUT_AVG", "GPU_COPY_INPUT_AVG", "GPU_COPY_INPUT_CPU_AVG", "GPU_COPY_OUTPUT_CPU_AVG"]
rename = {
        "GPU_QUEUE_AVG": "Worker queue time (+ network)",
        "GPU_WAIT_AVG": "Worker wait input time",
        "GPU_SEND_AVG": "Worker send output time",
        "GPU_RUN_AVG": "Worker pure inference time",
        "GPU_TOTAL_AVG": "Worker total time",
        "GPU_COPY_OUTPUT_AVG": "Copy outputs time",
        "GPU_COPY_INPUT_AVG": "Copy inputs time",
        "GPU_COPY_INPUT_CPU_AVG": "CPU->GPU Input copy time",
        "GPU_COPY_OUTPUT_CPU_AVG": "GPU->CPU Input copy time",
        "cpu-cpu": "CPU mediated",
        "gpu-gpu": "GPU driven",
        "cpu-gpu": "CPU rcv, GPU snd",
    }


res = gpu_results.reset_index()
res = res[res["MODE"] != "cpu-gpu"]


# The paper plot
res1 = res[res["MODEL"] == "a100_superresolution_tuned"]
fig, ax = stacked_plotter(res1, elements=elements, rename=rename)
format_time_plot(ax, ylabel="Time (ms)", div=1e6, log=False, stop=4e3, start=1)
# format_pktsize_plot(ax)
ax.set_ylim(0,1.5e6)
fig.tight_layout()
fig.savefig(output_path + "/worker_stacked_latencies.pdf")

# A plot for each model
res1 = res[res["MODE"] == "cpu-cpu"]
fig, ax = stacked_plotter(res1, elements=elements, rename=rename, by="MODEL")
format_time_plot(ax, ylabel="Time (ms)", div=1e6, log=False, stop=4e3, start=1)
# format_pktsize_plot(ax)
ax.set_ylim(0,1.5e6)
fig.tight_layout()
fig.savefig(output_path + "/worker_stacked_latencies_cpu-cpu_models.pdf")


res1 = res[res["MODE"] == "gpu-gpu"]
fig, ax = stacked_plotter(res1, elements=elements, rename=rename, by="MODEL")
format_time_plot(ax, ylabel="Time (ms)", div=1e6, log=False, stop=4e3, start=1)
# format_pktsize_plot(ax)
ax.set_ylim(0,1.5e6)
fig.tight_layout()
fig.savefig(output_path + "/worker_stacked_latencies_gpu-gpu_models.pdf")
