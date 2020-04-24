## Developer's guide


The key class is `Generator`, which implements a universal base for collecting and monitoring the data. It holds rolling windows of data, and can `analyze_as_needed`.

The `Collector` takes data from the single readings (run by `patient_*.py` code).

The `LocalGenerator` makes simulated data. The `RemoteGenerator` collects data via HTTP from a server serving data (probably from a `Collector`).
