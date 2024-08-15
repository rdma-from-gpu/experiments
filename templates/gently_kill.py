#!/usr/bin/python3

# Gently kill a process, then kill it brutally


import signal
import os
import argparse
import psutil
import time



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    description='Gently kill processes')
    parser.add_argument("--parent",
                        type=int,
                        help="The parent process pid where to look")
    parser.add_argument("--process-name",
                        type=str,
                        default="worker",
                        help="The process name to kill")
    parser.add_argument("--signal",
                        default=2,
                        type=int,
                        help="What signal to send (initially)")
    parser.add_argument("--kill-signal",
                        default=9,
                        type=int,
                        help="What signal to send, after timeout")
    parser.add_argument("--timeout",
                        default=10,
                        type=int,
                        help="How much to wait")

    args = parser.parse_args()


    if not psutil.pid_exists(args.parent):
        print("No process with PID", args.parent)
        exit(0)
    p = psutil.Process(args.parent)

    children = p.children(recursive=True)
    print(children)
    for c in children:
        print(c)
        if c.name == args.process_name:
            print(c)
            break


    c.send_signal(args.signal)
    for i in range(args.timeout):
        if not c.is_running():
            break
        else:
            time.sleep(1)
    if c.is_running():
        c.send_signal(args.kill_signal)
