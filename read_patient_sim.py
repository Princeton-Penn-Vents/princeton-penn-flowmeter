#!/usr/bin/env python3

import sys
import json
import time

from sim.rolling import Rolling

pressure_roll = Rolling(window_size=1000)
flow_roll = Rolling(window_size=1000)
time_roll = Rolling(window_size=1000)

jsons=[]
nC=0
while True:
    line = sys.stdin.readline()
    line2 = line.strip()
    if len(line2) > 0:
        try:
            jsons.append(json.loads(line2))
            j=jsons[-1]
            if 'P' in j:
                # its a sensor measurement
                pressure_roll.inject(j['P'])
                flow_roll.inject(j['F'])
                time_roll.inject(j['t'])
        except ValueError:
            print('Decoding JSON has failed',line2)
            print(len(line),len(line2))
        if len(jsons) % 50 == 0:
            print(len(jsons))
    else:
        time.sleep(0.005)

