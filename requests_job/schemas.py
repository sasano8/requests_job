from datetime import date, datetime
from functools import lru_cache
from typing import Any, Dict, Iterator, List, Literal, Set, Union

from pydantic import Field, FilePath, root_validator, validator
from pydantic.typing import Annotated as _

from .abc import BaseModel
from .utils import merge, merge_objects
from .values import (
    Alias,
    AttrPath,
    Auth,
    Cert,
    File,
    FString,
    MultiFile,
    Transport,
    Verify,
)

JsonTypes = Union[None, str, int, float, bool, dict, list]
YamlTypes = Union[None, str, int, float, bool, dict, list, datetime, date]


class Limits(BaseModel):
    max_connections: int
    max_keepalive_connections: int


class Extension(BaseModel):
    aliases: Dict[Alias, AttrPath] = {}


class ClientRequestCommon:
    __fields__ = {"params", "headers", "cookies"}

    # https://www.python-httpx.org/advanced/#merging-of-configuration
    # params, headers, cookiesは結合される
    # それ以外は上書き
    # merge戦略として、上記３つのNoneはNoneで上書きせずに無視する

    # paramsは
    # http://sample.com/{id}
    # にparamsを埋め込まない

    # マージは基本的にupdate方式

    @classmethod
    def merge_params(cls, obj1: Union[dict, None], obj2: Union[dict, None]):
        return merge(obj1, obj2)

    @classmethod
    def merge_headers(cls, obj1: Union[dict, None], obj2: Union[dict, None]):
        return merge(obj1, obj2)

    @classmethod
    def merge_cookies(cls, obj1: Union[dict, None], obj2: Union[dict, None]):
        return merge(obj1, obj2)


class EventHooks(BaseModel):
    """リクエストとレスポンスをトリガーします。
    例外を上げると後続のイベントフックは実行されません。
    """

    build_request: Union[List[AttrPath], None] = Field(
        None, description="想定しているリクエストが構成されない場合、リクエストを書き換えることができます。"
    )
    request: Union[List[AttrPath], None] = Field(None, description="リクエスト時にトリガーされます。")
    response: Union[List[AttrPath], None] = Field(
        None, description="応答時にトリガーされます。通信エラーの場合は、トリガーされません。"
    )
    expect: Union[List[AttrPath], None] = None
    success: Union[List[AttrPath], None] = None
    error: Union[List[AttrPath], None] = None
    complete: Union[List[AttrPath], None] = None
    exception: Union[List[AttrPath], None] = None
    asgi_startup: Union[List[AttrPath], None] = Field(
        None, description="asgiアプリケーションの起動前にトリガーされ、アプリケーションのインスタンスにアクセスすることができます"
    )
    asgi_shutdown: Union[List[AttrPath], None] = Field(
        None, description="asgiアプリケーションの終了後にトリガーされ、アプリケーションのインスタンスにアクセスすることができます"
    )


class Client(BaseModel):
    # fmt: off
    auth: Union[Auth, None] = None
    params: Union[Dict[str, Any], None] = None
    headers: Union[Dict[str, Any], None] = None
    cookies: Union[Dict[str, str], None] = None
    verify: Union[Verify, None] = Verify(True)
    cert: Union[Cert, None] = None
    http1: bool = True
    http2: bool = False
    proxies: _[Dict[str, str], Field(description="[httpx]HTTPX supports setting up HTTP proxies")] = {}
    # mounts
    timeout: _[float, Field(description="[httpx]You can specify the timeout in seconds.")] = 5.0
    limits: _[Limits, Field(description="[httpx]You can control the connection pool size.")] = Limits(max_connections=100, max_keepalive_connections=20)
    max_redirects: int = 20
    event_hooks: EventHooks = EventHooks()
    base_url: str = ""
    transport: Union[Transport, None] = None
    app: _[Union[AttrPath, None], Field(description="[httpx]An ASGI application to send requests to, rather than sending actual network requests.")] = None
    trust_env: _[bool, Field(description="[httpx]HTTPX supports .netrc file.")] = True
    # fmt: on

    @validator("event_hooks")
    def invalid_events(cls, v: EventHooks):
        if v.asgi_startup or v.asgi_shutdown:
            raise ValueError(
                "asgi_startup or asgi_shutdown cannot be configured at the client level."
            )
        return v


