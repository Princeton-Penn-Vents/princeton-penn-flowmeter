

## Data format (sensor -> patient event loop):

```json
{"v":1,"t":1234,"P":12.332,"F":-1.23,"temp":23.3}
```

One [JSON object](https://www.json.org/json-en.html) per line of text (delimited by `"\n"`, no `"\n"` allowed within a JSON object) at a rate of roughly 50 Hz. Field names are case-sensitive.

   * The `"v"` field (mandatory) is the version of the protocol; always `1`. Future versions are also integers (and version updates will be rare).
   * The `"t"` field (mandatory) is a time relative to an unspecified constant, which does not change through the interval in which the data collection box is connected to the nurse's station (with a given port number). This time is an integer in milliseconds.
   * The `"P"` field (mandatory) is [intrapleural pressure](https://en.wikipedia.org/wiki/Intrapleural_pressure) (difference between pressure in lungs and atmospheric pressure) in cm H2O. Positive pressure is greater than atmospheric; negative is less than atmospheric.
   * The `"F"` field (mandatory) is the flow rate in mL/sec. The volume can be computed by strictly integrating this field with respect to time. Positive flow is into the lungs; negative flow is out.
   * The `"temp"` field is optional, and in fact is only populated in about 1 out of 50 lines (1 Hz). It is the the temperature of the flow sensor in degrees C.

## Data format (patient -> nurse)

Note: comments inserted for clarity only - JSON does not allow comments.

```yaml
{
  "version": 1,
  "source": "Sim.send",
  "parameters": {
    # Simulation parameters here
  },
  "calibration": {
    # Calibration parameters here
  },
  "time":1234.343,   # Current packet timestamp
  "alarms": {
    "MinFlow": false,
    # Status of patient alarms here
  },
  "data": {
    "timestamps": [1,2,3,5],
    "flows": [23.2, 12.2, 123.2, -2.2],
    "pressures": [1.2, 3.4, 5.6, 7.8],
    "volumes": [1.2, 3.4, 5.6, 7.8]
  }
}
```
