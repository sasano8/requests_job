from json.decoder import JSONDecodeError


class AppException(Exception):
    pass


class DuplicateKeyError(KeyError):
    def __init__(self, keys):
        super().__init__(keys)


class ValidationError(AppException):
    def __init__(self, msg="", loc=""):
        self.msg = msg or ""
        self.loc = loc = f"{loc} == " if loc else ""
        super().__init__(f"{loc}{msg}")


class FailJSONDecode(ValidationError):
    def __init__(self, msg="", loc=""):
        super().__init__(msg, loc)

    @classmethod
    def create(cls, msg="", loc="", doc=""):
        return cls(msg + " => \n" + doc, loc)


class TypeMismatch(ValidationError):
    def __init__(self, actual, expect, loc=""):
        super().__init__(f"{actual} != {expect}", loc)


class ValueMismatch(ValidationError):
    def __init__(self, actual, expect, loc=""):
        super().__init__(f"{actual} != {expect}", loc)


class SizeMismatch(ValidationError):
    def __init__(self, actual: int, expect: int, loc=""):
        super().__init__(f"{actual} != {expect}", loc)
