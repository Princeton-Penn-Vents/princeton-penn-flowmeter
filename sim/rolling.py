import numpy as np


class Rolling:
    def __init__(self, *, size):
        self._values = np.empty((size * 2,), dtype=np.double)
        self._start = 0
        self.size = size
        self.current_size = 0

    def inject(self, values):
        """
        Add a value or an array of values to the end of the rolling buffer.
        It is currently invalid to input a 2D array.
        """

        # Make sure input is an array, truncate if larger than rolling buffer
        values = np.asarray(values)
        if values.size > self.size:
            values = values[-self.size :]
        if values.ndim > 1:
            raise RuntimeError("Only 0D and 1D supported")

        fill_start = (
            self._start if self.current_size == self.size else self.current_size
        )

        # Filling the first copy is always valid
        self._values[fill_start : fill_start + values.size] = values

        # If we go off the end, wrap around
        overlap = fill_start + values.size - self.size
        if overlap > 0:
            self._values[self.size + fill_start :] = values[: self.size - fill_start]
            self._values[:overlap] = values[self.size - fill_start :]
        else:
            self._values[
                fill_start + self.size : fill_start + self.size + values.size
            ] = values

        # Update current size and starting position
        self.current_size = min(self.current_size + values.size, self.size)
        self._start = (
            fill_start + values.size - (self.current_size - self.size)
        ) % self.size

        return self

    def explain(self):
        mask = np.ones_like(self._values, dtype=np.bool)
        mask[: self.current_size] = False
        mask[self.size : self.size + self.current_size] = False
        data = np.ma.masked_array(data=self._values, mask=mask)
        return f"{data} -> {self}"

    def __repr__(self):
        r = repr(np.asarray(self))
        if "\n" in r:
            return "Rolling(\n" + r[6:]
        else:
            return "Rolling(" + r[6:]

    def __str__(self):
        return str(np.array(self))

    def __array__(self):
        data = self._values[self._start : self._start + self.current_size]
        data.flags.writeable = False
        return data

    data = __array__
