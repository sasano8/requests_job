from typing import Callable, Optional, Tuple, Union

import httpx
from asgi_lifespan import LifespanManager as _LifespanManager
from pydantic import validate_arguments

from .values import AttrPath

unfefined = object()


class LifespanManager(_LifespanManager):
    manager = set()  # type: ignore

    async def __aenter__(self):
        if self.app in self.manager:
            raise RuntimeError("Application is already running")
        self.manager.add(self.app)
        return await super().__aenter__()

    async def __aexit__(self, exc_type, exc, tb):
        try:
            self.manager.remove(self.app)
        except:
            pass
        return await super().__aexit__(exc_type, exc, tb)


class ASGITransportLifespan(httpx.ASGITransport):
    def __init__(
        self,
        app: Union[str, Callable],
        raise_app_exceptions: bool = False,
        root_path: str = unfefined,  # type: ignore
        client: Tuple[str, int] = unfefined,  # 一般的には0をbindするとOSが自動でポートを割り当てる
        startup_timeout: Optional[float] = 60 * 5,
        shutdown_timeout: Optional[float] = 60 * 10,
    ):
        app, attr_path = self.get_app(app)
        kwargs = dict(
            app=app,
            raise_app_exceptions=raise_app_exceptions,
            root_path=root_path,
            client=client,
        )
        kwargs = {k: v for k, v in kwargs.items() if v is not unfefined}
        super().__init__(**kwargs)  # type: ignore

        self.startup_timeout = startup_timeout
        self.shutdown_timeout = shutdown_timeout
        self.lifespan: LifespanManager = None  # type: ignore

    @staticmethod
    @validate_arguments
    def validate(
        app: Union[AttrPath, Callable],
        raise_app_exceptions: bool = False,
        root_path: str = unfefined,  # type: ignore
        client: Tuple[str, int] = unfefined,  # 一般的には0をbindするとOSが自動でポートを割り当てる
        startup_timeout: Optional[float] = 60 * 5,
        shutdown_timeout: Optional[float] = 60 * 10,
    ):
        pass

    @classmethod
    def get_app(cls, app):
        if isinstance(app, str):
            return AttrPath(app).value.attr, app
        else:
            return app, None

    async def __aenter__(self):
        if self.lifespan:
            raise RuntimeError("Application is already running")

        lifespan = LifespanManager(
            self.app,
            startup_timeout=self.startup_timeout,
            shutdown_timeout=self.shutdown_timeout,
        )

        await lifespan.__aenter__()
        self.lifespan = lifespan
        await super().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        lifespan = self.lifespan
        self.lifespan = None  # type: ignore
        try:
            await lifespan.__aexit__(exc_type, exc, tb)
        finally:
            pass

        return await super().__aexit__(exc_type, exc, tb)

    async def handle_async_request(self, *args, **kwargs):
        if self.lifespan is None:
            raise RuntimeError("app is not running.")
        return await super().handle_async_request(*args, **kwargs)
