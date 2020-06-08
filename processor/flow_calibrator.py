#!/usr/bin/env python3

import numpy as np


def simple(f):
    return np.abs(f) ** (4 / 7)


class flow_calibrator:
    def __init__(self, block="simple") -> None:
        self.func = None
        if block == "simple":
            self.func = simple

        assert self.func is not None

    def deltaP(self, f) -> np.ndarray or float:
        return self.func(f)


if __name__ == "__main__":
    print("Checking default calibration")
    caliber = flow_calibrator()
    fs = np.arange(0.0, 110.0, 10.0)
    for f in fs:
        print(f, caliber.deltaP(f))

    print("Checking array syntax too")
    print(fs)
    print(caliber.deltaP(fs))
