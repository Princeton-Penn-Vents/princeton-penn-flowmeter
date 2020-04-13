#!/usr/bin/env python3

from .ventsim import VentSim
import random
import os

def start_sims(nSim, start_time, sim_time):

    sims = []
    for i in range(nSim):

        params = {}

        simulator = VentSim(start_time, sim_time)
        simulator.load_configs(os.path.join(os.path.dirname(os.path.realpath(__file__)),"sim_configs.yml"))
        if random.random() < 0.5:
            simulator.use_config("nominal_breather",params)
        else:
            simulator.use_config("nominal_nonbreather",params)
        simulator.initialize_sim()

        # advance it somewhat
        #t = sim.get_batch(100 * random.random())
        sims.append(simulator)

    return sims
