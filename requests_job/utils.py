from functools import wraps
from typing import Any, Dict, Union
from urllib.parse import urljoin as _urljoin

from pydantic.fields import Field
from typing_extensions import Annotated


@wraps(_urljoin)
def urljoin(base, url, allow_fragments=True):
    """urlを結合するか右辺を優先する。詳しい挙動はテストを参照"""
    if base:
        if not (base.startswith("https://") or base.startswith("http://")):
            raise ValueError(f"Invalid URL: '{base + url}'")

    url = _urljoin(base, url, allow_fragments=allow_fragments)
    if url:
        if not (url.startswith("https://") or url.startswith("http://")):
            raise ValueError(f"Invalid URL: '{url}'")
    return url


def normalize(obj1: Union[dict, None], obj2: Union[dict, None]):
    """"""
    if obj1 is None and not obj2:
        return None

    obj1 = obj1 or {}
    obj2 = obj2 or {}
    return obj1, obj2


def merge(obj1: Union[dict, None], obj2: Union[dict, None]):
    result = normalize(obj1, obj2)
    if result is None:
        return None
    return {**result[0], **result[1]}


def merge_objects(
    obj1, obj2, *, deep: bool = True, max_nest: int = 1, current_nest: int = 0
):
    if deep:
        import copy

        obj1 = copy.deepcopy(obj1)
        obj2 = copy.deepcopy(obj2)

    if not current_nest:
        current_nest = 0

    if isinstance(obj1, list):
        if not isinstance(obj2, list):
            raise TypeError(
                f"cant merge for not same type. {type(obj1)} : {type(obj2)}"
            )
        obj1 = obj1 + obj2
    elif isinstance(obj1, set):
        if not isinstance(obj2, set):
            raise TypeError(
                f"cant merge for not same type. {type(obj1)} : {type(obj2)}"
            )
        obj1 = obj1.union(obj2)
    elif isinstance(obj1, dict):
        if not isinstance(obj2, dict):
            raise TypeError(
                f"cant merge for not same type. {type(obj1)} : {type(obj2)}"
            )

        current_nest += 1
        if current_nest <= max_nest:
            for key in obj2.keys():
                obj2_val = obj2[key]

                if not key in obj1:
                    obj1[key] = obj2_val
                else:
                    if isinstance(obj2_val, (list, set, dict)):
                        obj1_val = obj1[key]
                        result = merge_objects(
                            obj1_val, obj2_val, deep=False, current_nest=current_nest
                        )
                        obj1[key] = result
                    else:
                        obj1[key] = obj2_val
        else:
            for key in obj2.keys():
                obj1[key] = obj2[key]

    else:
        raise TypeError(f"cant merge for unmergeable type: obj1 - {type(obj1)}")

    return obj1
