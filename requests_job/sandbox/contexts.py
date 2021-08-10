from collections.abc import Mapping
from copy import deepcopy
from types import MappingProxyType
from typing import Any, Callable, Union

from ..types import undefined
from .builtins_data import eval_builtins, eval_extend


class EvalStr(str):
    pass


class Env(dict):
    def __init__(self):
        from os import environ

        self.environ = environ

    def __getitem__(self, k):
        value = self.get(k, undefined)
        if value is undefined:
            return self.environ.get(k, None)
        else:
            return value


class Context(Mapping):
    def __init__(self, data):
        if not isinstance(data, dict):
            raise TypeError("Contexts cannot be initialized from dicts")
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def copy(self, deep: bool = False):
        if deep:
            copied = deepcopy(self)
        else:
            copied = self
        return self.__class__(copied)


def build_eval(builtins=None):
    globals = {}
    if builtins is not None:
        globals["__builtins__"] = builtins

    def sandbox_eval(src: str, locals=None):
        locals = locals or {}
        return eval(src, globals, locals)

    return sandbox_eval


class Engine:
    CLASS_CONTEXT = Context

    def __init__(
        self,
        locals: dict = None,
        *,
        context_class=Context,
        globals: dict = None,
    ):
        locals = locals or {}
        globals = globals or dict(**eval_builtins, **eval_extend)
        context_class = context_class or self.CLASS_CONTEXT
        self._eval: Callable[[str, dict], Any] = build_eval(globals)
        self.locals = locals

        if not isinstance(locals, dict):
            raise TypeError("locals must be a dict")

        if context_class:
            self.context_class = context_class
        else:
            self.context_class = lambda x: x

    @property
    def context(self):
        return self.context_class(self.locals)

    def __getitem__(self, k):
        return self.locals.__getitem__(k)

    def __setitem__(self, k, v):
        return self.locals.__setitem__(k, v)

    def __delitem__(self, k):
        return self.locals.__delitem__(k)

    def eval(self, src: str, locals={}):
        if src is None or src == "":
            return None
        return self._eval(src, self.context)

    def eval_obj(self, other):
        return self.evalute_recursive(other)

    def evalute_recursive(
        self,
        obj: Union[Any, EvalStr],
        is_root=True,
    ):
        if is_root:
            obj = deepcopy(obj)

        if isinstance(obj, dict):
            for k, v in obj.items():
                obj[k] = self.evalute_recursive(v, is_root=False)
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                obj[i] = self.evalute_recursive(value, is_root=False)
        else:
            if not isinstance(obj, EvalStr):
                return obj
            result = self.eval(obj)
            return self.evalute_recursive(result, is_root=False)

        return obj
