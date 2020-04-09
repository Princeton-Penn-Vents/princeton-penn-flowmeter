import numpy as np
import scipy.integrate
import scipy.signal

favorite = None

def analyze(generator):
    global favorite
    if favorite is None:
        favorite = generator

    if generator is favorite:
        time = generator.time
        flow = generator.flow
        volume = generator.volume
        pressure = generator.pressure
