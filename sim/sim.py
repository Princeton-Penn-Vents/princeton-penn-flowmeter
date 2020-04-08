#!/usr/bin/env python3

import sys
import numpy as np


def constant_compliance(**kwargs):
    return 0.4

class VentSim:
    def __init__(self,curr_time,sim_time_max,params={}):
        self.current_bin = 0
        self.sampling_rate = params.get("sampling_rate",100.)
        self.breathing_rate = params.get("breathing_rate",12.0)
        self.max_flow = params.get("max_flow",12.0)
        self.tidal_volume = params.get("tidal_volume",0.6)
        self.peep = params.get("peep",4)
        self.curr_time = curr_time
        self.sim_time = sim_time_max
        self.recovery_tau = params.get("recovery",15)
        self.compliance_func = params.get("compliance_func",constant_compliance)
        self.v0 = params.get("starting_volume",0.0)
        
        self.precompute()
        
    def precompute(self):
        self.times = np.arange(0, self.sim_time, 1.0 / self.sampling_rate)
        self.breath_starts = self.get_breath_starts()
        self.flow = self.nominal_flow()
        self.volume = self.nominal_volume()
        self.pressure = self.nominal_pressure()

    def get_breath_starts(self):
        """
        returns:
        array of breath start times
        """

        max_breaths = (
            1.2 * self.sim_time / self.breathing_rate
        )  # safety margin for fluctuating this later

        breath_starts = np.arange(0, max_breaths * self.breathing_rate, self.breathing_rate)
        return breath_starts 

    def nominal_flow(self):

        """
        expected parameters:
        inhale_exhale_ratio (optional, default is 0.5) (unused)
        """

        bins = int(self.sim_time * self.sampling_rate)
        flow = np.zeros(bins)
        
        flow_start_bins = ( self.breath_starts )  * self.sampling_rate
        # max_flow is in L/minute
        flow_end_bins = flow_start_bins + self.tidal_volume * self.sampling_rate / (self.max_flow / 60.0)
        
        flow_start_bins = flow_start_bins.astype(int)
        flow_end_bins = flow_end_bins.astype(int)
        breath_integrals = np.zeros(len(flow_start_bins))

        for i in range(len(flow_start_bins)):
            if flow_start_bins[i] < bins:
                flow[flow_start_bins[i] : min(bins, flow_end_bins[i])] = self.max_flow
                breath_integrals[i] = np.sum(
                    flow[flow_start_bins[i] : min(bins, flow_end_bins[i])]
                )

        exp_zero_bins = flow_start_bins[1:]
        exp_min_bins = flow_end_bins[:-1]
        times = np.arange(0, 1.2 * self.sim_time, 1.0 / self.sampling_rate)
        #print(current_time)
        
        for i in range(len(exp_min_bins)):
            if exp_min_bins[i] < bins:
                b_min = exp_min_bins[i] + 2
                b_max = min(bins, exp_zero_bins[i]) - 1
                flow[b_min:b_max] = np.log(
                    (times[b_min:b_max] - times[flow_start_bins[i]])
                    / (times[b_max] - times[flow_start_bins[i]])
                )
                flow[b_min:b_max] *= -1.0 * breath_integrals[i] / np.sum(flow[b_min:b_max])

        return flow

    def nominal_volume(self):
        return np.cumsum(self.flow) * (1.0 / self.sampling_rate) + self.v0

    def nominal_pressure(self):
        # We can add **kwargs and join it with locals if we need to go further up the chain
        compliance_val = self.compliance_func
        pressure = np.zeros(len(self.volume))
        pressure[0] = self.peep
        delta_p = (self.volume[1:] - self.volume[:-1]) * compliance_val()
        pressure[1:] = pressure[0] + np.cumsum(delta_p)
        return pressure

    def get_next(self):
        return 1

    def get_batch(self,nSeconds):
        return 1

    def get_all(self):
        return self.times,self.flow,self.volume,self.pressure
    
    

if __name__ == "__main__":

    import matplotlib.pyplot as plt
    from matplotlib import animation

    from datetime import datetime
    now_time = datetime.now().timestamp()
    print(now_time)

    simulator = VentSim(now_time,1200)

    time, flow, volume, pressure = simulator.get_all()

    fig = plt.figure()
    plt.subplot(3, 1, 1)
    (line_flow,) = plt.plot(time, flow)
    plt.xlabel("Time (seconds)")
    plt.ylabel("Flow (L/m)")

    plt.subplot(3, 1, 2)
    (line_volume,) = plt.plot(time, volume)
    plt.xlabel("Time (seconds)")
    plt.ylabel("Volume (L)")

    plt.subplot(3, 1, 3)
    (line_pressure,) = plt.plot(time, pressure)
    plt.xlabel("Time (seconds)")
    plt.ylabel("Pressure (cm H2O)")

    plt.show()
    
