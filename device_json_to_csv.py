#!/usr/bin/env python3

import json
import csv

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("input", help="Input single-line json file")
parser.add_argument("output", help="Output csv file")
args = parser.parse_args()

with open(args.input) as fin, open(args.output, "w") as fout:
    writer = csv.writer(fout, delimiter=",")

    # Heading
    writer.writerow(["t", "F", "P"])

    for line in fin:
        d = json.loads(line)
        writer.writerow([d["t"], d["F"], d["P"]])
