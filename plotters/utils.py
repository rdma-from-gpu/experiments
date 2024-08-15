import glob
import os 
from pathlib import Path
import re
import pandas as pd
import traceback
import argparse
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker


test_sh_re=r".*/(?P<test_name>[^/]*)/(?P<run>[^/]*)/test.sh"
result_re=r"^((?P<KIND>[^\d][^-]*)-)?((?P<TIME>[\d\.]*)-)?RESULT(-(?P<RESULT>[^ ]*)) *(?P<VALUE>.*)"



def find_tests(path, multi=False):
    # We use test.sh as sentinel to identify a good run
    if multi:
        g = glob.glob(f"{path}*/*/test.sh")
    else:
        g = glob.glob(f"{path}/*/test.sh")
    tests = []
    for t in g:
        r=re.match(test_sh_re, t).groupdict()
        r["full_path"] = os.path.abspath(os.path.dirname(t))
        # We save the last part (which should be a100, l40, cpu)
        if "_" in r["test_name"]:
            r["testname"] = r["test_name"].split("_")[-1]
        else:
            r["testname"] = r["test_name"]


        tests.append(r)

    return tests

def new_data(t):
    # Check whether there are new results
    h5_file = Path(t["full_path"])/"results.h5"
    if not os.path.exists(h5_file):
        return True
    h5_date = os.path.getmtime(h5_file)
    latest_file = max([os.path.getmtime(f) for f in  glob.glob(f"{t['full_path']}/*")])
    if h5_date < latest_file:
        return True
    else:
        return False

def parse_line(l):
    l=l.rstrip()
    m = re.match(result_re,l).groupdict()
    if "KIND" in m and m["KIND"]:
        k = m["KIND"]
        t = float(m["TIME"])
        v = float(m["VALUE"])
        r = m["RESULT"]
        return t,k,v,r
    elif m["TIME"] is not None:
        t = float(m["TIME"])
        v = float(m["VALUE"])
        r = m["RESULT"]
        return t,"TIME",v,r
    else:
        v = float(m["VALUE"])
        r = m["RESULT"]
        return 0, None, v, r



def parse_stdout(f):
    results = {}
    kind_results = {}

    with open(f) as lines:
        for l in lines:
            try:
                if not "RESULT" in l:
                    continue
                t,k,v,r = parse_line(l)
                if t:
                    if not k:
                        k="TIME"
                    kind_results.setdefault(k, {})
                    kind_results[k].setdefault(r, {})
                    # Assume that only 1 results per ts exists
                    #kind_results[k][r].setdefault({},t)
                    kind_results[k][r][t] = v
                else:
                    results[r] = v

            except Exception as ex:
                print("Error while parsing line", l,":")
    return results, kind_results

def infere_timestamp_div(ts):
    lts = len(str(int(ts)))
    # A standard EPOCH in seconds is 1722022227.429387
    if lts > 18: # ns
        div = 1e9
    elif lts > 15: # us
        div = 1e9
    elif lts > 12: # ms
        div = 1e3
    else: # It's already in seconds (hopefully)
        return 1
    return div

def change_precision(df, div=1, time_precision=1):
    # We want to reduce preicion, so that we would have less rows in our big df
    df.index = (df.index / div) * time_precision
    df.index = df.index.map(int)
    return df.index



# Variables will be used to look for strings line "VARIABLE=" or "--write-size" in any .sh file in the test directory
# Stripping of spaces, =, : is automatic
# The format is {'VARIABLE' : 'WHAT TO LOOK FOR'}
# e.g {'WRITE_SIZE':'--write-size', 'MODE': 'MODE'}
# The pattern could be any regextp pattern
# The name must be valid for Python names of groups in re
# So you can have different names too
def extract_variables(path, variables ):
    run_variables = {}
    for f in glob.glob(f"{path}/*.sh"):
        with open(f) as lines:
            for l in lines:
                v_p = "|".join(f"(?P<{v}>{p})" for v,p in variables.items())
                r = r".*("+v_p+")[:= ]?(?P<VALUE>[^ ]+).*"
                m = re.match(r, l)
                if m:
                    # This would overwrite duplicate variables line!
                    for k, v in m.groupdict().items():
                        if v is not None and k != "VALUE":
                            run_variables[k] = m["VALUE"]

    return run_variables


def join_timestamps(df, k = None):
    df = df.sort_index()
    if k:
        df.index.names = [k]
    # Leverage 'mean' capability to ignore NaN to combine the rows
    # Warning: in some cases (e.g. when printing counters more often than once per second)
    # this may not be super reliable
    df = df.groupby(df.index).mean()

    return df

# # This generates the "variables" columns in the result df
# def  add_vars_to_df(df, variables):
#     # This get the columns
#     # First we create a dataframe by multipling by rows #, then we transpose it to make it "vertical"
#     vars_df = pd.concat([variables]*df.shape[0], axis=1).T
#     index_names = df.index.names
#     # And then we add to the DF
#     try:
#         r =  pd.concat([vars_df, df], axis=1)

