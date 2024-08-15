#!/usr/bin/python3

# (C) 2024 Massimo Girondi girondi@kth.se GNU GPL v3

import glob
import os 
from pathlib import Path
import re
import pandas as pd
import traceback
import argparse
from utils import *


if __name__ == "__main__":


    file_path = os.path.dirname(__file__)
    results_path = os.path.abspath(Path(file_path)/ ".." / "results" / "generator_pktsize")

    parser = argparse.ArgumentParser(
        description='Look for results, and convert them to h5. Multi GPU version.')
    parser.add_argument("--force", action="store_true", help="Ignore last-modified date, always re-generate h5 files")
    parser.add_argument("--time-precision", type=int, help="Time precision to round results. If more results fall in the same 'slot', only average will be kept. Express it in fraction of seconds (e.g. 1 for 1 sample/sec, 10 for 10 samples/sec.. ", default=1)
    parser.add_argument("--path", default=str(results_path),
                        help="Where to look for results. IT COULD BE A PRECISE PATH (SINGLE TEST) OR A PREFIX (MULTI TEST).")
    parser.add_argument("--multi", action="store_true",
                        help="Look for results with a wildcard (e.g. './results_*'' for a './results' path). Suffix will be added in the .h5 file as 'test'.")
    # parser.add_argument("--normalize-times", default=False,
    #                     help="Wether to normalize timestamps to seconds from 0 - where 0 is the first timestamp found in the results")

    args = parser.parse_args()
    tests = find_tests(args.path, multi=args.multi)

    new = False
    # First we create a h5 file for each run
    for t in tests:
        if args.force or new_data(t):
            new = True
            print("Processing results for", t["full_path"])
            try:
                generate_h5(t, args.time_precision,
                            {"MODE":"--mode", "WRITE_SIZE": "--write-size"})
            except Exception as ex:
                print("Error while processing", t["full_path"])
                traceback.print_exc()
        else:
            print("Skipping", t["full_path"])

    # Then we combine then together so that we need to load a single file later.

    if not new:
        print("Skipping new main results file: nothing changed!")
        exit(0)

    print("Generating main results file")
    if args.multi:
        h5s = glob.glob(str(Path(str(Path(args.path))+"*")/ "*" / "results.h5"))
    else:
        h5s = glob.glob(str(Path(args.path)/ "*" / "results.h5"))

    all_r = []
    all_kr = []
    #all_variables = set()
    keys = set()
    for f in h5s:
        r, kr = read_h5(f)
        if r is None:
            print("Skipping", f, ": missing results")
            continue

        keys = keys.union(kr.keys())
        all_r.append(r)
        all_kr.append(kr)

    all_r, all_kr =  join_results(all_r, all_kr)

    if not os.path.exists(args.path):
        os.makedirs(args.path)
    dest = Path(args.path)/"results.h5"
    with pd.HDFStore(dest, "w") as store:
        print("Storing results in", dest)
        store.put("results", all_r)
        for k, r in all_kr.items():
            store.put(k, r)
        store.put("keys", pd.Series(list(keys)))


