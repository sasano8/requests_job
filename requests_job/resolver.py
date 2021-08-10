from typing import Callable

from .sandbox import eval, evalute_recursive


def resolve_eval_str_and_merge_context(context: dict, data: dict):
    for k, v in data.items():
        result = evalute_recursive(v, context)
        context[k] = result
    return context


def resolve_eval_str(context: dict, data: dict):
    result = {}
    for k, v in data.items():
        result[k] = evalute_recursive(v, context)

    return result
