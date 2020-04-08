#!/usr/bin/env python

from sim import VentSim
from datetime import datetime
import random

def start_sims(nSim=20):

    sims=[]
    now_time = datetime.now().timestamp()
    for i in range(nSim):

        params={}
        # 50% change of the patient breathing on their own
        if random.random()<0.5:
            params['breath_variation'] = 0.1
        params['tidal_volume']=0.5+random.random()*0.2
        
        sim = VentSim(now_time,1000,params)
        #advance it somewhat
        t=sim.get_batch(100*random.random())
        sims.append(sim)

    return sims

