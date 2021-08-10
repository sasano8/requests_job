import yaml

from .loader import AppDumper, AppLoader

__all__ = [
    "Parser",
    "AppLoader",
    "AppDumper",
    "parse_file",
    "parse_str",
    "dump",
]


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
        Dumper = Dumper or cls.__loader__.Dumper
        return yaml.dump(data, Dumper=Dumper, **kwargs)


parse_file = Parser.parse_file
parse_str = Parser.parse_str
dump = Parser.dump
