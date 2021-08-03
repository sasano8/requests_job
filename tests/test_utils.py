from functools import wraps
from typing import Type

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


def assert_exception(func):
    @wraps(func)
    def wrapper(**kwargs):

        expect = kwargs.get("expect")

        if isinstance(expect, Exception):
            if isinstance(expect, Exception):
                with pytest.raises(expect.__class__, match=str(expect)):
                    return func(**kwargs)
        else:
            return func(**kwargs)

    return wrapper


@pytest.mark.parametrize(
    "src, kwargs, expect",
    [
        ("1 > 0", {}, True),
        ("name == 'bob'", {"name": "bob"}, True),
        ("name == 'bob'", {"name": ""}, False),
    ],
)
@assert_exception
def test_eval(src, kwargs, expect):
    from requests_job.utils import eval

    assert eval(src, **kwargs) == expect


def get_case_for_test_eval_builtins():
    undefined = NameError("is not defined")
    # python 3.9.4
    cases = [
        ("open", undefined),
        ("abs", abs),
        ("all", all),
        ("any", any),
        ("ascii", ascii),
        ("bin", bin),
        ("bool", bool),
        ("breakpoint", undefined),
        ("bytearray", bytearray),
        ("bytes", bytes),
        ("callable", callable),
        ("chr", chr),
        ("classmethod", undefined),
        ("compile", undefined),
        ("complex", complex),
        ("delattr", undefined),
        ("dict", dict),
        ("dir", undefined),
        ("divmod", divmod),
        ("enumerate", enumerate),
        ("eval", undefined),
        ("exec", undefined),
        ("filter", filter),
        ("float", float),
        ("format", format),
        ("frozenset", frozenset),
        ("getattr", getattr),
        ("globals", undefined),
        ("hasattr", hasattr),
        ("hash", hash),
        ("help", undefined),
        ("hex", hex),
        ("id", id),
        ("input", undefined),
        ("int", int),
        ("isinstance", isinstance),
        ("issubclass", issubclass),
        ("iter", iter),
        ("len", len),
        ("list", list),
        ("locals", undefined),
        ("map", map),
        ("max", max),
        ("memoryview", undefined),
        ("min", min),
        ("next", next),
        ("object", object),
        ("oct", oct),
        ("open", undefined),
        ("ord", ord),
        ("pow", pow),
        ("print", undefined),
        ("property", undefined),
        ("range", range),
        ("repr", repr),
        ("reversed", reversed),
        ("round", round),
        ("set", set),
        ("setattr", undefined),
        ("slice", slice),
        ("sorted", sorted),
        ("staticmethod", undefined),
        ("str", str),
        ("sum", sum),
        ("super", undefined),
        ("tuple", tuple),
        ("type", type),
        ("vars", undefined),
        ("zip", zip),
        ("__import__", undefined),
    ]

    return cases


@pytest.mark.parametrize(
    "src, expect",
    get_case_for_test_eval_builtins(),
)
@assert_exception
def test_eval_builtins(src, expect):
    from requests_job.utils import eval

    assert eval(src) == expect
