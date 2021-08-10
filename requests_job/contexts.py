from types import MappingProxyType

from .values import undefined


class Env(dict):
    def __init__(self):
        from os import environ

        self.environ = environ

    def __getitem__(self, k):
        value = self.get(k, undefined)
        if value is undefined:
            return self.environ.get(k, None)


def Context():
    return MappingProxyType({"env": Env(), "cache": {}})
