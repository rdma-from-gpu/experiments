#!/bin/bash

TESTNAME="generator_pktsize"
T=$(date --iso-8601=minutes)
mkdir -p results/$TESTNAME/

mkdir -p ./tmp
rm -rf ./tmp/*

ansible-playbook -i ./inventory/t4.yml ./generator_pktsize.yml $@

mv tmp/* results/$TESTNAME/
