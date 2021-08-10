import re

from .sandbox import EvalStr
from .yaml import LoaderBase, constructor


class RefStr(str):
    pass


class TypeStr(str):
    pass


PATTERN_EVAL = re.compile(r"\$\{(.*)\}")


class AppLoader(LoaderBase):
    # Dumper = None
    # PATTERN_ENV = re.compile(r"\$\{(.*)\}")
    RESOLVERS = {"!env_var": PATTERN_EVAL}

    @classmethod
    @constructor("!env_var")
    def constructor_env_var(cls, loader, node):
        value = loader.construct_scalar(node)

        matched = PATTERN_EVAL.match(value)
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


class Parser:
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
        import yaml

        Dumper = Dumper or cls.__loader__.Dumper
        return yaml.dump(data, Dumper=Dumper, **kwargs)
