import numpy as np
import scipy.integrate
import scipy.signal

favorite = None

def smooth_derivative(times, values, sig=0.2):
    window_width = int(np.ceil(6*sig/np.min(times[1:] - times[:-1])))
    windowed_times  = np.lib.stride_tricks.as_strided(times,
                                                      (len(times) - window_width + 1, window_width),
                                                      (times.itemsize, times.itemsize))
    windowed_values = np.lib.stride_tricks.as_strided(values,
                                                      (len(values) - window_width + 1, window_width),
                                                      (values.itemsize, values.itemsize))

    centers = np.mean(windowed_times, axis=1)
    windowed_times_centered = windowed_times - centers[:, np.newaxis]
    windowed_weights = np.exp(-0.5 * windowed_times_centered**2 / sig**2)
    sumw   = np.sum(windowed_weights, axis=1)
    sumwx  = np.sum(windowed_weights * windowed_times_centered, axis=1)
    sumwy  = np.sum(windowed_weights * windowed_values, axis=1)
    sumwxx = np.sum(windowed_weights * windowed_times_centered * windowed_times_centered, axis=1)
    sumwxy = np.sum(windowed_weights * windowed_times_centered * windowed_values, axis=1)
    delta     = (sumw*sumwxx) - (sumwx*sumwx)
    intercept = ((sumwxx*sumwy) - (sumwx*sumwxy)) / delta
    slope     = ((sumw*sumwxy) - (sumwx*sumwy)) / delta
    
    return centers, intercept, slope

def find_breaths(times, values, derivative, threshold=0.02):
    values_threshold = threshold*np.max(abs(values))
    derivative_threshold = threshold*np.max(abs(derivative))

    A, = np.nonzero((values[:-1] < 0) & (values[1:] >= 0) & (0.5*(derivative[:-1] + derivative[1:]) >= derivative_threshold))
    B, = np.nonzero((derivative[:-1] >= 0) & (derivative[1:] < 0) & (0.5*(values[:-1] + values[1:]) >= values_threshold))
    C, = np.nonzero((values[:-1] >= 0) & (values[1:] < 0) & (0.5*(derivative[:-1] + derivative[1:]) < -derivative_threshold))
    D, = np.nonzero((derivative[:-1] < 0) & (derivative[1:] >= 0) & (0.5*(values[:-1] + values[1:]) < -values_threshold))

    return 0.5*(times[A] + times[A + 1]), 0.5*(times[B] + times[B + 1]), 0.5*(times[C] + times[C + 1]), 0.5*(times[D] + times[D + 1])

def analyze(generator):
    global favorite
    if favorite is None:
        favorite = generator

    if generator is favorite:
        time = -generator.time
        flow = generator.flow
        volume = scipy.integrate.cumtrapz(flow, time / 60.0)
        pressure = generator.pressure

        print(len(time))
        if len(time) == 1500:
            smooth_time, smooth_flow, smooth_dflow = smooth_derivative(time, flow)
            A, B, C, D = find_breaths(smooth_time, smooth_flow, smooth_dflow)

            # open("/tmp/flow.dat", "w").write("\n".join("%g, %g" % (x, y) for x, y in zip(time, flow)))
            # open("/tmp/smooth_flow.dat", "w").write("\n".join("%g, %g" % (x, y) for x, y in zip(smooth_time, smooth_flow)))
            # raise Exception("STOP")
