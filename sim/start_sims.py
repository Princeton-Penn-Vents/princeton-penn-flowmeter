#!/usr/bin/env python3

from .ventsim import VentSim
import random


def start_sims(nSim, start_time, sim_time):

    sims = []
    for i in range(nSim):

        params = {}
        # 50% change of the patient breathing on their own
        if random.random() < 0.5:
            params["breath_variation"] = 100. #milliseconds
        params["tidal_volume"] = 0.5 + random.random() * 0.2

        sim = VentSim(start_time, sim_time, params)
        # advance it somewhat
        t = sim.get_batch(100 * random.random())
        sims.append(sim)

    return sims
