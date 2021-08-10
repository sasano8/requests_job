from itertools import chain
from json.decoder import JSONDecodeError
from typing import List

from httpx import Response

from .exceptions import (
    AppException,
    FailJSONDecode,
    SizeMismatch,
    TypeMismatch,
    ValidationError,
    ValueMismatch,
)
from .types import undefined

# class Undefined:
#     singlton = None

#     def __init__(self):
#         if self.singlton is not None:
#             raise Exception("Undefined is singleton.")
#         self.__class__.singlton = self

#     def __str__(self):
#         return "undefined"

#     def __eq__(self, o: object) -> bool:
#         if self is o:
#             return True
#         else:
#             return False


# undefined = Undefined()


class LocationObject:
    def __init__(self, root_name):
        self.stack = []
        if root_name:
            self.push_key(root_name)

    def push_index(self, index: int):
        if not isinstance(index, int):
            raise TypeError()
        self.stack.append(index)

    def push_key(self, key):
        self.stack.append([key])

    def pop(self):
        return self.stack.pop()

    def __iter__(self):
        for item in self.stack:
            if isinstance(item, int):
                yield f"[{item}]"
            else:
                key = item[0]
                yield key

    def __str__(self):
        return ".".join(self.__iter__())


def compare(actual, expect, root_name=None):
    loc = LocationObject(root_name)

    try:
        yield from compare_value(actual, expect, loc)
    except Exception as e:
        raise AppException(f"{loc} => {e}")


def compare_value(actual, expect, loc):
    if isinstance(actual, ValidationError):
        yield actual.__class__(actual.msg, loc=loc)
        return
    # print(str(loc))
    if not is_same_type(actual, expect):
        yield TypeMismatch(actual, expect, loc)
        return

    if isinstance(expect, dict):
        yield from compare_dict(actual, expect, loc)
        return
    if isinstance(expect, list):
        yield from compare_list(actual, expect, loc)
        return
    else:
        if not actual == expect:
            yield ValueMismatch(actual, expect, loc)
            return


def compare_dict(actual, expect, loc: LocationObject):
    for key in expect:
        value_expect = expect.get(key, undefined)
        value_actual = actual.get(key, undefined)
        loc.push_key(key)
        yield from compare_value(value_actual, value_expect, loc)
        loc.pop()


def compare_list(actual, expect, loc: LocationObject):
    if not len(actual) == len(expect):
        yield SizeMismatch(len(actual), len(expect), loc)
        return

    for i in range(len(expect)):
        value_actual = actual[i]
        value_expect = expect[i]

        loc.push_index(i)
        yield from compare_value(value_actual, value_expect, loc)
        loc.pop()


def is_same_type(actual, expect):
    if not isinstance(actual, expect.__class__):
        if isinstance(actual, (int, float)):
            if isinstance(expect, (int, float)):
                return True
            else:
                return False
        else:
            return False

    return True


class GetterBase:
    def __init_subclass__(cls, **kwargs):
        attrs = [x for x in dir(cls) if x.startswith("get_")]
        names = {x.lstrip("get_"): x for x in attrs}
        functions = {k: getattr(cls, v) for k, v in names.items()}
        cls.getters = functions  # type: ignore

    @classmethod
    def create_actual(cls, res, expect: dict):
        actual = {}
        getters = cls.getters
        for key in expect:
            getter = getters.get(key, None)
            if getter:
                actual[key] = getter(res)
            else:
                actual[key] = undefined

        return actual


class Getter(GetterBase):
    @staticmethod
    def get_status_code(res):
        return res.status_code

    @staticmethod
    def get_json(res):
        try:
            value = res.json()
        except JSONDecodeError as e:
            value = FailJSONDecode.create(str(e), doc=res.text)
            return value

    @staticmethod
    def get_headers(res):
        return {k.lower(): v.lower() for k, v in res.headers.items()}

    @staticmethod
    def get_http_version(res):
        return res.http_version

    @staticmethod
    def get_reason_phrase(res):
        return res.reason_phrase

    @staticmethod
    def get_url(res):
        url = res.url
        if url:
            return dict(
                url=str(url),
                # authority=url.authority,
                host=url.host,
                port=url.port,
                path=url.path,
                query=url.query,
            )
        else:
            return url

    @staticmethod
    def get_content(res):
        return res.content

    @staticmethod
    def get_text(res):
        return res.text

    @staticmethod
    def get_encoding(res):
        return res.encoding

    @staticmethod
    def get_charset_encoding(res):
        return res.charset_encoding

    @staticmethod
    def get_is_error(res):
        return res.is_error

    @staticmethod
    def get_is_redirect(res):
        return res.is_redirect

    @staticmethod
    def get_cookies(res):
        return res.cookies

    @staticmethod
    def get_links(res):
        return res.links

    @staticmethod
    def get_num_bytes_downloaded(res):
        return res.num_bytes_downloaded

    @staticmethod
    def get_request(res):
        return res.request

    @staticmethod
    def get_extensions(res):
        return res.extensions

    @staticmethod
    def get_history(res):
        return res.history

    @staticmethod
    def get_elapsed(res):
        elapsed = res.elapsed
        return {
            "total_seconds": elapsed.total_seconds(),
            "min": elapsed.min,
            "max": elapsed.max,
            "days": elapsed.days,
            "microseconds": elapsed.microseconds,
            "resolution": elapsed.resolution,
            "seconds": elapsed.seconds,
        }

    @staticmethod
    def get_raise_for_status(res):
        try:
            res.raise_for_status()
            return False
        except:
            return True


class Verifier:
    __getter__ = Getter

    def __init__(self, expect):
        self.expect = expect

    def __call__(self, res: Response):
        expect = self.expect
        actual = Getter.create_actual(res, self.expect)

        errors: List[Exception] = []
        for err in compare(actual, expect, "response"):
            errors.append(err)

        for err in errors:
            print(f"{err.__class__.__name__}: {err}")
