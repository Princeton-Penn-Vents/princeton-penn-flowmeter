import numpy as np

def smooth_derivative(times, values, sig=0.2):
    window_width = int(np.ceil(4*sig/np.min(times[1:] - times[:-1])))
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
        return []

    # where does the cycle start?
    which = np.argmin([A[0], B[0], C[0], D[0]])

    ins = [A, B, C, D]
    outs = []
    while len(A) > 0 or len(B) > 0 or len(C) > 0 or len(D) > 0:
        if len(ins[which]) > 1 and all(len(ins[i]) > 0 for i in range(4)):
            nextwhich = np.argmin([ins[i][1 if i == which else 0] for i in range(4)])

            # normal case: A -> B -> C -> D -> ... cycle
            if nextwhich == (which + 1) % 4:
                outs.append((which, ins[which][0]))
                ins[which] = ins[which][1:]

            # too many of one type: A -> B -> B -> B -> C -> D -> ...
            elif nextwhich == which:
                combine = [ins[which][0]]
                ins[which] = ins[which][1:]
                while True:
                    if any(len(x) == 0 for x in ins) or np.argmin([ins[i][0] for i in range(4)]) != which:
                        break
                    combine.append(ins[which][0])
                    ins[which] = ins[which][1:]

                outs.append((which, np.mean(combine)))

            # missing one type: A -> C -> D -> ...
            else:
                fill_value = 0.5*(ins[which][0] + ins[nextwhich][0])
                ins[(which + 1) % 4] = np.concatenate((np.array([fill_value]), ins[(which + 1) % 4]))

                outs.append((which, ins[which][0]))
                ins[which] = ins[which][1:]

        # edge condition: less than one cycle left
        elif len(ins[which]) > 0:
            popped = ins[which][0]
            ins[which] = ins[which][1:]

            if len(outs) > 0 and (outs[-1][0] + 1) % 4 == which:
                outs.append((which, popped))

        else:
            break

        which = (which + 1) % 4
        A, B, C, D = ins

    return outs

def measure_breaths(generator):
    time = generator.timestamp
    flow = generator.flow
    volume = generator.volume
    pressure = generator.pressure

    try:
        smooth_time_f, smooth_flow, smooth_dflow = smooth_derivative(time, flow)
        smooth_time_p, smooth_pressure, smooth_dpressure = smooth_derivative(time, pressure)

        turning_points = find_roots(smooth_time_f, smooth_flow, smooth_dflow)

        breath_times = find_breaths(*turning_points)

    except ValueError:
        return []

    breaths = []
    breath = {}
    for i, (which, t) in enumerate(breath_times):
        index = np.argmin(abs(time - t))

        if which == 0:
            breath["empty timestamp"] = t
            breath["empty pressure"] = pressure[index]
            breath["empty volume"] = volume[index]
            if i >= 2:
                breath["inspiratory tidal volume"] = volume[np.argmin(abs(time - breath_times[i - 2][1]))] - breath["empty volume"]
            if len(breaths) > 0 and "empty timestamp" in breaths[-1]:
                breath["time since last"] = breath["empty timestamp"] - breaths[-1]["empty timestamp"]

            breaths.append(breath)
            breath = {}

        elif which == 1:
            breath["inhale timestamp"] = t
            breath["inhale flow"] = flow[index]
            breath["inhale dV/dt"] = smooth_flow[np.argmin(abs(smooth_time_f - t))] / 60.0
            breath["inhale dP/dt"] = smooth_dpressure[np.argmin(abs(smooth_time_p - t))]
            breath["inhale compliance"] = breath["inhale dV/dt"] / breath["inhale dP/dt"]
            if i >= 2:
                breath["min pressure"] = np.min(pressure[np.argmin(abs(time - breath_times[i - 2][1])):index])

        elif which == 2:
            breath["full timestamp"] = t
            breath["full pressure"] = pressure[index]
            breath["full volume"] = volume[index]
            if i >= 2:
                breath["expiratory tidal volume"] = breath["full volume"] - volume[np.argmin(abs(time - breath_times[i - 2][1]))]

        elif which == 3:
            breath["exhale timestamp"] = t
            breath["exhale flow"] = flow[index]
            breath["exhale dV/dt"] = smooth_flow[np.argmin(abs(smooth_time_f - t))] / 60.0
            breath["exhale dP/dt"] = smooth_dpressure[np.argmin(abs(smooth_time_p - t))]
            breath["exhale compliance"] = breath["exhale dV/dt"] / breath["exhale dP/dt"]
            if i >= 2:
                breath["max pressure"] = np.max(pressure[np.argmin(abs(time - breath_times[i - 2][1])):index])

    if len(breath) != 0:
        breaths.append(breath)

    return breaths

def combine_breaths(generator, old_breaths, new_breaths):
    breaths = list(old_breaths)
    new_breaths = list(new_breaths)

    first_to_check = max(0, len(breaths) - len(new_breaths) - 1)
    for i in range(first_to_check, len(breaths)):
        drop = []
        for j in range(len(new_breaths)):
            # the smoothing sigma is 0.2 sec (see smooth_derivative), so cut at 3*0.2
            same = False
            if "empty timestamp" in breaths[i]  and "empty timestamp" in new_breaths[j]:
                same = same or abs(breaths[i]["empty timestamp"]  - new_breaths[j]["empty timestamp"])  < 3*0.2
            if "inhale timestamp" in breaths[i] and "inhale timestamp" in new_breaths[j]:
                same = same or abs(breaths[i]["inhale timestamp"] - new_breaths[j]["inhale timestamp"]) < 3*0.2
            if "full timestamp" in breaths[i]   and "full timestamp" in new_breaths[j]:
                same = same or abs(breaths[i]["full timestamp"]   - new_breaths[j]["full timestamp"])   < 3*0.2
            if "exhale timestamp" in breaths[i] and "exhale timestamp" in new_breaths[j]:
                same = same or abs(breaths[i]["exhale timestamp"] - new_breaths[j]["exhale timestamp"]) < 3*0.2

            if same:
                # take all fields that are defined in either old or new, but preferring new if it's in both
                breaths[i] = {**breaths[i], **new_breaths[j]}  # Python>=3.5
                drop.append(j)
                break

        for j in drop[::-1]:
            del new_breaths[j]

    breaths.extend(new_breaths)

    return breaths
