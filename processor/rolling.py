import numpy as np


class Rolling:
    def __init__(self, init=None, *, window_size, dtype=None):
        if dtype is None:
            if init:
                dtype = np.asarray(init).dtype
            else:
                dtype = np.double

        self._values = np.empty((window_size * 2,), dtype=dtype)
        self._start = 0
        self._window_size = window_size
        self._current_size = 0

        if init is not None:
            self.inject(init)

    @property
    def window_size(self):
        return self._window_size

    def inject(self, values):
        """
        Add a value or an array of values to the end of the rolling buffer.  It
        is currently invalid to input a 2D array.

        This could be optimized or augmented in the future for faster scalar
        addition.
        """

        # Make sure input is an array, truncate if larger than rolling buffer
        values = np.asarray(values)
        if values.size > self._window_size:
            values = values[-self._window_size :]
        if values.ndim > 1:
            raise RuntimeError("Only 0D and 1D supported")

        fill_start = (
            self._start
            if self._current_size == self._window_size
            else self._current_size
        )

        # Filling the first copy is always valid
        self._values[fill_start : fill_start + values.size] = values

        # If we go off the end, wrap around
        overlap = fill_start + values.size - self._window_size
        if overlap > 0:
            self._values[self._window_size + fill_start :] = values[
                : self._window_size - fill_start
            ]
            self._values[:overlap] = values[self._window_size - fill_start :]
        else:
            self._values[
                fill_start
                + self._window_size : fill_start
                + self._window_size
                + values.size
            ] = values

        # Update current size and starting position
        self._current_size = min(self._current_size + values.size, self._window_size)
        self._start = (
            fill_start + values.size - (self._current_size - self._window_size)
        ) % self._window_size

        return self

    def explain(self):
        "Gives a nice text display of the internal structure"
        mask = np.ones_like(self._values, dtype=np.bool)
        mask[: self._current_size] = False
        mask[self._window_size : self._window_size + self._current_size] = False
        data = np.ma.masked_array(data=self._values, mask=mask)
        return f"{data} -> {self}"

    def __repr__(self):
        r = repr(np.asarray(self))
        start = "Rolling(" + "\n" if "\n" in r else ""
        return start + r[6:-1] + f", window_size={self._window_size})"

    def __str__(self):
        return str(np.array(self))

    def __array__(self):
        data = self._values[self._start : self._start + self._current_size]
        data.flags.writeable = False
        return data

    def __getitem__(self, arg):
        return np.asarray(self).__getitem__(arg)

    def __len__(self):
        return self._current_size


def get_last(rolling, n):
    """
    Get the last N items or less if less available.abs
    """

    if n < len(rolling):
        n = len(rolling)

    return rolling[-n:]


def new_elements(rolling, addition):
    """
    Given two sorted arrays, find the number of elements in the second array
    that are past the end of the first array.
    """

    if len(rolling) < 1:
        return len(addition)

    final_value = rolling[-1]
    ind = np.searchsorted(addition, final_value)
    if ind == len(addition):
        return 0
    else:
        return len(addition) - ind - (final_value == addition[ind])