#         r.index.names = df.index.names

#     except Exception as ex:
#         print("Error while joing dataframe:")
#         traceback.print_exc()
#     return r

def add_vars_to_df(df, variables):
    def adder(r):
        for vk,vv in variables.items():
            r[vk] = vv
        return r
    return df.apply(adder, axis=1)

def generate_h5(t, time_precision=1, variables = {}):
    # Generate a run-specific h5 file. Joined later
    all_results = []
    all_kind_results = {}
    for f in glob.glob(f"{t['full_path']}/*.stdout"):
        results, kind_results = parse_stdout(f)
        results_df = pd.Series(results)
        all_results.append(results_df)

        for k, this_kr in kind_results.items():
            this_kr_df = pd.DataFrame(this_kr)
            first, last = this_kr_df.index[[0,-1]]
            div = infere_timestamp_div(first)
            div_last = infere_timestamp_div(last)
            if div != div_last:
                print("Warning: the precision for",k, "it's not consistent:", div, div_last, "assuming", div)

            this_kr_df.index = change_precision(this_kr_df, div, time_precision)
            #this_kr_df = this_kr_df.groupby(this_kr_df.index).mean().reset_index()
            all_kind_results.setdefault(k, [])
            all_kind_results[k].append(this_kr_df)

    run_variables = extract_variables(t["full_path"], variables)
    run_variables["run"] = str(Path(t["full_path"]).name)
    run_variables["testname"] = str(Path(t["testname"]))
    #run_variables_df = pd.Series(run_variables)


    print("Variables:",run_variables)
    all_results = [r for r in all_results if len(r)]
    all_results = pd.concat(all_results)
    # First we solve the NaN for all missing values, joining rows
    all_kind_results = {k:join_timestamps(pd.concat(r), k) for k,r in all_kind_results.items()}
    # Then we stick the variables together
    all_kind_results = {k:add_vars_to_df(r, run_variables) for k,r in all_kind_results.items()}
    {k:r.index.rename(k) for k, r in  all_kind_results.items()}
    # # and restore the index
    all_kind_results = {k:r.reset_index().set_index(list(run_variables.keys())) for k,r in all_kind_results.items()}

    # Just a safety check, if the columns do not exist, skip setting them as index.
    # The DF is probably empty!
    # This should raise a bigger error, but for now we just ask the user to delete the broken test folder
    # THIS MEANS ONE NEEDS TO HAVE ALWAYS A RESULT!
    if len(all_results) == 0:
        print(f"Error while processing test {t['full_path']}: no RESULT found!")
        print("You may want to delete the folder.")
        all_results_df = pd.DataFrame()
    else:
        print(all_results)
        # Transform the variables Series into a DataFrame, and stick the variables 
        all_results_df = add_vars_to_df(pd.DataFrame([all_results]), run_variables)
        # Restore the index to original + all variables
        all_results_df = all_results_df.set_index(list(run_variables.keys()))

    results_store = pd.HDFStore(f"{t[r'full_path']}/results.h5","w")
    results_store.put("results", all_results_df)
    results_store.put("keys", pd.Series(all_kind_results.keys()))
    #results_store.put("variables", pd.Series(run_variables))#.convert_dtypes())

    for k, r in all_kind_results.items():
        results_store.put(k, r)

    results_store.close()

    return


def read_h5(path):
    keys = list(pd.read_hdf(path, "keys"))
    #variables = pd.read_hdf(path, "variables")
    results = pd.read_hdf(path, "results")
    kind_results = {}
    for k in keys:
        kind_results[k] = pd.read_hdf(path, k)

    return results, kind_results #, variables

def join_results(results, kind_results):
    all_results = pd.concat(results)
    all_kr = {}

    for kr in kind_results:
        for k, r in kr.items():
            all_kr.setdefault(k, [])
            all_kr[k].append(r)

    all_kr = {k: pd.concat(r) for k,r in all_kr.items()}


    return all_results, all_kr



def errorbar_plotter(data, X, Y, SERIES, medians=False, means=True, legend_loc = "lower right", point_labels=False):

    def low(data):
        return data.quantile(.1)
    def high(data):
        return data.quantile(.9)


    fig, ax = plt.subplots(1, 1)
    labels = []

    # We usually have the "run" column in index which we want to remove
    for g, gdata in data.reset_index()[[X,Y, SERIES]].groupby([SERIES]):
        gdata =gdata.reset_index()

        # This is not "safe"  for cases when the index shouldn't be a number
        gdata[X] = gdata[X].astype("float")
        grouped = gdata.groupby(X, group_keys=False)
        centrals = grouped[Y].apply("median" if medians else "mean")
        lows = grouped[Y].apply(low)
        highs = grouped[Y].apply(high)

        # The error bars need the differential values.
        # But when the test fails, some of them could be negative
        # So we cheat and set those to 0
        # The experienced viewer should note the "0 error" and suspect the error
        lows = centrals-lows
        highs = highs - centrals
        lows = [max(0,l) for l in lows]
        highs= [max(0,h) for h in highs]

        x = centrals.keys()

        label = g[0] if type(g) is tuple else g
        ax.errorbar(x, centrals,
                      marker=".",
                      linestyle="--",
                      yerr=(lows, highs),
                      label=label,
                      capsize=3,
                      markersize=7)


        if point_labels:
            for xx,yy in zip(x, centrals):
                ax.text(xx,yy,int(xx/1000), fontsize=5)
    ax.legend()
    return fig, ax

