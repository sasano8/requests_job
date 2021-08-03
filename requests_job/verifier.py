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


class Undefined:
    singlton = None

    def __init__(self):
        if self.singlton is not None:
            raise Exception("Undefined is singleton.")
        self.singlton = self

    def __str__(self):
        return "undefined"

    def __eq__(self, o: object) -> bool:
        if self is o:
            return True
        else:
            return False


undefined = Undefined()


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


class Verifier:
    def __init__(self, expect):
        self.expect = expect

    def __call__(self, res: Response):
        errors: List[Exception] = []
        expect = self.expect
        actual = {}

        if "status_code" in expect:
            actual["status_code"] = res.status_code

        if "json" in expect:
            try:
                actual["json"] = res.json()
            except JSONDecodeError as e:
                actual["json"] = FailJSONDecode.create(str(e), doc=res.text)

        if "headers" in expect:
            actual["headers"] = dict(
                {k.lower(): v.lower() for k, v in res.headers.items()}
            )

        if "http_version" in expect:
            actual["http_version"] = res.http_version

        if "reason_phrase" in expect:
            actual["reason_phrase"] = res.reason_phrase

        if "url" in expect:
            actual["url"] = res.url

        if "content" in expect:
            actual["content"] = res.content

        if "text" in expect:
            actual["text"] = res.text

        if "encoding" in expect:
            actual["encoding"] = res.encoding

        if "charset_encoding" in expect:
            actual["charset_encoding"] = res.charset_encoding

        if "is_error" in expect:
            actual["is_error"] = res.is_error

        if "is_redirect" in expect:
            actual["is_redirect"] = res.is_redirect

        if "cookies" in expect:
            actual["cookies"] = dict(res.cookies)

        if "links" in expect:
            actual["links"] = res.links

        if "num_bytes_downloaded" in expect:
            actual["num_bytes_downloaded"] = res.num_bytes_downloaded

        if "request" in expect:
            actual["request"] = res.request

        if "extensions" in expect:
            actual["extensions"] = res.extensions

        if "elapsed" in expect:
            actual["elapsed"] = res.elapsed

        if "raise_for_status" in expect:
            try:
                res.raise_for_status()
                actual["raise_for_status"] = False
            except:
                actual["raise_for_status"] = True

        for err in compare(actual, expect, "response"):
            errors.append(err)

        for err in errors:
            print(f"{err.__class__.__name__}: {err}")