class Request(BaseModel):
    url: FString = FString("")
    method: Literal["GET", "POST", "PATCH", "PUT", "DELETE"] = "GET"
    params: Union[Dict[str, Any], None] = None
    # pydanticがjsonを予約しているので、エイリアスを使う
    json_: Union[Dict[str, Any], None] = Field(
        None, alias="json", description="Content-Type: application/jsonとしてデータを送信します"
    )
    content: Union[str, None] = None
    data: Union[Dict[str, Any], None] = None
    files: Union[MultiFile, None] = None
    headers: Union[Dict[str, Any], None] = None
    cookies: Union[Dict[str, Any], None] = None
    auth: Union[Auth, None] = None
    allow_redirects: bool = True
    timeout: Union[float, None] = None

    @validator("method", pre=True)
    def upper_method(cls, v):
        if isinstance(v, str):
            return v.upper()
        else:
            return v


class Response(BaseModel):
    pass


class Task(Request, Extension):
    name: str = ""
    kwargs: Union[Dict[str, Any], None] = Field(
        None,
        description="url(f-string)にキーワードを渡せます。存在しないキーワードはparams(query parameter)として解釈されます。",
    )
    event_hooks: EventHooks = Field(
        EventHooks(), description="httpxと異なり、リクエストレベルでフックを設定できます。"
    )
    expect: Union[Dict[str, Any], None]
    tags: Set[str] = set()

    @root_validator
    def merge_kwargs(cls, values):
        url: FString = values["url"]
        kwargs = values.get("kwargs", {})
        params = values.get("params", None)
        if not url.keywords and params is None and kwargs is None:
            return values

        pulled_kwargs = url.pull_kwargs(kwargs)

        try:
            new_url = url.format(**pulled_kwargs)
        except ValueError as e:
            raise

        additional_params = {k: v for k, v in kwargs.items() if k not in pulled_kwargs}
        new_params = merge(params, additional_params)

        values["url"] = FString(new_url)
        values["params"] = new_params
        values.pop("kwargs", None)
        return values

    @staticmethod
    @lru_cache
    def _include_fields():
        includes = set(Extension.__fields__) | set(["event_hooks"])
        excludes = ClientRequestCommon.__fields__
        return frozenset(includes ^ excludes)

    def merge_parent(self, parent: "Job"):
        fields = self._include_fields()
        job_setting = parent.dict(include=fields)
        exclude = ClientRequestCommon.__fields__
        # exclude.pop("")
        task_setting = self.dict(exclude_unset=True, by_alias=True, exclude=exclude)
        merged = merge_objects(job_setting, task_setting)

        if self.url.keywords:
            kwargs = self.kwargs or {}
            params = self.params or {}
            keywords = {k: v for k, v in kwargs.items()}
            params = {k: v for k, v in kwargs.items() if k not in keywords}
            url = self.url.format(**keywords)
        else:
            params = merge(self.params, self.kwargs)
        return Task(**merged)

    def build_request_args(self, exclude_unset: bool = True):
        fields = set(Request.__fields__)
        dic = self.dict(
            include=fields,
            exclude={"event_hooks", "auth", "files"},
            exclude_none=True,
            by_alias=True,
        )
        dic["event_hooks"] = self._get_event_hooks()
        dic["auth"] = self._get_auth()
        self._attache_files(dic)
        return dic

    def _get_auth(self):
        if self.auth:
            return self.auth.get_value()
        else:
            return None

    def _attache_files(self, dic: dict):
        if not self.files:
            dic.pop("files", None)
            return

        if isinstance(self.files, File):
            dic["files"] = self.files.get_value()
        elif isinstance(self.files, MultiFile):
            dic["files"] = self.files.get_value()
        else:
            raise Exception()

    def _get_event_hooks(self):
        events = self.event_hooks
        event_hooks = {
            "build_request": events.build_request or [],
            "request": events.request or [],
            "response": events.response or [],
            "expect": events.expect or [],
            "success": events.success or [],
            "error": events.error or [],
            "complete": events.complete or [],
            "exception": events.exception or [],
            # "startup": events.startup or [],
            # "shutdown": events.shutdown or [],
        }
        keys = set(event_hooks)
        for key in keys:
            event_hooks[key] = [x.value.attr for x in event_hooks[key]]

        return event_hooks


