#!/usr/bin/env python3

import sys
import numpy as np


def constant_compliance(**kwargs):
    return 0.4


def get_breath_starts(*, max_time, breathing_rate):
    """
    expected parameters:
    breathing_rate (seconds between breaths)
    max_time (end time of the simulation)

    returns:
    array of breath start times
    """

    max_breaths = (
        1.2 * max_time / breathing_rate
    )  # safety margin for fluctuating this later

    breath_starts = np.arange(1, 1 + max_breaths * breathing_rate, breathing_rate)

    return breath_starts  # [breath_starts<max_time]


def nominal_flow(
    *,
    sim_time,
    sampling_rate,
    max_flow,
    tidal_volume,
    breath_starts,
    recovery_tau,
    inhale_exhale_ratio=0.5,
):
    """
    expected parameters
    sim_time, (seconds)
    sampling_rate (Hz)
    max_flow, L/minute
    tidal_volume, L
    breath_starts, array of timestamps 
    recovery_tau,
    inhale_exhale_ratio (optional, default is 0.5)
    """

    bins = int(sim_time * sampling_rate)
    flow = np.zeros(bins)

    flow_start_bins = breath_starts * sampling_rate
    # max_flow is in L/minute
    flow_end_bins = flow_start_bins + tidal_volume * sampling_rate / (max_flow / 60.0)

    flow_start_bins = flow_start_bins.astype(int)
    flow_end_bins = flow_end_bins.astype(int)
    breath_integrals = np.zeros(len(flow_start_bins))

    for i in range(len(flow_start_bins)):
        if flow_start_bins[i] < bins:
            flow[flow_start_bins[i] : min(bins, flow_end_bins[i])] = max_flow
            breath_integrals[i] = np.sum(
                flow[flow_start_bins[i] : min(bins, flow_end_bins[i])]
            )

    exp_zero_bins = flow_start_bins[1:]
    exp_min_bins = flow_end_bins[:-1]
    times = np.arange(0, 1.2 * sim_time, 1.0 / sampling_rate)

    for i in range(len(exp_min_bins)):
        if exp_min_bins[i] < bins:
            b_min = exp_min_bins[i] + 2
            b_max = min(bins, exp_zero_bins[i]) - 1
            flow[b_min:b_max] = np.log(
                (times[b_min:b_max] - times[flow_start_bins[i]])
                / (times[b_max] - times[flow_start_bins[i]])
            )
            flow[b_min:b_max] *= (
                -1.0 * breath_integrals[i] / np.sum(flow[b_min:b_max])
            )

    return flow


def nominal_volume(*, flow, v0, sample_rate):
    """
    expected parameters
    flow
    v0
    sample_rate
    """
    return np.cumsum(flow) * (1.0 / sample_rate) + v0


def nominal_pressure(*, volume, peep, compliance_func):
    """
    expected parameters
    volume
    peep (cm H20)
    compliance_func
    """

    # We can add **kwargs and join it with locals if we need to go further up the chain
    compliance_val = compliance_func(**locals())
    pressure = np.zeros(len(volume))
    pressure[0] = peep
    delta_p = (volume[1:] - volume[:-1]) * compliance_val
    pressure[1:] = pressure[0] + np.cumsum(delta_p)
    return pressure


def make(
    *,
    sim_time=120.0,
    sample_rate=100.0,
    breathing_rate=12.0,
    max_flow=12.0,  # L/m
    tidal_volume=0.6,  # L
    peep=4,  # cm H20
):

    breaths = get_breath_starts(max_time=sim_time, breathing_rate=breathing_rate)

    flow = nominal_flow(
        sim_time=sim_time,
        sampling_rate=sample_rate,
        max_flow=max_flow,
        tidal_volume=tidal_volume,
        breath_starts=breaths,
        recovery_tau=15.0,
    )

    volume = nominal_volume(flow=flow, v0=0.0, sample_rate=sample_rate)

    pressure = nominal_pressure(
        volume=volume, peep=peep, compliance_func=constant_compliance
    )

    time = np.arange(0, sim_time, 1.0 / sample_rate)

    return time, breaths, flow, volume, pressure


if __name__ == "__main__":
    time, breaths, flow, volume, pressure = make()

    import pylab

    fig = pylab.figure()
    pylab.subplot(3, 1, 1)
    pylab.plot(time, flow)
    pylab.xlabel("Time (seconds)")
    pylab.ylabel("Flow (L/m)")

    pylab.subplot(3, 1, 2)
    pylab.plot(time, volume)
    pylab.xlabel("Time (seconds)")
    pylab.ylabel("Volume (L)")

    pylab.subplot(3, 1, 3)
    pylab.plot(time, pressure)
    pylab.xlabel("Time (seconds)")
    pylab.ylabel("Pressure (cm H2O)")

    pylab.show()
