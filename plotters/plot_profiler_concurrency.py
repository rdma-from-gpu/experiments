#!/usr/bin/python3

# (C) 2024 Massimo Girondi girondi@kth.se GNU GPL v3

import pandas as pd
import glob
import os
from pathlib import Path
import argparse
import re
from utils import *
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

if __name__ != "__main__":
    exit(0)

file_path = os.path.dirname(__file__)
results_path = os.path.abspath(Path(file_path)/ ".." / "results" / "profiler_concurrency")
results_path_h5 = os.path.abspath(Path(file_path)/ ".." / "results"/"profiler_concurrency" / "results.h5")
output_path  = os.path.abspath(Path(file_path)/ ".." / "results"/"profiler_concurrency" / "plots")

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
    times = store.get("times")
    kind_results = {k: store.get(k) for k in keys}


if not os.path.exists(output_path):
    os.makedirs(output_path) # Global matplotlib settings



plt.rcParams["figure.figsize"] = (10,5.5)
plt.rcParams["figure.dpi"] = (180)
plt.rcParams["font.size"] = (15)
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42


# Just a single model
times = times[times["MODEL"] == "a100_superresolution_tuned"]

times = times.convert_dtypes()
times["CONCURRENCY"] = pd.to_numeric(times["CONCURRENCY"])

fig, ax = plt.subplots()
for concurrency, cdata in times.groupby("CONCURRENCY", sort=True):
    these_times = np.array(cdata["times"][0])
    these_times = these_times[these_times > 0]
    if not len(these_times):
        continue
    bins, edges = np.histogram(these_times, bins = 100)
    bins = np.cumsum(bins)
    bins = bins.astype("float") / bins[-1].astype("float")
    centers = (edges[:-1]+edges[1:])/2  
    l = ax.plot(centers,bins, label=concurrency)



    # Add lines at 0 and end to make it more beautiful
    first_bin = edges[0]
    last_bin = edges[-1]
    highest_bin = centers[-1]

    # Add heads and tails
    color = l[0].get_color()
    ax.hlines(y=0,xmin=0,xmax=first_bin,
              color=color, label="_START")
    ax.hlines(y=1,xmin=last_bin,xmax=last_bin+1000000000000,
              color=color, label="_STOP")


ax.set_xlim(0, .33e7)
ax.set_xlabel("Model runtime (ms)")
ax.set_ylabel("Cumulative distribution")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x,_: x/1e6))  
ax.legend(ncol=8, bbox_to_anchor=(.5, 1.3), loc="upper center")

fig.tight_layout()
fig.savefig(output_path + "/profiler_concurrency_cdf.pdf")


fig, ax = plt.subplots()
xy = results.reset_index()[["CONCURRENCY","AVG_RATE"]]
print(xy)
xy["CONCURRENCY"] = pd.to_numeric(xy["CONCURRENCY"])
xy = xy.sort_values("CONCURRENCY")
x = xy["CONCURRENCY"].to_numpy()
y = xy["AVG_RATE"].to_numpy()
ax.plot(x,y, label="Measured averages", marker=".")


def log4(x, a, b, c):
    return a * np.log2(x) + b *x  +  c

popt_log4, pcov_log4 = curve_fit(log4, x, y)

log4_label = "fit: y= %.2f * log2(x) + %.2f*x + %.2f" % tuple(popt_log4)
print(log4_label)
if "-" in log4_label:
    log4_label = re.sub("\+ -", "-", log4_label)
ax.plot(x, log4(x, *popt_log4), label=log4_label, marker="*", linestyle="-.")
ax.legend(loc="upper left")

fig.tight_layout()
fig.savefig(output_path + "/profiler_concurrency_fitting.pdf")