class Job(Client, Extension):
    name: str
    nodes: List[Task] = Field([], alias="tasks")
    tags: Set[str] = set()

    @property
    def tasks(self) -> Iterator[Task]:
        for task in self.nodes:
            yield task.merge_parent(self)

    @staticmethod
    @lru_cache
    def _include_fields():
        includes = set(Extension.__fields__) | set(Client.__fields__)
        excludes = ClientRequestCommon.__fields__
        return frozenset(includes ^ excludes)

    def merge_parent(self, parent: "Profile"):
        fields = self._include_fields()
        root_setting = parent.dict(include=fields)
        job_setting = self.dict(
            exclude_unset=True, by_alias=True, exclude=ClientRequestCommon.__fields__
        )
        merged = merge_objects(root_setting, job_setting)
        merged["params"] = ClientRequestCommon.merge_params(parent.params, self.params)
        merged["headers"] = ClientRequestCommon.merge_headers(
            parent.headers, self.headers
        )
        merged["cookies"] = ClientRequestCommon.merge_cookies(
            parent.cookies, self.cookies
        )
        return Job(**merged)

    def build_client_args(self, exclude_unset: bool = True):
        fields = set(Client.__fields__)
        dic = self.dict(
            include=fields,
            exclude={"event_hooks", "auth", "app", "cert", "transport"},
            exclude_unset=exclude_unset,
        )
        self._build_limits(dic)
        self._build_app(dic)
        dic["auth"] = self._get_auth()
        dic["transport"] = self._get_transport()
        dic["cert"] = self._get_cert()
        # dic["event_hooks"] = self._get_event_hooks()

        return dic

    # def _get_event_hooks(self):
    #     events = self.event_hooks
    #     event_hooks = {
    #         "build_request": events.request or [],
    #         "request": events.request or [],
    #         "response": events.response or [],
    #         "expect": events.expect or [],
    #         "success": events.success or [],
    #         "error": events.error or [],
    #         "complete": events.complete or [],
    #         "exception": events.exception or [],
    #         # "startup": events.startup or [],
    #         # "shutdown": events.shutdown or [],
    #     }
    #     keys = set(event_hooks)
    #     for key in keys:
    #         event_hooks[key] = [x.value.attr for x in event_hooks[key]]

    #     return event_hooks

    def _build_app(self, kwargs: dict):
        if self.app:
            kwargs["app"] = self.app.value.attr
        else:
            kwargs.pop("app", None)

    @staticmethod
    def _build_limits(kwargs: dict):
        if limits := kwargs.get("limits", None):
            from httpx import Limits as _Limits

            kwargs["limits"] = _Limits(**limits)

    def _get_transport(self):
        if self.transport:
            return self.transport.get_value()
        else:
            return None

    def _get_auth(self):
        if self.auth:
            return self.auth.get_value()
        else:
            return None

    def _get_cert(self):
        if self.cert:
            return self.cert.get_value()
        else:
            return None


class Profile(Client, Extension):
    version: Literal[0] = 0
    name: str = ""
    nodes: List[Job] = Field([], alias="jobs")
    tags: Set[str] = {"minutes", "hour", "daily", "month"}

    @property
    def jobs(self) -> Iterator[Job]:
        for job in self.nodes:
            yield job.merge_parent(self)


import httpx


async def func():
    async with httpx.AsyncClient() as client:
        client.request()
