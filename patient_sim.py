#!/usr/bin/env python3

import sys
import numpy as np
from datetime import datetime
from sim.start_sims import start_sims
import time
import json

start_time=int(1000*datetime.now().timestamp()) #milliseconds
sims=start_sims(1, start_time, 12000000) #milliseconds
sim=sims[0]

start_loop=datetime.now().timestamp()

write_alarms_every=20
#did we specify what alarms and their names yet?
alarms={"max_pressure" : 50., "max_flow" : 100.}

nC=0
while(nC<2000):
    t=int(1000*datetime.now().timestamp()) #milliseconds
    d=sim.get_next()
    d["t"]=t
    sys.stdout.write(json.dumps(d))#.encode("ascii"))
    sys.stdout.write('\n')
    sys.stdout.flush()
    if nC%write_alarms_every == 0:
        d2=alarms
        d2["t"]=t
        sys.stdout.write(json.dumps(d2))                       
        sys.stdout.write('\n')
    time.sleep(0.046) #tuned for my mac
    nC+=1

end_loop=datetime.now().timestamp()
#print()
#print(end_loop-start_loop)
