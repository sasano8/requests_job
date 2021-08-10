import pytest

from requests_job.utils import merge_objects


def test_merge_objects():
    assert merge_objects([1], [2]) == [1, 2]
    assert merge_objects({1}, {2}) == {1, 2}
    assert merge_objects({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}
    assert merge_objects(
        {"a": [1], "b": {1}, "c": {"a": 1}}, {"a": [2], "b": {2}, "c": {"b": 2}, "d": 2}
    ) == {"a": [1, 2], "b": {1, 2}, "c": {"a": 1, "b": 2}, "d": 2}

    a = {}
    b = {}
    c = merge_objects(a, b)
    assert id(a) != id(c)
    assert id(b) != id(c)

    c = merge_objects(a, b, deep=False)
    assert id(a) == id(c)
    assert id(b) != id(c)

    with pytest.raises(TypeError, match="unmergeable type"):
        merge_objects(1, 1)

    with pytest.raises(TypeError, match="not same type"):
        merge_objects({}, 1)

    with pytest.raises(TypeError, match="not same type"):
        merge_objects([], {})

    with pytest.raises(TypeError, match="not same type"):
        merge_objects([], set())

    with pytest.raises(TypeError, match="not same type"):
        merge_objects({}, set())

    with pytest.raises(TypeError, match="not same type"):
        merge_objects({"a": []}, {"a": set()})

    with pytest.raises(TypeError, match="not same type"):
        merge_objects({"a": []}, {"a": {}})

    with pytest.raises(TypeError, match="not same type"):
        merge_objects({"a": {}}, {"a": set()})


def test_urljoin():
    from requests_job.utils import urljoin

    assert urljoin("", "") == ""

    with pytest.raises(ValueError, match="Invalid URL"):
        urljoin("a", "b")

    assert urljoin("http://test", "b") == "http://test/b"

    with pytest.raises(ValueError, match="Invalid URL"):
        urljoin("a", "http://test")

    assert urljoin("http://test/a", "http://test/b") == "http://test/b"
