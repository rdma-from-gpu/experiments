#!/usr/bin/python3

# (C) 2024 Massimo Girondi girondi@kth.se GNU GPL v3

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
results_path = os.path.abspath(Path(file_path)/ ".." / "results" / "worker_poll")
results_path_h5 = os.path.abspath(Path(file_path)/ ".." / "results"/"worker_poll" / "results.h5")
output_path  = os.path.abspath(Path(file_path)/ ".." / "results"/"worker_poll" / "plots")

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

poll_colors = ["firebrick", "darkred", "red", "coral", "sienna"]
nopoll_colors = ["forestgreen", "darkgreen", "seagreen", "springgreen", "limegreen"]
poll_symbols = ["d", "p", "8"]
nopoll_symbols = ["^", "2", "v" ]

model_markers={}
model_colors = {}

def combo2marker(model, poll):
    name = "_".join([model, poll])
    poll = int(poll)
    if not name in model_markers:
        symbols = poll_symbols if poll else nopoll_symbols
        model_markers[name] = symbols[len(model_markers) % len( symbols)]
    return model_markers[name]


def combo2line(model, poll):
    name = "_".join([model, poll])
    poll = int(poll)
    if not model in model_colors:
        colors = poll_colors if poll else nopoll_colors
        model_colors[name] = colors[len(model_colors) % len(colors)]

    line = "--" if poll == 0 else "-."

    return model_colors[name], line






time_results = kind_results["TIME"]

# First we normalize times
data = []
for run, grun in time_results.groupby("run"):
    grun["TIME"] = grun["TIME"] - grun["TIME"].iloc[0]
    grun = grun.reset_index()
    data+=[grun[["TIME", "CPU_CORES_worker", "MODEL", "POLL"]]]
data = pd.concat(data)
data = data.dropna()

# Time cut - runtime was 30 seconds here (more or less)
data = data[data["TIME"] < 42]

fig, ax = plt.subplots()
labels_poll = ["CudaDeviceSynchronize"]
labels_nopoll = ["Our approach"]
# An empty first line
h1, = ax.plot([0], marker='None', linestyle='None', label='dummy-tophead')   

lines_poll = [h1]
lines_nopoll = [h1]

# Then we group by model and poll, and plot
for combo, gdata in data.groupby(["MODEL", "POLL"]):
    model, poll = combo
    color, linestyle = combo2line(model, poll)
    g = gdata[["TIME", "CPU_CORES_worker"]].sort_values("TIME")
    line,  = ax.plot(g["TIME"], g["CPU_CORES_worker"],
                     marker = combo2marker(model, poll),
                     linestyle = linestyle,
                     color = color
                     )#, label=combo)
    if int(poll):
        lines_poll.append(line)
        labels_poll.append(model)
    else:
        lines_nopoll.append(line)
        labels_nopoll.append(model)

ax.set_xlabel("Runtime (s)")
ax.set_ylabel("CPU usage (# of cores)")

plt.legend(lines_poll+lines_nopoll, labels_poll+labels_nopoll, ncol=2, bbox_to_anchor=(.955, 1.4),)


ax.text(2,.2,"Initialization\n")
ax.text(20,.2,"Inference\nserving",ha="center")
ax.text(38,.2,"Final\nSync", ha="center")
x = np.arange(-1,45)
ax.fill_between(x, -0.2,1.2, where=(x <= 10) & (x >= 0),
                alpha=0.3, color="yellow", edgecolor='white',linewidth=0)
ax.fill_between(x, -0.2,1.2, where=(x <= 35) & (x >= 10),
                alpha=0.3, color="green",edgecolor='white',linewidth=0)
ax.fill_between(x, -0.2,1.2, where=(x >= 35),
                alpha=0.2, color="red", edgecolor='white',linewidth=0)

fig.tight_layout()
fig.savefig(output_path + "/worker_cpu_poll.pdf")

