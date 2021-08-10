from copy import deepcopy
from typing import Any, Callable, Union

from .builtins_data import eval_builtins, eval_extend
from .contexts import EvalStr


def build_eval(builtins=None):
    globals = {}
    if builtins is not None:
        globals["__builtins__"] = builtins

    def sandbox_eval(___, locals={}):
        return eval(___, globals, locals)

    return sandbox_eval


def evalute_recursive(
    obj: Union[Any, EvalStr],
    locals: dict,
    is_root=True,
):
    if is_root:
        obj = deepcopy(obj)

    if isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = evalute_recursive(v, locals, is_root=False)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            obj[i] = evalute_recursive(value, locals, is_root=False)
    else:
        if not isinstance(obj, EvalStr):
            return obj

        if not obj:
            return None

        result = safe_eval(obj, locals)
        return evalute_recursive(result, locals, is_root=False)

    return obj


safe_eval = build_eval(dict(**eval_builtins, **eval_extend))
