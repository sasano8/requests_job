from typing import Any, Mapping, Sequence, Union

from httpx import Response

from .values import undefined

JSON = Mapping[str, Any]
JsonTypes = Union[None, str, int, float, bool, Mapping, list]


class ObjectWrapper(JSON):
    __name__ = None

    def __init__(self, response: Response):
        self.target = self.get_target(response)

    def get_target(self, response: Response):
        return getattr(response, self.__name__)

    def __getitem__(self, key):
        value = getattr(self.target, key, undefined)
        value = self.jsonalize(value)
        return value

    @staticmethod
    def jsonalize(value):
        if isinstance(value, str):  # strはシーケンスなので先に評価する
            return value
        if isinstance(value, Mapping):
            return value
        elif isinstance(value, Sequence):
            return value
        elif isinstance(value, (None, int, float, bool)):
            return value
        elif value is undefined:
            return value
        else:
            raise Exception()
