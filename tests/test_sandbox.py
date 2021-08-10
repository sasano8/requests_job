from functools import wraps

import pytest

from requests_job import undefined
from requests_job.sandbox import Engine


@pytest.fixture
def empty_engine():
    return Engine()


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
def test_eval_builtins(src, expect, empty_engine):
    assert empty_engine.eval(src) == expect


def test_evalue_obj(empty_engine):
    from requests_job import undefined
    from requests_job.sandbox import EvalStr

    engine = empty_engine
    evalute_recursive = engine.evalute_recursive

    assert 1 == evalute_recursive(1, {})
    assert "a" == evalute_recursive("a", {})
    assert [2, "b", False] == evalute_recursive([2, "b", False], {})
    assert {"a": False, "b": True} == evalute_recursive({"a": False, "b": True}, {})

    assert None is evalute_recursive(EvalStr(""), {})
    assert None is evalute_recursive(EvalStr("null"), {})
    assert undefined is evalute_recursive(EvalStr("undefined"), {})
    assert 1 == evalute_recursive(EvalStr("1"), {})
    assert "a" == evalute_recursive(EvalStr("'a'"), {})
    assert [2, "b", False] == evalute_recursive(
        [EvalStr("2"), EvalStr("'b'"), EvalStr("False")], {}
    )
    assert {"a": False, "b": True, "c": [1], "d": {"e": 3}} == evalute_recursive(
        {
            "a": EvalStr("False"),
            "b": EvalStr("True"),
            "c": EvalStr("[1]"),
            "d": EvalStr("{'e':3}"),
        },
        {},
    )


@pytest.mark.parametrize(
    "src, expect",
    [
        ("", None),
        ("None", None),
        ("null", None),
        ("undefined", undefined),
        ("1", 1),
        ("'a'", "a"),
        ("[1]", [1]),
        ("{'a': 1}", {"a": 1}),
        ("{2}", set([2])),
    ],
)
def test_context(src, expect, empty_engine):
    from requests_job.sandbox import Engine

    assert empty_engine.eval(src) == expect


def test_evalute_environ():
    import os

    from requests_job.sandbox import Engine, EvalStr

    os.environ["TEST_CONTEXT"] = "abc"

    engine = Engine({"env": os.environ})
    evalute_recursive = engine.evalute_recursive

    assert "abc" == evalute_recursive(EvalStr("env['TEST_CONTEXT']"))


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
    from requests_job.sandbox import Engine

    engine = Engine(kwargs)
    assert engine.eval(src) == expect
