# from . import contexts
from . import builtins
from .builtins_data import eval_builtins, eval_extend
from .contexts import Engine, EvalStr
from .utils import build_eval, evalute_recursive

__all__ = [
    # "Context",
    # "eval",
    # "build_eval",
    "EvalStr",
    "evalute_recursive",
    "Engine",
]


# def Context() -> contexts.Context:
#     raise NotImplementedError()
#     # return contexts.Context.instantiate()


# eval = build_eval(dict(**eval_builtins, **eval_extend))
