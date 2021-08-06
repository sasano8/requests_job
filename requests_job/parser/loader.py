import os
import re

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
# 解析によりタグが付与され、タグにマッチするconstructorが呼び出されます。

# construct
# ノードをデータに変換します。

##################
# Dumper
##################

# represent(resolver)
# データをノードにに変換します。

# serialize
# ノードをイベントに変換します。

# present(emit)
# イベントを文字列します。


class AppDumper(yaml.Dumper):
    pass


def constructor(tag):
    def wrapper(func):
        func.__constructor__ = tag
        return func

    return wrapper


class LoaderBase(yaml.Loader):
    Dumper = AppDumper

    def __init_subclass__(cls) -> None:
        cls._add_implicit_resolvers()
        cls._add_constructors()

    RESOLVERS = {}  # type: ignore

    @classmethod
    def _add_implicit_resolvers(cls):
        for tag, regexp in cls.RESOLVERS.items():
            yaml.add_implicit_resolver(
                tag=tag,
                regexp=regexp,
                first=None,
                Loader=cls,
                Dumper=cls.Dumper,
            )

    @classmethod
    def _add_constructors(cls):
        iterator = (getattr(cls, x) for x in dir(cls))
        funcs = [x for x in iterator if hasattr(x, "__constructor__")]
        for func in funcs:
            yaml.add_constructor(tag=func.__constructor__, constructor=func, Loader=cls)


class AppLoader(LoaderBase):
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

        default = None
        if len(proto.split(":")) > 1:
            env_key, default = proto.split(":")
        else:
            env_key = proto
        env_val = os.environ.get(env_key, default)

        try:
            env_val = float(env_val)  # type: ignore
        except:
            pass

        return env_val


class Parser:
    # __loader__ = yaml.SafeLoader
    __loader__ = AppLoader

    @classmethod
    def parse_file(cls, path: str, loader=None):
        with open(path, "r") as f:
            content = f.read()

        return cls.parse_str(content, loader=loader)

    @classmethod
    def parse_str(cls, content: str, loader=None):
        import yaml

        loader = loader or cls.__loader__
        return yaml.load(content, Loader=loader)

    @classmethod
    def dump(cls, data, Dumper=None, **kwargs):
        Dumper = Dumper or cls.__loader__.Dumper
        return yaml.dump(data, Dumper=Dumper, **kwargs)
