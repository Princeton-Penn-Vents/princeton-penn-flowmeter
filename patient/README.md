

## Data format (sensor -> patient event loop):

```json
{"v":1,"t":1234,"P":12.332,"F":-1.23,"temp":23.3}
```

Note that this is 1 per line, produced 50 times per second.
Order does not matter in JSON.

## Data format (patient -> nurse)

Note: comments inserted for clarity only - JSON does not allow comments

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
  "alarms":{
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
