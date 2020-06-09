#!/usr/bin/env python3

import numpy as np
import scipy.interpolate
import yaml


def get_yaml(yml_file):
    stream = open(yml_file, "r")
    params = yaml.safe_load(stream)
    qs = np.zeros(len(params))
    deltaPs = np.zeros(len(params))
    for i, d in enumerate(params):
        qs[i] = d["Q"]
        deltaPs[i] = d["deltaP"]

    return qs, deltaPs


class flow_calibrator:
    def __init__(self, block="simple") -> None:
        self.func = None
        if block == "simple":
            self.func = self.simple
        if block.endswith("yaml") or block.endswith("yml"):
            qs, deltaPs = get_yaml(block)
            self.func = scipy.interpolate.interp1d(
                deltaPs, qs, kind="cubic", fill_value="extrapolate"
            )

        assert self.func is not None

    def simple(self, deltaP):
        #        return np.copysign(np.abs(deltaP) ** (4 / 7),deltaP)*0.7198/0.09636372314370535
        return np.copysign(np.abs(deltaP / 0.02962975) ** (4 / 7), deltaP)

    def Q(self, f) -> np.ndarray or float:
        return self.func(f / 60.0)  # put f into Pa to get deltaP


if __name__ == "__main__":
    print("Checking default calibration")
    caliber = flow_calibrator()
    fs = np.arange(0.0, 110.0, 10.0)
    for f in fs:
        print(f, caliber.Q(f))

    print("Checking array syntax too")
    print(fs)
    print(caliber.Q(fs))

    print("Checking the average input file")
    caliber2 = flow_calibrator(
        "/Users/lange/covid/gui/princeton-penn-flowmeter/processor/flowcalib_ave.yaml"
    )
    fs = np.arange(0.0, 25000.0, 10.0)
    print(fs)
    print(caliber2.Q(fs))
    res2 = caliber2.Q(fs)
    
    caliber3 = flow_calibrator(
        "/Users/lange/covid/gui/princeton-penn-flowmeter/processor/flowcalib_det.yaml"
    )
    print(fs)
    print(caliber3.Q(fs))
    res3 = caliber3.Q(fs)

    import pylab

    pylab.plot(fs,res2,label="Ave")
    pylab.plot(fs,res3,label="All")
    pylab.xlabel('measured f')
    pylab.ylabel('Q (L/min)')
    pylab.legend(loc='best')
    pylab.show()
