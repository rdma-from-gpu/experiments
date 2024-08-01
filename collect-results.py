#!/usr/bin/python3

import glob
import os 
from pathlib import Path
import re
import pandas as pd
import traceback
import argparse

test_sh_re=r".*/(?P<test_name>[^/]*)/(?P<run>[^/]*)/test.sh"
result_re=r"^((?P<KIND>[^\d][^-]*)-)?((?P<TIME>[\d\.]*)-)?RESULT(-(?P<RESULT>[^ ]*))\s*(?P<VALUE>.*)"


def find_tests(path):
    # We use test.sh as sentinel to identify a good run
    g = glob.glob(f"{path}/*/*/test.sh")
    tests = []
    for t in g:
        r=re.match(test_sh_re, t).groupdict()
        r["full_path"] = os.path.abspath(os.path.dirname(t))
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
    if "KIND" in m:
        k = m["KIND"]
        t = float(m["TIME"])
        v = float(m["VALUE"])
        r = m["RESULT"]
        return t,k,v,r
    else:
        return 0,0,0,0



def parse_stdout(f):
    results = {}
    kind_results = {}

    with open(f) as lines:
        for l in lines:
            try:
                if not "RESULT" in l:
                    continue
                t,k,v,r = parse_line(l)
                if not k:
                    k="TIME"
                if t:
                    kind_results.setdefault(k, {})
                    kind_results[k].setdefault(r, {})
                    # Assume that only 1 results per ts exists
                    #kind_results[k][r].setdefault({},t)
                    kind_results[k][r][t] = v
                else:
                    results[r] = v

            except Exception as ex:
                print("Error while parsing line", l,":")
                traceback.print_exc()

    print(results)
    print(kind_results)
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



def generate_h5(t, time_precision=1):
    # Generate a run-specific h5 file. Joined later
    all_results = []
    all_kind_results = {}
    for f in glob.glob(f"{t['full_path']}/*.stdout"):
        results, kind_results = parse_stdout(f)
        results_df = pd.Series(results)
        all_results.append(results_df)
        # keys = keys.union(kind_results.keys())
        # results_store.put("results",results_df)

        for k, this_kr in kind_results.items():
            this_kr_df = pd.DataFrame(this_kr)
            first, last = this_kr_df.index[[0,-1]]
            div = infere_timestamp_div(first)
            div_last = infere_timestamp_div(last)
            if div != div_last:
                print("Warning: the preicision for",k, "it's not consistent:", div, div_last, "assuming", div)

            this_kr_df.index = change_precision(this_kr_df, div, time_precision)
            all_kind_results.setdefault(k, [])
            all_kind_results[k].append(this_kr_df)


    all_results = pd.concat(all_results)
    all_kind_results = {k:pd.concat(r) for k,r in all_kind_results.items()}
    results_store = pd.HDFStore(f"{t[r'full_path']}/results.h5","w")
    results_store.put("results", all_results)
    results_store.put("keys", pd.Series(all_kind_results.keys()))
    for k, r in all_kind_results.items():
        results_store.put(k, r)

    print(results_store.info())
    results_store.close()

    return



if __name__ == "__main__":


    file_path = os.path.dirname(__file__)
    results_path = os.path.abspath(Path(file_path)/ "results")

    parser = argparse.ArgumentParser(
                    description='Look for results, and convert them to h5')
    parser.add_argument("--force", action="store_true", help="Ignore last-modified date, always re-generate h5 files")
    parser.add_argument("--time-precision", type=int, help="Time precision to round results. If more results fall in the same 'slot', only average will be kept. Express it in fraction of seconds (e.g. 1 for 1 sample/sec, 10 for 10 samples/sec.. ", default=1)
    parser.add_argument("--path", default=str(results_path),
                        help="Where to look for results")
    # parser.add_argument("--normalize-times", default=False,
    #                     help="Wether to normalize timestamps to seconds from 0 - where 0 is the first timestamp found in the results")

    args = parser.parse_args()
    print(args)
    tests = find_tests(args.path)


    for t in tests:
        if args.force or new_data(t):
            print("Processing results for", t["full_path"])
            generate_h5(t, args.time_precision)
        else:
            print("Skipping", t["full_path"])

