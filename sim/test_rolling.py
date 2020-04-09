from numpy.testing import assert_all_close


def test_rolling_single():
    r = Rolling(size=3)

    assert r.current_size == 0
    assert r._start == 0
    assert_all_close(r.data(), [])

    r.inject(1)
    assert r.current_size == 1
    assert r._start == 0
    assert_all_close(r.data(), [1.0])

    r.inject(2)
    assert r.current_size == 2
    assert r._start == 0
    assert_all_close(r.data(), [1.0, 2.0])

    r.inject(3)
    assert r.current_size == 3
    assert r._start == 0
    assert_all_close(r.data(), [1.0, 2.0, 3.0])

    r.inject(4)
    assert r.current_size == 3
    assert r._start == 1
    assert_all_close(r.data(), [2.0, 3.0, 4.0])

    r.inject(5)
    assert r.current_size == 3
    assert r._start == 2
    assert_all_close(r.data(), [3.0, 4.0, 5.0])

    r.inject(6)
    assert r.current_size == 3
    assert r._start == 0
    assert_all_close(r.data(), [4.0, 5.0, 6.0])

    r.inject(7)
    assert r.current_size == 3
    assert r._start == 1
    assert_all_close(r.data(), [5.0, 6.0, 7.0])


def test_rolling_double():
    r = Rolling(size=3)

    r.inject([1, 2])
    assert r.current_size == 2
    assert r._start == 0
    assert_all_close(r.data(), [1.0, 2.0])

    r.inject([3, 4])
    assert r.current_size == 3
    assert r._start == 1
    assert_all_close(r.data(), [2.0, 3.0, 4.0])

    r.inject([5, 6])
    assert r.current_size == 3
    assert r._start == 0
    assert_all_close(r.data(), [4.0, 5.0, 6.0])


def test_rolling_full():
    r = Rolling(size=3)

    r.inject([1, 2, 3])
    assert r.current_size == 3
    assert r._start == 0
    assert_all_close(r.data(), [1.0, 2.0, 3.0])

    r.inject([4, 5, 6])
    assert r.current_size == 3
    assert r._start == 0
    assert_all_close(r.data(), [4.0, 5.0, 6.0])


def test_rolling_overlap():
    r = Rolling(size=3)

    r.inject([1, 2, 3, 4])
    assert r.current_size == 3
    assert r._start == 0
    assert_all_close(r.data(), [2.0, 3.0, 4.0])

    r.inject([5, 6, 7, 8])
    assert r.current_size == 3
    assert r._start == 0
    assert_all_close(r.data(), [6.0, 7.0, 8.0])
