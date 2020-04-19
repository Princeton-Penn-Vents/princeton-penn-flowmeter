#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("input", help="Input single-line json file")
parser.add_argument("output", help="Output csv file")
parser.add_argument("--config", help="Config file to change output")
args = parser.parse_args()

import json
import csv


def dig(d, key, *args, default=None):
    ret = d.get(key)
    if ret is None:
        return default
    elif not args:
        return ret
    else:
        return dig(ret, *args, default=default)


if args.config:
    import yaml

    with open(args.config) as f:
        config = yaml.load(f)
else:
    config = {}

flow_scale = dig(config, "device", "flow", "scale", default=1)
flow_offset = dig(config, "device", "flow", "offset", default=0)
pressure_scale = dig(config, "device", "pressure", "scale", default=1)
pressure_offset = dig(config, "device", "pressure", "offset", default=0)

with open(args.input) as fin, open(args.output, "w") as fout:
    writer = csv.writer(fout, delimiter=",")

    # Heading
    writer.writerow(["time", "Flow", "Pressure", "Current_temp", "DC_temp"])

    for line in fin:
        d = json.loads(line)
        writer.writerow(
            [
                d["t"],
                d["F"] * flow_scale - flow_offset,
                d["P"] * pressure_scale - pressure_offset,
                d.get("C"),
                d.get("D"),
            ]
        )
