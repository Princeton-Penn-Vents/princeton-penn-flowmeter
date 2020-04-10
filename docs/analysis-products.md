# Analysis products

The analysis stage of the workflow takes two time-series as input:

   * **flow (L/min):** the primary observable of the flow-meter, after conversion/calibration from delta pressure in Pa through a 4/7 power. Positive **flow** is into the lung; negative **flow** is out.
   * **pressure (cm-H₂O):** air pressure in the lungs relative to atmospheric pressure (i.e. this quantity is zero at atmospheric pressure). Positive **pressure** is above atmospheric pressure; negative **pressure** is below it.

Both are sampled in identical time-steps, and the time-steps themselves are given as a third array:

   * **realtime (sec):** floating point number of seconds since epoch (January 1, 1970). This includes millisecond resolution.

## Time-series products

Currently only one:

   * **volume (mL):** the time-integral of **flow**, after converting L to mL and sec to min. The zero-point for **volume** starts at the beginning of the **flow** integration, so positive **volume** is an inflated lung and negative **volume** is below the initial value.

**FIXME:** The "beginning of the **flow** integration" is at the beginning of the time-series in the rolling buffer, which has an arbitrary starting point. With the above definition, absolute volume is arbitrarily defined and it will be redefined as the time-series buffer rolls forward. Since old breath records are replaced with new breath records whenever the same data are recomputed (below), absolute volumes in the breath records will change as the starting point gets redefined. Volume differences for breaths that came from different rolling window segments would be wrong, but we don't have any of those: all volume differences are computed in the same rolling window segment, so they're both correct and unchanging. The features that are or arn't affected by this are noted below, but we should fix a definition that at least asymtotically stabilizes the absolute volume.

## Breath record products

The time-series data are summarized into records that each represent one breath. Breaths can be long or short, and represent a discretization of the original waveform. Four time points are identified on each wave:

   * **inhale:** when the **flow** is at a maximum.
   * **full:** when the **volume** is at a maximum.
   * **exhale:** when the **flow** is at a minimum (extremely negative).
   * **empty:** when the **volume** is at a minimum.

A breath record can have data on any phase of the breath that can be determined from the time-series, but the dividing line between two breaths is after **empty**. Although the beginning and end aren't guaranteed, each breath record is guaranteed to proceed in the same order: **inhale** → **full** → **exhale** → **empty** in time-order, without any skipped or duplicated steps. These four turning points are determined from a smoothed version of the data, to minimize spurious "breaths" due to noise; the Gaussian sigma for this smoothing procedure is 0.2 seconds.

A breath record may have any of the following fields. (Field names include spaces, but not parentheses or units.)

   * **inhale timestamp (sec):** the **realtime** (floating point seconds since epoch) when the **flow** is at a maximum.
   * **inhale flow (L/min):** the original, unsmoothed **flow** at the time of **inhale**.
   * **inhale dV/dt (mL/sec):** the smoothed **flow** at the time of **inhale**, converted into mL and seconds.
   * **inhale dP/dt (cm-H₂O/sec):** the rate of change of smoothed **pressure** at the time of **inhale**.
   * **inhale compliance (ml/cm-H₂O):** the ratio of **dV/dt** over **dP/dt** at the time of **inhale**.
   * **min pressure (cm-H₂O):** the minimum value of unsmoothed **pressure** between the **inhale** time and the previous **exhale**, if it exists.
   * **full timestamp (sec):** the **realtime** when the **volume** is at a maximum.
   * **full pressure (cm-H₂O):** the original, unsmoothed **pressure** at the time of **full**, which is often but not necessarily equal to **max pressure**.
   * **full volume (mL):** the original, unsmoothed **volume** at the time of **full**, which is always the maximum for this breath.
   * **expiratory tidal volume (mL):** the difference between the **full volume** and the previous **empty volume**, if it exists. This quantity is always positive and is a relative volume, computed within a single time-series buffer, so it is not sensitive to changes in the absolute **volume** as the time-series rolls (see **FIXME** above).
   * **exhale timestamp (sec):** the **realtime** when the **flow** is at a minimum (extremely negative).
   * **exhale flow (L/min):** the original, unsmoothed **flow** at the time of **exhale**.
   * **exhale dV/dt (mL/sec):** the smoothed **flow** at the time of **exhale**, converted into mL and seconds.
   * **exhale dP/dT (cm-H₂O/sec):** the rate of change of smoothed **pressure** at the time of **exhale**.
   * **exhale compliance (ml/cm-H₂O):** the ratio of **dV/dt** over **dP/dt** at the time of **exhale**.
   * **max pressure (cm-H₂O):** the maximum value of unsmoothed **pressure** between the **exhale** time and the previous **inhale**, if it exists.
   * **empty timestamp (sec):** the **realtime** when the **volume** is at a minimum.
   * **empty pressure (cm-H₂O):** the original, unsmoothed **pressure** at the time of **empty**, which is often but not necessarily equal to **min pressure**.
   * **empty volume (mL):** the original, unsmoothed **volume** at the time of **empty**, which is always the minimum for this breath.
   * **time since last (sec):** the time difference between this breath (at **empty**) and the previous breath (at its **empty**).
