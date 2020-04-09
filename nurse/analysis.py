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

def find_roots(times, values, derivative, threshold=0.02):
    values_threshold = threshold*np.max(abs(values))
    derivative_threshold = threshold*np.max(abs(derivative))

    A, = np.nonzero((values[:-1] < 0) & (values[1:] >= 0) & (0.5*(derivative[:-1] + derivative[1:]) >= derivative_threshold))
    B, = np.nonzero((derivative[:-1] >= 0) & (derivative[1:] < 0) & (0.5*(values[:-1] + values[1:]) >= values_threshold))
    C, = np.nonzero((values[:-1] >= 0) & (values[1:] < 0) & (0.5*(derivative[:-1] + derivative[1:]) < -derivative_threshold))
    D, = np.nonzero((derivative[:-1] < 0) & (derivative[1:] >= 0) & (0.5*(values[:-1] + values[1:]) < -values_threshold))
    
    return 0.5*(times[A] + times[A + 1]), 0.5*(times[B] + times[B + 1]), 0.5*(times[C] + times[C + 1]), 0.5*(times[D] + times[D + 1])

def find_breaths(A, B, C, D):
    # ensure that each type is sorted (though it probably already is)
    A = np.sort(A)
    B = np.sort(B)
    C = np.sort(C)
    D = np.sort(D)

    if len(A) == 0 or len(B) == 0 or len(C) == 0 or len(D) == 0:
        return A, B, C, D

    # where does the cycle start?
    which = np.argmin([A[0], B[0], C[0], D[0]])

    ins = [A, B, C, D]
    outs = ([], [], [], [])
    while len(A) > 0 or len(B) > 0 or len(C) > 0 or len(D) > 0:
        if len(ins[which]) > 1 and all(len(ins[i]) > 0 for i in range(4)):
            nextwhich = np.argmin([ins[i][1 if i == which else 0] for i in range(4)])

            # normal case: A -> B -> C -> D -> ... cycle
            if nextwhich == (which + 1) % 4:
                outs[which].append(ins[which][0])
                ins[which] = ins[which][1:]

            # too many of one type: A -> B -> B -> B -> C -> D -> ...
            elif nextwhich == which:
                combine = [ins[which][0]]
                ins[which] = ins[which][1:]
                while True:
                    if np.argmin([ins[i][0] for i in range(4)]) != which:
                        break
                    combine.append(ins[which][0])
                    ins[which] = ins[which][1:]

                outs[which].append(np.mean(combine))

            # missing one type: A -> C -> D -> ...
            else:
                fill_value = 0.5*(ins[which][0] + ins[nextwhich][0])
                ins[(which + 1) % 4] = np.concatenate((np.array([fill_value]), ins[(which + 1) % 4]))

                outs[which].append(ins[which][0])
                ins[which] = ins[which][1:]

        # edge condition: less than one cycle left
        elif len(ins[which]) > 0:
            outs[which].append(ins[which][0])
            ins[which] = ins[which][1:]

        else:
            break

        which = (which + 1) % 4
        A, B, C, D = ins

    return outs

def analyze(generator):
    global favorite
    if favorite is None:
        favorite = generator

    if generator is favorite:
        time = -generator.time
        flow = generator.flow
        volume = scipy.integrate.cumtrapz(flow, time / 60.0)
        pressure = generator.pressure

        # print(len(time))
        # if len(time) == 1500:
        #     smooth_time, smooth_flow, smooth_dflow = smooth_derivative(time, flow)
        #     A, B, C, D = find_breaths(*find_roots(smooth_time, smooth_flow, smooth_dflow))

        #     open("/tmp/flow.dat", "w").write("\n".join("%g, %g" % (x, y) for x, y in zip(time, flow)))
        #     open("/tmp/smooth_flow.dat", "w").write("\n".join("%g, %g" % (x, y) for x, y in zip(smooth_time, smooth_flow)))

        #     smooth_time, smooth_pressure, smooth_dpressure = smooth_derivative(time, pressure)

        #     open("/tmp/pressure.dat", "w").write("\n".join("%g, %g" % (x, y) for x, y in zip(time, pressure)))
        #     open("/tmp/smooth_pressure.dat", "w").write("\n".join("%g, %g" % (x, y) for x, y in zip(smooth_time, smooth_pressure)))
        #     open("/tmp/A.dat", "w").write("\n".join("%g, 0" % (x,) for x in A))
        #     open("/tmp/B.dat", "w").write("\n".join("%g, 0" % (x,) for x in B))
        #     open("/tmp/C.dat", "w").write("\n".join("%g, 0" % (x,) for x in C))
        #     open("/tmp/D.dat", "w").write("\n".join("%g, 0" % (x,) for x in D))

        #     raise Exception("STOP")
