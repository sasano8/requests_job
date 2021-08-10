import re
from typing import Dict

import yaml

# https://gihyo.jp/dev/serial/01/yaml_library/0001

##################
# Roader
##################

# parse
# YAML文字列を構文解析し，イベントの列に変換します。例えば、⁠StartSequence, ScalarData, ScalarData, EndSequence

# compose
# イベントをノードに変換します。ノードは3種類あり，シーケンス，マッピング，スカラーを表します。

# resolver
# 解析によりタグが付与されます。

# construct
# タグにマッチするconstructorが呼び出され、ノードをデータに変換します。

##################
# Dumper
##################

# represent(resolver)
# データをノードにに変換します。

# serialize
# ノードをイベントに変換します。

# present(emit)
# イベントを文字列します。


def constructor(tag):
    def wrapper(func):
        func.__constructor__ = tag
        return func

    return wrapper


def extract_constructors(cls):
    iterator = (getattr(cls, x) for x in dir(cls))
    funcs = {x.__constructor__: x for x in iterator if hasattr(x, "__constructor__")}
    return funcs


class LoaderBase(yaml.Loader):
    Dumper = None
    RESOLVERS: Dict[str, re.Pattern] = {}

    def __init_subclass__(cls) -> None:
        if cls.Dumper is None:

            class Dumper(yaml.Dumper):
                pass

            cls.Dumper = Dumper

        for tag, regexp in cls.RESOLVERS.items():
            yaml.add_implicit_resolver(
                tag=tag,
                regexp=regexp,
                first=None,
                Loader=cls,
                Dumper=cls.Dumper,
            )

        funcs = extract_constructors(cls)
        for tag, func in funcs.items():
            yaml.add_constructor(tag=tag, constructor=func, Loader=cls)
