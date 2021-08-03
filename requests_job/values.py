from pathlib import Path
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
    no_type_check,
)

from pydantic import BaseModel, Field, FilePath
from pydantic import HttpUrl
from pydantic import HttpUrl as HttpUrlBase
from pydantic import PrivateAttr, validator
from pydantic.generics import GenericModel
from pydantic.utils import update_not_none
from requests.auth import HTTPBasicAuth, HTTPDigestAuth, HTTPProxyAuth

HTTP_BASIC_AUTH = "HTTPBasicAuth"
HTTP_DIGEST_AUTH = "HTTPDigestAuth"
HTTP_PROXY_AUTH = "HTTPProxyAuth"

auth_types = {
    HTTP_BASIC_AUTH: HTTPBasicAuth,
    HTTP_DIGEST_AUTH: HTTPDigestAuth,
    HTTP_PROXY_AUTH: HTTPProxyAuth,
}

T = TypeVar("T")


class Undefined:
    pass


undefined = Undefined()


class ValueObject(GenericModel, Generic[T]):
    __root__: T

    def __init__(self, __root__: T):
        super().__init__(__root__=__root__)
        self.__post_init__()

    def __post_init__(self):
        pass

    @property
    def value(self) -> T:
        return self.__root__

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))

    @validator("__root__")
    def __validate__(cls, v):
        errors = cls.check(v)
        if errors:
            if isinstance(errors, str):
                raise ValueError(errors)
            else:
                raise ValueError(list(errors))
        return v

    @classmethod
    def check(cls, v) -> Union[None, Any]:
        pass

    @classmethod
    def is_valid(cls, v) -> bool:
        try:
            cls.__validate__(v)
            return True
        except:
            return False


class Alias(ValueObject[str]):
    block_words: ClassVar[set] = {":", ",", "-", "/"}

    @classmethod
    def check(cls, v: str):
        if not v:
            raise ValueError("value is empty.")

        for block_word in cls.block_words:
            if block_word in v:
                raise ValueError(f"can not contains '{block_word}' in value.")


class AttrInfo(BaseModel):
    module_name: str
    attr_name: str
    module: Any
    attr: Any = None

    def raise_if_not_valid(self):
        messages = []
        if self.module is None or self.module is undefined:
            messages.append(f"{self.module_name}: is not exists.")

        if self.attr is None:
            messages.append(f"{self.attr_name}: is none.")

        if self.attr is undefined:
            messages.append(f"{self.attr_name}: is not exists.")

        if err := " ".join(messages):
            raise ValueError(f"{self.module_name}:{self.attr_name} - " + err)


class AttrPath(ValueObject[str]):
    """<module or package>:<attr>"""

    @property
    def value(self):
        return self.get_module_attr(self.__root__)

    @classmethod
    def check(cls, v: str):
        cls.get_module_attr(v)

    @classmethod
    def get_module_attr_or_none(cls, v):
        try:
            return cls.get_module_attr(v)
        except ValueError:
            return None

    @classmethod
    def get_module_attr(cls, v):
        module_name, attr_name = cls.split_module_attr(v)

        from importlib import import_module

        try:
            module = import_module(module_name)
        except ModuleNotFoundError:
            module = None

        if module:
            attr = getattr(module, attr_name, undefined)
        else:
            attr = undefined

        result = AttrInfo(
            module_name=module_name, module=module, attr_name=attr_name, attr=attr
        )
        result.raise_if_not_valid()
        return result

    @classmethod
    def split_module_attr(cls, v):
        if not isinstance(v, str):
            raise TypeError(f"{v} is {type(v)}. A value must be str.")

        if not v:
            raise ValueError("value is empty.")

        if v.count(":") != 1:
            raise ValueError(
                f"'{v}' is invalid format. <module or package>:<attribute>"
            )

        arr = v.split(":")
        module_name, attr_name = arr
        return module_name, attr_name


