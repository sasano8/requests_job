import re
from typing import Callable, Dict

import yaml

from ..sandbox import EvalStr

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


# class EvalStr(str):
#     pass


class RefStr(str):
    pass


class TypeStr(str):
    pass


class AppDumper(yaml.Dumper):
    pass


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
    Dumper = AppDumper
    RESOLVERS: Dict[str, re.Pattern] = {}

    def __init_subclass__(cls) -> None:
        # add_implicit_resolvers(cls, cls.RESOLVERS)
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


class AppLoader(LoaderBase):
    Dumper = AppDumper
    PATTERN_ENV = re.compile(r"\$\{(.*)\}")
    RESOLVERS = {"!env_var": PATTERN_ENV}

    @classmethod
    @constructor("!env_var")
    def constructor_env_var(cls, loader, node):
        value = loader.construct_scalar(node)

        matched = cls.PATTERN_ENV.match(value)
        if matched is None:
            return value
        proto = matched.group(1)
        return EvalStr(proto)

    @classmethod
    @constructor("!ref")
    def constructor_ref(cls, loader, node):
        value = loader.construct_scalar(node)
        if value is None:
            value = ""
        return RefStr(value)

    @classmethod
    @constructor("!call")
    def constructor_call(cls, loader, node):
        value = loader.construct_scalar(node)
        if value is None:
            value = ""
        return TypeStr(value)