def format_bw_plot(ax, ylabel="Throughput (Gbps)", div=1e9):
    ax.set_ylabel(ylabel)
    ticks_y = ticker.FuncFormatter(lambda y, pos: '{0:g}'.format(y/div))
    ax.yaxis.set_major_formatter(ticks_y)
    ax.tick_params(axis="y",direction="in")
    ax.grid(which="major", axis="y")

def format_pktsize_plot(ax, xlabel="Payload Size (B)", div = 1):
    ax.set_xlabel(xlabel)
    ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/div))
    ax.tick_params(axis="x",direction="in")
    #ax.grid(which="major", axis="x")
    ax.xaxis.set_major_formatter(ticks_x)

def format_time_plot(ax, ylabel="Application time", div=1, log=False, start =0, stop=1e3):
    ax.set_ylabel(ylabel)
    ticks_y = ticker.FuncFormatter(lambda y, pos: '{0:g}'.format(y/div))
    ax.tick_params(axis="y",direction="in")

    if log:
        def timelabel(t):
            if t == 10:
                return "10 ns"
            if t == 100:
                return "100 ns"
            if t == 1000:
                return "1 µs"
            if t == 10000:
                return "10 us"
            if t == 100000:
                return "100 us"
            return f"{int(t)} ns"

        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(lambda y, pos : timelabel(y))
    else:
        ax.yaxis.set_major_formatter(ticks_y)
    ax.set_ylim(start, stop)
    ax.grid(which='major',linestyle='-',axis='y')

def time_cutter(data, column, threshold, cut_start = 3, cut_end = 1):
    data = data[data[column] >= threshold]
    start = data.groupby("run")["TIME"].min()
    stop = data.groupby("run")["TIME"].max()
    start += cut_start
    stop -= cut_end
    # To keep things simple, we join on the "run", adding start and stop times
    # And then filter on these.
    data = data.join(start, on="run", how="left", rsuffix="_CUT_START")
    data = data.join(stop, on="run", how="left", rsuffix="_CUT_STOP")
    data = data[data["TIME"] > data["TIME_CUT_START"]]
    data = data[data["TIME"] < data["TIME_CUT_STOP"]]
    del data["TIME_CUT_START"]
    del data["TIME_CUT_STOP"]

    return data


# This is a simple attempt to retrieve test name without a regexp (sigh)
def parse_testname(path, base):
    # if base:
    #     if "*" in base:
    #         base = base.replace("*", "")
    #     path = path.replace(base, "")
    #     path = path.split("/")[0]
    #     while path.startswith("_"):
    #         path = path[1:]
    #     return path
    # else:
    #     return path.split("/"
    return path

def stacked_plotter(time_results, by="MODE",
                    elements = ['GPU_RUN_AVG', 'GPU_WAIT_AVG', 'GPU_SEND_AVG'],
                    rename= {}):

    fig, ax = plt.subplots(1, 1)
    means=[]
    stds=[]
    lowers=[]
    highers=[]
    groups=[]
    for g, gdata in time_results.groupby(by):
        m=np.array([np.mean(gdata[e]) for e in elements])
        s=np.array([np.std(gdata[e]) for e in elements])
        l=np.array([np.quantile(gdata[e],.05) for e in elements])
        h=np.array([np.quantile(gdata[e],.95) for e in elements])
        #stats[g] = {"means":means, "stds":stds,  "delta_low":means-lowers, "delta_high":highers-means}
        groups.append(str(g))
        means.append(m)
        stds.append(s)
        highers.append(h)
        lowers.append(l)
        #print(g)
        #print("MEANS", m)
        #print("DEVS", s)

    comulatives = np.array([0.0]*len(groups))
    bottoms = np.array([0.0]*len(groups))
    for i,e in enumerate(elements):
        v = [m[i] for m in means]
        l = [l[i] for l in lowers]
        h = [h[i] for h in highers]
        vv = np.array(h)
        hd = h - vv
        ld = vv - l
        #vb=v+bottoms
        ax.bar(groups,v, bottom=bottoms,
              #yerr=(ld,hd),
              label = rename[e] if e in rename else e,
              zorder=5)
        #comulatives = comulatives + means[i]
        bottoms+=v

    labels = [item.get_text() for item in ax.get_xticklabels()]
    labels = [rename[l] if l in rename else l for l in labels]
    ax.set_xticklabels(labels)


    ax.legend()
    return fig,ax