class FString(ValueObject[str]):
    _keywords: set = PrivateAttr(set())

    def __post_init__(self):
        self._keywords = self._extract_keywords(self.__root__)

    @property
    def keywords(self):
        return self._keywords

    def pull_kwargs(self, kwargs: dict):
        """対象の辞書から有効なキーのみ取り出す。"""
        if kwargs is None:
            return {}
        return {k: v for k, v in kwargs.items()}

    def format(self, **kwargs):
        """str.formatの結果を返す。f-stringに渡すキーワード引数が足りない場合は例外が発生する。認識しないキーワード引数は無視される。"""
        try:
            result = self.__root__.format(**kwargs)
        except KeyError as e:
            required = {k for k in self.keywords if k not in kwargs}
            raise ValueError(f"required kwargs: {required}")
        return result

    def format_as(self, kwargs: dict, default=None, ignore_extra=True):
        dic = self._create_kwargs(kwargs, default=default, ignore_extra=ignore_extra)
        return self.format(**dic)

    def _create_kwargs(self, kwargs: dict, default=None, ignore_extra=True):
        dic = {x: default for x in self._keywords}
        if ignore_extra:
            includes = {k: v for k, v in kwargs.items() if k in dic}
        else:
            includes = {k: v for k, v in kwargs.items()}
        dic.update(includes)
        return dic

    @staticmethod
    def _extract_keywords(s: str):
        import re

        res = re.findall(r"\{.*?\}", s)
        keywords = set()
        for x in res:
            a = x.replace("{", "")
            b = a.replace("}", "")
            keywords.add(b)
        return keywords


class Instance(BaseModel):
    type: Union[Alias, AttrPath]
    args: Union[Tuple, None] = None
    kwargs: Union[Dict[str, Any], None] = None

    def get_value(self, context=None):
        if isinstance(self.type, Alias):
            raise NotImplementedError()
        elif isinstance(self.type, AttrPath):
            cls = self.type.value.attr
        else:
            raise Exception()

        args = self.args or []  # type: ignore
        kwargs = self.kwargs or {}
        return cls(*args, **kwargs)


class Auth(Instance):
    pass


class Cert(Instance):
    pass


class Transport(Instance):
    pass


class Verify(BaseModel):
    __root__: Union[str, bool, Instance] = True

    def __init__(self, __root__):
        super().__init__(__root__=__root__)

    def get_value(self, context=None):
        if isinstance(self.__root__, (str, bool)):
            return self.__root__
        elif isinstance(self.__root__, Instance):
            return self.get_value(context=context)
        else:
            raise TypeError()


class File(BaseModel):
    key: str
    name: Optional[str] = None
    path: FilePath
    media_type: Optional[str] = None
    exist: bool = Field(True, description="ファイルが途中で作成される場合など、事前検証を無効化できます")

    @validator("path")
    def exists_file(cls, v, values):
        if isinstance(v, HttpUrl):
            # web上のファイルを落として、そのままアップロードできればいいなぁ
            raise NotImplementedError()
        elif isinstance(v, Path):
            pass
        else:
            raise ValueError(f"Unkown type: {v} => {type(v)}")

        if values.get("exist", True) and not v.exists():
            raise ValueError("not exists file.")

        return v

    def get_value(self, context=None):
        builder = [self.key]

        if self.name is not None:
            builder.append(self.name)

        builder.append(open(self.path, "rb"))  # type: ignore

        if self.media_type is not None:
            builder.append(self.media_type)

        return tuple(builder)


class MultiFile(BaseModel):
    __root__: List[File] = []

    def get_value(self, context=None):
        files = [x.get_value(context) for x in self.__root__]
        return files

    # files = {'upload_file': ('foobar.txt', open('file.txt','rb'), 'text/x-spam')}

    # https://datatracker.ietf.org/doc/html/rfc1867
    # files = {'upload-file': open('report.xls', 'rb')}
    # httpx.post("https://httpbin.org/post", files=files)

    # https://datatracker.ietf.org/doc/html/rfc1867
    # files = {'upload-file': ('report.xls', open('report.xls', 'rb'), 'application/vnd.ms-excel')}
    # httpx.post("https://httpbin.org/post", files=files)

    # files = [('file', open('report.xls', 'rb')), ('file', open('report2.xls', 'rb'))]
    # httpx.post("https://httpbin.org/post", files=files)

    # files = {'file1': open('report.xls', 'rb'), 'file2': open('otherthing.txt', 'rb')}
    # httpx.post("https://httpbin.org/post", files=files)

    # マルチパートフォームにデータフィールドを含める場合はdataを利用する
    # data = {'message': 'Hello, world!'}
    # files = {'file': open('report.xls', 'rb')}
    # httpx.post("https://httpbin.org/post", data=data, files=files)
